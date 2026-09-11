#!/usr/bin/env python3
"""tools/carver/detectors_code.py — Saturn Code & Control-Flow Detectors.

Authoritative SH-2 instruction decoding is delegated 100% to C++ thor_sh2.
No hand-written Python opcode bitmasks or displacement arithmetic.
"""

from typing import Any, Dict, List, Optional

from .detector_base import CarverDetector, CandidateRange, CarverContext
from .interval_db import IntervalDatabase
from .provenance_dag import ProvenanceDAG
from .thor_decoder import decode_intervals_with_thor_sh2, DecodedInstruction


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
                if 0x06000000 <= vma_base < 0x06100000 and ctx.cdl_hwr:
                    cdl_data = ctx.cdl_hwr
                    cdl_offset_in_ram = vma_base - 0x06000000
                elif 0x00200000 <= vma_base < 0x00300000 and ctx.cdl_lwr:
                    cdl_data = ctx.cdl_lwr
                    cdl_offset_in_ram = vma_base - 0x00200000

            if not cdl_data:
                continue

            unknown_ivs = [iv for iv in db.intervals[mod_name] if iv.classification == "UNKNOWN"]
            for iv in unknown_ivs:
                s_off = iv.offset_start
                e_off = iv.offset_end_exclusive

                exec_indices = []
                for off in range(s_off, e_off):
                    ram_off = cdl_offset_in_ram + off
                    if 0 <= ram_off < len(cdl_data):
                        if cdl_data[ram_off] & 1:
                            exec_indices.append(off)

                if not exec_indices:
                    continue

                run_start = None
                prev = None
                for idx in exec_indices:
                    if run_start is None:
                        run_start = idx
                        prev = idx
                    elif idx == prev + 1:
                        prev = idx
                    else:
                        align_s = run_start & ~1
                        align_e = min(((prev + 1) + 1) & ~1, e_off)
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
                    align_e = min(((prev + 1) + 1) & ~1, e_off)
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
    """Detects control-flow targets using C++ thor_sh2 decoded branch instructions."""

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
            if not confirmed_ivs:
                continue

            # Query C++ thor_sh2 decoder: authoritative decode, no Python bitmasks
            instructions = decode_intervals_with_thor_sh2(
                ctx.repo_root, mod_name, vma_base, raw, confirmed_ivs
            )

            for ins in instructions:
                if not ins.is_branch or ins.target_vma == 0:
                    continue

                target_pc = ins.target_vma
                target_off = target_pc - vma_base
                if 0 <= target_off < meta["size"] - 2:
                    target_iv = db.find_interval(mod_name, target_off)
                    if target_iv and target_iv.classification == "UNKNOWN":
                        # Parent is the confirmed block containing this instruction
                        parent_iv = db.find_interval(mod_name, ins.offset)
                        parent_id = f"{mod_name}_{parent_iv.offset_start:06X}" if parent_iv else None
                        candidates.append(CandidateRange(
                            module=mod_name,
                            offset_start=target_off,
                            offset_end_exclusive=target_off + 2,
                            classification="CONFIRMED_CODE",
                            representation="RAW_CODE_PENDING",
                            confidence="HIGH",
                            evidence=[f"BRANCH_TARGET_FROM_0x{ins.pc:08X}"],
                            parent_node_id=parent_id,
                            detector_name=self.name,
                            block_id=f"cand_branch_{target_pc:08X}",
                        ))

        return candidates


class CallTargetDetector(CarverDetector):
    """Detects call targets using C++ thor_sh2 decoded call instructions."""

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
            if not confirmed_ivs:
                continue

            # Query C++ thor_sh2 decoder: authoritative decode, no Python bitmasks
            instructions = decode_intervals_with_thor_sh2(
                ctx.repo_root, mod_name, vma_base, raw, confirmed_ivs
            )

            for ins in instructions:
                if not ins.is_call or ins.target_vma == 0:
                    continue

                target_pc = ins.target_vma
                target_off = target_pc - vma_base
                if 0 <= target_off < meta["size"] - 2:
                    t_iv = db.find_interval(mod_name, target_off)
                    if t_iv and t_iv.classification == "UNKNOWN":
                        parent_iv = db.find_interval(mod_name, ins.offset)
                        parent_id = f"{mod_name}_{parent_iv.offset_start:06X}" if parent_iv else None
                        candidates.append(CandidateRange(
                            module=mod_name,
                            offset_start=target_off,
                            offset_end_exclusive=target_off + 2,
                            classification="CONFIRMED_CODE",
                            representation="RAW_CODE_PENDING",
                            confidence="HIGH",
                            evidence=[f"CALL_TARGET_FROM_0x{ins.pc:08X}"],
                            parent_node_id=parent_id,
                            detector_name=self.name,
                            block_id=f"cand_call_{target_pc:08X}",
                        ))

        return candidates
