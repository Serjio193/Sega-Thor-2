#!/usr/bin/env python3
"""tests/asm/test_rts_domain_closure.py — Proof Invariants for RTS Caller-Domain Closure.

Verifies structural and semantic proof invariants:
  1. Accounting invariants:
     - historical_indirect == 2,233
     - false_bsrf == 7
     - canonical_indirect == 2,226
     - canonical_bsrf == 0
     - call/jump total == 1,588, unresolved == 0
     - RTS resolved + RTS unresolved == 638
  2. For every RESOLVED RTS:
     - PR paths complete == True
     - PR slot verified == True
     - caller domain complete == True
     - zero unresolved entry sources
     - zero unresolved reference sources
     - return domain count == caller count
  3. For every incomplete function certificate:
     - all owned RTS sites remain unresolved
  4. Zero synthetic placeholders (no CALLERS_OF_*).
"""

from pathlib import Path
import json
import unittest

repo_root = Path(__file__).resolve().parent.parent.parent


class TestRTSDomainClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        audit_p = repo_root / "workstreams/T2-ASM-09/canonical_indirect_site_audit.json"
        cls.audit = json.loads(audit_p.read_text(encoding="utf-8"))

        rts_p = repo_root / "workstreams/T2-ASM-09/rts_completeness_v2.json"
        cls.rts_v2 = json.loads(rts_p.read_text(encoding="utf-8"))

        fc_p = repo_root / "workstreams/T2-ASM-09/function_caller_certificates.json"
        cls.fc = json.loads(fc_p.read_text(encoding="utf-8"))

        sc_p = repo_root / "workstreams/T2-ASM-08/final_indirect_scorecard.json"
        cls.sc = json.loads(sc_p.read_text(encoding="utf-8"))

    def test_indirect_accounting_invariants(self):
        """Verify indirect site count accounting and zero false decodes."""
        self.assertEqual(self.audit["historical_indirect_site_count"], 2233)
        self.assertEqual(self.audit["false_positive_bsrf_count"], 7)
        self.assertEqual(self.audit["canonical_indirect_sites_checked"], 2226)
        self.assertEqual(self.audit["canonical_indirect_sites_invalid"], 0)
        self.assertEqual(self.audit["opcode_distribution"].get("BSRF", 0), 0)

        # Call/jump total is 1,465 JSR + 121 JMP + 2 BRAF == 1,588
        call_jump_total = sum(
            1 for s in self.sc["sites"] if s["opcode_id"] in ("JSR", "JMP", "BRAF")
        )
        self.assertEqual(call_jump_total, 1588)
        call_jump_unresolved = sum(
            1 for s in self.sc["sites"]
            if s["opcode_id"] in ("JSR", "JMP", "BRAF") and not s["resolution_status"].startswith("RESOLVED")
        )
        self.assertEqual(call_jump_unresolved, 0)

    def test_rts_total_and_resolution_split(self):
        """Verify RTS total == 638 and exact resolved + unresolved balance."""
        tot = self.rts_v2["total_rts_sites"]
        res = self.rts_v2["certified_resolved"]
        unres = self.rts_v2["honest_unresolved"]
        self.assertEqual(tot, 638)
        self.assertEqual(res + unres, 638)
        self.assertEqual(len(self.rts_v2["certificates"]), 638)

    def test_resolved_rts_invariants(self):
        """Verify strict proof invariants for every certified RESOLVED RTS site."""
        fc_map = {f["entries"][0]: f for f in self.fc["certificates"]}
        for cert in self.rts_v2["certificates"]:
            if cert["is_certified_resolved"]:
                self.assertTrue(cert["pr_paths_complete"], f"{cert['site_id']} missing pr_paths_complete")
                self.assertTrue(cert["pr_slot_verified"], f"{cert['site_id']} missing pr_slot_verified")
                self.assertTrue(cert["caller_domain_complete"], f"{cert['site_id']} missing caller_domain_complete")
                self.assertGreater(cert["caller_count"], 0, f"{cert['site_id']} has 0 callers")
                self.assertEqual(cert["caller_count"], cert["return_domain_count"])
                self.assertEqual(len(cert["callers"]), len(cert["return_pcs"]))

                # Check owning function certificate
                f_entry = cert["function_entry_pc"]
                if f_entry in fc_map:
                    f_cert = fc_map[f_entry]
                    self.assertTrue(f_cert["CALLER_DOMAIN_COMPLETE"])
                    self.assertEqual(f_cert["unresolved_reference_sources"], [])
                    self.assertEqual(f_cert["unresolved_entry_sources"], [])
                    self.assertTrue(f_cert["unknown_executable_regions_complete"])

    def test_incomplete_functions_quarantined(self):
        """Verify that incomplete function certificates leave all owned RTS unresolved."""
        fc_incomplete = {f["entries"][0] for f in self.fc["certificates"] if not f["CALLER_DOMAIN_COMPLETE"]}
        for cert in self.rts_v2["certificates"]:
            f_entry = cert["function_entry_pc"]
            if f_entry in fc_incomplete:
                self.assertFalse(
                    cert["is_certified_resolved"],
                    f"Violation: {cert['site_id']} in incomplete function {f_entry} marked resolved!"
                )
                self.assertIn(
                    cert["resolution_status"],
                    ("UNRESOLVED_CALLER_DOMAIN", "UNRESOLVED_PR_PATH", "UNRESOLVED_FUNCTION_BOUNDARY", "UNRESOLVED_EXTERNAL_ENTRY")
                )

    def test_zero_synthetic_placeholders(self):
        """Assert no synthetic placeholders (CALLERS_OF_*) in any certificate."""
        for cert in self.rts_v2["certificates"]:
            for c in cert["callers"]:
                self.assertFalse(c.startswith("CALLERS_OF_"), f"Synthetic placeholder found: {c}")
                self.assertTrue(c.startswith("0x") or c == "RESET_VECTOR", f"Invalid caller format: {c}")


if __name__ == '__main__':
    unittest.main()
