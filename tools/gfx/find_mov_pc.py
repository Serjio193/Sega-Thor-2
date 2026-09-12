#!/usr/bin/env python3
"""Find instructions referencing specific literal pool constants."""
import struct
import sys
from pathlib import Path

def analyze_mov_pc(bin_path: Path, base_vma: int, target_vma: int):
    data = bin_path.read_bytes()
    print(f"Searching {bin_path.name} for MOV.L/MOVA referencing 0x{target_vma:08X}...")
    for offset in range(0, len(data) - 2, 2):
        pc = base_vma + offset
        op = struct.unpack_from(">H", data, offset)[0]
        # MOV.L @(disp, PC), Rn : 1101nnnn dddddddd (0xD...)
        if (op & 0xF000) == 0xD000:
            rn = (op >> 8) & 0x0F
            disp = op & 0xFF
            ref_vma = (pc & ~3) + 4 + (disp * 4)
            if ref_vma == target_vma:
                val = struct.unpack_from(">I", data, ref_vma - base_vma)[0] if (ref_vma - base_vma + 4 <= len(data)) else 0
                print(f"  PC 0x{pc:08X} (offset 0x{offset:05X}): MOV.L @(0x{disp:02X}, PC), R{rn} -> [0x{ref_vma:08X}] = 0x{val:08X}")
        # MOVA @(disp, PC), R0 : 11000111 dddddddd (0xC7..)
        elif (op & 0xFF00) == 0xC700:
            disp = op & 0xFF
            ref_vma = (pc & ~3) + 4 + (disp * 4)
            if ref_vma == target_vma:
                print(f"  PC 0x{pc:08X} (offset 0x{offset:05X}): MOVA @(0x{disp:02X}, PC), R0 -> 0x{ref_vma:08X}")

if __name__ == "__main__":
    p = Path(".private/rus/0TH2.BIN")
    # Pointers to CHR.BIN (0x0600A688), P0.BIN (0x0600A854), MAP.BIN (0x0600AAC4), MONS.BIN (0x0600AAD0)
    for target in [0x0600A688, 0x0600A68C, 0x0600A82C, 0x0600A854, 0x0600AAC4, 0x0600AAD0]:
        analyze_mov_pc(p, 0x06004000, target)
