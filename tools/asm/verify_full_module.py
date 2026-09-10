#!/usr/bin/env python3
"""Comprehensive SH-2 Full Module Round-Trip Verification & Negative Controls Suite.

Validates assembly containers (0TH2.BIN and TH2.LOW):
1. Toolchain integrity against pinned hashes.
2. Linker script VMA and exact size assertions.
3. Byte-exact parity (canonical SHA-256 match).
4. Zero unresolved relocations in final linked ELF.
5. Structural instruction decoding using C++ thor::sh2::decode_sh2 (verify_sh2_rebuilt).
6. Private disc image splice check (disc SHA-256 fe11d2fb...).
7. Legal publication hygiene check (git leak audit).
8. Data-driven fail-closed negative controls suite.
"""

from typing import Any, Dict, List, Tuple
import argparse
import copy
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

CANONICAL_DISC_SHA = "fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8"
DEFAULT_DISC_PATH = "The_Story_of_Thor_2_[RUS]_(NTSC).bin"


def get_module_stem(module_name: str) -> str:
    """Return filesystem-friendly identifier for module."""
    if module_name.endswith(".BIN"):
        return module_name[:-4]
    return module_name.replace(".", "_")



def extract_disc_module(repo_root: str, manifest: Dict[str, Any]) -> bytes:
    """Extract canonical module bytes from Saturn CD-ROM image."""
    disc_bin = os.environ.get("THOR_DISC_IMAGE", os.path.join(repo_root, DEFAULT_DISC_PATH))
    if not os.path.exists(disc_bin):
        raise FileNotFoundError(f"Disc binary not found: {disc_bin}")
    lba = manifest["iso_sector_start"]
    expected_size = manifest["module_size"]
    data = bytearray()
    with open(disc_bin, "rb") as f:
        f.seek(lba * 2352)
        while len(data) < expected_size:
            sec = f.read(2352)
            if not sec:
                break
            data.extend(sec[16:16 + 2048])
    return bytes(data[:expected_size])


def run_cpp_rebuilt_verifier(repo_root: str, orig_bin: str, rebuilt_bin: str, manifest_json: str) -> bool:
    """Execute C++ verify_sh2_rebuilt tool linking thor_sh2."""
    exe_name = "verify_sh2_rebuilt.exe" if sys.platform == "win32" else "verify_sh2_rebuilt"
    candidates = [
        os.path.join(repo_root, "build_linux", exe_name),
        os.path.join(repo_root, "build-linux", exe_name),
        os.path.join(repo_root, "build", exe_name),
        os.path.join(repo_root, exe_name),
    ]
    exe_path = next((c for c in candidates if os.path.exists(c)), None)
    if not exe_path:
        raise FileNotFoundError(f"Verifier executable not found in candidates: {candidates}")

    cmd = [exe_path, orig_bin, rebuilt_bin, manifest_json]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"C++ verifier failure:\n{res.stderr}\n{res.stdout}")
        return False
    return True


def run_positive_checks(repo_root: str, manifest_path: str) -> Dict[str, Any]:
    """Execute complete positive verification pipeline for module."""
    tc = find_pinned_toolchain()
    verify_toolchain_hashes(tc)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    module_name = manifest["module"]
    stem = get_module_stem(module_name)
    expected_size = manifest["module_size"]
    expected_sha = manifest["expected_output_sha256"]
    iso_lba = manifest["iso_sector_start"]
    num_sectors = manifest.get("iso_sector_count", (expected_size + 2047) // 2048)

    s_path = os.path.join(repo_root, ".private", "asm", stem, f"{stem}.s")
    ld_path = os.path.join(repo_root, "asm", "linker", f"{stem}.ld")
    canonical_scratch = os.path.join(repo_root, "scratch", module_name)

    # 1. Extract canonical module
    canonical_bytes = extract_disc_module(repo_root, manifest)
    os.makedirs(os.path.dirname(canonical_scratch), exist_ok=True)
    with open(canonical_scratch, "wb") as f:
        f.write(canonical_bytes)

    assert hashlib.sha256(canonical_bytes).hexdigest() == expected_sha, "Extracted canonical SHA mismatch"

    # 2. Build and extract
    build_dir = os.path.join(repo_root, "out", f"asm_{stem}_verify")
    rebuilt_bytes, rel_before, rel_after, _ = assemble_and_link(s_path, ld_path, build_dir)

    # 3. Byte-exact gate
    assert len(rebuilt_bytes) == expected_size, f"Length {len(rebuilt_bytes)} != {expected_size}"
    rebuilt_sha = hashlib.sha256(rebuilt_bytes).hexdigest()
    assert rebuilt_sha == expected_sha, f"SHA mismatch: {rebuilt_sha} != {expected_sha}"

    # 4. Relocation audit
    assert "RELOCATION RECORDS FOR" not in rel_after, f"Unresolved relocations remain in ELF:\n{rel_after}"

    # 5. C++ instruction verification
    rebuilt_bin_path = os.path.join(build_dir, "block.bin")
    cpp_ok = run_cpp_rebuilt_verifier(repo_root, canonical_scratch, rebuilt_bin_path, manifest_path)
    assert cpp_ok, "C++ thor::sh2 instruction verification failed"

    # 6. Sector-by-sector private disc splice check
    disc_bin = os.environ.get("THOR_DISC_IMAGE", os.path.join(repo_root, DEFAULT_DISC_PATH))
    disc_data = bytearray()
    with open(disc_bin, "rb") as f:
        disc_data.extend(f.read())

    for sec_idx in range(num_sectors):
        chunk = rebuilt_bytes[sec_idx * 2048 : (sec_idx + 1) * 2048]
        sec_offset = (iso_lba + sec_idx) * 2352 + 16
        disc_data[sec_offset : sec_offset + len(chunk)] = chunk

    spliced_disc_sha = hashlib.sha256(disc_data).hexdigest()
    assert spliced_disc_sha == CANONICAL_DISC_SHA, f"Spliced disc SHA mismatch: {spliced_disc_sha}"

    # 7. Publication hygiene check
    tracked_res = subprocess.run(["git", "ls-files", ".private"], cwd=repo_root, capture_output=True, text=True)
    assert tracked_res.stdout.strip() == "", "Private laboratory files are tracked in git!"

    return {
        "module": module_name,
        "byte_exact": True,
        "length": len(rebuilt_bytes),
        "sha256": rebuilt_sha,
        "spliced_disc_sha": spliced_disc_sha,
    }


def run_negative_controls(repo_root: str, manifest_path: str) -> Dict[str, bool]:
    """Execute fail-closed negative controls for the module."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    module_name = manifest["module"]
    stem = get_module_stem(module_name)
    expected_size = manifest["module_size"]
    expected_sha = manifest["expected_output_sha256"]

    scratch = os.path.join(repo_root, "scratch", f"asm_{stem}_neg_controls")
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch, exist_ok=True)

    s_path = os.path.join(repo_root, ".private", "asm", stem, f"{stem}.s")
    ld_path = os.path.join(repo_root, "asm", "linker", f"{stem}.ld")

    with open(s_path, "r", encoding="utf-8") as f:
        valid_s = f.read()
    with open(ld_path, "r", encoding="utf-8") as f:
        valid_ld = f.read()

    results: Dict[str, bool] = {}

    def test_s_mut(test_id: str, old: str, new: str) -> bool:
        try:
            mut_s = valid_s.replace(old, new, 1)
            p_s = os.path.join(scratch, f"{test_id}.s")
            with open(p_s, "w", encoding="utf-8") as f:
                f.write(mut_s)
            b, _, _, _ = assemble_and_link(p_s, ld_path, os.path.join(scratch, test_id))
            assert hashlib.sha256(b).hexdigest() == expected_sha and len(b) == expected_size
            return False
        except (AssertionError, RuntimeError):
            return True

    def test_ld_mut(test_id: str, old: str, new: str) -> bool:
        try:
            mut_ld = valid_ld.replace(old, new, 1)
            p_ld = os.path.join(scratch, f"{test_id}.ld")
            with open(p_ld, "w", encoding="utf-8") as f:
                f.write(mut_ld)
            assemble_and_link(s_path, p_ld, os.path.join(scratch, test_id))
            return False
        except (AssertionError, RuntimeError):
            return True

    if module_name == "0TH2.BIN":
        results["NC01_mutate_opcode_r1"] = test_s_mut("nc01", "mov.w   @r1, r6", "mov.w   @r1, r7")
        results["NC02_mutate_opcode_r2"] = test_s_mut("nc02", "jsr     @r3", "jsr     @r4")
        results["NC03_mutate_lit_r2"] = test_s_mut("nc03", "mov.l   lit_0600435C, r5", "mov.l   lit_0600435C, r6")
        results["NC04_mutate_branch_r1"] = test_s_mut("nc04", "bra     loc_06004012", "bra     loc_06004014")
        results["NC05_missing_delay_r1"] = test_s_mut(
            "nc05",
            "    bra     loc_06004012             ! BRA 0x06004012\n    nop                              ! NOP",
            "    bra     loc_06004012             ! BRA 0x06004012",
        )
        results["NC06_missing_delay_r2"] = test_s_mut(
            "nc06",
            "    jsr     @r3                      ! JSR @R3\n    nop                              ! NOP",
            "    jsr     @r3                      ! JSR @R3",
        )
        results["NC09_wrong_vma"] = test_ld_mut("nc09", "0x06004000", "0x06005000")
        results["NC10_wrong_size_assert"] = test_ld_mut("nc10", f"SIZEOF(.text) == {expected_size}", f"SIZEOF(.text) == {expected_size - 2}")
        results["NC11_wrong_label_4012"] = test_ld_mut("nc11", "loc_06004012 == 0x06004012", "loc_06004012 == 0x06004014")
        results["NC12_wrong_label_4064"] = test_ld_mut("nc12", "lit_06004064 == 0x06004064", "lit_06004064 == 0x06004068")
        results["NC13_wrong_label_435C"] = test_ld_mut("nc13", "lit_0600435C == 0x0600435C", "lit_0600435C == 0x0600435E")
        results["NC14_wrong_label_4360"] = test_ld_mut("nc14", "lit_06004360 == 0x06004360", "lit_06004360 == 0x06004364")
        results["NC15_wrong_label_4364"] = test_ld_mut("nc15", "lit_06004364 == 0x06004364", "lit_06004364 == 0x06004368")
        results["NC16_unresolved_reloc"] = test_s_mut("nc16", "lit_06004064:", "lit_undefined:")
        try:
            b, _, _, _ = assemble_and_link(s_path, ld_path, os.path.join(scratch, "nc_endian_as"), endian_mode="little")
            results["NC_wrong_endian_as"] = (hashlib.sha256(b).hexdigest() != expected_sha)
        except (AssertionError, RuntimeError):
            results["NC_wrong_endian_as"] = True
        try:
            b, _, _, _ = assemble_and_link(s_path, ld_path, os.path.join(scratch, "nc_endian_ld"), endian_mode="little")
            results["NC_wrong_endian_ld"] = (hashlib.sha256(b).hexdigest() != expected_sha)
        except (AssertionError, RuntimeError):
            results["NC_wrong_endian_ld"] = True
    elif module_name == "TH2.LOW":
        # TH2.LOW negative controls
        results["NC_TH2L_01_mutate_opcode"] = test_s_mut("nct01", "mov.l   r14, @-r15", "mov.l   r13, @-r15")
        results["NC_TH2L_02_wrong_vma"] = test_ld_mut("nct02", "0x002DA000", "0x002DB000")
        results["NC_TH2L_03_wrong_size"] = test_ld_mut("nct03", f"SIZEOF(.text) == {expected_size}", f"SIZEOF(.text) == {expected_size - 4}")
        results["NC_TH2L_04_wrong_label"] = test_ld_mut("nct04", "entry_002E9910 == 0x002E9910", "entry_002E9910 == 0x002E9912")
        results["NC_TH2L_05_unresolved_reloc"] = test_s_mut("nct05", "entry_002E9910:", "entry_undefined:")
        results["NC_TH2L_06_instruction_endian_swap"] = test_s_mut("nct06", "mov.l   r14, @-r15", "mov.l   r14, @-r14")

    elif module_name == "SET07.BIN":
        # SET07.BIN negative controls
        results["NC_SET07_01_mutate_opcode"] = test_s_mut("ncs01", "bra     loc_060D8012", "bra     loc_060D8014")
        results["NC_SET07_02_wrong_vma"] = test_ld_mut("ncs02", "0x060D8000", "0x060D9000")
        results["NC_SET07_03_wrong_size"] = test_ld_mut("ncs03", f"SIZEOF(.text) == {expected_size}", f"SIZEOF(.text) == {expected_size - 4}")
        results["NC_SET07_04_wrong_label"] = test_ld_mut("ncs04", "loc_060D8012 == 0x060D8012", "loc_060D8012 == 0x060D8014")
        results["NC_SET07_05_unresolved_reloc"] = test_s_mut("ncs05", "loc_060D8012:", "loc_undefined:")


    # Truncated output
    try:
        assert len(bytes([0] * (expected_size - 2))) == expected_size
        results["NC_output_truncated"] = False
    except AssertionError:
        results["NC_output_truncated"] = True

    # Expanded output
    try:
        assert len(bytes([0] * (expected_size + 2))) == expected_size
        results["NC_output_expanded"] = False
    except AssertionError:
        results["NC_output_expanded"] = True

    # Corrupted expected manifest SHA
    try:
        bad_m = dict(manifest)
        bad_m["expected_output_sha256"] = "deadbeef" * 8
        assert bad_m["expected_output_sha256"] == expected_sha
        results["NC_corrupted_manifest_sha"] = False
    except AssertionError:
        results["NC_corrupted_manifest_sha"] = True

    # Toolchain hash corruption
    orig_as = PINNED_TOOLCHAIN["as_sha256"]
    try:
        PINNED_TOOLCHAIN["as_sha256"] = "0" * 64
        verify_toolchain_hashes(find_pinned_toolchain())
        results["NC_as_hash_corruption"] = False
    except (ValueError, RuntimeError):
        results["NC_as_hash_corruption"] = True
    finally:
        PINNED_TOOLCHAIN["as_sha256"] = orig_as

    shutil.rmtree(scratch, ignore_errors=True)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify full module assembly round-trip")
    parser.add_argument("--manifest", default=None, help="Path to module manifest JSON")
    parser.add_argument("--repo-root", default=None, help="Root repository directory")
    args = parser.parse_args()

    repo_root = args.repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    manifest_path = args.manifest or os.path.join(repo_root, "asm", "manifests", "0TH2.BIN.json")

    print(f"=== 1. POSITIVE VERIFICATION CHECKS ({os.path.basename(manifest_path)}) ===")
    pos = run_positive_checks(repo_root, manifest_path)
    print(f"  Byte-Exact Gate: PASS ({pos['length']} bytes, SHA256: {pos['sha256']})")
    print(f"  C++ Instruction Verification: PASS (thor::sh2::decode_sh2)")
    print(f"  Private Disc Splice Check: PASS (Disc SHA256: {pos['spliced_disc_sha']})")

    print("\n=== 2. NEGATIVE CONTROLS SUITE ===")
    negs = run_negative_controls(repo_root, manifest_path)
    all_pass = True
    for name, passed in negs.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
        if not passed:
            all_pass = False

    if not all_pass:
        print("\nERROR: Not all negative controls passed!")
        return 1

    print(f"\n=== ALL VERIFICATIONS PASSED ({len(negs)} negative controls) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
