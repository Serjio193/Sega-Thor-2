#!/usr/bin/env python3
"""Inspect 14-byte sprite record definitions in Ancient sprite packages."""
import struct
import sys
from pathlib import Path

def inspect_records(path: Path):
    data = path.read_bytes()
    hdr_size, anim_off, sprite_off = struct.unpack_from(">III", data, 0)
    payload = data[sprite_off:]
    num_records = struct.unpack_from(">H", payload, 0)[0]
    print(f"\n=== {path.name} Sprite Records ({num_records} total) ===")
    
    offsets = [struct.unpack_from(">H", payload, 2 + i*2)[0] for i in range(num_records)]
    valid_offsets = [o for o in offsets if o > 0]
    print(f"Non-zero record offsets: {len(valid_offsets)}")
    
    for idx in range(min(10, len(valid_offsets))):
        rec_off = valid_offsets[idx]
        rec = payload[rec_off:rec_off+14]
        if len(rec) == 14:
            w = [f"0x{struct.unpack_from('>H', rec, j)[0]:04X}" for j in range(0, 14, 2)]
            sw = [struct.unpack_from(">h", rec, j)[0] for j in range(0, 14, 2)]
            b = list(rec)
            print(f"  Rec [{idx:02d}] at +0x{rec_off:04X}:")
            print(f"    hex:   {rec.hex(' ')}")
            print(f"    words: {' '.join(w)}")
            print(f"    signed: {sw}")
            print(f"    bytes:  {b}")

if __name__ == "__main__":
    inspect_records(Path(".private/rus/ARELE.BIN"))
    inspect_records(Path(".private/rus/BAW.BIN"))
    inspect_records(Path(".private/rus/SHADE.BIN"))
