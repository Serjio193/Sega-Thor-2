#!/usr/bin/env python3
"""tools/map/map_collision.py — Thor 2 Collision and Heightfield Decoder.

Decodes 48KB (49,152 bytes) decompressed collision buffers produced by
sub_4108 for High Work RAM at 0x060D3D34, evaluated at runtime by 0x060784B4.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import struct


@dataclass
class CollisionCell:
    elevation: int
    flags: int
    is_walkable: bool
    is_water: bool
    is_wall: bool
    is_pit: bool


@dataclass
class CollisionTile:
    tile_index: int
    cells: List[List[CollisionCell]]


class MapCollisionDecoder:
    """Decodes 48KB collision buffers into 8x8 cell tiles."""

    BUFFER_SIZE = 49152
    TILES_COUNT = 1536
    TILE_SIZE = 32

    def __init__(self, raw_buffer: bytes):
        if len(raw_buffer) != self.BUFFER_SIZE:
            raise ValueError(
                f"Collision buffer must be {self.BUFFER_SIZE} bytes, got {len(raw_buffer)}"
            )
        self.raw_buffer = raw_buffer

    def decode_cell(self, byte_val: int) -> CollisionCell:
        elevation = byte_val & 0x0F
        flags = (byte_val >> 4) & 0x0F
        is_wall = flags == 0x0F or elevation == 0x0F
        is_water = flags == 0x0E
        is_pit = flags == 0x0D
        is_walkable = not is_wall and not is_pit
        return CollisionCell(
            elevation=elevation,
            flags=flags,
            is_walkable=is_walkable,
            is_water=is_water,
            is_wall=is_wall,
            is_pit=is_pit,
        )

    def get_tile(self, tile_idx: int) -> CollisionTile:
        if not (0 <= tile_idx < self.TILES_COUNT):
            raise IndexError(f"Tile index {tile_idx} out of range (0..{self.TILES_COUNT-1})")
        offset = tile_idx * self.TILE_SIZE
        tile_bytes = self.raw_buffer[offset : offset + self.TILE_SIZE]
        
        # 32 bytes = 64 4-bit nibbles or 32 cells (8x4 or 8x8 4bpp)
        cells: List[List[CollisionCell]] = []
        for y in range(8):
            row: List[CollisionCell] = []
            for x in range(8):
                byte_offset = (y * 8 + x) // 2
                raw_byte = tile_bytes[byte_offset] if byte_offset < len(tile_bytes) else 0
                nibble = (raw_byte >> 4) if (x % 2 == 0) else (raw_byte & 0x0F)
                row.append(self.decode_cell(nibble))
            cells.append(row)
        return CollisionTile(tile_index=tile_idx, cells=cells)

    def sample_elevation(self, tile_x: int, tile_y: int, cell_x: int, cell_y: int, stride_tiles: int = 48) -> int:
        tile_idx = tile_y * stride_tiles + tile_x
        if tile_idx >= self.TILES_COUNT:
            return 0
        tile = self.get_tile(tile_idx)
        cx = max(0, min(7, cell_x))
        cy = max(0, min(7, cell_y))
        return tile.cells[cy][cx].elevation
