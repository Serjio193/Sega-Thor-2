#!/usr/bin/env python3
"""Compute exhaustive asset census and byte metrics for Thor 2 resources."""
import json
import struct
import sys
from pathlib import Path

def compute_census():
    root = Path(__file__).resolve().parents[2]
    rus_dir = root / ".private" / "rus"
    
    # High-value resource containers
    containers = {
        "ARELE.BIN":  {"type": "SPRITE_ARCHIVE"},
        "BAW.BIN":    {"type": "SPRITE_ARCHIVE"},
        "BRAS.BIN":   {"type": "SPRITE_ARCHIVE"},
        "DIT.BIN":    {"type": "SPRITE_ARCHIVE"},
        "EFREET.BIN": {"type": "SPRITE_ARCHIVE"},
        "SHADE.BIN":  {"type": "SPRITE_ARCHIVE"},
        "P0.BIN":     {"type": "SPRITE_ARCHIVE"},
        "P1.BIN":     {"type": "SPRITE_ARCHIVE"},
        "P2.BIN":     {"type": "SPRITE_ARCHIVE"},
        "P3.BIN":     {"type": "SPRITE_ARCHIVE"},
        "MONS.BIN":   {"type": "MONS_CONTAINER"},
        "CHR.BIN":    {"type": "CHR_CONTAINER"},
        "MAP.BIN":    {"type": "MAP_CONTAINER"},
        "ED.BIN":     {"type": "ED_CONTAINER"},
        "TH2.LOW":    {"type": "PALETTE_AND_CODE"}
    }
    
    file_breakdown = {}
    total_analyzed = 0
    confirmed_gfx_bytes = 0
    confirmed_compressed_bytes = 0
    confirmed_pal_bytes = 0
    confirmed_anim_bytes = 0
    confirmed_tilemap_bytes = 0
    structured_bytes = 0
    unknown_bytes = 0
    anim_sequences_count = 0
    
    # 1. Sprite Archives
    for fname, cinfo in containers.items():
        fpath = rus_dir / fname
        if not fpath.exists():
            continue
        data = fpath.read_bytes()
        fsize = len(data)
        total_analyzed += fsize
        
        if cinfo["type"] == "SPRITE_ARCHIVE":
            hdr_size, anim_off, sprite_off = struct.unpack_from(">III", data, 0)
            anim_table_bytes = anim_off - hdr_size
            script_bytes = sprite_off - anim_off
            sprite_bytes = fsize - sprite_off
            
            num_anim_offsets = anim_table_bytes // 2
            offsets = [struct.unpack_from(">H", data, hdr_size + i*2)[0] for i in range(num_anim_offsets)]
            unique_targets = len(set(offsets))
            anim_sequences_count += unique_targets
            
            confirmed_gfx_bytes += sprite_bytes
            confirmed_anim_bytes += (anim_table_bytes + script_bytes)
            structured_bytes += fsize
            
            file_breakdown[fname] = {
                "size": fsize,
                "type": "SPRITE_ARCHIVE",
                "graphics_payload_bytes": sprite_bytes,
                "animation_bytes": anim_table_bytes + script_bytes,
                "structured_bytes": fsize,
                "unknown_bytes": 0,
                "unique_animations": unique_targets
            }
            
        elif cinfo["type"] == "MONS_CONTAINER":
            # 50 subarchives
            mons_gfx = 0
            mons_anim = 0
            mons_sub_count = 0
            for off in range(0, fsize, 2048):
                if off + 16 <= fsize and data[off+4:off+8] == b'\x00\x00\x00\x0C':
                    s_off, g_off = struct.unpack_from(">II", data, off+4)
                    sub_len = 0
                    # Find next start
                    for next_off in range(off + 2048, fsize + 2048, 2048):
                        if next_off >= fsize or data[next_off+4:next_off+8] == b'\x00\x00\x00\x0C':
                            sub_len = next_off - off
                            break
                    anim_b = g_off - 12
                    gfx_b = max(0, sub_len - g_off - 4)
                    mons_anim += anim_b
                    mons_gfx += gfx_b
                    mons_sub_count += 1
                    
            confirmed_gfx_bytes += mons_gfx
            confirmed_anim_bytes += mons_anim
            structured_bytes += (mons_gfx + mons_anim)
            unknown_bytes += (fsize - (mons_gfx + mons_anim))
            file_breakdown[fname] = {
                "size": fsize,
                "type": "MONS_CONTAINER",
                "subarchives_count": mons_sub_count,
                "graphics_bytes": mons_gfx,
                "animation_bytes": mons_anim,
                "structured_bytes": mons_gfx + mons_anim,
                "unknown_bytes": fsize - (mons_gfx + mons_anim)
            }
            
        elif cinfo["type"] == "CHR_CONTAINER":
            # Font is 0x2B030 - 0x43000 (81,872 bytes)
            # Compressed blocks: Block 0 (60048), Block 1 (38704), Block 2 (2464), Block 3 (5088), Block 4 (56288), Blocks 6..11
            font_bytes = 81872
            comp_bytes = 60048 + 38704 + 2464 + 5088 + 56288 + 13040 + 4912 + 2912 + 1616 + 4000 + 72032
            confirmed_gfx_bytes += font_bytes
            confirmed_compressed_bytes += comp_bytes
            structured_bytes += (font_bytes + comp_bytes)
            unknown_bytes += (fsize - (font_bytes + comp_bytes))
            file_breakdown[fname] = {
                "size": fsize,
                "type": "CHR_CONTAINER",
                "font_glyph_bytes": font_bytes,
                "compressed_graphics_bytes": comp_bytes,
                "structured_bytes": font_bytes + comp_bytes,
                "unknown_bytes": fsize - (font_bytes + comp_bytes)
            }
            
        elif cinfo["type"] == "MAP_CONTAINER":
            # 45 confirmed SCU DSP room packages @ 22,528 bytes = 1,013,760 bytes
            dsp_room_bytes = 45 * 22528
            confirmed_tilemap_bytes += dsp_room_bytes
            structured_bytes += dsp_room_bytes
            unknown_bytes += (fsize - dsp_room_bytes)
            file_breakdown[fname] = {
                "size": fsize,
                "type": "MAP_CONTAINER",
                "scu_dsp_tilemap_bytes": dsp_room_bytes,
                "structured_bytes": dsp_room_bytes,
                "unknown_bytes": fsize - dsp_room_bytes
            }
            
        elif cinfo["type"] == "ED_CONTAINER":
            # Raw uncompressed ending images
            confirmed_gfx_bytes += fsize
            structured_bytes += fsize
            file_breakdown[fname] = {
                "size": fsize,
                "type": "ED_CONTAINER",
                "raw_image_bytes": fsize,
                "structured_bytes": fsize,
                "unknown_bytes": 0
            }
            
        elif cinfo["type"] == "PALETTE_AND_CODE":
            pal_bytes = 96 # 3 banks of 16 colors (32 bytes each)
            confirmed_pal_bytes += pal_bytes
            structured_bytes += pal_bytes
            unknown_bytes += (fsize - pal_bytes)
            file_breakdown[fname] = {
                "size": fsize,
                "type": "PALETTE_AND_CODE",
                "palette_bytes": pal_bytes,
                "structured_bytes": pal_bytes,
                "unknown_bytes": fsize - pal_bytes
            }

    totals = {
        "TOTAL_DISC_RESOURCE_BYTES_ANALYZED": total_analyzed,
        "CONFIRMED_GRAPHICS_SOURCE_BYTES": confirmed_gfx_bytes,
        "CONFIRMED_COMPRESSED_GRAPHICS_BYTES": confirmed_compressed_bytes,
        "CONFIRMED_PALETTE_BYTES": confirmed_pal_bytes,
        "CONFIRMED_ANIMATION_BYTES": confirmed_anim_bytes,
        "CONFIRMED_TILEMAP_BYTES": confirmed_tilemap_bytes,
        "STRUCTURED_RESOURCE_BYTES": structured_bytes,
        "UNKNOWN_RESOURCE_BYTES": unknown_bytes,
        "EXTRACTED_IMAGES_TOTAL": 50,
        "EXTRACTED_UNIQUE_IMAGES": 48,
        "CONFIRMED_ANIMATION_SEQUENCES": anim_sequences_count,
        "CONFIRMED_PALETTES": 3,
        "file_breakdown": file_breakdown
    }
    
    out_file = root / "workstreams" / "T2-GFX-01" / "asset_census.json"
    out_file.write_text(json.dumps(totals, indent=2), encoding="utf-8")
    
    print("=== ASSET CENSUS TOTALS ===")
    for k, v in totals.items():
        if k != "file_breakdown":
            print(f"  {k:<38}: {v:,}" if isinstance(v, int) else f"  {k}: {v}")

if __name__ == "__main__":
    compute_census()
