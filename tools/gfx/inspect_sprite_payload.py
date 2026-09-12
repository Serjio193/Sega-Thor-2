#!/usr/bin/env python3
"""Inspect the sprite_data payload header and records."""
import struct
import sys
from pathlib import Path

def inspect_sprite_payload(path: Path):
    data = path.read_bytes()
    hdr_size, anim_off, sprite_off = struct.unpack_from(">III", data, 0)
    print(f"\n=== {path.name} Sprite Payload at 0x{sprite_off:05X} (size {len(data)-sprite_off}) ===")
    
    # Read first 128 bytes of sprite payload
    payload = data[sprite_off:]
    for i in range(0, min(128, len(payload)), 16):
        row = payload[i:i+16]
        hex_s = " ".join(f"{b:02X}" for b in row)
        words = [f"0x{struct.unpack_from('>H', row, j)[0]:04X}" for j in range(0, 16, 2)]
        print(f"  +0x{i:03X}: {hex_s:<48} | {' '.join(words)}")

if __name__ == "__main__":
    for name in ["ARELE.BIN", "BAW.BIN", "DIT.BIN", "EFREET.BIN", "SHADE.BIN"]:
        inspect_sprite_payload(Path(f".private/rus/{name}"))
