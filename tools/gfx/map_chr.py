#!/usr/bin/env python3
"""Map structures and sub-blocks in CHR.BIN."""
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.disc_extractor import SaturnDisc

def map_chr(data: bytes, label: str):
    print(f"\n=== Mapping {label} (size {len(data)}) ===")
    
    # Check if there are known headers or repeated signatures
    # Check 16-byte aligned blocks for non-zero transitions
    transitions = []
    in_zero = True
    zero_start = 0
    
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        all_zero = all(b == 0 for b in chunk)
        if all_zero and not in_zero:
            transitions.append(("DATA", zero_start, i))
            in_zero = True
            zero_start = i
        elif not all_zero and in_zero:
            if i > 0:
                transitions.append(("ZERO", zero_start, i))
            in_zero = False
            zero_start = i
    transitions.append(("ZERO" if in_zero else "DATA", zero_start, len(data)))
    
    for t_type, start, end in transitions:
        length = end - start
        if length >= 128:
            first_words = [f"{b:02X}" for b in data[start:start+16]]
            print(f"  {t_type:<5} 0x{start:05X} - 0x{end:05X} (0x{length:05X} = {length:<7} bytes) : {' '.join(first_words)}")

def main():
    rus_disc = SaturnDisc(Path("The_Story_of_Thor_2_[RUS]_(NTSC).bin"))
    usa_disc = SaturnDisc(Path("Legend of Oasis The (USA)/Legend of Oasis, The (USA) (Track 1).bin"))
    map_chr(usa_disc.read_file("CHR.BIN"), "CHR.BIN USA")
    map_chr(rus_disc.read_file("CHR.BIN"), "CHR.BIN RUS")

if __name__ == "__main__":
    main()
