#!/usr/bin/env python3
"""Analyze entropy and bit-level structure of CHR.BIN sub-blocks."""
import math
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.disc_extractor import SaturnDisc

def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    ent = 0.0
    n = len(data)
    for count in freq.values():
        p = count / n
        ent -= p * math.log2(p)
    return ent

def main():
    usa_disc = SaturnDisc(Path("Legend of Oasis The (USA)/Legend of Oasis, The (USA) (Track 1).bin"))
    chr_usa = usa_disc.read_file("CHR.BIN")
    
    blocks = [
        ("Block 0", 0x00000, 60048),
        ("Block 1", 0x0F000, 38704),
        ("Block 2", 0x18800, 2464),
        ("Block 3", 0x19800, 5088),
        ("Block 4", 0x1B000, 56288),
        ("Font 0",  0x29080, 160),
        ("Block 6", 0x41000, 13040),
        ("Block 7", 0x44800, 4912),
        ("Block 8", 0x46000, 2912),
        ("Block 9", 0x47000, 1616),
        ("Block 10",0x47800, 4048),
        ("Block 11",0x48800, 72064),
    ]
    
    for name, start, length in blocks:
        sub = chr_usa[start:start+length]
        ent = entropy(sub)
        h16 = " ".join(f"{b:02X}" for b in sub[:16])
        print(f"{name:<10} 0x{start:05X} (size {length:<6}): ent={ent:.3f} | {h16}")

if __name__ == "__main__":
    main()
