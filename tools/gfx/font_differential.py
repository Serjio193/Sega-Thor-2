#!/usr/bin/env python3
"""Compare and render font glyphs between USA and RUS CHR.BIN."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.disc_extractor import SaturnDisc

def render_glyph(data: bytes, width: int = 16, height: int = 16) -> list[str]:
    # 1 bit per pixel: row = width // 8 bytes
    row_bytes = (width + 7) // 8
    lines = []
    for y in range(height):
        row = data[y * row_bytes : (y + 1) * row_bytes]
        bits = "".join(f"{b:08b}" for b in row)[:width]
        lines.append("".join("#" if b == '1' else "." for b in bits))
    return lines

def main():
    usa_disc = SaturnDisc(Path("Legend of Oasis The (USA)/Legend of Oasis, The (USA) (Track 1).bin"))
    rus_disc = SaturnDisc(Path("The_Story_of_Thor_2_[RUS]_(NTSC).bin"))
    
    chr_usa = usa_disc.read_file("CHR.BIN")
    chr_rus = rus_disc.read_file("CHR.BIN")
    
    print("=== Font Differential: USA (0x29030) vs RUS (0x2B030) ===")
    
    # Render 16 glyphs from USA (at 0x29030) and RUS (at 0x2B030)
    for i in range(16):
        off_usa = 0x29030 + i * 32
        off_rus = 0x2B030 + i * 32
        
        g_usa = render_glyph(chr_usa[off_usa : off_usa + 32], 16, 16)
        g_rus = render_glyph(chr_rus[off_rus : off_rus + 32], 16, 16)
        
        print(f"\n--- Glyph Index {i:02d} | USA (0x{off_usa:05X}) vs RUS (0x{off_rus:05X}) ---")
        for y in range(16):
            print(f"  {g_usa[y]}    {g_rus[y]}")

if __name__ == "__main__":
    main()
