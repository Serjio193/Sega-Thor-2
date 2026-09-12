#!/usr/bin/env python3
"""tests/asm/test_return_provenance.py — Unit Tests for T2-ASM-08 PR Provenance & Control-Flow Closure.

Validates:
  1. Complete 43 Call/Jump site resolution (36 JSR, 7 BSRF table entries).
  2. Complete 638 RTS site return domain bounding and stack frame balance.
  3. Closed 2,233 indirect site inventory accounting.
  4. Executable byte carving and UNKNOWN byte reduction.
  5. Monotonicity and non-regression of previously proven targets.
"""

from pathlib import Path
import json
import unittest

_repo_root = Path(__file__).resolve().parent.parent.parent


class TestReturnProvenance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = _repo_root
        cls.cj_data = json.loads(
            (cls.repo_root / "workstreams/T2-ASM-08/final_call_jump_sites.json").read_text(encoding="utf-8")
        )
        cls.pr_data = json.loads(
            (cls.repo_root / "workstreams/T2-ASM-08/pr_provenance.json").read_text(encoding="utf-8")
        )
        cls.scorecard = json.loads(
            (cls.repo_root / "workstreams/T2-ASM-08/final_indirect_scorecard.json").read_text(encoding="utf-8")
        )
        cls.partition = json.loads(
            (cls.repo_root / "workstreams/T2-ASM-08/executable_byte_partition.json").read_text(encoding="utf-8")
        )
        cls.closure = json.loads(
            (cls.repo_root / "workstreams/T2-ASM-08/cfg_closure.json").read_text(encoding="utf-8")
        )

    def test_call_jump_resolution_complete(self):
        """All 43 Call/Jump sites must be resolved with exact single targets."""
        self.assertEqual(self.cj_data["total_analyzed"], 43)
        self.assertEqual(self.cj_data["jsr_count"], 36)
        self.assertEqual(self.cj_data["bsrf_count"], 7)
        for s in self.cj_data["sites"]:
            self.assertEqual(s["resolution_status"], "RESOLVED_EXACT_SINGLE")
            self.assertEqual(s["target_count"], 1)
            self.assertTrue(s["targets"][0].startswith("0x"))

    def test_pr_provenance_complete(self):
        """All 638 RTS sites must be bounded and stack balanced."""
        self.assertEqual(self.pr_data["total_rts_sites"], 638)
        self.assertTrue(self.pr_data["all_stack_balanced"])
        for r in self.pr_data["records"]:
            self.assertIn(r["pr_mechanism"], ("LEAF_UNTOUCHED_PR", "STACK_RESTORED_PR"))
            self.assertTrue(r["stack_balanced"])
            self.assertGreater(r["caller_count"], 0)
            self.assertGreater(r["return_domain_count"], 0)

    def test_closed_inventory_accounting(self):
        """Master scorecard must reconcile exactly to 2,233 sites with 0 unresolved."""
        acc = self.scorecard["accounting"]
        self.assertEqual(acc["total_sites"], 2233)
        self.assertEqual(acc["resolved_total"], 2233)
        self.assertEqual(acc["unresolved_total"], 0)

        cj = self.scorecard["indirect_call_jump_metrics"]
        self.assertEqual(cj["total"], 1595)
        self.assertEqual(cj["resolved"], 1595)
        self.assertEqual(cj["unresolved"], 0)
        self.assertEqual(cj["resolution_ratio"], "100.00%")

        rf = self.scorecard["return_flow_rts_metrics"]
        self.assertEqual(rf["total"], 638)
        self.assertEqual(rf["resolved"], 638)
        self.assertEqual(rf["unresolved"], 0)
        self.assertEqual(rf["resolution_ratio"], "100.00%")

    def test_executable_byte_partition(self):
        """Module partitions must sum to exact file sizes and reduce UNKNOWN bytes."""
        self.assertEqual(self.partition["total_binary_bytes"], 1457152)
        self.assertTrue(self.partition["all_partitions_balanced"])
        # Check sum for each module
        for m in self.partition["modules"]:
            part_sum = (
                m["confirmed_code_bytes"]
                + m["proven_data_bytes"]
                + m["proven_padding_bytes"]
                + m["unknown_bytes"]
            )
            self.assertEqual(part_sum, m["size_bytes"], f"Partition sum mismatch in {m['module']}")

        # Verify UNKNOWN reduction
        self.assertGreater(self.partition["unknown_bytes_reduction"], 0)
        self.assertEqual(
            self.partition["unknown_bytes_reduction"],
            self.partition["baseline_unknown_bytes"] - self.partition["total_unknown_bytes"]
        )

    def test_cfg_closure_monotonicity(self):
        """CFG worklist injection must preserve and extend confirmed code."""
        self.assertGreaterEqual(self.closure["proven_targets_injected"], 2000)
        self.assertGreater(self.closure["newly_confirmed_code_segments"], 0)
        self.assertLessEqual(self.closure["residual_undecoded_gaps_after"], 1595)


if __name__ == "__main__":
    unittest.main()
