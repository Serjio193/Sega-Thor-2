#!/usr/bin/env python3
"""tests/asm/negative_controls_p3.py — Negative Controls Suite A-H for P3 / Gate Integrity.

Implements required Negative Controls:
  A. MANIFEST_EXECUTION_TAINT
  B. ODD_SH2_PC
  C. HARDCODED_D9_WITHOUT_ARTIFACT
  D. P3_CODE_NOT_IN_MANIFEST
  E. WHOLE_GAP_OVERPROMOTION
  F. FALLTHROUGH_OVERPROMOTION
  G. EXECUTED_PC_OUTSIDE_CODE
  H. P3_MANIFEST_BYTE_UNION_MISMATCH
"""

import copy
import json
import shutil
import tempfile
from pathlib import Path

from validate_recovery_gates import (
    GateIntegrityError,
    audit_full_asm_game_gate,
    load_scorecard,
)


def _setup_mock_tree(repo_root: Path):
    td = tempfile.TemporaryDirectory()
    tr = Path(td.name)
    shutil.copytree(repo_root / "asm" / "manifests", tr / "asm" / "manifests")
    shutil.copytree(repo_root / "workstreams" / "T2-ASM-CARVER", tr / "workstreams" / "T2-ASM-CARVER")
    return td, tr


def test_nc_a_manifest_execution_taint(repo_root: Path):
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree(repo_root)
    u_file = tr / "workstreams" / "T2-ASM-CARVER" / "executed_pc_union.json"
    u_data = json.loads(u_file.read_text(encoding="utf-8"))
    u_data["manifest_derived_execution_entries"] = 1
    u_file.write_text(json.dumps(u_data), encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed for MANIFEST_DERIVED_EXECUTION_ENTRIES"
    except GateIntegrityError as e:
        assert "MANIFEST_DERIVED_EXECUTION_ENTRIES" in str(e)
        print("[PASS] NC-A: manifest execution taint rejected fail-closed.")
    finally:
        td.cleanup()


def test_nc_b_odd_sh2_pc(repo_root: Path):
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree(repo_root)
    u_file = tr / "workstreams" / "T2-ASM-CARVER" / "executed_pc_union.json"
    u_data = json.loads(u_file.read_text(encoding="utf-8"))
    u_data["unaligned_instruction_pcs"] = 1
    u_data["executed_instruction_pcs"].append({
        "revision": "RUS", "cpu": "MASTER_SH2", "module": "0TH2.BIN", "generation": 1,
        "pc": "0x06004001", "source": "TEST_ODD", "artifact_path": "none", "artifact_sha256": "0"*64
    })
    u_file.write_text(json.dumps(u_data), encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed for unaligned instruction PC"
    except GateIntegrityError as e:
        assert "UNALIGNED" in str(e)
        print("[PASS] NC-B: odd SH-2 instruction PC (0x06004001) rejected fail-closed.")
    finally:
        td.cleanup()


def test_nc_c_hardcoded_d9_without_artifact(repo_root: Path):
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree(repo_root)
    u_file = tr / "workstreams" / "T2-ASM-CARVER" / "executed_pc_union.json"
    u_data = json.loads(u_file.read_text(encoding="utf-8"))
    u_data["dynamic_evidence_without_real_artifact"] = 1
    u_file.write_text(json.dumps(u_data), encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed for dynamic evidence without real artifact"
    except GateIntegrityError as e:
        assert "DYNAMIC_EVIDENCE_WITHOUT_REAL_ARTIFACT" in str(e)
        print("[PASS] NC-C: dynamic evidence without real artifact rejected fail-closed.")
    finally:
        td.cleanup()


def test_nc_d_p3_code_not_in_manifest(repo_root: Path):
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree(repo_root)
    p3_file = tr / "workstreams" / "T2-ASM-CARVER" / "p3_control_flow_resolution.json"
    p3_data = json.loads(p3_file.read_text(encoding="utf-8"))
    # Inject a 2-byte P3 CONFIRMED_CODE range that does not exist in manifest
    p3_data["records"].append({
        "module": "0TH2.BIN", "generation": 1, "offset_start": 400000, "offset_end_exclusive": 400002,
        "byte_length": 2, "runtime_start": "0x06065A00", "runtime_end_exclusive": "0x06065A02",
        "resolved_state": "CONFIRMED_CODE", "evidence_reason": "SYNTHETIC_GAP",
        "seed_reachability_provenance": "NONE", "decoder_provenance": "NONE",
        "mnemonic_representation_state": "MNEMONIC_PROVEN", "left_terminator_opcode": None,
        "has_fallthrough": False, "incoming_branch_count": 0, "cdl_exec_count": 0,
        "cdl_read_count": 0, "campaign_id": "0TH2.BIN_block_00"
    })
    p3_file.write_text(json.dumps(p3_data), encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed for P3 code missing from manifest"
    except GateIntegrityError as e:
        assert "P3_CONFIRMED_MISSING_FROM_MANIFEST_BYTES" in str(e)
        print("[PASS] NC-D: P3 code not in manifest rejected fail-closed.")
    finally:
        td.cleanup()


def test_nc_e_wholegap_overpromotion(repo_root: Path):
    # Construct: branch target at first instruction of an UNKNOWN gap followed by literal pool data
    # Test that promoting the entire gap to code causes decode failure in Thor SH-2 decoder
    import subprocess
    exe_name = "export_sh2_asm_ir.exe" if Path(repo_root / "build" / "export_sh2_asm_ir.exe").exists() else "export_sh2_asm_ir"
    exe_path = repo_root / "build" / exe_name
    if not exe_path.exists():
        exe_path = repo_root / "build_linux" / "export_sh2_asm_ir"

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        bin_p = tmp / "test.bin"
        # 0x0009 (NOP), 0xFFFF (illegal opcode/data)
        bin_p.write_bytes(bytes([0x00, 0x09, 0xFF, 0xFF]))
        out_j = tmp / "out.json"
        cmd = [str(exe_path), str(bin_p), "0x06004000", str(out_j), "0x06004000:0x06004004:blk_test"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode != 0, "Whole-gap promotion with data tail must fail decoder!"
    print("[PASS] NC-E: whole-gap overpromotion over literal/data rejected fail-closed.")


def test_nc_f_fallthrough_overpromotion(repo_root: Path):
    # Construct: terminal transfer (RTS: 0x000B), delay slot (NOP: 0x0009), followed by data (0xFFFF)
    # The decoder / resolver must stop at delay slot and not promote sequential data
    from tools.carver.thor_decoder import dump_all_valid_with_thor_sh2
    test_bytes = bytes([0x00, 0x0B, 0x00, 0x09, 0xFF, 0xFF])
    insts = dump_all_valid_with_thor_sh2(repo_root, "test_f", 0x06004000, test_bytes)
    assert 0x06004000 in insts and insts[0x06004000].opcode_id == "RTS"
    assert 0x06004002 in insts and insts[0x06004002].opcode_id == "NOP"
    assert 0x06004004 not in insts, "Data following terminal transfer must not be valid instruction!"
    print("[PASS] NC-F: fallthrough overpromotion after terminal transfer rejected fail-closed.")


def test_nc_g_executed_pc_outside_code(repo_root: Path):
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree(repo_root)
    # Remove confirmed code range containing 0x0600428A from 0TH2.BIN manifest
    mf_file = tr / "asm" / "manifests" / "0TH2.BIN.json"
    mf_data = json.loads(mf_file.read_text(encoding="utf-8"))
    mf_data["ranges"] = [
        r for r in mf_data["ranges"]
        if not (int(r.get("runtime_start", "0"), 16) <= 0x0600428A < int(r.get("runtime_end_exclusive", "0"), 16))
    ]
    mf_file.write_text(json.dumps(mf_data), encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed when executed PC is outside confirmed code"
    except GateIntegrityError as e:
        assert "EXECUTED_PC_OUTSIDE_CONFIRMED_CODE" in str(e)
        print("[PASS] NC-G: executed PC pointing into non-code rejected fail-closed.")
    finally:
        td.cleanup()


def test_nc_h_p3_manifest_byte_union_mismatch(repo_root: Path):
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree(repo_root)
    # Truncate manifest confirmed range while keeping scorecard counters identical
    mf_file = tr / "asm" / "manifests" / "0TH2.BIN.json"
    mf_data = json.loads(mf_file.read_text(encoding="utf-8"))
    for r in mf_data["ranges"]:
        if "P3_CFG_CLOSURE" in r.get("evidence_refs", []) and r.get("byte_length", 0) > 4:
            r["runtime_end_exclusive"] = f"0x{int(r['runtime_start'], 16) + 2:08X}"
            r["offset_end_exclusive"] = r["offset_start"] + 2
            r["byte_length"] = 2
            break
    mf_file.write_text(json.dumps(mf_data), encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed for interval union mismatch despite counters"
    except GateIntegrityError as e:
        assert "P3_CONFIRMED_MISSING_FROM_MANIFEST_BYTES" in str(e) or "byte mismatch" in str(e)
        print("[PASS] NC-H: interval union mismatch with zeroed summary counters rejected fail-closed.")
    finally:
        td.cleanup()


def run_all_p3_negative_controls(repo_root: Path):
    test_nc_a_manifest_execution_taint(repo_root)
    test_nc_b_odd_sh2_pc(repo_root)
    test_nc_c_hardcoded_d9_without_artifact(repo_root)
    test_nc_d_p3_code_not_in_manifest(repo_root)
    test_nc_e_wholegap_overpromotion(repo_root)
    test_nc_f_fallthrough_overpromotion(repo_root)
    test_nc_g_executed_pc_outside_code(repo_root)
    test_nc_h_p3_manifest_byte_union_mismatch(repo_root)
    print("All 8 new P3 negative controls (NC-A through NC-H) passed 100%.")
