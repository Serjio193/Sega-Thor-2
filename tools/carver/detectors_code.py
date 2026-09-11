#!/usr/bin/env python3
"""tools/carver/detectors_code.py — Saturn Code & Control-Flow Detectors."""

from typing import Any, Dict, List, Optional
import struct

from .detector_base import CarverDetector, CandidateRange, CarverContext
from .interval_db import IntervalDatabase
from .provenance_dag import ProvenanceDAG


def sign_extend_8(val: int) -> int:
    return (val - 256) if (val & 0x80) else val


def sign_extend_12(val: int) -> int:
    return (val - 4096) if (val & 0x800) else val


class ExecutedPcDetector(CarverDetector):
    """Detects dynamically retired CPU instructions from CDL traces (Rule 4)."""

    def __init__(self) -> None:
        super().__init__("EXECUTED_PC_DETECTOR", "CODE", default_confidence="CONFIRMED")

    def detect(
        self,
        db: IntervalDatabase,
        dag: ProvenanceDAG,
        ctx: CarverContext,
    ) -> List[CandidateRange]:
        candidates: List[CandidateRange] = []

        for mod_name, meta in db.modules.items():
            mod_size = meta["size"]
            vma_base = meta["vma_base"]
            cpu = meta["cpu"]

            cdl_data: Optional[bytes] = None
            cdl_offset_in_ram = 0

            if cpu == "MASTER_SH2":
                # Check HWR (0x06000000..0x06100000)
                if 0x06000000 <= vma_base < 0x06100000 and ctx.cdl_hwr:
                    cdl_data = ctx.cdl_hwr
                    cdl_offset_in_ram = vma_base - 0x06000000
                # Check LWR (0x00200000..0x00300000)
                elif 0x00200000 <= vma_base < 0x00300000 and ctx.cdl_lwr:
                    cdl_data = ctx.cdl_lwr
                    cdl_offset_in_ram = vma_base - 0x00200000

            if not cdl_data:
                continue

            # Identify executed bytes landing in UNKNOWN intervals
            unknown_ivs = [iv for iv in db.intervals[mod_name] if iv.classification == "UNKNOWN"]
            for iv in unknown_ivs:
                s_off = iv.offset_start
                e_off = iv.offset_end_exclusive

                # Scan CDL for execution bits (bit 0 set)
                exec_indices = []
                for off in range(s_off, e_off):
                    ram_off = cdl_offset_in_ram + off
                    if 0 <= ram_off < len(cdl_data):
                        if cdl_data[ram_off] & 1:
                            exec_indices.append(off)

                if not exec_indices:
                    continue

                # Group contiguous executed runs
                run_start = None
                prev = None
                for idx in exec_indices:
                    if run_start is None:
                        run_start = idx
                        prev = idx
                    elif idx == prev + 1:
                        prev = idx
                    else:
                        # Ensure 2-byte instruction alignment
                        align_s = run_start & ~1
                        align_e = ((prev + 1) + 1) & ~1
                        align_e = min(align_e, e_off)
                        candidates.append(CandidateRange(
                            module=mod_name,
                            offset_start=align_s,
                            offset_end_exclusive=align_e,
                            classification="CONFIRMED_CODE",
                            representation="RAW_CODE_PENDING",
                            confidence="CONFIRMED",
                            evidence=["DYNAMIC_CPU_RETIREMENT", f"CDL_HIT_0x{vma_base + align_s:08X}"],
                            detector_name=self.name,
                            block_id=f"cand_exec_{vma_base + align_s:08X}",
                        ))
                        run_start = idx
                        prev = idx

                if run_start is not None:
                    align_s = run_start & ~1
                    align_e = ((prev + 1) + 1) & ~1
                    align_e = min(align_e, e_off)
                    candidates.append(CandidateRange(
                        module=mod_name,
                        offset_start=align_s,
                        offset_end_exclusive=align_e,
                        classification="CONFIRMED_CODE",
                        representation="RAW_CODE_PENDING",
                        confidence="CONFIRMED",
                        evidence=["DYNAMIC_CPU_RETIREMENT", f"CDL_HIT_0x{vma_base + align_s:08X}"],
                        detector_name=self.name,
                        block_id=f"cand_exec_{vma_base + align_s:08X}",
                    ))

        return candidates


class DirectBranchTargetDetector(CarverDetector):
    """Detects control-flow targets from direct branch instructions in confirmed code."""

    def __init__(self) -> None:
        super().__init__("DIRECT_BRANCH_TARGET_DETECTOR", "CODE", default_confidence="HIGH")

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
                # Rule 5: parent must be confirmed
                parent_id = f"{mod_name}_{iv.offset_start:06X}"
                for off in range(iv.offset_start, iv.offset_end_exclusive, 2):
                    if off + 2 > len(raw):
                        break
                    op = (raw[off] << 8) | raw[off + 1]
                    pc = vma_base + off
                    target_pc: Optional[int] = None

                    # BRA disp12 (0xAxxx)
                    if (op & 0xF000) == 0xA000:
                        disp = sign_extend_12(op & 0x0FFF)
                        target_pc = pc + 4 + (disp * 2)
                    # BSR disp12 (0xBxxx)
                    elif (op & 0xF000) == 0xB000:
                        disp = sign_extend_12(op & 0x0FFF)
                        target_pc = pc + 4 + (disp * 2)
                    # BT, BF, BTS, BFS (0x89xx, 0x8Bxx, 0x8Dxx, 0x8Fxx)
                    elif (op & 0xF900) in (0x8900, 0x8B00, 0x8D00, 0x8F00):
                        disp = sign_extend_8(op & 0x00FF)
                        target_pc = pc + 4 + (disp * 2)

                    if target_pc is not None:
                        target_off = target_pc - vma_base
                        if 0 <= target_off < meta["size"] - 2:
                            target_iv = db.find_interval(mod_name, target_off)
                            if target_iv and target_iv.classification == "UNKNOWN":
                                candidates.append(CandidateRange(
                                    module=mod_name,
                                    offset_start=target_off,
                                    offset_end_exclusive=target_off + 2,
                                    classification="CONFIRMED_CODE",
                                    representation="RAW_CODE_PENDING",
                                    confidence="HIGH",
                                    evidence=[f"BRANCH_TARGET_FROM_0x{pc:08X}"],
                                    parent_node_id=parent_id,
                                    detector_name=self.name,
                                    block_id=f"cand_branch_{target_pc:08X}",
                                ))

        return candidates


class CallTargetDetector(CarverDetector):
    """Detects function call targets (BSR, JSR) and records call-graph edges."""

    def __init__(self) -> None:
        super().__init__("CALL_TARGET_DETECTOR", "CODE", default_confidence="HIGH")

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
                for off in range(iv.offset_start, iv.offset_end_exclusive, 2):
                    if off + 2 > len(raw):
                        break
                    op = (raw[off] << 8) | raw[off + 1]
                    pc = vma_base + off
                    if (op & 0xF000) == 0xB000:  # BSR
                        disp = sign_extend_12(op & 0x0FFF)
                        target_pc = pc + 4 + (disp * 2)
                        target_off = target_pc - vma_base
                        if 0 <= target_off < meta["size"] - 2:
                            t_iv = db.find_interval(mod_name, target_off)
                            if t_iv and t_iv.classification == "UNKNOWN":
                                candidates.append(CandidateRange(
                                    module=mod_name,
                                    offset_start=target_off,
                                    offset_end_exclusive=target_off + 2,
                                    classification="CONFIRMED_CODE",
                                    representation="RAW_CODE_PENDING",
                                    confidence="HIGH",
                                    evidence=[f"CALL_TARGET_FROM_0x{pc:08X}"],
                                    parent_node_id=f"{mod_name}_{iv.offset_start:06X}",
                                    detector_name=self.name,
                                    block_id=f"cand_call_{target_pc:08X}",
                                ))
        return candidates
