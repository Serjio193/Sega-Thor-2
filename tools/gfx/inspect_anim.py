#!/usr/bin/env python3
"""Decode and analyze animation scripts in Ancient sprite archives."""
import struct
import sys
from pathlib import Path

def analyze_archive_anim(archive_path: Path):
    data = archive_path.read_bytes()
    hdr_size, anim_off, sprite_off = struct.unpack_from(">III", data, 0)
    print(f"\n=== {archive_path.name} ===")
    print(f"Header: anim_off=0x{anim_off:X}, sprite_off=0x{sprite_off:X}, total=0x{len(data):X}")
    
    num_offsets = (anim_off - hdr_size) // 2
    offsets = [struct.unpack_from(">H", data, hdr_size + i*2)[0] for i in range(num_offsets)]
    
    unique_offsets = sorted(list(set(offsets)))
    print(f"Animation offsets: {num_offsets} entries, {len(unique_offsets)} unique targets")
    
    # Inspect words at anim_off
    print("\nFirst 128 bytes of script:")
    for i in range(0, min(128, len(data) - anim_off), 16):
        row = data[anim_off + i : anim_off + i + 16]
        words = [f"0x{struct.unpack_from('>H', row, j)[0]:04X}" for j in range(0, 16, 2)]
        print(f"  +0x{i:03X} (file 0x{anim_off+i:05X}): {' '.join(words)}")

if __name__ == "__main__":
    analyze_archive_anim(Path(".private/rus/ARELE.BIN"))
