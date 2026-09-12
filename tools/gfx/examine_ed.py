#!/usr/bin/env python3
"""Inspect ED.BIN structure and differential."""
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.disc_extractor import SaturnDisc

def examine_ed():
    rus_disc = SaturnDisc(Path("The_Story_of_Thor_2_[RUS]_(NTSC).bin"))
    usa_disc = SaturnDisc(Path("Legend of Oasis The (USA)/Legend of Oasis, The (USA) (Track 1).bin"))
    
    ed_rus = rus_disc.read_file("ED.BIN")
    ed_usa = usa_disc.read_file("ED.BIN")
    
    print(f"ED.BIN size: RUS={len(ed_rus)}, USA={len(ed_usa)}")
    
    # Check header
    print("ED.BIN header (first 32 bytes):")
    for i in range(0, 32, 16):
        print(f"  {i:04X}: {' '.join(f'{b:02X}' for b in ed_rus[i:i+16])}")
        
    diff_off = 467456 # 0x72200
    print(f"\nED.BIN diff starts at 0x{diff_off:X}:")
    print("USA at 0x72200:")
    for i in range(diff_off, diff_off + 48, 16):
        print(f"  0x{i:05X}: {' '.join(f'{b:02X}' for b in ed_usa[i:i+16])}")
    print("RUS at 0x72200:")
    for i in range(diff_off, diff_off + 48, 16):
        print(f"  0x{i:05X}: {' '.join(f'{b:02X}' for b in ed_rus[i:i+16])}")

if __name__ == "__main__":
    examine_ed()
