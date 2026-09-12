#!/usr/bin/env python3
"""Inspect palette data in TH2.LOW and other containers."""
import struct
import sys
from pathlib import Path

def decode_rgb555(word: int) -> tuple[int, int, int]:
    # Saturn standard format: bit 15 is 0, B=14..10, G=9..5, R=4..0
    # Scaled to 0..255: (val << 3) | (val >> 2)
    b5 = (word >> 10) & 0x1F
    g5 = (word >> 5) & 0x1F
    r5 = word & 0x1F
    r8 = (r5 << 3) | (r5 >> 2)
    g8 = (g5 << 3) | (g5 >> 2)
    b8 = (b5 << 3) | (b5 >> 2)
    return (r8, g8, b8)

def main():
    low = Path(".private/rus/TH2.LOW").read_bytes()
    base = 0x002DA000
    targets = [
        ("CRAM Bank 0 (lit_0600AAB0)", 0x002FCDB6),
        ("CRAM Bank 1 (lit_0600AAB8)", 0x002FCFB6),
        ("CRAM Bank 2 (lit_0600AAE8)", 0x002FD1B6),
    ]
    
    for name, vma in targets:
        off = vma - base
        print(f"\n=== {name} at 0x{vma:08X} (offset 0x{off:05X}) ===")
        for i in range(16):
            word = struct.unpack_from(">H", low, off + i*2)[0]
            r, g, b = decode_rgb555(word)
            print(f"  Color [{i:02d}]: 0x{word:04X} -> RGB({r:3d}, {g:3d}, {b:3d}) #{r:02X}{g:02X}{b:02X}")

if __name__ == "__main__":
    main()
