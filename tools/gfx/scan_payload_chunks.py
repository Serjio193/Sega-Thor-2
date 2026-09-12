#!/usr/bin/env python3
"""Scan all records and pixel data in ARELE.BIN sprite payload."""
import struct
import sys
from pathlib import Path

def scan_payload(path: Path):
    data = path.read_bytes()
    hdr_size, anim_off, sprite_off = struct.unpack_from(">III", data, 0)
    payload = data[sprite_off:]
    print(f"\n=== Scanning {path.name} sprite payload (size {len(payload)}) ===")
    
    # Check transitions
    in_zero = True
    zero_start = 0
    chunks = []
    for i in range(0, len(payload), 16):
        block = payload[i:i+16]
        all_z = all(b == 0 for b in block)
        if all_z and not in_zero:
            chunks.append(("DATA", zero_start, i))
            in_zero = True
            zero_start = i
        elif not all_z and in_zero:
            chunks.append(("ZERO", zero_start, i))
            in_zero = False
            zero_start = i
    chunks.append(("ZERO" if in_zero else "DATA", zero_start, len(payload)))
    
    for ctype, s, e in chunks[:25]:
        length = e - s
        if length >= 16:
            first_16 = payload[s:s+16].hex(' ')
            print(f"  {ctype:<5} +0x{s:05X} - +0x{e:05X} (size {length:<6}): {first_16}")

if __name__ == "__main__":
    scan_payload(Path(".private/rus/ARELE.BIN"))
    scan_payload(Path(".private/rus/BAW.BIN"))
