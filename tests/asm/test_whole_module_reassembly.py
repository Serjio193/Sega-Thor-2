#!/usr/bin/env python3
"""tests/asm/test_whole_module_reassembly.py — Unit Tests for Whole-Module Reassembly.

Phase 26 of T2-ASM-10:
  Verifies whole-module source reassembly invariants:
  1. Every byte of each module is owned exactly once (no gaps, no overlaps).
  2. Module interval sums match module sizes exactly.
  3. All 4 rebuilt modules match canonical SHA-256 hashes.
  4. Binary diff shows 0 differing bytes across all modules.
  5. Multi-build determinism is verified (0 drift).
  6. Instruction roundtrip has 0 mismatches and 0 delay-slot reorderings.
"""

from pathlib import Path
import json
import unittest

repo_root = Path(__file__).resolve().parent.parent.parent


class TestWholeModuleReassembly(unittest.TestCase):

    def setUp(self):
        self.workstream_dir = repo_root / "workstreams" / "T2-ASM-10"
        self.ownership_path = self.workstream_dir / "module_byte_ownership_v3.json"
        self.rebuild_path = self.workstream_dir / "module_reassembly_results.json"
        self.diff_path = self.workstream_dir / "module_binary_diff.json"
        self.det_path = self.workstream_dir / "reassembly_determinism.json"
        self.rt_path = self.workstream_dir / "instruction_roundtrip.json"

        self.assertTrue(self.ownership_path.exists(), "module_byte_ownership_v3.json must exist")
        self.assertTrue(self.rebuild_path.exists(), "module_reassembly_results.json must exist")
        self.assertTrue(self.diff_path.exists(), "module_binary_diff.json must exist")
        self.assertTrue(self.det_path.exists(), "reassembly_determinism.json must exist")
        self.assertTrue(self.rt_path.exists(), "instruction_roundtrip.json must exist")

        self.ownership = json.loads(self.ownership_path.read_text(encoding="utf-8"))
        self.rebuild = json.loads(self.rebuild_path.read_text(encoding="utf-8"))
        self.diff = json.loads(self.diff_path.read_text(encoding="utf-8"))
        self.det = json.loads(self.det_path.read_text(encoding="utf-8"))
        self.rt = json.loads(self.rt_path.read_text(encoding="utf-8"))

    def test_interval_coverage_exact(self):
        """Every module byte must be owned exactly once with no gaps or overlaps."""
        expected_sizes = {
            "0TH2.BIN": 535552,
            "TH2.LOW": 149504,
            "SET07.BIN": 98304,
            "BGM.BIN": 673792,
        }
        for mod_name, exp_sz in expected_sizes.items():
            self.assertIn(mod_name, self.ownership["modules"])
            mod = self.ownership["modules"][mod_name]
            intervals = mod["intervals"]

            curr_offset = 0
            for iv in intervals:
                self.assertEqual(
                    iv["offset_start"],
                    curr_offset,
                    f"Gap or overlap in {mod_name} at offset {curr_offset} (start={iv['offset_start']})",
                )
                self.assertGreater(iv["byte_length"], 0)
                self.assertEqual(iv["byte_length"], iv["offset_end_exclusive"] - iv["offset_start"])
                curr_offset = iv["offset_end_exclusive"]

            self.assertEqual(curr_offset, exp_sz, f"Total intervals length does not match module size for {mod_name}")

    def test_rebuilt_module_hashes(self):
        """All 4 rebuilt modules must match canonical SHA-256 hashes."""
        expected_shas = {
            "0TH2.BIN": "c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64",
            "TH2.LOW": "781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224",
            "SET07.BIN": "bb6072222e19f8cb68934cbdb94e7d187c67680bb9e167524f85579ee6bc0af6",
            "BGM.BIN": "c1d11d5386eaffbd4ca6443c3de615312a71cc678ba4d76c2c9d6035acf9a8f6",
        }
        for rec in self.rebuild["modules"]:
            mod_name = rec["module"]
            self.assertIn(mod_name, expected_shas)
            self.assertEqual(rec["rebuilt_sha256"], expected_shas[mod_name])
            self.assertTrue(rec["sha256_match"])
            self.assertTrue(rec["BYTE_EXACT_CONTAINER_REASSEMBLY"])

    def test_binary_diff_zero(self):
        """Binary diff must show zero differing bytes across all modules."""
        self.assertTrue(self.diff["summary"]["all_modules_zero_diff"])
        self.assertEqual(self.diff["summary"]["total_differing_bytes_across_all_modules"], 0)
        for rec in self.diff["modules"]:
            self.assertEqual(rec["total_differing_bytes"], 0)
            self.assertIsNone(rec["first_differing_offset"])
            self.assertEqual(rec["differing_intervals"], [])

    def test_multi_build_determinism(self):
        """Rebuilds must be 100% deterministic across repeated runs."""
        self.assertTrue(self.det["summary"]["all_modules_deterministic"])
        for rec in self.det["modules"]:
            self.assertTrue(rec["is_deterministic"])
            self.assertEqual(rec["build_1_sha256"], rec["build_2_sha256"])

    def test_instruction_roundtrip_integrity(self):
        """Instruction roundtrip must have zero mismatches and no delay-slot reordering."""
        summary = self.rt["summary"]
        self.assertEqual(summary["confirmed_code_byte_mismatches"], 0)
        self.assertEqual(summary["delay_slot_reordering_detected"], 0)
        self.assertEqual(summary["instruction_roundtrip_status"], "PASS")
        self.assertEqual(summary["pointer_tables_protected_as_data"], 3)
        self.assertEqual(summary["false_bsrf_halfwords_retained_as_data"], 7)


if __name__ == "__main__":
    unittest.main()
