#!/usr/bin/env python3
"""Test decoding all monster sprite packages inside MONS.BIN."""
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.disc_extractor import SaturnDisc
from tools.gfx.sprite_archive_analyzer import analyze_archive

def main():
    mons = Path(".private/rus/MONS.BIN").read_bytes()
    
    # Identify sector starts
    starts = []
    for i in range(0, len(mons), 2048):
        if i + 16 <= len(mons) and mons[i+4:i+8] == b'\x00\x00\x00\x0C':
            starts.append(i)
            
    print(f"Found {len(starts)} monster package starts in MONS.BIN.")
    
    success = 0
    records = []
    for idx, start in enumerate(starts):
        end = starts[idx+1] if idx + 1 < len(starts) else len(mons)
        # Strip trailing padding zeros from end
        while end > start + 12 and mons[end-1] == 0:
            end -= 1
        # The archive payload starts at start + 4 (first 4 bytes are prefix)
        pkg_data = mons[start + 4 : end]
        w0, w1 = struct.unpack_from(">HH", mons, start)
        res = analyze_archive(pkg_data, f"MONS_{idx:02d}")
        
        if res["status"] == "SPRITE_ARCHIVE_CONFIRMED":
            success += 1
        records.append({
            "index": idx,
            "sector_offset": start,
            "prefix_w0": f"0x{w0:04X}",
            "prefix_w1": f"0x{w1:04X}",
            "archive_size": len(pkg_data),
            "status": res["status"],
            "offsets": res.get("num_anim_offsets", 0),
            "script_bytes": res.get("anim_script_bytes", 0),
            "sprite_bytes": res.get("sprite_bytes", 0)
        })
        print(f"[{idx:02d}] off 0x{start:06X}: status={res['status']} size={len(pkg_data):<6} offsets={res.get('num_anim_offsets', 0):<4} script={res.get('anim_script_bytes', 0):<5} sprites={res.get('sprite_bytes', 0):<6}")
        
    print(f"\nResult: {success}/{len(starts)} subarchives CONFIRMED as valid SpriteArchives!")

if __name__ == "__main__":
    main()
