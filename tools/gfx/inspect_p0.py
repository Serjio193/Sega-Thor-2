#!/usr/bin/env python3
"""Inspect sprite payload at offset 0xFF5C in P0.BIN."""
import struct
import sys
from pathlib import Path

def main():
    p0 = Path(".private/rus/P0.BIN").read_bytes()
    hdr_size, anim_off, sprite_off = struct.unpack_from(">III", p0, 0)
    print(f"P0.BIN: hdr_size={hdr_size}, anim_off=0x{anim_off:X}, sprite_off=0x{sprite_off:X}")
    
    print(f"\nBytes at sprite_off (0x{sprite_off:X}):")
    data = p0[sprite_off:sprite_off+64]
    for i in range(0, len(data), 16):
        row = data[i:i+16]
        print(f"  +0x{i:02X}: {' '.join(f'{b:02X}' for b in row)}")
        
    # Check if there are sub-headers or frame dimensions
    # Let's inspect the animation script data [anim_off : sprite_off]
    script = p0[anim_off:sprite_off]
    print(f"\nAnimation script size: {len(script)} bytes")
    print("First 64 bytes of animation script:")
    for i in range(0, min(64, len(script)), 16):
        row = script[i:i+16]
        words = [f"{struct.unpack_from('>H', row, j)[0]:04X}" for j in range(0, 16, 2)]
        print(f"  +0x{i:02X}: {' '.join(words)}")
        
    # Check offset table [12 : anim_off]
    num_offsets = (anim_off - 12) // 2
    print(f"\nAnimation offset table: {num_offsets} entries")
    offsets = [struct.unpack_from(">H", p0, 12 + i*2)[0] for i in range(min(16, num_offsets))]
    print("First 16 offsets:", [f"0x{x:04X}" for x in offsets])

if __name__ == "__main__":
    main()
