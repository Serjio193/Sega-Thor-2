#!/usr/bin/env python3
"""Mass sprite exporter for Thor 2.

Exports deduplicated 4bpp VDP1 sprites to lossless PNGs with palette application,
pixel SHA-256 deduplication, and structured export manifest.
All outputs are stored in .private/extracted_sprites/ (repository hygiene safe).
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.inspect_palettes import decode_rgb555


def load_cram_palettes(cram_path: Path) -> Dict[int, List[Tuple[int, int, int]]]:
    """Load all 16-color banks from a 4KB VDP2 CRAM dump."""
    if not cram_path.exists():
        return {}
    cram = cram_path.read_bytes()
    palettes: Dict[int, List[Tuple[int, int, int]]] = {}
    num_banks = len(cram) // 32
    for b in range(num_banks):
        colors = []
        for i in range(16):
            w = struct.unpack_from(">H", cram, b * 32 + i * 2)[0]
            colors.append(decode_rgb555(w))
        palettes[b] = colors
    return palettes


def decode_4bpp_pixels(
    pix_data: bytes, width: int, height: int, palette: List[Tuple[int, int, int]]
) -> Image.Image:
    """Render 4bpp linear Saturn VDP1 sprite data to RGBA image."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    byte_idx = 0
    for y in range(height):
        for x in range(0, width, 2):
            if byte_idx < len(pix_data):
                b = pix_data[byte_idx]
                byte_idx += 1
                p0 = (b >> 4) & 0x0F
                p1 = b & 0x0F
                if p0 != 0 and p0 < len(palette):
                    img.putpixel((x, y), (*palette[p0], 255))
                if x + 1 < width and p1 != 0 and p1 < len(palette):
                    img.putpixel((x + 1, y), (*palette[p1], 255))
    return img


def export_all_sprites() -> None:
    root = Path(__file__).resolve().parents[2]
    out_dir = root / ".private" / "extracted_sprites"
    out_dir.mkdir(parents=True, exist_ok=True)
    usa_dir = root / ".private" / "usa"
    records_file = root / "workstreams" / "T2-GFX-01.5" / "sprite_records.json"
    cram_file = (
        root / ".private" / "vdp1_captures" / "frame_2200_idle" / "vdp2_cram.bin"
    )

    if not records_file.exists():
        print(f"Error: {records_file} not found. Run sprite_mapper.py first.")
        return

    palettes = load_cram_palettes(cram_file)
    default_palette = palettes.get(3, [(i * 16, i * 16, i * 16) for i in range(16)])
    records: List[Dict[str, Any]] = json.loads(records_file.read_text(encoding="utf-8"))

    print(f"Loaded {len(records)} sprite records.")
    exported_count = 0
    unique_hashes: Dict[str, str] = {}
    manifest_entries: List[Dict[str, Any]] = []

    # Cache loaded binary files
    loaded_files: Dict[str, bytes] = {}

    for rec in records:
        arch = rec["archive_name"]
        w = rec["pixel_width"]
        h = rec["pixel_height"]
        pix_bytes = rec["pixel_bytes"]
        pix_off = rec["pixel_data_offset"]

        if w <= 0 or h <= 0 or pix_bytes <= 0:
            continue

        # Load archive raw bytes
        if arch.startswith("MONS_"):
            source_file = "MONS.BIN"
        else:
            source_file = arch

        if source_file not in loaded_files:
            fp = usa_dir / source_file
            if fp.exists():
                loaded_files[source_file] = fp.read_bytes()
            else:
                continue

        fbytes = loaded_files[source_file]
        if pix_off + pix_bytes > len(fbytes):
            continue

        pix_data = fbytes[pix_off : pix_off + pix_bytes]

        # Select appropriate palette bank
        if arch in ("P0.BIN", "P1.BIN", "P2.BIN", "P3.BIN"):
            pal = palettes.get(3, default_palette)  # Bank 3: Leon
            pal_id = 3
        elif arch.startswith("MONS_"):
            pal = palettes.get(2, default_palette)  # Bank 2: Monster/Ordan
            pal_id = 2
        else:
            pal = palettes.get(1, default_palette)  # Bank 1: Spirit/UI
            pal_id = 1

        img = decode_4bpp_pixels(pix_data, w, h, pal)
        img_bytes = img.tobytes()
        sha256_hash = hashlib.sha256(img_bytes).hexdigest()

        is_duplicate = sha256_hash in unique_hashes
        if not is_duplicate:
            img_name = f"{arch.lower()}_rec{rec['record_idx']:03d}_{w}x{h}.png"
            img.save(out_dir / img_name)
            unique_hashes[sha256_hash] = img_name
            canonical_name = img_name
            exported_count += 1
        else:
            canonical_name = unique_hashes[sha256_hash]

        manifest_entries.append(
            {
                "archive_name": arch,
                "record_idx": rec["record_idx"],
                "file_offset": f"0x{rec['descriptor_offset']:06X}",
                "pixel_offset": f"0x{pix_off:06X}",
                "dimensions": {"width": w, "height": h},
                "byte_size": pix_bytes,
                "palette_bank": pal_id,
                "pixel_sha256": sha256_hash,
                "is_duplicate": is_duplicate,
                "image_file": canonical_name,
            }
        )

    # Save export manifest inside .private/
    manifest_path = out_dir / "sprite_export_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "total_records": len(records),
                "unique_sprites": len(unique_hashes),
                "exported_pngs": exported_count,
                "sprites": manifest_entries,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"Exported {exported_count} unique PNG sprites ({len(unique_hashes)} unique hashes) to {out_dir}"
    )
    print(f"Manifest written to {manifest_path}")


def main() -> None:
    export_all_sprites()


if __name__ == "__main__":
    main()
