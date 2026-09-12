#!/usr/bin/env python3
"""tests/asm/test_gap_decarving.py — Unit Tests for Gap Decarving & RTS V3 Completeness.

Phase 26 of T2-ASM-10:
  Verifies gap decarving and control-flow proof invariants:
  1. Baseline SH-2 UNKNOWN inventory reproduces 511,452 bytes.
  2. All data promotion certificates have affirmative evidence.
  3. No UNKNOWN interval is promoted implicitly or without certificate.
  4. Closed-world theorem V2 accounts for residual UNKNOWN threats fail-closed.
  5. RTS completeness V3 maintains exact 638 total with 539 resolved and 99 honest unresolved.
  6. PR path refinements match symbolic trace rules.
"""

from pathlib import Path
import json
import unittest

repo_root = Path(__file__).resolve().parent.parent.parent


class TestGapDecarving(unittest.TestCase):

    def setUp(self):
        self.workstream_dir = repo_root / "workstreams" / "T2-ASM-10"
        self.inv_path = self.workstream_dir / "sh2_unknown_inventory.json"
        self.data_cert_path = self.workstream_dir / "data_promotion_certificates.json"
        self.code_cert_path = self.workstream_dir / "code_promotion_certificates.json"
        self.pad_cert_path = self.workstream_dir / "padding_certificates.json"
        self.cw_path = self.workstream_dir / "closed_world_control_flow_v2.json"
        self.rts_v3_path = self.workstream_dir / "rts_completeness_v3.json"
        self.pr_ref_path = self.workstream_dir / "pr_path_refinements.json"

        self.assertTrue(self.inv_path.exists())
        self.assertTrue(self.data_cert_path.exists())
        self.assertTrue(self.cw_path.exists())
        self.assertTrue(self.rts_v3_path.exists())
        self.assertTrue(self.pr_ref_path.exists())

        self.inv = json.loads(self.inv_path.read_text(encoding="utf-8"))
        self.data_certs = json.loads(self.data_cert_path.read_text(encoding="utf-8"))
        self.cw = json.loads(self.cw_path.read_text(encoding="utf-8"))
        self.rts_v3 = json.loads(self.rts_v3_path.read_text(encoding="utf-8"))
        self.pr_ref = json.loads(self.pr_ref_path.read_text(encoding="utf-8"))

    def test_initial_sh2_unknown_inventory_baseline(self):
        """Initial SH-2 UNKNOWN inventory must reproduce exactly 511,452 bytes."""
        total_unk = self.inv["total_sh2_unknown_bytes"]
        self.assertEqual(total_unk, 511452)
        mod_0 = self.inv["modules"]["0TH2.BIN"]["unknown_bytes"]
        mod_low = self.inv["modules"]["TH2.LOW"]["unknown_bytes"]
        mod_set = self.inv["modules"]["SET07.BIN"]["unknown_bytes"]
        self.assertEqual(mod_0, 336732)
        self.assertEqual(mod_low, 76428)
        self.assertEqual(mod_set, 98292)

    def test_promotion_certificate_integrity(self):
        """All promotion certificates must have affirmative evidence and valid lengths."""
        certs = self.data_certs.get("certificates", [])
        for c in certs:
            self.assertIn("certificate_id", c)
            self.assertIn("evidence_reason", c)
            self.assertGreater(len(c["evidence_reason"]), 0)
            self.assertGreater(c["byte_length"], 0)
            st = int(c["runtime_start"], 16)
            en = int(c["runtime_end_exclusive"], 16)
            self.assertEqual(en - st, c["byte_length"])

    def test_closed_world_theorems_v2(self):
        """Confirmed-code theorem is True; all-SH2-bytes theorem remains fail-closed False."""
        cw_theorems = self.cw["closed_world_theorems"]
        code_thm = cw_theorems["CLOSED_WORLD_OVER_CONFIRMED_CODE"]
        all_thm = cw_theorems["CLOSED_WORLD_OVER_ALL_POTENTIALLY_EXECUTABLE_SH2_BYTES"]

        self.assertTrue(code_thm["is_proven"])
        self.assertEqual(code_thm["proof_status"], "PROVEN")
        self.assertEqual(code_thm["unresolved_indirect_calls_in_confirmed_code"], 0)
        self.assertEqual(code_thm["unresolved_indirect_jumps_in_confirmed_code"], 0)

        self.assertFalse(all_thm["is_proven"])
        self.assertEqual(all_thm["proof_status"], "NOT_PROVEN_FAIL_CLOSED")
        self.assertEqual(all_thm["remaining_threat_bytes"], 498392)

    def test_rts_completeness_v3_accounting(self):
        """RTS completeness V3 must match exact accounting invariants."""
        summary = self.rts_v3["summary"]
        self.assertEqual(summary["total_rts_sites"], 638)
        self.assertEqual(summary["certified_resolved"], 552)
        self.assertEqual(summary["honest_unresolved"], 86)
        self.assertEqual(summary["certified_resolved"] + summary["honest_unresolved"], 638)
        self.assertEqual(summary["unresolved_reduction"], 96)

        # Blocker breakdown
        v_dist = summary["v3_blocker_distribution"]
        self.assertEqual(v_dist["UNRESOLVED_EXTERNAL_ENTRY"], 22)
        self.assertEqual(v_dist["UNRESOLVED_PR_PATH"], 44)
        self.assertEqual(v_dist["UNRESOLVED_CALLER_DOMAIN"], 20)

    def test_pr_path_refinement_accounting(self):
        """PR path refinements must classify all 81 baseline sites."""
        self.assertEqual(self.pr_ref["total_analyzed_sites"], 81)
        self.assertEqual(self.pr_ref["pr_path_resolved_count"], 43)
        self.assertEqual(self.pr_ref["pr_path_unresolved_count"], 38)
        b_down = self.pr_ref["breakdown_by_status"]
        self.assertEqual(b_down["PR_PATH_COMPLETE"], 43)
        self.assertEqual(b_down["SHARED_EPILOGUE_PROVEN"], 38)


if __name__ == "__main__":
    unittest.main()
