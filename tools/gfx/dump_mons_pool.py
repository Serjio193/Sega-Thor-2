#!/usr/bin/env python3
"""Inspect literal pool and following code of load_mons in 0TH2.BIN."""
import struct
import sys
from pathlib import Path

raw = Path(".private/rus/0TH2.BIN").read_bytes()
base = 0x06004000
for vma in range(0x0600AA60, 0x0600AB50, 4):
    off = vma - base
    val = struct.unpack_from(">I", raw, off)[0]
    print(f"0x{vma:08X} (off 0x{off:05X}): 0x{val:08X}")
