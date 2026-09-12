#!/usr/bin/env python3
"""Investigate CHR.BIN structure and differential between RUS and USA."""
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.disc_extractor import SaturnDisc

def examine_chr():
    rus_disc = SaturnDisc(Path("The_Story_of_Thor_2_[RUS]_(NTSC).bin"))
    usa_disc = SaturnDisc(Path("Legend of Oasis The (USA)/Legend of Oasis, The (USA) (Track 1).bin"))
    
    chr_rus = rus_disc.read_file("CHR.BIN")
    chr_usa = usa_disc.read_file("CHR.BIN")
    
    print(f"CHR.BIN RUS size: {len(chr_rus)} (0x{len(chr_rus):X})")
    print(f"CHR.BIN USA size: {len(chr_usa)} (0x{len(chr_usa):X})")
    
    # First 64 bytes
    print("\nCHR.BIN header (first 64 bytes, identical in both):")
    for i in range(0, 64, 16):
        row = chr_rus[i:i+16]
        hex_str = " ".join(f"{b:02X}" for b in row)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
        print(f"  {i:04X}: {hex_str:<48}  {asc}")
        
    # Check if CHR.BIN starts with an offset table
    print("\nReading first 16 BE32 values:")
    for i in range(16):
        val = struct.unpack_from(">I", chr_rus, i*4)[0]
        print(f"  [{i}]: 0x{val:08X} ({val})")
        
    # Look at offset 167984 (0x29030) where diff starts
    diff_off = 167984
    print(f"\nDifference point: 0x{diff_off:X} ({diff_off})")
    print("USA bytes around 0x29030:")
    for i in range(diff_off - 16, diff_off + 48, 16):
        row = chr_usa[i:i+16]
        print(f"  0x{i:05X}: {' '.join(f'{b:02X}' for b in row)}")
    print("RUS bytes around 0x29030:")
    for i in range(diff_off - 16, diff_off + 48, 16):
        row = chr_rus[i:i+16]
        print(f"  0x{i:05X}: {' '.join(f'{b:02X}' for b in row)}")

    rus_disc.close()
    usa_disc.close()

if __name__ == "__main__":
    examine_chr()
