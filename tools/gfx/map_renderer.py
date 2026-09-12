#!/usr/bin/env python3
"""tools/gfx/map_renderer.py — Offline VDP2 Map and Room Tile Renderer.

Renders decompressed 49,152-byte room tile patterns and pattern-name maps
from MAP.BIN into deterministic PNG images and metadata.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import struct
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.chr_decompressor import AncientDecompressor


def create_png(width: int, height: int, rgba_bytes: bytes) -> bytes:
    """Creates a raw 32-bit RGBA PNG image without external dependencies."""
    def chunk(chunk_type: bytes, chunk_data: bytes) -> bytes:
        c = chunk_type + chunk_data
        crc = zlib.crc32(c) & 0xFFFFFFFF
        return struct.pack(">I", len(chunk_data)) + c + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw_lines = bytearray()
    row_stride = width * 4
    for y in range(height):
        raw_lines.append(0)  # Filter type None
        start = y * row_stride
        raw_lines.extend(rgba_bytes[start : start + row_stride])

    idat = zlib.compress(bytes(raw_lines), level=9)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def decode_4bpp_tiles(tile_data: bytes, palette_rgb: List[Tuple[int, int, int]]) -> bytes:
    """Decodes 4bpp linear 8x8 tiles into 32-bit RGBA pixels.

    Each 8x8 tile is 32 bytes (2 pixels per byte, 4 bits each).
    Tile data of 49,152 bytes contains exactly 1,536 tiles.
    We arrange them in a grid of 32 tiles wide (256 pixels) x 48 tiles high (384 pixels).
    """
    tiles_x = 32
    tiles_y = (len(tile_data) // 32 + tiles_x - 1) // tiles_x
    img_width = tiles_x * 8
    img_height = tiles_y * 8
    rgba = bytearray(img_width * img_height * 4)

    num_tiles = len(tile_data) // 32
    for t in range(num_tiles):
        tile_x = (t % tiles_x) * 8
        tile_y = (t // tiles_x) * 8
        tile_offset = t * 32

        for y in range(8):
            row_bytes = tile_data[tile_offset + y * 4 : tile_offset + (y + 1) * 4]
            for x in range(4):
                b = row_bytes[x]
                p0 = (b >> 4) & 0x0F
                p1 = b & 0x0F

                # Pixel 0
                px0 = tile_x + x * 2
                py0 = tile_y + y
                dest_idx0 = (py0 * img_width + px0) * 4
                c0 = palette_rgb[p0] if p0 < len(palette_rgb) else (0, 0, 0)
                a0 = 0 if p0 == 0 else 255
                rgba[dest_idx0 : dest_idx0 + 4] = bytes([c0[0], c0[1], c0[2], a0])

                # Pixel 1
                px1 = tile_x + x * 2 + 1
                py1 = tile_y + y
                dest_idx1 = (py1 * img_width + px1) * 4
                c1 = palette_rgb[p1] if p1 < len(palette_rgb) else (0, 0, 0)
                a1 = 0 if p1 == 0 else 255
                rgba[dest_idx1 : dest_idx1 + 4] = bytes([c1[0], c1[1], c1[2], a1])

    return img_width, img_height, bytes(rgba)


def generate_default_palette() -> List[Tuple[int, int, int]]:
    """Generates standard 16-color test palette for VDP2 background tiles."""
    return [
        (0, 0, 0),
        (30, 80, 50),
        (50, 110, 70),
        (80, 140, 90),
        (120, 170, 110),
        (160, 200, 130),
        (200, 220, 160),
        (230, 240, 190),
        (90, 60, 40),
        (120, 80, 50),
        (150, 110, 70),
        (180, 140, 90),
        (210, 180, 120),
        (70, 100, 140),
        (110, 140, 180),
        (255, 255, 255),
    ]


class MapRenderer:
    """Renderer for MAP.BIN room packages and tilemaps."""

    def __init__(self, map_bin_path: Path):
        self.map_data = map_bin_path.read_bytes()
        self.decompressor = AncientDecompressor()
        self.palette = generate_default_palette()

    def render_room(self, lba: int, tag: str, output_path: Path) -> Dict:
        """Decompresses and renders a single room's 48KB tile payload to PNG."""
        off = lba * 2048
        res = self.decompressor.decompress(self.map_data, off)

        width, height, rgba = decode_4bpp_tiles(res.data, self.palette)
        png_bytes = create_png(width, height, rgba)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(png_bytes)

        return {
            "room_tag": tag,
            "lba": lba,
            "disc_offset": off,
            "compressed_size": res.bytes_consumed,
            "decompressed_size": len(res.data),
            "tile_count": len(res.data) // 32,
            "dimensions": [width, height],
            "output_png": str(output_path.name),
        }

    def render_all_rooms(self, output_dir: Path) -> List[Dict]:
        """Renders all 45 rooms in MAP.BIN into PNG tile sheets."""
        results = []
        total_sectors = len(self.map_data) // 2048
        room_idx = 0

        for lba in range(total_sectors):
            off = lba * 2048
            if self.map_data[off + 2 : off + 4] == b"P<":
                tag = self.map_data[off : off + 2].decode("latin1", errors="replace")
                clean_tag = "".join(c if c.isalnum() else "_" for c in tag)
                png_name = f"room_{room_idx:02d}_{clean_tag}.png"
                rec = self.render_room(lba, tag, output_dir / png_name)
                rec["room_index"] = room_idx
                results.append(rec)
                room_idx += 1

        manifest_path = output_dir / "map_render_manifest.json"
        manifest_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        return results


def main():
    map_path = Path(".private/usa/MAP.BIN")
    if not map_path.exists():
        print(f"MAP.BIN not found at {map_path}")
        sys.exit(1)

    out_dir = Path(".private/extracted_graphics/rooms")
    renderer = MapRenderer(map_path)
    print("Rendering all 45 rooms from MAP.BIN...")
    results = renderer.render_all_rooms(out_dir)
    print(f"Successfully rendered {len(results)} rooms to {out_dir}")


if __name__ == "__main__":
    main()
