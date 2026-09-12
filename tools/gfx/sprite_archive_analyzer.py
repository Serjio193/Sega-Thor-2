#!/usr/bin/env python3
"""Analyzer and validator for Thor 2 SpriteArchive packages."""
import json
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.disc_extractor import SaturnDisc

SPRITE_CANDIDATES = [
    "ARELE.BIN", "BAW.BIN", "BRAS.BIN", "DIT.BIN", "EFREET.BIN",
    "SHADE.BIN", "P0.BIN", "P1.BIN", "P2.BIN", "P3.BIN", "P4.BIN"
]

CANONICAL_HEADER_SIZE = 12

def analyze_archive(data: bytes, filename: str) -> dict:
    if len(data) < CANONICAL_HEADER_SIZE:
        return {"status": "SPRITE_ARCHIVE_REJECTED", "reason": "too_small", "size": len(data)}
    
    header_size, anim_script_off, sprite_data_off = struct.unpack(">III", data[:12])
    
    valid = (
        header_size == CANONICAL_HEADER_SIZE and
        anim_script_off >= header_size and
        sprite_data_off >= anim_script_off and
        sprite_data_off <= len(data) and
        ((anim_script_off - header_size) % 2 == 0)
    )
    
    if not valid:
        return {
            "status": "SPRITE_ARCHIVE_REJECTED",
            "reason": "invalid_header",
            "header_size": header_size,
            "anim_script_offset": anim_script_off,
            "sprite_data_offset": sprite_data_off,
            "total_size": len(data)
        }
    
    num_anim_offsets = (anim_script_off - header_size) // 2
    anim_offsets = [struct.unpack(">H", data[12 + i*2 : 14 + i*2])[0] for i in range(num_anim_offsets)]
    anim_script_bytes = sprite_data_off - anim_script_off
    sprite_bytes = len(data) - sprite_data_off
    
    # Test encode roundtrip
    rebuilt = bytearray()
    rebuilt.extend(struct.pack(">III", header_size, anim_script_off, sprite_data_off))
    for off in anim_offsets:
        rebuilt.extend(struct.pack(">H", off))
    rebuilt.extend(data[anim_script_off:sprite_data_off])
    rebuilt.extend(data[sprite_data_off:])
    roundtrip_exact = (bytes(rebuilt) == data)
    
    status = "SPRITE_ARCHIVE_CONFIRMED" if roundtrip_exact else "SPRITE_ARCHIVE_VARIANT"
    
    return {
        "filename": filename,
        "status": status,
        "roundtrip_exact": roundtrip_exact,
        "header_size": header_size,
        "anim_script_offset": anim_script_off,
        "sprite_data_offset": sprite_data_off,
        "num_anim_offsets": num_anim_offsets,
        "anim_offsets_sample": anim_offsets[:8] if anim_offsets else [],
        "anim_script_bytes": anim_script_bytes,
        "sprite_bytes": sprite_bytes,
        "total_size": len(data)
    }

def main():
    rus_bin = Path("The_Story_of_Thor_2_[RUS]_(NTSC).bin")
    rus_disc = SaturnDisc(rus_bin)
    usa_bin = Path("Legend of Oasis The (USA)/Legend of Oasis, The (USA) (Track 1).bin")
    usa_disc = SaturnDisc(usa_bin)
    
    out_dir = Path("workstreams/T2-GFX-01")
    results = {"rus": {}, "usa": {}}
    
    print(f"{'Filename':<12} {'Rev':<5} {'Status':<25} {'Total Size':<10} {'Offsets':<8} {'Script':<8} {'Sprites':<10} {'Roundtrip'}")
    print("-" * 90)
    
    for fname in SPRITE_CANDIDATES:
        for rev_name, disc in [("RUS", rus_disc), ("USA", usa_disc)]:
            if fname in disc.files:
                data = disc.read_file(fname)
                res = analyze_archive(data, fname)
                results[rev_name.lower()][fname] = res
                print(f"{fname:<12} {rev_name:<5} {res['status']:<25} {res.get('total_size', 0):<10} {res.get('num_anim_offsets', 0):<8} {res.get('anim_script_bytes', 0):<8} {res.get('sprite_bytes', 0):<10} {res.get('roundtrip_exact', False)}")
            else:
                results[rev_name.lower()][fname] = {"status": "FILE_NOT_FOUND"}
    
    (out_dir / "sprite_archive_verification.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    rus_disc.close()
    usa_disc.close()

if __name__ == "__main__":
    main()
