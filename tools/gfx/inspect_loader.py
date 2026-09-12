#!/usr/bin/env python3
"""Inspect resource loading and decompressor routines in 0TH2.BIN and TH2.LOW."""
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.disc_extractor import SaturnDisc

def main():
    disc = SaturnDisc(Path("The_Story_of_Thor_2_[RUS]_(NTSC).bin"))
    raw_0th2 = disc.read_file("0TH2.BIN")
    base_0th2 = 0x06004000
    
    print("=== 0TH2.BIN File String Area ===")
    for i in range(0x7E1A0, 0x7E240, 16):
        row = raw_0th2[i:i+16]
        hex_s = " ".join(f"{b:02X}" for b in row)
        asc_s = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
        print(f"0x{i:05X}: {hex_s:<48} {asc_s}")
        
    print("\n=== Pointers to String Area (0x060821A0 - 0x06082240) ===")
    for i in range(0, len(raw_0th2) - 4, 2):
        val = struct.unpack_from(">I", raw_0th2, i)[0]
        if 0x060821A0 <= val <= 0x06082240:
            print(f"  Ptr at 0x{i:05X} (runtime 0x{base_0th2+i:08X}) -> 0x{val:08X}")
            
    print("\n=== Pointer table right before string area (0x7E140 - 0x7E1BC) ===")
    for i in range(0x7E140, 0x7E1BC, 4):
        val = struct.unpack_from(">I", raw_0th2, i)[0]
        print(f"  0x{i:05X}: 0x{val:08X}")
        
    disc.close()

if __name__ == "__main__":
    main()
