#!/usr/bin/env python3
"""Investigate MAP.BIN structure, room tables, and graphics tiles."""
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.disc_extractor import SaturnDisc

def examine_map():
    usa_disc = SaturnDisc(Path("Legend of Oasis The (USA)/Legend of Oasis, The (USA) (Track 1).bin"))
    map_data = usa_disc.read_file("MAP.BIN")
    print(f"MAP.BIN size: {len(map_data)} (0x{len(map_data):X})")
    
    # First 128 bytes
    print("\nFirst 128 bytes of MAP.BIN:")
    for i in range(0, 128, 16):
        row = map_data[i:i+16]
        hex_s = " ".join(f"{b:02X}" for b in row)
        words = [f"0x{struct.unpack_from('>H', row, j)[0]:04X}" for j in range(0, 16, 2)]
        print(f"  {i:04X}: {hex_s:<48} | {' '.join(words)}")
        
    # Check if there is an offset table
    print("\nReading first 32 BE32 values:")
    offsets = []
    for i in range(32):
        val = struct.unpack_from(">I", map_data, i*4)[0]
        offsets.append(val)
        print(f"  [{i:02d}]: 0x{val:08X} ({val})")
        
    # Count P< markers
    matches = [i for i in range(0, len(map_data)-2, 2) if map_data[i:i+2] == b'P<']
    sec_matches = [m for m in matches if m % 2048 == 2]
    print(f"\nOccurrences of P< at sector offset + 2: {len(sec_matches)}")
    for sm in sec_matches[:20]:
        lba = sm // 2048
        prefix = map_data[sm-2:sm+14]
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in prefix)
        print(f"  LBA {lba:4d} (0x{sm-2:06X}): {prefix.hex(' ')} | {asc}")

if __name__ == "__main__":
    examine_map()
