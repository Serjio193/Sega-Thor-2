#!/usr/bin/env python3
"""tests/carver/test_carver_pipeline.py — Unit & Integration Test Suite for Carver.

Tests:
1. Manifest import and range algebra validation (no gaps, no overlaps).
2. Execution conflict rule (Rule 4 fail-closed).
3. Graph expansion safety (Rule 5: only CONFIRMED parents expand).
4. RAM to disc signature carving.
5. Dual-run fixed-point determinism.
6. Gap reporter priority hierarchy.
7. File line count limit (<= 500 lines) across all carver source files.
"""

from pathlib import Path
import hashlib
import json
import os
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.carver.interval_db import IntervalDatabase, MemoryInterval, IntervalConflictError
from tools.carver.provenance_dag import ProvenanceDAG
from tools.carver.detector_base import CarverContext, CandidateRange
from tools.carver.detector_registry import DetectorRegistry
from tools.carver.detectors_code import ExecutedPcDetector, DirectBranchTargetDetector
from tools.carver.detectors_data import LiteralPoolDetector, PointerTableDetector, PaddingDetector
from tools.carver.ram_disc_carver import RamDiscCarver
from tools.carver.gap_reporter import GapReporter
from tools.carver.carver_pipeline import CarverPipeline


class TestCarverPipeline(unittest.TestCase):

    def setUp(self) -> None:
        self.db = IntervalDatabase()
        self.dag = ProvenanceDAG()

    def test_01_interval_db_algebra_and_validation(self) -> None:
        self.db.register_module("TEST.BIN", size=100, vma_base=0x06000000, cpu="MASTER_SH2")
        self.db.intervals["TEST.BIN"] = [
            MemoryInterval(
                module="TEST.BIN", generation="gen_0", cpu="MASTER_SH2",
                offset_start=0, offset_end_exclusive=100,
                runtime_start=0x06000000, runtime_end_exclusive=0x06000064,
                classification="UNKNOWN", representation="RAW_UNKNOWN"
            )
        ]
        self.db.validate_module("TEST.BIN")

        # Split middle: [20..40)
        self.db.split_and_classify(
            module="TEST.BIN", start=20, end=40,
            classification="CONFIRMED_CODE", representation="RAW_CODE_PENDING"
        )
        self.assertEqual(len(self.db.intervals["TEST.BIN"]), 3)
        self.assertEqual(self.db.intervals["TEST.BIN"][0].offset_end_exclusive, 20)
        self.assertEqual(self.db.intervals["TEST.BIN"][1].offset_start, 20)
        self.assertEqual(self.db.intervals["TEST.BIN"][1].offset_end_exclusive, 40)
        self.assertEqual(self.db.intervals["TEST.BIN"][2].offset_start, 40)
        self.assertEqual(self.db.intervals["TEST.BIN"][2].offset_end_exclusive, 100)

    def test_02_execution_conflict_rule_fail_closed(self) -> None:
        self.db.register_module("CONF.BIN", size=50, vma_base=0x06000000, cpu="MASTER_SH2")
        self.db.intervals["CONF.BIN"] = [
            MemoryInterval(
                module="CONF.BIN", generation="gen_0", cpu="MASTER_SH2",
                offset_start=0, offset_end_exclusive=50,
                runtime_start=0x06000000, runtime_end_exclusive=0x06000032,
                classification="DATA", representation="RAW_DATA",
                evidence_refs=["PROVEN_DATA"]
            )
        ]
        # Attempt to decode proven DATA as code -> must raise IntervalConflictError
        with self.assertRaises(IntervalConflictError):
            self.db.split_and_classify(
                module="CONF.BIN", start=10, end=20,
                classification="CONFIRMED_CODE", representation="RAW_CODE_PENDING"
            )

    def test_03_graph_expansion_safety(self) -> None:
        # Rule 5: Only CONFIRMED nodes can authoritatively expand
        self.dag.add_node("node_conf", "CODE_BLOCK", "CONFIRMED", "MOD.BIN", 0, 10)
        self.dag.add_node("node_prob", "CODE_BLOCK", "PROBABLE", "MOD.BIN", 10, 20)
        self.dag.add_node("node_hyp", "CODE_BLOCK", "HYPOTHESIS", "MOD.BIN", 20, 30)

        self.assertTrue(self.dag.can_authoritatively_expand("node_conf"))
        self.assertFalse(self.dag.can_authoritatively_expand("node_prob"))
        self.assertFalse(self.dag.can_authoritatively_expand("node_hyp"))

    def test_04_padding_detector(self) -> None:
        raw = b"\x00" * 32 + b"\x12\x34" * 10
        self.db.register_module("PAD.BIN", size=len(raw), vma_base=0x06000000, cpu="MASTER_SH2")
        self.db.intervals["PAD.BIN"] = [
            MemoryInterval(
                module="PAD.BIN", generation="gen_0", cpu="MASTER_SH2",
                offset_start=0, offset_end_exclusive=len(raw),
                runtime_start=0x06000000, runtime_end_exclusive=0x06000000 + len(raw),
                classification="UNKNOWN", representation="RAW_UNKNOWN"
            )
        ]
        ctx = CarverContext(repo_root=REPO_ROOT, module_bytes={"PAD.BIN": raw})
        detector = PaddingDetector()
        cands = detector.detect(self.db, self.dag, ctx)
        self.assertTrue(len(cands) >= 1)
        self.assertEqual(cands[0].offset_start, 0)
        self.assertEqual(cands[0].offset_end_exclusive, 32)
        self.assertEqual(cands[0].classification, "PADDING")

    def test_05_ram_disc_carver_signature(self) -> None:
        carver = RamDiscCarver(REPO_ROOT)
        # Test signature from 0TH2.BIN header
        sig = bytes([0x66, 0x11, 0x6F, 0x03, 0xD4, 0x17, 0x64, 0x42, 0xA0, 0x03, 0x00, 0x09, 0xE2, 0x00, 0x24, 0x20])
        matches = carver.search_signature_on_disc(sig, min_length=16)
        self.assertTrue(len(matches) >= 1)
        file_name, off = matches[0]
        self.assertEqual(file_name, "0TH2.BIN")
        self.assertEqual(off, 0)

    def test_06_fixed_point_determinism(self) -> None:
        p1 = CarverPipeline(REPO_ROOT, max_passes=2)
        res1 = p1.run_fixed_point_loop()

        p2 = CarverPipeline(REPO_ROOT, max_passes=2)
        res2 = p2.run_fixed_point_loop()

        self.assertEqual(res1["passes"], res2["passes"])
        self.assertEqual(
            res1["db_summary"]["aggregate"]["confirmed_code_bytes"],
            res2["db_summary"]["aggregate"]["confirmed_code_bytes"]
        )
        self.assertEqual(
            res1["db_summary"]["aggregate"]["data_bytes"],
            res2["db_summary"]["aggregate"]["data_bytes"]
        )

    def test_07_source_file_line_limits(self) -> None:
        carver_dir = REPO_ROOT / "tools" / "carver"
        for p in carver_dir.glob("*.py"):
            with open(p, "r", encoding="utf-8") as f:
                lines = len(f.readlines())
            self.assertLessEqual(lines, 500, f"File '{p.name}' exceeds 500 lines ({lines} lines)")

    def test_08_evidence_contracts_evaluation(self) -> None:
        from tools.carver.evidence_contracts import (
            EvidenceContractEvaluator,
            PromotionStatus,
            ContractType,
        )
        self.db.register_module("0TH2.BIN", size=535552, vma_base=0x06004000, cpu="MASTER_SH2")
        self.db.intervals["0TH2.BIN"] = [
            MemoryInterval(
                module="0TH2.BIN", generation="gen_0", cpu="MASTER_SH2",
                offset_start=0, offset_end_exclusive=535552,
                runtime_start=0x06004000, runtime_end_exclusive=0x06004000 + 535552,
                classification="UNKNOWN", representation="RAW_UNKNOWN"
            )
        ]
        ctx = CarverContext(repo_root=REPO_ROOT)
        evaluator = EvidenceContractEvaluator(self.db, ctx)

        # Dynamic code with CDL hit -> CONFIRMED
        cand_dyn = CandidateRange(
            module="0TH2.BIN", offset_start=0, offset_end_exclusive=10,
            classification="CONFIRMED_CODE", representation="RAW_CODE_PENDING",
            confidence="CONFIRMED", evidence=["DYNAMIC_CPU_RETIREMENT", "CDL_HIT_0x06004000"],
            detector_name="EXECUTED_PC_DETECTOR",
        )
        dec_dyn = evaluator.evaluate(cand_dyn, self.dag)
        self.assertEqual(dec_dyn.status, PromotionStatus.CONFIRMED)
        self.assertTrue(dec_dyn.can_commit_to_db)

        # Dynamic code lacking CDL hit -> REJECTED
        cand_fake = CandidateRange(
            module="0TH2.BIN", offset_start=0, offset_end_exclusive=10,
            classification="CONFIRMED_CODE", representation="RAW_CODE_PENDING",
            confidence="CONFIRMED", evidence=["SOME_HEURISTIC"],
            detector_name="EXECUTED_PC_DETECTOR",
        )
        dec_fake = evaluator.evaluate(cand_fake, self.dag)
        self.assertEqual(dec_fake.status, PromotionStatus.REJECTED)
        self.assertFalse(dec_fake.can_commit_to_db)

    def test_09_heuristic_never_promotes_negative(self) -> None:
        from tools.carver.evidence_contracts import EvidenceContractEvaluator, PromotionStatus
        self.db.register_module("0TH2.BIN", size=535552, vma_base=0x06004000, cpu="MASTER_SH2")
        self.db.intervals["0TH2.BIN"] = [
            MemoryInterval(
                module="0TH2.BIN", generation="gen_0", cpu="MASTER_SH2",
                offset_start=0, offset_end_exclusive=535552,
                runtime_start=0x06004000, runtime_end_exclusive=0x06004000 + 535552,
                classification="UNKNOWN", representation="RAW_UNKNOWN"
            )
        ]
        ctx = CarverContext(repo_root=REPO_ROOT)
        evaluator = EvidenceContractEvaluator(self.db, ctx)

        # String candidate without proven xref -> CANDIDATE only (never commits to DB)
        cand_str = CandidateRange(
            module="0TH2.BIN", offset_start=100, offset_end_exclusive=120,
            classification="DATA", representation="RAW_DATA", subclass="STRING_TABLE",
            confidence="LOW", evidence=["PRINTABLE_ASCII_RUN_LEN_20"],
            detector_name="STRING_DETECTOR",
        )
        dec_str = evaluator.evaluate(cand_str, self.dag)
        self.assertEqual(dec_str.status, PromotionStatus.CANDIDATE)
        self.assertFalse(dec_str.can_commit_to_db)

    def test_10_campaign_accounting_consistency(self) -> None:
        gap_rep_path = REPO_ROOT / "workstreams" / "T2-ASM-CARVER" / "unknown_gap_report.json"
        self.assertTrue(gap_rep_path.exists())
        gap_data = json.loads(gap_rep_path.read_text(encoding="utf-8"))
        canonical_count = gap_data["total_campaigns"]
        self.assertEqual(canonical_count, len(gap_data["campaigns"]))

        # Assert documentation matches canonical machine count
        worklog_text = (REPO_ROOT / "docs" / "WORKLOG.md").read_text(encoding="utf-8")
        roadmap_text = (REPO_ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
        self.assertNotIn("43 campaigns", worklog_text)
        self.assertNotIn("43 campaigns", roadmap_text)
        self.assertIn(f"{canonical_count} campaigns", worklog_text)
        self.assertIn(f"{canonical_count} campaigns", roadmap_text)

    def test_11_p3_control_flow_resolution(self) -> None:
        p3_path = REPO_ROOT / "workstreams" / "T2-ASM-CARVER" / "p3_control_flow_resolution.json"
        self.assertTrue(p3_path.exists())
        p3_data = json.loads(p3_path.read_text(encoding="utf-8"))
        self.assertEqual(p3_data["unresolved_control_flow_unknown"], 0)
        self.assertGreater(p3_data["total_p3_gaps_audited"], 0)


if __name__ == "__main__":
    unittest.main()
