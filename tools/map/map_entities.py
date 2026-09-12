#!/usr/bin/env python3
"""tools/map/map_entities.py — Thor 2 Map Entity Spawn Table Extractor.

Parses entity spawn definitions located in MAP.BIN room record pointer
sectors, consumed by entity dispatcher routine 0x06014A94 in 0TH2.BIN.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import struct


@dataclass
class SpawnCoordinate:
    x: int
    y: int
    z: int


@dataclass
class EntitySpawnRecord:
    entity_id: int
    room_id: int
    sector_index: int
    record_index: int
    type_id: int
    subtype: int
    spawn_coords: SpawnCoordinate
    flags: int
    script_id: int


class MapEntityExtractor:
    """Extracts entity spawn records from room sectors."""

    def __init__(self, sector_bytes: bytes, sector_index: int, room_id: int):
        self.sector_bytes = sector_bytes
        self.sector_index = sector_index
        self.room_id = room_id

    def extract(self) -> List[EntitySpawnRecord]:
        if len(self.sector_bytes) < 8:
            return []
        w0, w1, w2, w3 = struct.unpack('>4H', self.sector_bytes[:8])
        if not (w3 in range(0x10, 0x80) and w3 % 2 == 0):
            return []
        w4, w5 = struct.unpack('>HH', self.sector_bytes[8:12])
        if not (w4 > w3 and w5 > w4):
            return []

        num_recs = (w3 - 6) // 2
        offsets = [w3] + [
            struct.unpack('>H', self.sector_bytes[6 + i * 2 : 8 + i * 2])[0]
            for i in range(1, num_recs)
        ]

        entities: List[EntitySpawnRecord] = []
        for r_idx in range(1, len(offsets) - 1):
            st = offsets[r_idx]
            en = offsets[r_idx + 1]
            chunk = self.sector_bytes[st:en]
            if len(chunk) == 22:
                f0, x, f1, y, target_or_type, f2, f3, f4, f5, f6, f7 = struct.unpack(
                    '>HHHHHHHHHHH', chunk
                )
                sx = struct.unpack('>h', chunk[2:4])[0]
                sy = struct.unpack('>h', chunk[6:8])[0]
                # Filter out warp/exit records
                if (f0 & 0xFF00) not in [0x0800, 0x1000, 0x2000]:
                    entities.append(
                        EntitySpawnRecord(
                            entity_id=len(entities),
                            room_id=self.room_id,
                            sector_index=self.sector_index,
                            record_index=r_idx,
                            type_id=f0 & 0x00FF,
                            subtype=f0 >> 8,
                            spawn_coords=SpawnCoordinate(x=sx, y=sy, z=0),
                            flags=f1,
                            script_id=target_or_type,
                        )
                    )
            elif len(chunk) >= 14 and len(chunk) % 14 == 0:
                for k in range(0, len(chunk), 14):
                    sub = chunk[k : k + 14]
                    t, x, y, z, fl, sc, extra = struct.unpack('>HhhhHHH', sub)
                    entities.append(
                        EntitySpawnRecord(
                            entity_id=len(entities),
                            room_id=self.room_id,
                            sector_index=self.sector_index,
                            record_index=r_idx,
                            type_id=t & 0xFF,
                            subtype=t >> 8,
                            spawn_coords=SpawnCoordinate(x=x, y=y, z=z),
                            flags=fl,
                            script_id=sc,
                        )
                    )
        return entities
