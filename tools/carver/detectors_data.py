#!/usr/bin/env python3
"""tools/carver/detectors_data.py — Saturn Data, Table & Resource Detectors.

Authoritative SH-2 PC-relative decoding is delegated 100% to C++ thor_sh2.
No hand-written Python opcode bitmasks or displacement arithmetic.
"""

from typing import Any, Dict, List, Optional
import struct

from .detector_base import CarverDetector, CandidateRange, CarverContext
from .interval_db import IntervalDatabase
from .provenance_dag import ProvenanceDAG
from .thor_decoder import decode_intervals_with_thor_sh2, DecodedInstruction


class LiteralPoolDetector(CarverDetector):
    """Detects PC-relative literal references using C++ thor_sh2 decoded instructions."""

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
            if not confirmed_ivs:
                continue

            # Query C++ thor_sh2 decoder: authoritative decode, no Python bitmasks
            instructions = decode_intervals_with_thor_sh2(
                ctx.repo_root, mod_name, vma_base, raw, confirmed_ivs
            )

            for ins in instructions:
                if not ins.is_pc_rel_data or ins.target_vma == 0:
                    continue

                target_pc = ins.target_vma
                target_len = ins.data_access_size
                t_off = target_pc - vma_base
                if 0 <= t_off <= meta["size"] - target_len:
                    t_iv = db.find_interval(mod_name, t_off)
                    if t_iv and t_iv.classification == "UNKNOWN":
                        parent_iv = db.find_interval(mod_name, ins.offset)
                        parent_id = f"{mod_name}_{parent_iv.offset_start:06X}" if parent_iv else None
                        candidates.append(CandidateRange(
                            module=mod_name,
                            offset_start=t_off,
                            offset_end_exclusive=t_off + target_len,
                            classification="DATA",
                            representation="RAW_DATA",
                            subclass="LITERAL_POOL",
                            confidence="CONFIRMED",
                            evidence=[f"LITERAL_REF_FROM_0x{ins.pc:08X}"],
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
                    if 32 <= b <= 126:
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
