#!/usr/bin/env python3
"""tools/carver/evidence_contracts.py — Formal Evidence Contracts for Carver.

Implements typed evidence evaluation between candidate detectors and IntervalDatabase:
CandidateRecord -> EvidenceStore -> ConflictCheck -> TypedEvidenceContract -> PromotionDecision

Enforces strict promotion states:
- CONFIRMED: Indisputable evidence (dynamic CDL retirement, proven CFG/literal xref).
- PROBABLE: Strong structural evidence without dynamic execution or consumer proof.
- CANDIDATE: Heuristic match only (unreferenced strings, interior padding without boundary).
- REJECTED: Violates execution invariants, overlaps conflicting types, or invalid.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import struct

from .detector_base import CandidateRange, CarverContext
from .interval_db import IntervalDatabase, MemoryInterval


class PromotionStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    PROBABLE = "PROBABLE"
    CANDIDATE = "CANDIDATE"
    REJECTED = "REJECTED"


class ContractType(str, Enum):
    CONFIRMED_CODE_DYNAMIC = "CONFIRMED_CODE_DYNAMIC"
    CONFIRMED_CODE_DIRECT_CFG = "CONFIRMED_CODE_DIRECT_CFG"
    DATA_LITERAL_POOL = "DATA_LITERAL_POOL"
    DATA_POINTER_TABLE = "DATA_POINTER_TABLE"
    DATA_MMIO_POINTER = "DATA_MMIO_POINTER"
    DATA_STRING = "DATA_STRING"
    PADDING_BOUNDARY_CHECKED = "PADDING_BOUNDARY_CHECKED"
    PADDING_HEURISTIC = "PADDING_HEURISTIC"
    UNKNOWN_CONTRACT = "UNKNOWN_CONTRACT"


@dataclass
class PromotionDecision:
    status: PromotionStatus
    contract_type: ContractType
    classification: str
    representation: str
    confidence: str
    subclass: Optional[str] = None
    reasons: List[str] = field(default_factory=list)
    can_commit_to_db: bool = False


class EvidenceContractEvaluator:
    """Evaluates candidate ranges against typed contracts and interval database state."""

    def __init__(self, db: IntervalDatabase, ctx: CarverContext) -> None:
        self.db = db
        self.ctx = ctx
        self._proven_xref_targets: Dict[str, Set[int]] = {}
        self._build_xref_cache()

    def _build_xref_cache(self) -> None:
        """Scan confirmed code for literal pool and branch references using C++ thor_sh2."""
        from .thor_decoder import decode_intervals_with_thor_sh2

        for mod_name, meta in self.db.modules.items():
            self._proven_xref_targets[mod_name] = set()
            raw = self.ctx.module_bytes.get(mod_name)
            if not raw or meta.get("cpu") != "MASTER_SH2":
                continue

            vma_base = meta["vma_base"]
            confirmed_ivs = [iv for iv in self.db.intervals[mod_name] if iv.classification == "CONFIRMED_CODE"]
            if not confirmed_ivs:
                continue

            instructions = decode_intervals_with_thor_sh2(
                self.ctx.repo_root, mod_name, vma_base, raw, confirmed_ivs
            )
            for ins in instructions:
                if (ins.is_branch or ins.is_pc_rel_data or ins.is_call) and ins.target_vma:
                    t_off = ins.target_vma - vma_base
                    if 0 <= t_off < meta["size"]:
                        self._proven_xref_targets[mod_name].add(t_off)

    def evaluate(self, cand: CandidateRange, dag: Any) -> PromotionDecision:
        """Evaluate a CandidateRange and return a formal PromotionDecision."""
        mod = cand.module
        meta = self.db.modules.get(mod)
        if not meta:
            return PromotionDecision(
                status=PromotionStatus.REJECTED,
                contract_type=ContractType.UNKNOWN_CONTRACT,
                classification=cand.classification,
                representation=cand.representation,
                confidence="LOW",
                reasons=[f"Module '{mod}' not registered in IntervalDatabase"],
            )

        # Basic bounds and overlap validation
        if cand.offset_start < 0 or cand.offset_end_exclusive > meta["size"]:
            return PromotionDecision(
                status=PromotionStatus.REJECTED,
                contract_type=ContractType.UNKNOWN_CONTRACT,
                classification=cand.classification,
                representation=cand.representation,
                confidence="LOW",
                reasons=[f"Candidate range [{cand.offset_start:#x}..{cand.offset_end_exclusive:#x}) out of bounds"],
            )

        target_iv = self.db.find_interval(mod, cand.offset_start)
        if not target_iv or target_iv.classification != "UNKNOWN":
            return PromotionDecision(
                status=PromotionStatus.REJECTED,
                contract_type=ContractType.UNKNOWN_CONTRACT,
                classification=cand.classification,
                representation=cand.representation,
                confidence="LOW",
                reasons=["Target interval is not UNKNOWN"],
            )

        # Route by detector / classification
        if cand.detector_name == "EXECUTED_PC_DETECTOR":
            return self._eval_dynamic_code(cand)
        elif cand.detector_name in ("DIRECT_BRANCH_TARGET_DETECTOR", "CALL_TARGET_DETECTOR"):
            return self._eval_direct_cfg(cand, dag)
        elif cand.detector_name == "LITERAL_POOL_DETECTOR":
            return self._eval_literal_pool(cand, dag)
        elif cand.detector_name == "POINTER_TABLE_DETECTOR":
            return self._eval_pointer_table(cand)
        elif cand.detector_name == "MMIO_POINTER_DETECTOR":
            return self._eval_mmio_pointer(cand)
        elif cand.detector_name == "STRING_DETECTOR":
            return self._eval_string(cand)
        elif cand.detector_name == "PADDING_DETECTOR":
            return self._eval_padding(cand, target_iv)

        return PromotionDecision(
            status=PromotionStatus.CANDIDATE,
            contract_type=ContractType.UNKNOWN_CONTRACT,
            classification=cand.classification,
            representation=cand.representation,
            confidence=cand.confidence,
            subclass=cand.subclass,
            reasons=["Unrecognized detector without typed contract"],
            can_commit_to_db=False,
        )

    def _eval_dynamic_code(self, cand: CandidateRange) -> PromotionDecision:
        has_cdl_hit = any("CDL_HIT" in ev or "DYNAMIC_CPU_RETIREMENT" in ev for ev in cand.evidence)
        if not has_cdl_hit:
            return PromotionDecision(
                status=PromotionStatus.REJECTED,
                contract_type=ContractType.CONFIRMED_CODE_DYNAMIC,
                classification=cand.classification,
                representation=cand.representation,
                confidence="LOW",
                reasons=["Dynamic code candidate lacks CDL retirement evidence"],
            )
        return PromotionDecision(
            status=PromotionStatus.CONFIRMED,
            contract_type=ContractType.CONFIRMED_CODE_DYNAMIC,
            classification="CONFIRMED_CODE",
            representation="RAW_CODE_PENDING",
            confidence="CONFIRMED",
            reasons=["Verified dynamic CPU instruction retirement from CDL trace"],
            can_commit_to_db=True,
        )

    def _eval_direct_cfg(self, cand: CandidateRange, dag: Any) -> PromotionDecision:
        if not cand.parent_node_id or not dag.can_authoritatively_expand(cand.parent_node_id):
            return PromotionDecision(
                status=PromotionStatus.PROBABLE,
                contract_type=ContractType.CONFIRMED_CODE_DIRECT_CFG,
                classification="PROBABLE_CODE",
                representation="RAW_CODE_PENDING",
                confidence="MEDIUM",
                reasons=["Parent block is not CONFIRMED in DAG"],
                can_commit_to_db=False,
            )
        return PromotionDecision(
            status=PromotionStatus.CONFIRMED,
            contract_type=ContractType.CONFIRMED_CODE_DIRECT_CFG,
            classification="CONFIRMED_CODE",
            representation="RAW_CODE_PENDING",
            confidence="CONFIRMED",
            reasons=["Direct CFG transfer from CONFIRMED parent block"],
            can_commit_to_db=True,
        )

    def _eval_literal_pool(self, cand: CandidateRange, dag: Any) -> PromotionDecision:
        if not cand.parent_node_id or not dag.can_authoritatively_expand(cand.parent_node_id):
            return PromotionDecision(
                status=PromotionStatus.PROBABLE,
                contract_type=ContractType.DATA_LITERAL_POOL,
                classification="DATA",
                representation="RAW_DATA",
                subclass="LITERAL_POOL",
                confidence="MEDIUM",
                reasons=["Parent block is not CONFIRMED in DAG"],
                can_commit_to_db=False,
            )
        return PromotionDecision(
            status=PromotionStatus.CONFIRMED,
            contract_type=ContractType.DATA_LITERAL_POOL,
            classification="DATA",
            representation="RAW_DATA",
            subclass="LITERAL_POOL",
            confidence="CONFIRMED",
            reasons=["Exact PC-relative consumer reference from CONFIRMED instruction"],
            can_commit_to_db=True,
        )

    def _eval_pointer_table(self, cand: CandidateRange) -> PromotionDecision:
        mod = cand.module
        has_xref = False
        xrefs = self._proven_xref_targets.get(mod, set())
        for off in range(cand.offset_start, cand.offset_end_exclusive, 4):
            if off in xrefs:
                has_xref = True
                break

        if has_xref:
            return PromotionDecision(
                status=PromotionStatus.CONFIRMED,
                contract_type=ContractType.DATA_POINTER_TABLE,
                classification="DATA",
                representation="RAW_DATA",
                subclass="POINTER_TABLE",
                confidence="CONFIRMED",
                reasons=["Pointer table with confirmed entry xref from proven code"],
                can_commit_to_db=True,
            )
        return PromotionDecision(
            status=PromotionStatus.PROBABLE,
            contract_type=ContractType.DATA_POINTER_TABLE,
            classification="DATA",
            representation="RAW_DATA",
            subclass="POINTER_TABLE",
            confidence="HIGH",
            reasons=["Dense pointer array without consumer xref (PROBABLE)"],
            can_commit_to_db=True,
        )

    def _eval_mmio_pointer(self, cand: CandidateRange) -> PromotionDecision:
        mod = cand.module
        xrefs = self._proven_xref_targets.get(mod, set())
        has_xref = cand.offset_start in xrefs
        return PromotionDecision(
            status=PromotionStatus.CONFIRMED if has_xref else PromotionStatus.PROBABLE,
            contract_type=ContractType.DATA_MMIO_POINTER,
            classification="DATA",
            representation="RAW_DATA",
            subclass="MMIO_POINTER",
            confidence="CONFIRMED" if has_xref else "HIGH",
            reasons=["Saturn hardware MMIO address literal" + (" with xref" if has_xref else "")],
            can_commit_to_db=True,
        )

    def _eval_string(self, cand: CandidateRange) -> PromotionDecision:
        mod = cand.module
        xrefs = self._proven_xref_targets.get(mod, set())
        has_xref = cand.offset_start in xrefs
        if has_xref:
            return PromotionDecision(
                status=PromotionStatus.CONFIRMED,
                contract_type=ContractType.DATA_STRING,
                classification="DATA",
                representation="RAW_DATA",
                subclass="STRING_TABLE",
                confidence="CONFIRMED",
                reasons=["ASCII string with consumer xref from confirmed code"],
                can_commit_to_db=True,
            )
        # Unreferenced ASCII string must remain CANDIDATE
        return PromotionDecision(
            status=PromotionStatus.CANDIDATE,
            contract_type=ContractType.DATA_STRING,
            classification="DATA",
            representation="RAW_DATA",
            subclass="STRING_TABLE",
            confidence="LOW",
            reasons=["Printable ASCII sequence without consumer xref remains CANDIDATE"],
            can_commit_to_db=False,
        )

    def _eval_padding(self, cand: CandidateRange, target_iv: MemoryInterval) -> PromotionDecision:
        # Check if padding touches confirmed boundary (start or end of UNKNOWN interval)
        touches_left = (cand.offset_start == target_iv.offset_start and target_iv.offset_start > 0)
        touches_right = (cand.offset_end_exclusive == target_iv.offset_end_exclusive)

        raw = self.ctx.module_bytes.get(cand.module, b"")
        has_exec = False
        cdl = self.ctx.cdl_hwr if "0TH2" in cand.module or "SET07" in cand.module else self.ctx.cdl_lwr
        if cdl:
            meta = self.db.modules[cand.module]
            vma_base = meta["vma_base"]
            ram_base = 0x06000000 if vma_base >= 0x06000000 else 0x00200000
            for off in range(cand.offset_start, cand.offset_end_exclusive):
                cdl_idx = (vma_base - ram_base) + off
                if 0 <= cdl_idx < len(cdl) and (cdl[cdl_idx] & 1):
                    has_exec = True
                    break

        if has_exec:
            return PromotionDecision(
                status=PromotionStatus.REJECTED,
                contract_type=ContractType.PADDING_HEURISTIC,
                classification="PADDING",
                representation="RAW_DATA",
                subclass="ALIGNMENT_PADDING",
                confidence="LOW",
                reasons=["Padding candidate has recorded CPU execution hits!"],
                can_commit_to_db=False,
            )

        if touches_left or touches_right:
            return PromotionDecision(
                status=PromotionStatus.CONFIRMED,
                contract_type=ContractType.PADDING_BOUNDARY_CHECKED,
                classification="PADDING",
                representation="RAW_DATA",
                subclass="ALIGNMENT_PADDING",
                confidence="CONFIRMED",
                reasons=["Boundary-checked padding run touching confirmed boundary without execution hits"],
                can_commit_to_db=True,
            )

        # Interior unreferenced padding without boundary proof remains CANDIDATE
        return PromotionDecision(
            status=PromotionStatus.CANDIDATE,
            contract_type=ContractType.PADDING_HEURISTIC,
            classification="PADDING",
            representation="RAW_DATA",
            subclass="ALIGNMENT_PADDING",
            confidence="MEDIUM",
            reasons=["Interior padding run without confirmed boundary anchor remains CANDIDATE"],
            can_commit_to_db=False,
        )
