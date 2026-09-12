#!/usr/bin/env python3
"""Inspect map loader instructions around 0x06014880 - 0x06014D00."""
import struct
import sys
from pathlib import Path

def main():
    raw = Path(".private/rus/0TH2.BIN").read_bytes()
    base = 0x06004000
    
    print("=== Instructions around 0x060148B6 ===")
    for vma in range(0x06014880, 0x06014920, 2):
        off = vma - base
        w = struct.unpack_from(">H", raw, off)[0]
        print(f"  0x{vma:08X} (off 0x{off:05X}): 0x{w:04X}")

if __name__ == "__main__":
    main()
