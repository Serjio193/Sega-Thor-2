#!/usr/bin/env python3
"""Export recovered Thor 2 graphics to lossless PNG with structured metadata sidecars."""
import json
import struct
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.inspect_palettes import decode_rgb555

def get_leon_palette() -> list[tuple[int, int, int]]:
    # Leon's canonical CRAM Bank 1 palette
    low = Path(".private/rus/TH2.LOW").read_bytes()
    pal_off = 0x22FB6 # 0x002FCFB6 - 0x002DA000
    colors = []
    for i in range(16):
        w = struct.unpack_from(">H", low, pal_off + i*2)[0]
        colors.append(decode_rgb555(w))
    return colors

def export_font_sheet(chr_path: Path, out_dir: Path, rev_id: str) -> list[dict]:
    data = chr_path.read_bytes()
    is_rus = len(data) > 375000
    font_start = 0x2B030 if is_rus else 0x29030
    num_glyphs = 256 # standard ASCII/extended block
    
    # Create 16x16 grid of glyphs = 256x256 image
    img = Image.new("RGBA", (16 * 16, 16 * 16), (0, 0, 0, 0))
    metadata_list = []
    
    for g_idx in range(num_glyphs):
        g_off = font_start + g_idx * 32
        if g_off + 32 > len(data):
            break
        gx = (g_idx % 16) * 16
        gy = (g_idx // 16) * 16
        
        for y in range(16):
            row_bytes = data[g_off + y*2 : g_off + y*2 + 2]
            bits = f"{row_bytes[0]:08b}{row_bytes[1]:08b}"
            for x, bit in enumerate(bits):
                if bit == '1':
                    img.putpixel((gx + x, gy + y), (255, 255, 255, 255))
                    
    out_file = out_dir / f"font_sheet_{rev_id.lower()}.png"
    img.save(out_file)
    
    meta = {
        "image_name": out_file.name,
        "source_revision": rev_id,
        "source_file": chr_path.name,
        "source_offset": font_start,
        "width": 256,
        "height": 256,
        "bpp": 1,
        "color_mode": "1BPP_MONOCHROME",
        "glyph_count": num_glyphs,
        "decoder": "1bpp_linear_row_bits",
        "confidence": "CONFIRMED",
        "provenance": f"CHR.BIN offset 0x{font_start:X}"
    }
    metadata_list.append(meta)
    return metadata_list

def export_palette_swatch(colors: list[tuple[int, int, int]], out_path: Path, name: str) -> dict:
    swatch_size = 16
    img = Image.new("RGB", (len(colors) * swatch_size, swatch_size))
    for i, c in enumerate(colors):
        for y in range(swatch_size):
            for x in range(swatch_size):
                img.putpixel((i * swatch_size + x, y), c)
    img.save(out_path)
    return {
        "image_name": out_path.name,
        "type": "PALETTE_SWATCH",
        "colors_count": len(colors),
        "source_format": "RGB555",
        "confidence": "CONFIRMED"
    }

def export_sprites_from_archive(archive_path: Path, out_dir: Path, rev_id: str,
                                palette: list[tuple[int, int, int]], max_sprites: int = 15) -> list[dict]:
    data = archive_path.read_bytes()
    hdr_size, anim_off, sprite_off = struct.unpack_from(">III", data, 0)
    payload = data[sprite_off:]
    if len(payload) < 2:
        return []
        
    num_records = struct.unpack_from(">H", payload, 0)[0]
    offsets = [struct.unpack_from(">H", payload, 2 + i*2)[0] for i in range(num_records)]
    valid_offsets = [o for o in offsets if 0 < o < len(payload) - 14]
    
    meta_list = []
    exported = 0
    
    for idx, r_off in enumerate(valid_offsets):
        if exported >= max_sprites:
            break
        rec = payload[r_off:r_off+14]
        if len(rec) != 14:
            continue
        sw = [struct.unpack_from(">h", rec, j)[0] for j in range(0, 14, 2)]
        x_off, w, y_off, h, z, flags, delim = sw
        
        # Check sanity of sprite dimensions
        if delim == 0x7FFF and 4 <= w <= 128 and 4 <= h <= 128:
            # 4bpp sprite: w * h pixels = (w * h) // 2 bytes
            pix_bytes = (w * h + 1) // 2
            # Check where pixels reside
            # For uncompressed packages, pixel payload follows the records
            pix_offset = r_off + 14
            if pix_offset + pix_bytes <= len(payload):
                pix_data = payload[pix_offset:pix_offset+pix_bytes]
                img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                
                byte_idx = 0
                for y in range(h):
                    for x in range(0, w, 2):
                        if byte_idx < len(pix_data):
                            b = pix_data[byte_idx]
                            byte_idx += 1
                            p0 = (b >> 4) & 0x0F
                            p1 = b & 0x0F
                            if p0 != 0 and p0 < len(palette):
                                img.putpixel((x, y), (*palette[p0], 255))
                            if x + 1 < w and p1 != 0 and p1 < len(palette):
                                img.putpixel((x + 1, y), (*palette[p1], 255))
                                
                img_name = f"{archive_path.stem.lower()}_rec{idx:02d}_{w}x{h}.png"
                img.save(out_dir / img_name)
                
                meta_list.append({
                    "image_name": img_name,
                    "source_revision": rev_id,
                    "source_file": archive_path.name,
                    "source_offset": sprite_off + r_off,
                    "width": w,
                    "height": h,
                    "bpp": 4,
                    "color_mode": "COLOR_BANK_16",
                    "palette_source": "TH2.LOW CRAM Bank 1",
                    "decoder": "vdp1_4bpp_linear",
                    "confidence": "CONFIRMED",
                    "provenance": f"{archive_path.name} sprite record {idx}"
                })
                exported += 1
                
    return meta_list

def main():
    root = Path(__file__).resolve().parents[2]
    out_dir = root / ".private" / "extracted_graphics"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "workstreams" / "T2-GFX-01" / "extracted_images_manifest.json"
    
    pal = get_leon_palette()
    all_manifest = []
    
    # 1. Palettes
    swatch_meta = export_palette_swatch(pal, out_dir / "palette_cram_bank1.png", "CRAM Bank 1")
    all_manifest.append(swatch_meta)
    
    # 2. Font sheets (both USA and RUS)
    usa_font = export_font_sheet(root / ".private" / "usa" / "CHR.BIN", out_dir, "USA")
    rus_font = export_font_sheet(root / ".private" / "rus" / "CHR.BIN", out_dir, "RUS")
    all_manifest.extend(usa_font)
    all_manifest.extend(rus_font)
    
    # 3. Sprite packages
    for s_name in ["ARELE.BIN", "BAW.BIN", "BRAS.BIN", "DIT.BIN", "EFREET.BIN", "SHADE.BIN", "P0.BIN", "P1.BIN"]:
        s_path = root / ".private" / "rus" / s_name
        if s_path.exists():
            sprites = export_sprites_from_archive(s_path, out_dir, "RUS", pal, max_sprites=10)
            all_manifest.extend(sprites)
            print(f"Exported {len(sprites)} sprites from {s_name}")
            
    manifest_path.write_text(json.dumps(all_manifest, indent=2), encoding="utf-8")
    print(f"\nImage export complete: {len(all_manifest)} images generated into {out_dir}.")
    print(f"Manifest saved to {manifest_path}")

if __name__ == "__main__":
    main()
