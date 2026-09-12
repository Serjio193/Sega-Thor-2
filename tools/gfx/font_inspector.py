#!/usr/bin/env python3
"""Inspect font glyphs and structures in CHR.BIN."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.disc_extractor import SaturnDisc

def print_glyph_1bpp(data, width=16, height=16):
    # If 1bpp: each row is width // 8 bytes
    row_bytes = (width + 7) // 8
    for y in range(height):
        row = data[y * row_bytes : (y + 1) * row_bytes]
        bits = "".join(f"{b:08b}" for b in row)[:width]
        print("".join("#" if b == '1' else "." for b in bits))

def main():
    usa_disc = SaturnDisc(Path("Legend of Oasis The (USA)/Legend of Oasis, The (USA) (Track 1).bin"))
    rus_disc = SaturnDisc(Path("The_Story_of_Thor_2_[RUS]_(NTSC).bin"))
    chr_usa = usa_disc.read_file("CHR.BIN")
    chr_rus = rus_disc.read_file("CHR.BIN")
    
    print("USA glyph at 0x29030 (16x16?):")
    for glyph_idx in range(6):
        offset = 0x29030 + glyph_idx * 32
        print(f"--- Glyph {glyph_idx} at 0x{offset:X} ---")
        print_glyph_1bpp(chr_usa[offset:offset+32], 16, 16)
        
    print("\nLet's check what is at 0x29000 - 0x29030 in USA:")
    row = chr_usa[0x29000:0x29030]
    print(" ".join(f"{b:02X}" for b in row))

if __name__ == "__main__":
    main()
