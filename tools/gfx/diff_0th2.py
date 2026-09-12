#!/usr/bin/env python3
"""Compare 0TH2.BIN between RUS and USA to find redirected resource pointers."""
import struct
import sys
from pathlib import Path

def main():
    rus = Path(".private/rus/0TH2.BIN").read_bytes()
    usa = Path(".private/usa/0TH2.BIN").read_bytes()
    base = 0x06004000
    
    print(f"Comparing 0TH2.BIN (size {len(rus)}):")
    diff_count = 0
    # Group differences into 32-bit words
    diff_words = []
    for i in range(0, min(len(rus), len(usa)) - 4, 4):
        w_rus = struct.unpack_from(">I", rus, i)[0]
        w_usa = struct.unpack_from(">I", usa, i)[0]
        if w_rus != w_usa:
            diff_words.append((i, w_rus, w_usa))
            
    print(f"Found {len(diff_words)} differing 32-bit words.")
    
    # Filter for pointer differences where value looks like an address or offset
    ptr_diffs = []
    for off, r_val, u_val in diff_words:
        # Check if difference is exactly 0x2000 (8192 bytes = the CHR.BIN shift!)
        if r_val - u_val == 0x2000 or u_val - r_val == 0x2000:
            ptr_diffs.append((off, r_val, u_val, "SHIFT_0x2000"))
        elif 0x06000000 <= r_val <= 0x06100000 and 0x06000000 <= u_val <= 0x06100000:
            ptr_diffs.append((off, r_val, u_val, "CODE_PTR"))
            
    print(f"Found {len(ptr_diffs)} pointer/offset differences:")
    for off, r_val, u_val, dtype in ptr_diffs[:25]:
        vma = base + off
        print(f"  PC 0x{vma:08X} (off 0x{off:05X}): RUS=0x{r_val:08X}, USA=0x{u_val:08X} [{dtype}]")

if __name__ == "__main__":
    main()
