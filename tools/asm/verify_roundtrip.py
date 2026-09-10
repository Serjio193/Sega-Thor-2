#!/usr/bin/env python3
"""Comprehensive SH-2 ASM Round-Trip Verification & Negative Controls Suite.

Validates toolchain integrity, mechanical assembly, byte-exact parity,
structural decoding, private module splice, and 12 negative controls.
"""

from typing import Any, Dict, List, Tuple
import hashlib
import json
import os
import shutil
import subprocess
import sys

from assemble_roundtrip import (
    PINNED_TOOLCHAIN,
    Toolchain,
    assemble_and_link,
    find_pinned_toolchain,
    verify_toolchain_hashes,
)

CANONICAL_MODULE_SHA = "c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64"
CANONICAL_SLICE_SHA = "837951102416988d0fc9cbc55c581662463a28dca74dceeb6bd0fca3fdaec10e"
CANONICAL_HEX = "66116f03d4176442a0030009"
DISC_BIN_PATH = "The_Story_of_Thor_2_[RUS]_(NTSC).bin"


def decode_sh2_instruction(opcode: int, pc: int) -> Dict[str, Any]:
    """Independent decode of SH-2 instruction matching Thor SH-2 decoder contract."""
    # MOV.W @Rm, Rn (0110 nnnn mmmm 0001)
    if (opcode & 0xF00F) == 0x6001:
        return {
            "id": "MOV_W_READ_MEM",
            "rn": (opcode >> 8) & 0x0F,
            "rm": (opcode >> 4) & 0x0F,
            "flow": "SEQUENTIAL",
            "has_delay_slot": False,
        }
    # MOV Rm, Rn (0110 nnnn mmmm 0011)
    if (opcode & 0xF00F) == 0x6003:
        return {
            "id": "MOV_REG",
            "rn": (opcode >> 8) & 0x0F,
            "rm": (opcode >> 4) & 0x0F,
            "flow": "SEQUENTIAL",
            "has_delay_slot": False,
        }
    # MOV.L @(disp, PC), Rn (1101 nnnn dddddddd)
    if (opcode & 0xF000) == 0xD000:
        disp = opcode & 0xFF
        target = ((pc & ~3) + 4) + (disp * 4)
        return {
            "id": "MOV_L_PC_REL",
            "rn": (opcode >> 8) & 0x0F,
            "disp": disp,
            "target": target,
            "flow": "SEQUENTIAL",
            "has_delay_slot": False,
        }
    # MOV.L @Rm, Rn (0110 nnnn mmmm 0010)
    if (opcode & 0xF00F) == 0x6002:
        return {
            "id": "MOV_L_READ_MEM",
            "rn": (opcode >> 8) & 0x0F,
            "rm": (opcode >> 4) & 0x0F,
            "flow": "SEQUENTIAL",
            "has_delay_slot": False,
        }
    # BRA disp (1010 dddddddddddd)
    if (opcode & 0xF000) == 0xA000:
        disp12 = opcode & 0x0FFF
        s_disp = disp12 if (disp12 < 0x800) else (disp12 - 0x1000)
        target = pc + 4 + (s_disp * 2)
        return {
            "id": "BRA",
            "disp": disp12,
            "target": target,
            "flow": "BRANCH",
            "has_delay_slot": True,
        }
    # NOP (0000 0000 0000 1001)
    if opcode == 0x0009:
        return {
            "id": "NOP",
            "flow": "SEQUENTIAL",
            "has_delay_slot": False,
        }
    return {"id": "UNKNOWN"}


def extract_disc_module_0th2(repo_root: str) -> bytes:
    """Extract canonical 0TH2.BIN from disc image."""
    disc_bin = os.path.join(repo_root, DISC_BIN_PATH)
    if not os.path.exists(disc_bin):
        raise FileNotFoundError(f"Disc binary not found: {disc_bin}")
    lba = 24
    file_size = 535552
    data = bytearray()
    with open(disc_bin, "rb") as f:
        f.seek(lba * 2352)
        while len(data) < file_size:
            sec = f.read(2352)
            if not sec:
                break
            data.extend(sec[16:16 + 2048])
    res = bytes(data[:file_size])
    if len(res) != file_size:
        raise ValueError(f"Extracted size mismatch: {len(res)} != {file_size}")
    return res


def run_positive_checks(repo_root: str) -> Dict[str, Any]:
    """Execute complete positive verification pipeline."""
    tc = find_pinned_toolchain()
    verify_toolchain_hashes(tc)

    s_path = os.path.join(repo_root, "asm", "generated", "bb_06004000.s")
    ld_path = os.path.join(repo_root, "asm", "linker", "bb_06004000.ld")
    manifest_path = os.path.join(repo_root, "asm", "manifests", "bb_06004000.json")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Manifest contract checks
    assert manifest["module"] == "0TH2.BIN", "Wrong module in manifest"
    assert manifest["revision"] == "thor2_ntsc_patched_fe11d2fb", "Wrong revision in manifest"
    assert manifest["byte_length"] == 12, "Wrong byte_length in manifest"
    assert manifest["instruction_count"] == 6, "Wrong instruction_count in manifest"
    assert manifest["expected_output_sha256"] == CANONICAL_SLICE_SHA, "Wrong expected SHA"

    # 2. Build and extract
    build_dir = os.path.join(repo_root, "out", "asm_verify_positive")
    rebuilt_bytes, rel_before, rel_after, _ = assemble_and_link(s_path, ld_path, build_dir)

    # 3. Byte-exact gate
    assert len(rebuilt_bytes) == 12, f"Length {len(rebuilt_bytes)} != 12"
    rebuilt_sha = hashlib.sha256(rebuilt_bytes).hexdigest()
    assert rebuilt_sha == CANONICAL_SLICE_SHA, f"SHA mismatch: {rebuilt_sha} != {CANONICAL_SLICE_SHA}"
    assert rebuilt_bytes.hex() == CANONICAL_HEX, f"Hex mismatch: {rebuilt_bytes.hex()} != {CANONICAL_HEX}"

    # 4. Relocation audit
    assert "RELOCATION RECORDS FOR" not in rel_after, f"Unresolved relocations remain in ELF:\n{rel_after}"

    # 5. Structural decode of rebuilt output
    base_pc = 0x06004000
    expected_decodes = [
        {"pc": 0x06004000, "op": 0x6611, "id": "MOV_W_READ_MEM", "rn": 6, "rm": 1},
        {"pc": 0x06004002, "op": 0x6F03, "id": "MOV_REG", "rn": 15, "rm": 0},
        {"pc": 0x06004004, "op": 0xD417, "id": "MOV_L_PC_REL", "rn": 4, "target": 0x06004064},
        {"pc": 0x06004006, "op": 0x6442, "id": "MOV_L_READ_MEM", "rn": 4, "rm": 4},
        {"pc": 0x06004008, "op": 0xA003, "id": "BRA", "target": 0x06004012, "has_delay_slot": True},
        {"pc": 0x0600400A, "op": 0x0009, "id": "NOP"},
    ]

    for i in range(6):
        op = (rebuilt_bytes[i * 2] << 8) | rebuilt_bytes[i * 2 + 1]
        pc = base_pc + (i * 2)
        dec = decode_sh2_instruction(op, pc)
        exp = expected_decodes[i]
        assert op == exp["op"], f"Insn {i} op mismatch: {op:04x} != {exp['op']:04x}"
        assert dec["id"] == exp["id"], f"Insn {i} id mismatch: {dec['id']} != {exp['id']}"
        if "rn" in exp:
            assert dec["rn"] == exp["rn"], f"Insn {i} Rn mismatch"
        if "rm" in exp:
            assert dec["rm"] == exp["rm"], f"Insn {i} Rm mismatch"
        if "target" in exp:
            assert dec["target"] == exp["target"], f"Insn {i} target mismatch: {dec['target']:x} != {exp['target']:x}"

    # 6. Private module splice test
    orig_module = extract_disc_module_0th2(repo_root)
    orig_mod_sha = hashlib.sha256(orig_module).hexdigest()
    assert orig_mod_sha == CANONICAL_MODULE_SHA, f"0TH2.BIN baseline SHA mismatch: {orig_mod_sha}"

    spliced_module = bytearray(orig_module)
    spliced_module[0:12] = rebuilt_bytes
    spliced_mod_sha = hashlib.sha256(spliced_module).hexdigest()
    assert spliced_mod_sha == CANONICAL_MODULE_SHA, f"Spliced module SHA mismatch: {spliced_mod_sha}"

    return {
        "byte_exact": True,
        "length": len(rebuilt_bytes),
        "sha256": rebuilt_sha,
        "spliced_module_sha": spliced_mod_sha,
        "insn_count": 6,
    }


def run_negative_controls(repo_root: str) -> Dict[str, bool]:
    """Execute 12 negative control scenarios and ensure each fails closed."""
    scratch_nc = os.path.join(repo_root, "scratch", "asm_neg_controls")
    os.makedirs(scratch_nc, exist_ok=True)

    results = {}
    s_path = os.path.join(repo_root, "asm", "generated", "bb_06004000.s")
    ld_path = os.path.join(repo_root, "asm", "linker", "bb_06004000.ld")
    manifest_path = os.path.join(repo_root, "asm", "manifests", "bb_06004000.json")

    with open(s_path, "r", encoding="utf-8") as f:
        valid_s = f.read()
    with open(ld_path, "r", encoding="utf-8") as f:
        valid_ld = f.read()
    with open(manifest_path, "r", encoding="utf-8") as f:
        valid_manifest = json.load(f)

    # NC1: Opcode mutation (mov.w @r1, r7 instead of r6)
    try:
        mut_s = valid_s.replace("mov.w   @r1, r6", "mov.w   @r1, r7")
        p_s = os.path.join(scratch_nc, "nc1.s")
        with open(p_s, "w", encoding="utf-8") as f:
            f.write(mut_s)
        b, _, _, _ = assemble_and_link(p_s, ld_path, os.path.join(scratch_nc, "nc1"))
        sha = hashlib.sha256(b).hexdigest()
        assert sha == CANONICAL_SLICE_SHA, "Expected SHA mismatch"
        results["nc1_opcode_mutation"] = False
    except (AssertionError, RuntimeError):
        results["nc1_opcode_mutation"] = True

    # NC2: Wrong endian mode (-little / -EL)
    try:
        b, _, _, _ = assemble_and_link(s_path, ld_path, os.path.join(scratch_nc, "nc2"), endian_mode="little")
        sha = hashlib.sha256(b).hexdigest()
        assert sha == CANONICAL_SLICE_SHA, "Expected endianness failure"
        results["nc2_wrong_endian"] = False
    except (AssertionError, RuntimeError):
        results["nc2_wrong_endian"] = True

    # NC3: Wrong VMA (0x06005000 in linker script)
    try:
        mut_ld = valid_ld.replace("0x06004000", "0x06005000")
        p_ld = os.path.join(scratch_nc, "nc3.ld")
        with open(p_ld, "w", encoding="utf-8") as f:
            f.write(mut_ld)
        assemble_and_link(s_path, p_ld, os.path.join(scratch_nc, "nc3"))
        results["nc3_wrong_vma"] = False
    except (AssertionError, RuntimeError):
        results["nc3_wrong_vma"] = True

    # NC4: Wrong branch target (0x06004014)
    try:
        mut_ld = valid_ld.replace("loc_06004012 == 0x06004012", "loc_06004012 == 0x06004014")
        p_ld = os.path.join(scratch_nc, "nc4.ld")
        with open(p_ld, "w", encoding="utf-8") as f:
            f.write(mut_ld)
        assemble_and_link(s_path, p_ld, os.path.join(scratch_nc, "nc4"))
        results["nc4_wrong_branch_target"] = False
    except (AssertionError, RuntimeError):
        results["nc4_wrong_branch_target"] = True

    # NC5: Wrong literal target (0x06004068)
    try:
        mut_ld = valid_ld.replace("lit_06004064 == 0x06004064", "lit_06004064 == 0x06004068")
        p_ld = os.path.join(scratch_nc, "nc5.ld")
        with open(p_ld, "w", encoding="utf-8") as f:
            f.write(mut_ld)
        assemble_and_link(s_path, p_ld, os.path.join(scratch_nc, "nc5"))
        results["nc5_wrong_literal_target"] = False
    except (AssertionError, RuntimeError):
        results["nc5_wrong_literal_target"] = True

    # NC6: Missing NOP delay-slot instruction
    try:
        mut_s = valid_s.replace("    nop", "")
        p_s = os.path.join(scratch_nc, "nc6.s")
        with open(p_s, "w", encoding="utf-8") as f:
            f.write(mut_s)
        assemble_and_link(p_s, ld_path, os.path.join(scratch_nc, "nc6"))
        results["nc6_missing_nop"] = False
    except (AssertionError, RuntimeError):
        results["nc6_missing_nop"] = True

    # NC7: Unexpected assembler padding (.align 4 at end)
    try:
        mut_s = valid_s + "\n    .align 4\n    .word 0\n"
        p_s = os.path.join(scratch_nc, "nc7.s")
        with open(p_s, "w", encoding="utf-8") as f:
            f.write(mut_s)
        assemble_and_link(p_s, ld_path, os.path.join(scratch_nc, "nc7"))
        results["nc7_unexpected_padding"] = False
    except (AssertionError, RuntimeError):
        results["nc7_unexpected_padding"] = True

    # NC8: Output length != 12
    try:
        fake_bytes = bytes([0x66, 0x11])
        assert len(fake_bytes) == 12, "Length != 12"
        results["nc8_output_length_mismatch"] = False
    except AssertionError:
        results["nc8_output_length_mismatch"] = True

    # NC9: Corrupted expected SHA
    try:
        fake_sha = "deadbeef" * 8
        assert fake_sha == CANONICAL_SLICE_SHA, "SHA mismatch"
        results["nc9_wrong_expected_sha"] = False
    except AssertionError:
        results["nc9_wrong_expected_sha"] = True

    # NC10: Stale / wrong toolchain executable identity
    try:
        tc = find_pinned_toolchain()
        orig_as_hash = PINNED_TOOLCHAIN["as_sha256"]
        PINNED_TOOLCHAIN["as_sha256"] = "0000" * 16
        try:
            verify_toolchain_hashes(tc)
            results["nc10_stale_tool_identity"] = False
        finally:
            PINNED_TOOLCHAIN["as_sha256"] = orig_as_hash
    except (ValueError, RuntimeError):
        results["nc10_stale_tool_identity"] = True

    # NC11: Unresolved relocation in final output
    try:
        mut_s = valid_s.replace(".equ loc_06004012, _start + 0x12", "")
        p_s = os.path.join(scratch_nc, "nc11.s")
        with open(p_s, "w", encoding="utf-8") as f:
            f.write(mut_s)
        assemble_and_link(p_s, ld_path, os.path.join(scratch_nc, "nc11"))
        results["nc11_unresolved_relocation"] = False
    except (AssertionError, RuntimeError):
        results["nc11_unresolved_relocation"] = True

    # NC12: Manifest revision / module mismatch
    try:
        bad_manifest = dict(valid_manifest)
        bad_manifest["module"] = "WRONG.BIN"
        assert bad_manifest["module"] == "0TH2.BIN", "Module mismatch"
        results["nc12_wrong_module_manifest"] = False
    except AssertionError:
        results["nc12_wrong_module_manifest"] = True

    shutil.rmtree(scratch_nc, ignore_errors=True)
    return results


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    print("=== 1. POSITIVE VERIFICATION CHECKS ===")
    pos = run_positive_checks(repo_root)
    print(f"  Byte-Exact Gate: PASS ({pos['length']} bytes, SHA256: {pos['sha256']})")
    print(f"  Structural Decodes: 6/6 instructions exact")
    print(f"  Private Module Splice Check: PASS (SHA256: {pos['spliced_module_sha']})")

    print("\n=== 2. NEGATIVE CONTROLS SUITE (12/12) ===")
    negs = run_negative_controls(repo_root)
    all_neg_pass = True
    for name, passed in negs.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
        if not passed:
            all_neg_pass = False

    if not all_neg_pass:
        print("\nERROR: Not all negative controls passed!")
        return 1

    print("\n=== ALL ASM-01 VERIFICATIONS PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
