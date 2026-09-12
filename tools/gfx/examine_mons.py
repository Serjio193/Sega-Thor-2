#!/usr/bin/env python3
"""Investigate MONS.BIN structure and sub-archives."""
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.disc_extractor import SaturnDisc

def examine_mons():
    usa_disc = SaturnDisc(Path("Legend of Oasis The (USA)/Legend of Oasis, The (USA) (Track 1).bin"))
    mons = usa_disc.read_file("MONS.BIN")
    print(f"MONS.BIN size: {len(mons)} (0x{len(mons):X})")
    
    # Check first 128 bytes
    print("\nMONS.BIN first 128 bytes:")
    for i in range(0, 128, 16):
        row = mons[i:i+16]
        hex_s = " ".join(f"{b:02X}" for b in row)
        asc_s = "".join(chr(b) if 32 <= b < 127 else "." for b in row)
        print(f"  {i:04X}: {hex_s:<48} {asc_s}")
        
    # Check if there is a table of 32-bit offsets at the start
    print("\nFirst 32 BE32 values:")
    offsets = []
    for i in range(32):
        val = struct.unpack_from(">I", mons, i*4)[0]
        offsets.append(val)
        print(f"  [{i:02d}]: 0x{val:08X} ({val})")
        
    # Check if these point to valid sprite archives (header 0x0000000C)
    print("\nChecking if offsets point to SpriteArchive headers (0x0000000C):")
    valid_archives = 0
    for idx, off in enumerate(offsets):
        if 0 < off < len(mons) - 12:
            hdr_size, s_off, g_off = struct.unpack_from(">III", mons, off)
            if hdr_size == 12:
                valid_archives += 1
                print(f"  Offset [{idx}] at 0x{off:06X}: VALID SpriteArchive! anim_script=0x{s_off:X}, sprites=0x{g_off:X}")
            else:
                first4 = " ".join(f"{b:02X}" for b in mons[off:off+16])
                print(f"  Offset [{idx}] at 0x{off:06X}: not sprite archive. First bytes: {first4}")

if __name__ == "__main__":
    examine_mons()
