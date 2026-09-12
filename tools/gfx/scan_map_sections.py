#!/usr/bin/env python3
"""Scan MAP.BIN for section markers, sub-packages, and alignment boundaries."""
import struct
import sys
from pathlib import Path

def scan_map():
    map_data = Path(".private/rus/MAP.BIN").read_bytes()
    print(f"Total size: {len(map_data)} bytes ({len(map_data)//2048} sectors)")
    
    # Check sector boundaries for non-zero headers
    print("\nScanning sector boundaries (every 2048 bytes):")
    non_zero_sectors = []
    for lba in range(len(map_data) // 2048):
        off = lba * 2048
        sector = map_data[off:off+2048]
        if not all(b == 0 for b in sector[:16]):
            first16 = sector[:16]
            asc = "".join(chr(b) if 32 <= b < 127 else "." for b in first16)
            hex_s = " ".join(f"{b:02X}" for b in first16[:8])
            non_zero_sectors.append((lba, off, hex_s, asc))
            
    print(f"Found {len(non_zero_sectors)} sectors starting with non-zero headers.")
    for s in non_zero_sectors[:30]:
        print(f"  LBA {s[0]:4d} (0x{s[1]:06X}): {s[2]:<24} {s[3]}")

if __name__ == "__main__":
    scan_map()
