#!/usr/bin/env python3
"""Manifest-Driven Lossless Assembly Container Generator.

Mechanically generates:
1. Private assembly container (.private/asm/{STEM}/{STEM}.s) with proven code
   emitted as real SH-2 mnemonics and RAW_UNKNOWN emitted as .byte directives.
2. Linker script (asm/linker/{STEM}.ld) asserting VMA and exact module size.
"""

from typing import Any, Dict, List, Set, Tuple
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

DEFAULT_DISC_PATH = "The_Story_of_Thor_2_[RUS]_(NTSC).bin"


def get_module_stem(module_name: str) -> str:
    """Return filesystem-friendly identifier for module."""
    if module_name.endswith(".BIN"):
        return module_name[:-4]
    return module_name.replace(".", "_")



def extract_module_from_disc(repo_root: str, manifest: Dict[str, Any]) -> bytes:
    """Extract canonical module bytes from Saturn CD-ROM image."""
    disc_path = os.environ.get("THOR_DISC_IMAGE", os.path.join(repo_root, DEFAULT_DISC_PATH))
    if not os.path.exists(disc_path):
        raise FileNotFoundError(f"Disc image not found: {disc_path}")

    lba = manifest["iso_sector_start"]
    expected_size = manifest["module_size"]
    expected_sha = manifest["expected_output_sha256"]

    data = bytearray()
    with open(disc_path, "rb") as f:
        f.seek(lba * 2352)
        while len(data) < expected_size:
            sec = f.read(2352)
            if not sec:
                break
            data.extend(sec[16:16 + 2048])

    module_bytes = bytes(data[:expected_size])
    if len(module_bytes) != expected_size:
        raise ValueError(f"Extracted size mismatch: {len(module_bytes)} != {expected_size}")
    actual_sha = hashlib.sha256(module_bytes).hexdigest()
    if actual_sha != expected_sha:
        raise ValueError(f"Module SHA mismatch: {actual_sha} != {expected_sha}")
    return module_bytes


def run_cpp_ir_exporter(
    repo_root: str,
    module_bin_path: str,
    base_vma: int,
    proven_ranges: List[Dict[str, Any]],
    ir_out_path: str,
) -> Dict[str, Any]:
    """Execute C++ export_sh2_asm_ir tool to obtain Thor-decoder-backed IR."""
    exe_name = "export_sh2_asm_ir.exe" if sys.platform == "win32" else "export_sh2_asm_ir"
    candidates = [
        os.path.join(repo_root, "build-linux", exe_name),
        os.path.join(repo_root, "build", exe_name),
        os.path.join(repo_root, exe_name),
    ]
    exe_path = next((c for c in candidates if os.path.exists(c)), None)
    if not exe_path:
        raise FileNotFoundError(f"IR exporter executable not found in candidates: {candidates}")

    os.makedirs(os.path.dirname(os.path.abspath(ir_out_path)), exist_ok=True)
    range_args = []
    for r in proven_ranges:
        blk_id = r.get("block_id") or f"blk_{r['offset_start']:06X}"
        range_args.append(f"{r['runtime_start']}:{r['runtime_end_exclusive']}:{blk_id}")

    cmd = [
        exe_path,
        os.path.abspath(module_bin_path),
        f"0x{base_vma:08X}",
        os.path.abspath(ir_out_path),
    ] + range_args

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"C++ IR exporter failed:\n{res.stderr}\n{res.stdout}")

    with open(ir_out_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_label_vma(label_name: str, base_vma: int, module_size: int) -> int:
    """Infer VMA from label name suffix if formatted like *_06004012."""
    match = re.search(r"([0-9A-Fa-f]{8})$", label_name)
    if match:
        return int(match.group(1), 16)
    return 0


def generate_assembly(
    module_bytes: bytes,
    manifest: Dict[str, Any],
    ir_data: Dict[str, Any],
    out_s_path: str,
) -> None:
    """Generate private lossless assembly file."""
    os.makedirs(os.path.dirname(os.path.abspath(out_s_path)), exist_ok=True)

    module_name = manifest["module"]
    stem = get_module_stem(module_name)
    base_vma = int(manifest["module_runtime_base"], 0)
    module_size = manifest["module_size"]

    labels_by_offset: Dict[int, List[str]] = {}

    # 1. Labels from IR exporter
    for l in ir_data.get("labels", []):
        offset = l["offset"]
        labels_by_offset.setdefault(offset, []).append(l["name"])

    # 2. Labels from manifest
    for lbl in manifest.get("labels", []):
        vma = parse_label_vma(lbl, base_vma, module_size)
        if base_vma <= vma < base_vma + module_size:
            offset = vma - base_vma
            if lbl not in labels_by_offset.get(offset, []):
                labels_by_offset.setdefault(offset, []).append(lbl)

    blocks_by_offset: Dict[int, Dict[str, Any]] = {}
    for b in ir_data.get("blocks", []):
        start_vma = int(b["start_vma"], 0)
        offset = start_vma - base_vma
        blocks_by_offset[offset] = b

    # Map ranges from manifest
    ranges_by_start: Dict[int, Dict[str, Any]] = {
        r["offset_start"]: r for r in manifest.get("ranges", [])
    }

    all_globals = ["_start"]
    for offset_lbls in labels_by_offset.values():
        for lbl in offset_lbls:
            if lbl not in all_globals:
                all_globals.append(lbl)

    lines: List[str] = [
        "! ==============================================================================",
        f"! The Story of Thor 2 (Saturn) — {module_name} Lossless Assembly Container",
        f"! Revision: {manifest['revision']}",
        f"! Base VMA: 0x{base_vma:08X} | Size: {module_size} bytes (0x{module_size:05X})",
        "! Toolchain target: GNU assembler (binutils-sh-elf 2.40+2)",
        "! Mechanically generated by tools/asm/generate_full_module_asm.py",
        "! DO NOT COMMIT THIS FILE (Contains full commercial binary payload)",
        "! ==============================================================================",
        "",
        '    .section .text, "ax"',
    ]
    for g in all_globals:
        lines.append(f"    .global {g}")

    lines.extend([
        "",
        "_start:",
    ])

    offset = 0
    total_len = len(module_bytes)

    while offset < total_len:
        # 1. Emit labels at current offset
        if offset in labels_by_offset:
            for lbl in labels_by_offset[offset]:
                if lbl != "_start":
                    lines.append(f"{lbl}:")

        # 2. Check if proven MNEMONIC code starts here
        if offset in blocks_by_offset:
            blk = blocks_by_offset[offset]
            blk_id = blk.get("block_id", f"bb_{base_vma + offset:08X}")
            lines.append(f"! --- CONFIRMED_CODE: {blk_id} (VMA 0x{base_vma + offset:08X}) ---")
            for insn in blk["instructions"]:
                lines.append(f"    {insn['asm_line']:<32} ! {insn['comment']}")
            offset += blk["byte_length"]
            continue

        # 3. Check if RAW_CODE_PENDING_DECODE range
        rng = ranges_by_start.get(offset)
        if rng and rng.get("assembly_representation") == "RAW_CODE_PENDING_DECODE":
            end_off = rng["offset_end_exclusive"]
            lines.append(f"! --- CONFIRMED_CODE (RAW_CODE_PENDING_DECODE: VMA 0x{base_vma + offset:08X}) ---")
            for cur_off in range(offset, end_off, 2):
                b0 = module_bytes[cur_off]
                b1 = module_bytes[cur_off + 1]
                lines.append(f"    .byte   0x{b0:02X}, 0x{b1:02X} ! opcode 0x{(b0 << 8) | b1:04X}")
            offset = end_off
            continue

        # 4. Emit RAW_UNKNOWN / RAW_DATA byte directives
        next_boundary = total_len
        for b_off in blocks_by_offset:
            if b_off > offset and b_off < next_boundary:
                next_boundary = b_off
        for l_off in labels_by_offset:
            if l_off > offset and l_off < next_boundary:
                next_boundary = l_off
        for r_off in ranges_by_start:
            if r_off > offset and r_off < next_boundary:
                next_boundary = r_off

        chunk_len = min(16, next_boundary - offset)
        chunk = module_bytes[offset:offset + chunk_len]
        byte_str = ", ".join(f"0x{b:02X}" for b in chunk)
        lines.append(f"    .byte   {byte_str}")
        offset += chunk_len

    lines.append("")
    lines.append(f"    .global _end_{stem}")
    lines.append(f"_end_{stem}:")
    lines.append("")

    with open(out_s_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"Generated Assembly: {out_s_path} ({len(lines)} lines)")


def generate_linker_script(manifest: Dict[str, Any], ir_data: Dict[str, Any], out_ld_path: str) -> None:
    """Generate linker script with address and size assertions."""
    os.makedirs(os.path.dirname(os.path.abspath(out_ld_path)), exist_ok=True)

    module_name = manifest["module"]
    base_vma = int(manifest["module_runtime_base"], 0)
    module_size = manifest["module_size"]

    assertions: List[str] = [
        f'    ASSERT(ADDR(.text) == 0x{base_vma:08X}, "VMA of .text must be 0x{base_vma:08X}")',
        f'    ASSERT(SIZEOF(.text) == {module_size}, "Size of .text must be exactly {module_size} bytes")',
    ]
    seen_labels: Set[str] = set()

    for lbl in ir_data.get("labels", []):
        name = lbl["name"]
        vma = lbl["vma"]
        if name not in seen_labels:
            seen_labels.add(name)
            assertions.append(f'    ASSERT({name} == {vma}, "{name} address mismatch")')

    for lbl in manifest.get("labels", []):
        if lbl not in seen_labels:
            vma = parse_label_vma(lbl, base_vma, module_size)
            if vma != 0:
                seen_labels.add(lbl)
                assertions.append(f'    ASSERT({lbl} == 0x{vma:08X}, "{lbl} address mismatch")')

    ld_content = f"""/* Linker script for {module_name} lossless assembly container */
OUTPUT_FORMAT("elf32-sh")
OUTPUT_ARCH(sh:sh2)
ENTRY(_start)

SECTIONS
{{
    . = 0x{base_vma:08X};

    .text : {{
        _text_start = .;
        *(.text)
        *(.text.*)
        _text_end = .;
    }}

{chr(10).join(assertions)}

    /DISCARD/ : {{
        *(.comment)
        *(.note.*)
    }}
}}
"""
    with open(out_ld_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(ld_content)
    print(f"Generated Linker Script: {out_ld_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Lossless Assembly Container")
    parser.add_argument("--manifest", default=None, help="Path to module manifest JSON")
    parser.add_argument("--repo-root", default=None, help="Root repository directory")
    args = parser.parse_args()

    repo_root = args.repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    manifest_path = args.manifest or os.path.join(repo_root, "asm", "manifests", "0TH2.BIN.json")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    module_name = manifest["module"]
    stem = get_module_stem(module_name)
    base_vma = int(manifest["module_runtime_base"], 0)

    scratch_module = os.path.join(repo_root, "scratch", module_name)
    ir_path = os.path.join(repo_root, "scratch", f"{stem}_ir.json")
    out_s_path = os.path.join(repo_root, ".private", "asm", stem, f"{stem}.s")
    out_ld_path = os.path.join(repo_root, "asm", "linker", f"{stem}.ld")

    print(f"Extracting {module_name} from disc...")
    module_bytes = extract_module_from_disc(repo_root, manifest)
    os.makedirs(os.path.dirname(scratch_module), exist_ok=True)
    with open(scratch_module, "wb") as f:
        f.write(module_bytes)

    proven_ranges = [
        r for r in manifest.get("ranges", [])
        if r.get("assembly_representation") == "MNEMONIC_PROVEN"
    ]

    ir_data: Dict[str, Any] = {"blocks": [], "labels": []}
    if proven_ranges:
        print(f"Running C++ export_sh2_asm_ir for {len(proven_ranges)} proven blocks...")
        ir_data = run_cpp_ir_exporter(repo_root, scratch_module, base_vma, proven_ranges, ir_path)

    print(f"Generating private assembly {out_s_path}...")
    generate_assembly(module_bytes, manifest, ir_data, out_s_path)

    print(f"Generating linker script {out_ld_path}...")
    generate_linker_script(manifest, ir_data, out_ld_path)

    print(f"\n=== MODULE ASSEMBLY GENERATION COMPLETE: {module_name} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
