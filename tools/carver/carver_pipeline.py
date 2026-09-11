#!/usr/bin/env python3
"""tools/carver/carver_pipeline.py — Fixed-Point Saturn Recovery Carver Pipeline.

Orchestrates iterative candidate discovery, conflict detection, proof evaluation,
gap auditing, and denominator re-audit until true fixed-point convergence.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import os
import sys

from .interval_db import IntervalDatabase, MemoryInterval, IntervalConflictError
from .provenance_dag import ProvenanceDAG
from .detector_base import CarverDetector, CandidateRange, CarverContext
from .detector_registry import DetectorRegistry
from .detectors_code import ExecutedPcDetector, DirectBranchTargetDetector, CallTargetDetector
from .detectors_data import (
    LiteralPoolDetector,
    PointerTableDetector,
    MmioPointerDetector,
    StringDetector,
    PaddingDetector,
)
from .gap_reporter import GapReporter
from .evidence_contracts import EvidenceContractEvaluator, PromotionStatus


class CarverPipeline:
    """Fixed-point carver convergence loop engine."""

    def __init__(self, repo_root: Path, max_passes: int = 10) -> None:
        self.repo_root = repo_root
        self.max_passes = max_passes
        self.db = IntervalDatabase()
        self.dag = ProvenanceDAG()
        self.registry = DetectorRegistry()
        self.pass_records: List[Dict[str, Any]] = []
        self._setup_detectors()

    def _setup_detectors(self) -> None:
        # Prioritized registration order:
        # 1. Dynamic execution retirements (Rule 4)
        self.registry.register(ExecutedPcDetector())
        # 2. Control flow branch/call targets
        self.registry.register(DirectBranchTargetDetector())
        self.registry.register(CallTargetDetector())
        # 3. Proven data structures
        self.registry.register(LiteralPoolDetector())
        self.registry.register(PointerTableDetector())
        self.registry.register(MmioPointerDetector())
        # 4. Formatted data and padding
        self.registry.register(StringDetector())
        self.registry.register(PaddingDetector())

    def load_context(self) -> CarverContext:
        ctx = CarverContext(repo_root=self.repo_root)

        # Load CDL traces if present
        hwr_path = self.repo_root / ".private" / "harvest_ipc_hwr" / "hwr_gameplay_cdl.bin"
        if not hwr_path.exists():
            hwr_path = self.repo_root / ".private" / "cdl_ipc" / "hwr_cdl.bin"
        if hwr_path.exists():
            with open(hwr_path, "rb") as f:
                f.seek(8)
                ctx.cdl_hwr = f.read()

        lwr_path = self.repo_root / ".private" / "harvest_ipc_lwr" / "lwr_gameplay_cdl.bin"
        if not lwr_path.exists():
            lwr_path = self.repo_root / ".private" / "cdl_ipc_lwr" / "lwr_cdl.bin"
        if lwr_path.exists():
            with open(lwr_path, "rb") as f:
                f.seek(8)
                ctx.cdl_lwr = f.read()

        # Load raw bytes for each registered module
        disc_path = self.repo_root / "The_Story_of_Thor_2_[RUS]_(NTSC).bin"
        if disc_path.exists():
            ctx.disc_path = disc_path
            with open(disc_path, "rb") as df:
                for mod_name, meta in self.db.modules.items():
                    sec = meta["iso_sector_start"]
                    sz = meta["size"]
                    df.seek(sec * 2352)
                    buf = bytearray()
                    while len(buf) < sz:
                        chunk = df.read(2352)
                        if not chunk:
                            break
                        buf.extend(chunk[16:16 + 2048])
                    ctx.module_bytes[mod_name] = bytes(buf[:sz])

        return ctx

    def import_all_manifests(self) -> None:
        manifest_dir = self.repo_root / "asm" / "manifests"
        for mf in sorted(manifest_dir.glob("*.json")):
            if mf.name in ("0TH2.BIN.json", "TH2.LOW.json", "SET07.BIN.json", "BGM.BIN.json"):
                self.db.import_manifest(mf)
                meta = self.db.modules[self.db.intervals[list(self.db.intervals.keys())[-1]][0].module]
                # Seed Provenance DAG with confirmed nodes
                for iv in self.db.intervals[meta["name"]]:
                    if iv.classification == "CONFIRMED_CODE":
                        node_id = f"{meta['name']}_{iv.offset_start:06X}"
                        self.dag.add_node(
                            node_id=node_id,
                            node_type="CODE_BLOCK",
                            status="CONFIRMED",
                            module=meta["name"],
                            offset_start=iv.offset_start,
                            offset_end_exclusive=iv.offset_end_exclusive,
                            runtime_address=iv.runtime_start,
                            evidence_refs=iv.evidence_refs,
                        )

    def run_fixed_point_loop(self) -> Dict[str, Any]:
        self.import_all_manifests()
        ctx = self.load_context()

        evaluator = EvidenceContractEvaluator(self.db, ctx)
        integrity_records: List[Dict[str, Any]] = []

        pass_num = 1
        while pass_num <= self.max_passes:
            ctx.pass_number = pass_num
            candidates = self.registry.run_all(self.db, self.dag, ctx)

            promoted_this_pass = 0
            conflicts_this_pass = 0

            # Sort candidates: CONFIRMED first, then by offset length
            candidates.sort(key=lambda c: (0 if c.confidence == "CONFIRMED" else 1, -c.byte_length))

            for cand in candidates:
                # Check if range is still UNKNOWN in DB
                target_iv = self.db.find_interval(cand.module, cand.offset_start)
                if not target_iv or target_iv.classification != "UNKNOWN":
                    continue

                # Ensure candidate fits inside the target UNKNOWN interval
                fit_end = min(cand.offset_end_exclusive, target_iv.offset_end_exclusive)
                if fit_end <= cand.offset_start:
                    continue

                # Formally evaluate candidate against typed evidence contract
                decision = evaluator.evaluate(cand, self.dag)
                record_entry = {
                    "module": cand.module,
                    "offset_start": cand.offset_start,
                    "offset_end_exclusive": fit_end,
                    "byte_length": fit_end - cand.offset_start,
                    "detector": cand.detector_name,
                    "contract_type": decision.contract_type.value,
                    "status": decision.status.value,
                    "classification": decision.classification,
                    "representation": decision.representation,
                    "subclass": decision.subclass,
                    "reasons": decision.reasons,
                    "pass": pass_num,
                }
                integrity_records.append(record_entry)

                if not decision.can_commit_to_db:
                    continue

                try:
                    # Enforce Rule 5: Graph expansion parent check
                    if cand.parent_node_id and not self.dag.can_authoritatively_expand(cand.parent_node_id):
                        continue

                    new_iv = self.db.split_and_classify(
                        module=cand.module,
                        start=cand.offset_start,
                        end=fit_end,
                        classification=decision.classification,
                        representation=decision.representation,
                        subclass=decision.subclass,
                        evidence=cand.evidence + decision.reasons,
                        discovered_by=cand.detector_name,
                        discovery_pass=pass_num,
                        block_id=cand.block_id,
                    )
                    promoted_this_pass += new_iv.byte_length

                    # Add node to Provenance DAG
                    node_id = f"{cand.module}_{new_iv.offset_start:06X}"
                    self.dag.add_node(
                        node_id=node_id,
                        node_type="CODE_BLOCK" if decision.classification == "CONFIRMED_CODE" else "DATA_BLOCK",
                        status="CONFIRMED" if decision.status == PromotionStatus.CONFIRMED else "PROBABLE",
                        module=cand.module,
                        offset_start=new_iv.offset_start,
                        offset_end_exclusive=new_iv.offset_end_exclusive,
                        runtime_address=new_iv.runtime_start,
                        evidence_refs=new_iv.evidence_refs,
                    )
                    if cand.parent_node_id:
                        self.dag.add_edge(
                            source_id=cand.parent_node_id,
                            target_id=node_id,
                            relation="EXPANSION_CHILD",
                            confidence=decision.confidence,
                            evidence_ref=cand.evidence[0] if cand.evidence else "EXPANSION",
                        )
                except IntervalConflictError as e:
                    conflicts_this_pass += 1

            record = {
                "pass": pass_num,
                "candidates_found": len(candidates),
                "bytes_promoted": promoted_this_pass,
                "conflicts": conflicts_this_pass,
            }
            self.pass_records.append(record)
            for mod in self.db.modules:
                self.db.validate_module(mod)

            # Fixed-point convergence criterion
            if promoted_this_pass == 0:
                break
            pass_num += 1

        # Audit UNKNOWN gaps
        gap_reporter = GapReporter(self.db)
        gap_summary = gap_reporter.audit_gaps(ctx)

        # Update and save evidence artifacts
        evidence_dir = self.repo_root / "workstreams" / "T2-ASM-CARVER"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        db_summary = self.db.export_summary()
        dag_summary = self.dag.export_summary()

        (evidence_dir / "interval_db_summary.json").write_text(
            json.dumps(db_summary, indent=2) + "\n", encoding="utf-8"
        )
        (evidence_dir / "carver_passes.json").write_text(
            json.dumps({"passes": self.pass_records, "total_passes": len(self.pass_records)}, indent=2) + "\n",
            encoding="utf-8"
        )
        (evidence_dir / "unknown_gap_report.json").write_text(
            json.dumps(gap_summary, indent=2) + "\n", encoding="utf-8"
        )
        (evidence_dir / "provenance_graph_summary.json").write_text(
            json.dumps(dag_summary, indent=2) + "\n", encoding="utf-8"
        )

        # Output formal audit log carver_integrity_diff.json
        integrity_summary = {
            "total_candidates_evaluated": len(integrity_records),
            "keep_confirmed": sum(1 for r in integrity_records if r["status"] == "CONFIRMED"),
            "demote_to_probable": sum(1 for r in integrity_records if r["status"] == "PROBABLE"),
            "demote_to_candidate": sum(1 for r in integrity_records if r["status"] == "CANDIDATE"),
            "rejected": sum(1 for r in integrity_records if r["status"] == "REJECTED"),
            "decisions": integrity_records,
        }
        (evidence_dir / "carver_integrity_diff.json").write_text(
            json.dumps(integrity_summary, indent=2) + "\n", encoding="utf-8"
        )

        return {
            "passes": len(self.pass_records),
            "db_summary": db_summary,
            "dag_summary": dag_summary,
            "gap_summary": gap_summary,
            "integrity_summary": integrity_summary,
        }


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent.parent
    pipeline = CarverPipeline(repo_root)
    results = pipeline.run_fixed_point_loop()
    print(f"Carver pipeline finished in {results['passes']} passes.")
    print(f"Candidates evaluated: {results['integrity_summary']['total_candidates_evaluated']}")
    print(f"  KEEP_CONFIRMED: {results['integrity_summary']['keep_confirmed']}")
    print(f"  DEMOTE_TO_PROBABLE: {results['integrity_summary']['demote_to_probable']}")
    print(f"  DEMOTE_TO_CANDIDATE: {results['integrity_summary']['demote_to_candidate']}")
    print(f"  REJECTED: {results['integrity_summary']['rejected']}")
