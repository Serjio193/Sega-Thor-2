#!/usr/bin/env python3
"""tools/carver/detectors_data.py — Saturn Data, Table & Resource Detectors."""

from typing import Any, Dict, List, Optional
import struct

from .detector_base import CarverDetector, CandidateRange, CarverContext
from .interval_db import IntervalDatabase
from .provenance_dag import ProvenanceDAG


class LiteralPoolDetector(CarverDetector):
    """Detects PC-relative literal pool references (MOV.W, MOV.L, MOVA) from confirmed code."""

    def __init__(self) -> None:
        super().__init__("LITERAL_POOL_DETECTOR", "DATA", default_confidence="CONFIRMED")

    def detect(
        self,
        db: IntervalDatabase,
        dag: ProvenanceDAG,
        ctx: CarverContext,
    ) -> List[CandidateRange]:
        candidates: List[CandidateRange] = []

        for mod_name, meta in db.modules.items():
            if meta["cpu"] != "MASTER_SH2":
                continue
            raw = ctx.module_bytes.get(mod_name)
            if not raw:
                continue

            vma_base = meta["vma_base"]
            confirmed_ivs = [iv for iv in db.intervals[mod_name] if iv.classification == "CONFIRMED_CODE"]

            for iv in confirmed_ivs:
                parent_id = f"{mod_name}_{iv.offset_start:06X}"
                for off in range(iv.offset_start, iv.offset_end_exclusive, 2):
                    if off + 2 > len(raw):
                        break
                    op = (raw[off] << 8) | raw[off + 1]
                    pc = vma_base + off

                    target_pc: Optional[int] = None
                    target_len = 0

                    # MOV.W @(disp, PC), Rn: 0x9ndd
                    if (op & 0xF000) == 0x9000:
                        disp = op & 0x00FF
                        target_pc = pc + 4 + (disp * 2)
                        target_len = 2
                    # MOV.L @(disp, PC), Rn: 0xDndd
                    elif (op & 0xF000) == 0xD000:
                        disp = op & 0x00FF
                        target_pc = (pc & ~3) + 4 + (disp * 4)
                        target_len = 4
                    # MOVA @(disp, PC), R0: 0xC7dd
                    elif (op & 0xFF00) == 0xC700:
                        disp = op & 0x00FF
                        target_pc = (pc & ~3) + 4 + (disp * 4)
                        target_len = 4

                    if target_pc is not None:
                        t_off = target_pc - vma_base
                        if 0 <= t_off <= meta["size"] - target_len:
                            t_iv = db.find_interval(mod_name, t_off)
                            if t_iv and t_iv.classification == "UNKNOWN":
                                candidates.append(CandidateRange(
                                    module=mod_name,
                                    offset_start=t_off,
                                    offset_end_exclusive=t_off + target_len,
                                    classification="DATA",
                                    representation="RAW_DATA",
                                    subclass="LITERAL_POOL",
                                    confidence="CONFIRMED",
                                    evidence=[f"LITERAL_REF_FROM_0x{pc:08X}"],
                                    parent_node_id=parent_id,
                                    detector_name=self.name,
                                ))

        return candidates


class PointerTableDetector(CarverDetector):
    """Detects dense arrays of 32-bit Saturn RAM pointers inside UNKNOWN ranges."""

    def __init__(self) -> None:
        super().__init__("POINTER_TABLE_DETECTOR", "DATA", default_confidence="HIGH")

    def detect(
        self,
        db: IntervalDatabase,
        dag: ProvenanceDAG,
        ctx: CarverContext,
    ) -> List[CandidateRange]:
        candidates: List[CandidateRange] = []

        for mod_name, meta in db.modules.items():
            raw = ctx.module_bytes.get(mod_name)
            if not raw:
                continue

            unknown_ivs = [iv for iv in db.intervals[mod_name] if iv.classification == "UNKNOWN"]
            for iv in unknown_ivs:
                s_off = (iv.offset_start + 3) & ~3
                e_off = iv.offset_end_exclusive & ~3
                if e_off - s_off < 12:
                    continue

                ptr_run_start = None
                prev_off = None

                for off in range(s_off, e_off - 3, 4):
                    val = struct.unpack(">I", raw[off:off + 4])[0]
                    # Valid Saturn RAM pointers: HWR 0x06000000..0x06100000, LWR 0x00200000..0x00300000
                    is_valid_ptr = (0x06000000 <= val < 0x06100000) or (0x00200000 <= val < 0x00300000)

                    if is_valid_ptr:
                        if ptr_run_start is None:
                            ptr_run_start = off
                            prev_off = off
                        else:
                            prev_off = off
                    else:
                        if ptr_run_start is not None:
                            count = (prev_off - ptr_run_start) // 4 + 1
                            if count >= 3:
                                candidates.append(CandidateRange(
                                    module=mod_name,
                                    offset_start=ptr_run_start,
                                    offset_end_exclusive=prev_off + 4,
                                    classification="DATA",
                                    representation="RAW_DATA",
                                    subclass="POINTER_TABLE",
                                    confidence="HIGH",
                                    evidence=[f"POINTER_ARRAY_COUNT_{count}"],
                                    detector_name=self.name,
                                ))
                            ptr_run_start = None
                            prev_off = None

                if ptr_run_start is not None:
                    count = (prev_off - ptr_run_start) // 4 + 1
                    if count >= 3:
                        candidates.append(CandidateRange(
                            module=mod_name,
                            offset_start=ptr_run_start,
                            offset_end_exclusive=prev_off + 4,
                            classification="DATA",
                            representation="RAW_DATA",
                            subclass="POINTER_TABLE",
                            confidence="HIGH",
                            evidence=[f"POINTER_ARRAY_COUNT_{count}"],
                            detector_name=self.name,
                        ))

        return candidates


class MmioPointerDetector(CarverDetector):
    """Detects 32-bit pointers targeting Saturn MMIO registers (VDP1/2, SCU, SCSP)."""

    def __init__(self) -> None:
        super().__init__("MMIO_POINTER_DETECTOR", "DATA", default_confidence="HIGH")

    def detect(
        self,
        db: IntervalDatabase,
        dag: ProvenanceDAG,
        ctx: CarverContext,
    ) -> List[CandidateRange]:
        candidates: List[CandidateRange] = []
        for mod_name, meta in db.modules.items():
            raw = ctx.module_bytes.get(mod_name)
            if not raw:
                continue
            unknown_ivs = [iv for iv in db.intervals[mod_name] if iv.classification == "UNKNOWN"]
            for iv in unknown_ivs:
                s_off = (iv.offset_start + 3) & ~3
                e_off = iv.offset_end_exclusive & ~3
                for off in range(s_off, e_off - 3, 4):
                    val = struct.unpack(">I", raw[off:off + 4])[0]
                    # Saturn MMIO: 0x25C00000..0x25FFFFFF or SH-2 on-chip MMIO: 0xFFFFFE00..0xFFFFFFFF
                    if (0x25C00000 <= val < 0x26000000) or (0xFFFFFE00 <= val <= 0xFFFFFFFF):
                        candidates.append(CandidateRange(
                            module=mod_name,
                            offset_start=off,
                            offset_end_exclusive=off + 4,
                            classification="DATA",
                            representation="RAW_DATA",
                            subclass="MMIO_POINTER",
                            confidence="HIGH",
                            evidence=[f"MMIO_TARGET_0x{val:08X}"],
                            detector_name=self.name,
                        ))
        return candidates


class StringDetector(CarverDetector):
    """Detects null-terminated ASCII string sequences in UNKNOWN data."""

    def __init__(self) -> None:
        super().__init__("STRING_DETECTOR", "DATA", default_confidence="HIGH")

    def detect(
        self,
        db: IntervalDatabase,
        dag: ProvenanceDAG,
        ctx: CarverContext,
    ) -> List[CandidateRange]:
        candidates: List[CandidateRange] = []
        for mod_name, meta in db.modules.items():
            raw = ctx.module_bytes.get(mod_name)
            if not raw:
                continue
            unknown_ivs = [iv for iv in db.intervals[mod_name] if iv.classification == "UNKNOWN"]
            for iv in unknown_ivs:
                s = iv.offset_start
                e = iv.offset_end_exclusive
                cur_str_start = None
                for i in range(s, e):
                    b = raw[i]
                    if 32 <= b <= 126:  # Printable ASCII
                        if cur_str_start is None:
                            cur_str_start = i
                    elif b == 0:
                        if cur_str_start is not None:
                            length = i - cur_str_start
                            if length >= 4:
                                candidates.append(CandidateRange(
                                    module=mod_name,
                                    offset_start=cur_str_start,
                                    offset_end_exclusive=i + 1,
                                    classification="DATA",
                                    representation="RAW_DATA",
                                    subclass="STRING_TABLE",
                                    confidence="HIGH",
                                    evidence=[f"ASCII_STRING_LEN_{length}"],
                                    detector_name=self.name,
                                ))
                            cur_str_start = None
                    else:
                        cur_str_start = None
        return candidates


class PaddingDetector(CarverDetector):
    """Detects continuous runs of zero/alignment padding bytes."""

    def __init__(self) -> None:
        super().__init__("PADDING_DETECTOR", "PADDING", default_confidence="CONFIRMED")

    def detect(
        self,
        db: IntervalDatabase,
        dag: ProvenanceDAG,
        ctx: CarverContext,
    ) -> List[CandidateRange]:
        candidates: List[CandidateRange] = []
        for mod_name, meta in db.modules.items():
            raw = ctx.module_bytes.get(mod_name)
            if not raw:
                continue
            unknown_ivs = [iv for iv in db.intervals[mod_name] if iv.classification == "UNKNOWN"]
            for iv in unknown_ivs:
                s = iv.offset_start
                e = iv.offset_end_exclusive
                if e - s < 8:
                    continue
                # Check for runs of 0x00 or 0xFF
                run_byte = None
                run_start = None
                for i in range(s, e):
                    b = raw[i]
                    if b in (0x00, 0xFF):
                        if run_byte is None or run_byte != b:
                            if run_start is not None and (i - run_start) >= 8:
                                candidates.append(CandidateRange(
                                    module=mod_name,
                                    offset_start=run_start,
                                    offset_end_exclusive=i,
                                    classification="PADDING",
                                    representation="RAW_DATA",
                                    subclass="ALIGNMENT_PADDING",
                                    confidence="CONFIRMED",
                                    evidence=[f"PADDING_RUN_{run_byte:#04x}_{i - run_start}_BYTES"],
                                    detector_name=self.name,
                                ))
                            run_byte = b
                            run_start = i
                    else:
                        if run_start is not None and (i - run_start) >= 8:
                            candidates.append(CandidateRange(
                                module=mod_name,
                                offset_start=run_start,
                                offset_end_exclusive=i,
                                classification="PADDING",
                                representation="RAW_DATA",
                                subclass="ALIGNMENT_PADDING",
                                confidence="CONFIRMED",
                                evidence=[f"PADDING_RUN_{run_byte:#04x}_{i - run_start}_BYTES"],
                                detector_name=self.name,
                            ))
                        run_byte = None
                        run_start = None
                if run_start is not None and (e - run_start) >= 8:
                    candidates.append(CandidateRange(
                        module=mod_name,
                        offset_start=run_start,
                        offset_end_exclusive=e,
                        classification="PADDING",
                        representation="RAW_DATA",
                        subclass="ALIGNMENT_PADDING",
                        confidence="CONFIRMED",
                        evidence=[f"PADDING_RUN_{run_byte:#04x}_{e - run_start}_BYTES"],
                        detector_name=self.name,
                    ))
        return candidates
