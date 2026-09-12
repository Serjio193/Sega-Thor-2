#!/usr/bin/env python3
"""tools/map/map_triggers.py — Thor 2 Triggers and Warp Transitions Extractor.

Parses trigger bounding boxes, event IDs, and exit warp records located in
MAP.BIN room sectors, evaluated at runtime by 0x0604B070 (triggers) and
0x0600A416 (warps).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import struct


@dataclass
class TriggerBoundingBox:
    x_min: int
    y_min: int
    x_max: int
    y_max: int


@dataclass
class TriggerRecord:
    trigger_id: int
    room_id: int
    sector_index: int
    record_index: int
    bounds: TriggerBoundingBox
    trigger_type: int
    event_id: int
    one_shot: bool


@dataclass
class WarpRecord:
    exit_id: int
    source_room_id: int
    target_room_id: int
    sector_index: int
    record_index: int
    warp_type: int
    trigger_x: int
    trigger_y: int
    flags: int


class MapTriggerExtractor:
    """Extracts trigger volumes and exit warp records from room sectors."""

    def __init__(self, sector_bytes: bytes, sector_index: int, room_id: int):
        self.sector_bytes = sector_bytes
        self.sector_index = sector_index
        self.room_id = room_id

    def extract_triggers(self) -> List[TriggerRecord]:
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

        triggers: List[TriggerRecord] = []
        for r_idx in range(1, len(offsets) - 1):
            st = offsets[r_idx]
            en = offsets[r_idx + 1]
            chunk = self.sector_bytes[st:en]
            if len(chunk) in [12, 14, 16, 22, 30, 38] and len(chunk) >= 12:
                x1, y1, x2, y2, ttype, evid = struct.unpack('>hhhhhh', chunk[:12])
                if -8192 <= x1 <= 8192 and -8192 <= y1 <= 8192:
                    triggers.append(
                        TriggerRecord(
                            trigger_id=len(triggers),
                            room_id=self.room_id,
                            sector_index=self.sector_index,
                            record_index=r_idx,
                            bounds=TriggerBoundingBox(x1, y1, x2, y2),
                            trigger_type=ttype & 0xFFFF,
                            event_id=evid,
                            one_shot=bool(ttype & 0x8000),
                        )
                    )
        return triggers

    def extract_warps(self) -> List[WarpRecord]:
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

        warps: List[WarpRecord] = []
        for r_idx in range(1, len(offsets) - 1):
            st = offsets[r_idx]
            en = offsets[r_idx + 1]
            chunk = self.sector_bytes[st:en]
            if len(chunk) >= 6:
                h0 = struct.unpack('>H', chunk[:2])[0]
                if (h0 & 0xF000) in [0x0000, 0x0800, 0x1000, 0x2000, 0x3000, 0x4000]:
                    h1 = struct.unpack('>H', chunk[2:4])[0]
                    h2 = struct.unpack('>H', chunk[4:6])[0]
                    target_room = (h1 & 0x00FF) if (h1 & 0x00FF) < 104 else (h0 & 0x00FF) % 104
                    if len(chunk) >= 14:
                        ix, iy = struct.unpack('>hh', chunk[6:10])
                    else:
                        ix, iy = struct.unpack('>hh', chunk[2:6])
                    warps.append(
                        WarpRecord(
                            exit_id=len(warps),
                            source_room_id=self.room_id,
                            target_room_id=target_room,
                            sector_index=self.sector_index,
                            record_index=r_idx,
                            warp_type=h0,
                            trigger_x=int(ix),
                            trigger_y=int(iy),
                            flags=h2,
                        )
                    )
        return warps
