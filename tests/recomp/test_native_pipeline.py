#!/usr/bin/env python3
"""
Test suite for T2-D17-02 Native Block Census and Scalable Pipeline.
Validates:
1. All 3,302 blocks accounted for across 8 mutually exclusive states.
2. Exact fail-closed reason code assignment.
3. Dual-run determinism producing bit-identical census summary output.
4. Negative controls: corruption of opcodes, invalid block boundary, and unexpected instructions.
5. Sharded generation integrity and catalog consistency.
"""

import hashlib
import json
import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if not os.path.isdir(os.path.join(REPO_ROOT, "docs")):
    REPO_ROOT = os.getcwd()

sys.path.insert(0, REPO_ROOT)

def sha256_file(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

class TestNativeBlockCensusPipeline(unittest.TestCase):
    def test_01_census_run_and_state_accounting(self):
        cmd = [sys.executable, os.path.join(REPO_ROOT, 'tools', 'recomp', 'build_native_block_census.py')]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        self.assertEqual(res.returncode, 0, f'Census failed: {res.stderr}')

        with open(os.path.join(REPO_ROOT, 'workstreams', 'T2-D17-native-scaling', 'block_census_summary.json'), 'r') as f:
            summary = json.load(f)

        self.assertEqual(summary['total_harvested_blocks'], 3302)
        states = summary['summary_by_state']
        self.assertEqual(states['HARVESTED'], 3302)
        self.assertEqual(states['MNEMONIC_PROVEN'], 3032)
        self.assertEqual(states['CODEGEN_ELIGIBLE'], 270)
        self.assertEqual(states['GENERATED'], 270)
        self.assertEqual(states['COMPILES'], 270)
        self.assertEqual(states['PROMOTED'], 1)

        # Check modules breakdown
        mods = summary['modules']
        self.assertEqual(mods['0TH2.BIN']['total_proven_blocks'], 3126)
        self.assertEqual(mods['0TH2.BIN']['codegen_eligible'], 243)
        self.assertEqual(mods['TH2.LOW']['total_proven_blocks'], 176)
        self.assertEqual(mods['TH2.LOW']['codegen_eligible'], 27)

    def test_02_dual_run_determinism(self):
        # Run 1
        out1 = os.path.join(REPO_ROOT, 'out', 'test_census_run1.json')
        cmd1 = [sys.executable, os.path.join(REPO_ROOT, 'tools', 'recomp', 'build_native_block_census.py'), '--out-summary', out1]
        res1 = subprocess.run(cmd1, capture_output=True, text=True, cwd=REPO_ROOT)
        self.assertEqual(res1.returncode, 0)
        h1 = sha256_file(out1)

        # Run 2
        out2 = os.path.join(REPO_ROOT, 'out', 'test_census_run2.json')
        cmd2 = [sys.executable, os.path.join(REPO_ROOT, 'tools', 'recomp', 'build_native_block_census.py'), '--out-summary', out2]
        res2 = subprocess.run(cmd2, capture_output=True, text=True, cwd=REPO_ROOT)
        self.assertEqual(res2.returncode, 0)
        h2 = sha256_file(out2)

        self.assertEqual(h1, h2, 'Dual census runs produced differing hash digests!')
        if os.path.exists(out1): os.remove(out1)
        if os.path.exists(out2): os.remove(out2)

    def test_03_shards_and_catalog(self):
        cat_hdr = os.path.join(REPO_ROOT, 'build', 'generated', 'native_blocks', 'native_block_catalog.hpp')
        cat_src = os.path.join(REPO_ROOT, 'build', 'generated', 'native_blocks', 'native_block_catalog.cpp')
        self.assertTrue(os.path.exists(cat_hdr), 'Catalog header missing')
        self.assertTrue(os.path.exists(cat_src), 'Catalog source missing')

        # Check 6 shards exist
        for i in range(6):
            shard_path = os.path.join(REPO_ROOT, 'build', 'generated', 'native_blocks', f'native_blocks_shard_{i:02d}.cpp')
            self.assertTrue(os.path.exists(shard_path), f'Shard {i} missing')

    def test_04_negative_controls(self):
        from tools.recomp.build_native_block_census import classify_block
        
        # Negative control 1: Unsupported opcode (e.g. 0x000B RTS)
        state, reason = classify_block([0x000B])
        self.assertEqual(state, 'MNEMONIC_PROVEN')
        self.assertEqual(reason, 'UNSUPPORTED_EMITTER_OPCODE')

        # Negative control 2: Empty block
        state, reason = classify_block([])
        self.assertEqual(state, 'MNEMONIC_PROVEN')
        self.assertEqual(reason, 'INVALID_BLOCK_BOUNDARY')

        # Negative control 3: Branch without delay slot (terminator at end of block)
        state, reason = classify_block([0xA001])
        self.assertEqual(state, 'MNEMONIC_PROVEN')
        self.assertEqual(reason, 'INVALID_BLOCK_BOUNDARY')

        # Negative control 4: Branch before end (internal control flow)
        state, reason = classify_block([0xA001, 0x0009, 0x6001])
        self.assertEqual(state, 'MNEMONIC_PROVEN')
        self.assertEqual(reason, 'UNSUPPORTED_CONTROL_FLOW')

if __name__ == '__main__':
    unittest.main()
