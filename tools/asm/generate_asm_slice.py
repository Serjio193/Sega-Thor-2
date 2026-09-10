#!/usr/bin/env python3
"""Mechanical SH-2 Assembly Slice Emitter.

Translates proven SH-2 block instruction records into real SH-2 assembly mnemonics
supported by GNU as (binutils-sh-elf). Fails closed on any unsupported instruction.
"""

from dataclasses import dataclass
from typing import List, Tuple
import json
import os
import sys

# Proven specification for bb_06004000
BB_06004000_SPEC = {
    "block_id": "bb_06004000",
    "revision": "thor2_ntsc_patched_fe11d2fb",
    "module": "0TH2.BIN",
    "module_sha256": "c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64",
    "module_runtime_base": 0x06004000,
    "source_file_offset": 0,
    "runtime_start": 0x06004000,
    "runtime_end": 0x0600400A,
    "byte_length": 12,
    "instruction_count": 6,
    "original_slice_sha256": "837951102416988d0fc9cbc55c581662463a28dca74dceeb6bd0fca3fdaec10e",
    "cpu": "MASTER_SH2",
    "generation_provenance_identity": "T2-V02a / T2-D4-D5 / T2-ASM-01",
    "classification_state": "CONFIRMED_CODE / EXECUTED",
    "assembler_tool_identity": "GNU assembler (binutils-sh-elf 2.40+2) 2.40",
    "link_vma": 0x06004000,
    "instructions": [
        (0x06004000, 0x6611, "MOV.W @R1, R6"),
        (0x06004002, 0x6F03, "MOV R0, R15"),
        (0x06004004, 0xD417, "MOV.L @(disp,PC), R4"),
        (0x06004006, 0x6442, "MOV.L @R4, R4"),
        (0x06004008, 0xA003, "BRA 0x06004012"),
        (0x0600400A, 0x0009, "NOP"),
    ],
    "branch_targets": [0x06004012],
    "literal_targets": [0x06004064],
}


@dataclass
class AsmInstruction:
    address: int
    opcode: int
    mnemonic: str
    symbolic_line: str
    comment: str


def decode_and_emit_instruction(pc: int, opcode: int, base_vma: int) -> AsmInstruction:
    """Decode a 16-bit opcode into GNU SH-2 assembly mnemonic or fail closed."""
    # Form 1: MOV.W @Rm, Rn (0110 nnnn mmmm 0001)
    if (opcode & 0xF00F) == 0x6001:
        rn = (opcode >> 8) & 0x0F
        rm = (opcode >> 4) & 0x0F
        line = f"    mov.w   @r{rm}, r{rn}"
        comment = f"MOV.W @R{rm}, R{rn}"
        return AsmInstruction(pc, opcode, f"MOV.W @R{rm}, R{rn}", line, comment)

    # Form 2: MOV Rm, Rn (0110 nnnn mmmm 0011)
    if (opcode & 0xF00F) == 0x6003:
        rn = (opcode >> 8) & 0x0F
        rm = (opcode >> 4) & 0x0F
        line = f"    mov     r{rm}, r{rn}"
        comment = f"MOV R{rm}, R{rn}"
        return AsmInstruction(pc, opcode, f"MOV R{rm}, R{rn}", line, comment)

    # Form 3: MOV.L @(disp,PC), Rn (1101 nnnn dddddddd)
    if (opcode & 0xF000) == 0xD000:
        rn = (opcode >> 8) & 0x0F
        disp = opcode & 0xFF
        target = ((pc & ~3) + 4) + (disp * 4)
        sym_name = f"lit_{target:08x}"
        line = f"    mov.l   {sym_name}, r{rn}"
        comment = f"MOV.L @({disp},PC), R{rn} -> 0x{target:08X}"
        return AsmInstruction(pc, opcode, f"MOV.L @(disp,PC), R{rn}", line, comment)

    # Form 4: MOV.L @Rm, Rn (0110 nnnn mmmm 0010)
    if (opcode & 0xF00F) == 0x6002:
        rn = (opcode >> 8) & 0x0F
        rm = (opcode >> 4) & 0x0F
        line = f"    mov.l   @r{rm}, r{rn}"
        comment = f"MOV.L @R{rm}, R{rn}"
        return AsmInstruction(pc, opcode, f"MOV.L @R{rm}, R{rn}", line, comment)

    # Form 5: BRA disp (1010 dddddddddddd)
    if (opcode & 0xF000) == 0xA000:
        disp12 = opcode & 0x0FFF
        s_disp = disp12 if (disp12 < 0x800) else (disp12 - 0x1000)
        target = pc + 4 + (s_disp * 2)
        sym_name = f"loc_{target:08x}"
        line = f"    bra     {sym_name}"
        comment = f"BRA 0x{target:08X}"
        return AsmInstruction(pc, opcode, f"BRA disp", line, comment)

    # Form 6: NOP (0000 0000 0000 1001)
    if opcode == 0x0009:
        line = "    nop"
        comment = "NOP (delay slot)"
        return AsmInstruction(pc, opcode, "NOP", line, comment)

    raise ValueError(f"FAIL CLOSED: Unsupported opcode 0x{opcode:04X} at 0x{pc:08X}")


def generate_assembly(spec: dict) -> Tuple[str, str, dict]:
    """Generate .s assembly, .ld linker script, and .json manifest."""
    base_vma = spec["runtime_start"]
    block_id = spec["block_id"]

    emitted_insns: List[AsmInstruction] = []
    symbolic_targets: set = set()

    for pc, opcode, _ in spec["instructions"]:
        insn = decode_and_emit_instruction(pc, opcode, base_vma)
        emitted_insns.append(insn)
        if (opcode & 0xF000) == 0xD000:
            disp = opcode & 0xFF
            target = ((pc & ~3) + 4) + (disp * 4)
            symbolic_targets.add(("lit", target))
        elif (opcode & 0xF000) == 0xA000:
            disp12 = opcode & 0x0FFF
            s_disp = disp12 if (disp12 < 0x800) else (disp12 - 0x1000)
            target = pc + 4 + (s_disp * 2)
            symbolic_targets.add(("loc", target))

    # Construct Assembly Source
    s_lines = [
        "/* Mechanically generated SH-2 assembly for Thor 2 recovery */",
        f"/* Block: {block_id} | Base VMA: 0x{base_vma:08X} | CPU: {spec['cpu']} */",
        f"/* Classification: {spec['classification_state']} */",
        "/* Invariant: Real mnemonics only; raw opcode words forbidden */",
        "",
        "    .text",
        "    .global _start",
    ]

    for prefix, target in sorted(symbolic_targets):
        s_lines.append(f"    .global {prefix}_{target:08x}")

    s_lines.append("")
    s_lines.append("_start:")

    for insn in emitted_insns:
        comment = f"/* 0x{insn.address:08X} [0x{insn.opcode:04X}] {insn.comment} */"
        s_lines.append(f"{insn.symbolic_line:<32} {comment}")

    s_lines.append("")
    s_lines.append("    /* Symbolic resolution relative to section origin */")
    for prefix, target in sorted(symbolic_targets):
        rel_offset = target - base_vma
        s_lines.append(f"    .equ {prefix}_{target:08x}, _start + 0x{rel_offset:x}")

    s_lines.append("")
    s_content = "\n".join(s_lines) + "\n"

    # Construct Linker Script
    ld_lines = [
        "/* Linker script for bounded SH-2 recovery specimen */",
        "ENTRY(_start)",
        "",
        "SECTIONS",
        "{",
        f"    . = 0x{base_vma:08X};",
        "",
        "    .text : {",
        "        *(.text)",
        "    }",
        "",
        "    /DISCARD/ : {",
        "        *(.comment)",
        "        *(.note*)",
        "    }",
        "}",
        "",
        f'ASSERT(SIZEOF(.text) == {spec["byte_length"]}, "Error: .text section length mismatch");',
        f'ASSERT(_start == 0x{base_vma:08X}, "Error: _start VMA mismatch");',
    ]

    for prefix, target in sorted(symbolic_targets):
        ld_lines.append(f'ASSERT({prefix}_{target:08x} == 0x{target:08X}, "Error: {prefix}_{target:08x} VMA mismatch");')

    ld_lines.append("")
    ld_content = "\n".join(ld_lines) + "\n"

    # Construct Manifest
    manifest = {
        "schema_version": "1.0.0",
        "revision": spec["revision"],
        "module": spec["module"],
        "module_sha256": spec["module_sha256"],
        "module_runtime_base": f"0x{spec['module_runtime_base']:08X}",
        "source_file_offset": f"0x{spec['source_file_offset']:08X}",
        "runtime_start": f"0x{spec['runtime_start']:08X}",
        "runtime_end": f"0x{spec['runtime_end']:08X}",
        "byte_length": spec["byte_length"],
        "instruction_count": spec["instruction_count"],
        "original_slice_sha256": spec["original_slice_sha256"],
        "cpu": spec["cpu"],
        "generation_provenance_identity": spec["generation_provenance_identity"],
        "classification_state": spec["classification_state"],
        "assembler_tool_identity": spec["assembler_tool_identity"],
        "link_vma": f"0x{spec['link_vma']:08X}",
        "branch_targets": [f"0x{t:08X}" for t in spec["branch_targets"]],
        "literal_targets": [f"0x{t:08X}" for t in spec["literal_targets"]],
        "expected_output_sha256": spec["original_slice_sha256"],
    }

    return s_content, ld_content, manifest


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    out_s_path = os.path.join(repo_root, "asm", "generated", "bb_06004000.s")
    out_ld_path = os.path.join(repo_root, "asm", "linker", "bb_06004000.ld")
    out_json_path = os.path.join(repo_root, "asm", "manifests", "bb_06004000.json")

    os.makedirs(os.path.dirname(out_s_path), exist_ok=True)
    os.makedirs(os.path.dirname(out_ld_path), exist_ok=True)
    os.makedirs(os.path.dirname(out_json_path), exist_ok=True)

    s_content, ld_content, manifest = generate_assembly(BB_06004000_SPEC)

    with open(out_s_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(s_content)
    print(f"Generated ASM: {out_s_path}")

    with open(out_ld_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(ld_content)
    print(f"Generated LD:  {out_ld_path}")

    with open(out_json_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print(f"Generated Manifest: {out_json_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
