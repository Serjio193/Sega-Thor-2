#!/usr/bin/env python3
"""Inspect 6-byte animation frame records in Ancient sprite packages."""
import struct
import sys
from pathlib import Path

def inspect_frames(archive_path: Path):
    data = archive_path.read_bytes()
    hdr_size, anim_off, sprite_off = struct.unpack_from(">III", data, 0)
    print(f"\n=== {archive_path.name} Frame Records ===")
    
    # In ARELE.BIN: Target [0] starts at anim_off + 0x00D8
    # Let's inspect 10 6-byte records starting at anim_off + 0x00D8 (or similar)
    script_data = data[anim_off:sprite_off]
    
    # Let's find all unique 16-bit pointers in the first script table
    # Word 0: number of frames or first frame offset
    first_word = struct.unpack_from(">H", script_data, 0)[0]
    second_word = struct.unpack_from(">H", script_data, 2)[0]
    print(f"Script start: first_word=0x{first_word:04X} ({first_word}), second_word=0x{second_word:04X} ({second_word})")
    
    # Let's inspect records at offset second_word
    base_frame = second_word
    for i in range(12):
        foff = base_frame + i * 6
        if foff + 6 <= len(script_data):
            b = script_data[foff:foff+6]
            # Unpack as various interpretations: 3 x BE16, or 6 bytes, or signed offsets
            w0, w1, w2 = struct.unpack_from(">HHH", b, 0)
            sw0, sw1, sw2 = struct.unpack_from(">hhh", b, 0)
            b0, b1, b2, b3, b4, b5 = b
            print(f"  Frame [{i:02d}] at script+0x{foff:04X}:")
            print(f"     hex: {b.hex(' ')}")
            print(f"     words: 0x{w0:04X} 0x{w1:04X} 0x{w2:04X} | signed: {sw0:6d} {sw1:6d} {sw2:6d}")
            print(f"     bytes: {b0:3d}, {b1:3d}, {b2:3d}, {b3:3d}, {b4:3d}, {b5:3d}")

if __name__ == "__main__":
    inspect_frames(Path(".private/rus/ARELE.BIN"))
    inspect_frames(Path(".private/rus/BAW.BIN"))
    inspect_frames(Path(".private/rus/P0.BIN"))
