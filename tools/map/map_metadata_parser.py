#!/usr/bin/env python3
"""tools/map/map_metadata_parser.py — Thor 2 MAP.BIN Master Metadata Parser.

Extracts all room bounds, entity spawns, trigger volumes, and exit warps
from MAP.BIN disc sectors (sectors 823..1970).
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional
import json
import struct
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tools.map.map_collision import MapCollisionDecoder
from tools.map.map_entities import MapEntityExtractor
from tools.map.map_triggers import MapTriggerExtractor


@dataclass
class RoomHeaderBounds:
    room_id: int
    sector_lba: int
    sector_offset: str
    width_px: int
    height_px: int
    mode_flags: str
    min_x: int
    min_y: int
    max_x: int
    max_y: int
    entity_count_declared: int


class MapMetadataParser:
    """Master parser for MAP.BIN room records and metadata."""

    SECTOR_SIZE = 2048
    TAIL_START_SECTOR = 823
    TAIL_END_SECTOR = 1970

    def __init__(self, map_bytes: bytes):
        self.map_bytes = map_bytes

    def parse_room_header(self, sector_bytes: bytes, sec_idx: int, room_id: int) -> Optional[RoomHeaderBounds]:
        if len(sector_bytes) < 8:
            return None
        w0, w1, w2, w3 = struct.unpack('>4H', sector_bytes[:8])
        if not (w3 in range(0x10, 0x80) and w3 % 2 == 0):
            return None
        w4, w5 = struct.unpack('>HH', sector_bytes[8:12])
        if not (w4 > w3 and w5 > w4):
            return None

        # Record 0 is at offset w3
        rec0 = sector_bytes[w3 : w4]
        if len(rec0) < 14:
            return None

        w_px, h_px, ent_cnt, mode = struct.unpack('>HHHH', rec0[:8])
        min_x, min_y, max_x = struct.unpack('>hhh', rec0[8:14])
        max_y = struct.unpack('>h', rec0[14:16])[0] if len(rec0) >= 16 else 0

        return RoomHeaderBounds(
            room_id=room_id,
            sector_lba=sec_idx,
            sector_offset=f"0x{sec_idx * self.SECTOR_SIZE:06X}",
            width_px=w_px,
            height_px=h_px,
            mode_flags=f"0x{mode:04X}",
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
            entity_count_declared=ent_cnt,
        )

    def parse_all_rooms(self) -> Dict[str, any]:
        rooms = []
        all_entities = []
        all_triggers = []
        all_warps = []

        room_id = 0
        for sec_idx in range(self.TAIL_START_SECTOR, self.TAIL_END_SECTOR + 1):
            off = sec_idx * self.SECTOR_SIZE
            sec = self.map_bytes[off : off + self.SECTOR_SIZE]
            hdr = self.parse_room_header(sec, sec_idx, room_id)
            if not hdr:
                continue

            # Extract entities
            ee = MapEntityExtractor(sec, sec_idx, room_id)
            ents = ee.extract()
            all_entities.extend(ents)

            # Extract triggers and warps
            te = MapTriggerExtractor(sec, sec_idx, room_id)
            trigs = te.extract_triggers()
            all_triggers.extend(trigs)
            warps = te.extract_warps()
            all_warps.extend(warps)

            rooms.append({
                "header": asdict(hdr),
                "entities_count": len(ents),
                "triggers_count": len(trigs),
                "warps_count": len(warps),
            })
            room_id += 1

        return {
            "total_rooms": len(rooms),
            "total_entities": len(all_entities),
            "total_triggers": len(all_triggers),
            "total_warps": len(all_warps),
            "rooms": rooms,
        }


def main():
    map_path = Path('.private/usa/MAP.BIN')
    if not map_path.exists():
        print(f"MAP.BIN not found at {map_path}")
        return
    data = map_path.read_bytes()
    parser = MapMetadataParser(data)
    result = parser.parse_all_rooms()
    print(f"Parsed {result['total_rooms']} rooms from MAP.BIN:")
    print(f"  Entities: {result['total_entities']}")
    print(f"  Triggers: {result['total_triggers']}")
    print(f"  Warps: {result['total_warps']}")


if __name__ == '__main__':
    main()
