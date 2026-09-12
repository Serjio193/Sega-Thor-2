#!/usr/bin/env python3
"""tests/asm/test_return_provenance.py — Unit Tests for Audited T2-ASM-08 PR Provenance & Control-Flow Closure.

Validates:
  1. Removal of 7 false-positive BSRF decode sites in pointer tables (canonical BSRF = 0).
  2. 36 Raw-byte path-sensitive JSR proofs with zero clobbers and invariant definitions.
  3. RTS completeness certificates enforcing strict caller and PR contracts with zero synthetic placeholders.
  4. Exact canonical 2,226 indirect site accounting with honest derived totals.
  5. Module byte partitions, checksum balance, and code retraction accounting.
  6. Monotonicity and non-regression of previously proven targets.
"""

from pathlib import Path
import json
import unittest

_repo_root = Path(__file__).resolve().parent.parent.parent


class TestReturnProvenance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = _repo_root
        cls.false_tables = json.loads(
            (cls.repo_root / "workstreams/T2-ASM-08/false_decode_pointer_tables.json").read_text(encoding="utf-8")
        )
        cls.raw_jsr = json.loads(
            (cls.repo_root / "workstreams/T2-ASM-08/raw_byte_jsr_proofs.json").read_text(encoding="utf-8")
        )
        cls.rts_certs = json.loads(
            (cls.repo_root / "workstreams/T2-ASM-08/rts_completeness_certificates.json").read_text(encoding="utf-8")
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

    def test_pointer_table_classification_and_bsrf_correction(self):
        """7 false-positive BSRF sites must be removed and reclassified as pointer table DATA."""
        acc = self.false_tables["accounting"]
        self.assertEqual(acc["historical_indirect_site_count"], 2233)
        self.assertEqual(acc["false_positive_indirect_sites"], 7)
        self.assertEqual(acc["canonical_indirect_site_count"], 2226)
        self.assertEqual(acc["canonical_bsrf_count"], 0)
        self.assertEqual(len(self.false_tables["false_instruction_pcs"]), 7)

    def test_raw_byte_jsr_proofs(self):
        """All 36 residual JSR sites must be verified from raw binary bytes with zero clobbers."""
        self.assertEqual(self.raw_jsr["total_analyzed"], 36)
        self.assertEqual(self.raw_jsr["resolved_count"], 36)
        self.assertEqual(self.raw_jsr["unresolved_count"], 0)
        self.assertTrue(self.raw_jsr["all_paths_proven"])
        for p in self.raw_jsr["proofs"]:
            self.assertEqual(p["final_status"], "RESOLVED_EXACT_SINGLE")
            self.assertTrue(p["all_paths_same_definition"])
            self.assertEqual(len(p["clobber_sites"]), 0)
            self.assertTrue(p["literal_value"].startswith("0x"))

    def test_rts_completeness_certificates(self):
        """RTS completeness certificates must strictly enforce contracts without synthetic placeholders."""
        self.assertEqual(self.rts_certs["total_rts_sites"], 638)
        self.assertTrue(self.rts_certs["all_certified_meet_contract"])
        self.assertTrue(self.rts_certs["zero_synthetic_placeholders"])

        # Derived counts invariant
        resolved = self.rts_certs["certified_resolved"]
        unresolved = self.rts_certs["honest_unresolved"]
        self.assertEqual(resolved + unresolved, 638)
        self.assertGreater(resolved, 0)
        self.assertGreater(unresolved, 0)

        for c in self.rts_certs["certificates"]:
            if c["is_certified_resolved"]:
                self.assertEqual(c["resolution_status"], "RESOLVED_FINITE_SET")
                self.assertTrue(c["pr_paths_complete"])
                self.assertTrue(c["caller_domain_complete"])
                self.assertEqual(c["unresolved_possible_callers"], 0)
                self.assertGreater(c["caller_count"], 0)
                self.assertGreater(c["return_domain_count"], 0)
                for caller in c["callers"]:
                    self.assertFalse(caller.startswith("CALLERS_OF"))
            else:
                self.assertEqual(c["resolution_status"], "UNRESOLVED")

    def test_canonical_scorecard_accounting(self):
        """Scorecard must reflect canonical 2,226 denominator and derived metrics."""
        acc = self.scorecard["accounting"]
        self.assertEqual(acc["historical_denominator"], 2233)
        self.assertEqual(acc["false_positive_sites_removed"], 7)
        self.assertEqual(acc["canonical_denominator"], 2226)
        self.assertEqual(acc["resolved_total"] + acc["unresolved_total"], 2226)

        cj = self.scorecard["indirect_call_jump_metrics"]
        self.assertEqual(cj["total"], 1588)
        self.assertEqual(cj["resolved"], 1588)
        self.assertEqual(cj["unresolved"], 0)
        self.assertEqual(cj["resolution_ratio"], "100.00%")

        rf = self.scorecard["return_flow_rts_metrics"]
        self.assertEqual(rf["total"], 638)
        self.assertEqual(rf["resolved"], self.rts_certs["certified_resolved"])
        self.assertEqual(rf["unresolved"], self.rts_certs["honest_unresolved"])

        # Opcode check
        op = self.scorecard["opcode_breakdown"]
        self.assertEqual(op["JSR"]["total"], 1465)
        self.assertEqual(op["JSR"]["resolved"], 1465)
        self.assertEqual(op["JMP"]["total"], 121)
        self.assertEqual(op["JMP"]["resolved"], 121)
        self.assertEqual(op["BRAF"]["total"], 2)
        self.assertEqual(op["BRAF"]["resolved"], 2)
        self.assertEqual(op["BSRF"]["total"], 0)
        self.assertEqual(op["BSRF"]["resolved"], 0)
        self.assertEqual(op["RTS"]["total"], 638)
        self.assertEqual(op["RTS"]["resolved"], self.rts_certs["certified_resolved"])

    def test_executable_byte_partition_and_retraction(self):
        """Partitions must balance and record honest code retractions."""
        self.assertEqual(self.partition["total_binary_bytes"], 1457152)
        self.assertTrue(self.partition["all_partitions_balanced"])
        for m in self.partition["modules"]:
            part_sum = (
                m["confirmed_code_bytes"]
                + m["proven_data_bytes"]
                + m["proven_padding_bytes"]
                + m["unknown_bytes"]
            )
            self.assertEqual(part_sum, m["size_bytes"], f"Partition sum mismatch in {m['module']}")

        self.assertGreater(self.partition["unknown_bytes_reduction"], 0)
        self.assertEqual(
            self.partition["unknown_bytes_reduction"],
            self.partition["baseline_unknown_bytes"] - self.partition["total_unknown_bytes"]
        )
        self.assertGreaterEqual(self.partition["code_bytes_retracted"], 0)

    def test_cfg_closure_monotonicity(self):
        """CFG closure must track audited targets and residual gaps."""
        self.assertGreater(self.closure["proven_targets_injected"], 0)
        self.assertLessEqual(self.closure["residual_undecoded_gaps_after"], 1595)


if __name__ == "__main__":
    unittest.main()
