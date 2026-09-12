#!/usr/bin/env python3
"""
tests/asm/test_recovery_gates.py ? Unit Tests & Negative Controls for Gate Validators
"""

import copy
import json
import sys
from pathlib import Path

# Add tools/asm to path
repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root / "tools" / "asm"))

from validate_recovery_gates import (
    GateIntegrityError,
    audit_asm_90_gate,
    audit_full_asm_game_gate,
    audit_d18_guest_removal,
    audit_l5_oracle_equivalence,
    load_scorecard,
    run_full_validation,
)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from negative_controls_p3 import run_all_p3_negative_controls
from negative_controls_p4 import run_all_p4_negative_controls
from negative_controls_p5 import run_all_p5_negative_controls


def test_honest_scorecard_passes():
    scorecard_path = repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json"
    scorecard = load_scorecard(scorecard_path)

    full_asm = audit_full_asm_game_gate(scorecard)
    assert full_asm["claimed_status"] == "NOT_YET_REPROVEN"
    assert full_asm["can_pass"] is False, "FULL_ASM_GAME_GATE must not pass while indirect sites remain unresolved"
    assert any("P3 residual ambiguity" in issue for issue in full_asm["issues"])

    runtime_src = repo_root / "src" / "runtime" / "standalone_runtime.cpp"
    d18 = audit_d18_guest_removal(runtime_src, scorecard)
    assert d18["has_guest_fallback"] is True, "step_sh2 should be detected in production runtime"
    assert d18["claimed_status"] in ("NOT_SATISFIED", "FROZEN_BY_ASM_FIRST_ARCHITECTURE")

    print("[PASS] Current honest scorecard passes validation.")


def test_premature_full_asm_rejected():
    scorecard_path = repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json"
    scorecard = load_scorecard(scorecard_path)

    # Corrupt: set full_gameplay_verified = False while claiming PASS
    fake_scorecard = copy.deepcopy(scorecard)
    fake_scorecard["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    fake_scorecard["metrics"]["full_gameplay_verified"] = False

    try:
        audit_full_asm_game_gate(fake_scorecard)
        assert False, "Should have raised GateIntegrityError for unverified gameplay"
    except GateIntegrityError as e:
        assert "falsely claimed PASS" in str(e)
        print("[PASS] Negative control: unverified gameplay rejected fail-closed.")


def test_premature_d18_guest_removal_rejected():
    scorecard_path = repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json"
    scorecard = load_scorecard(scorecard_path)

    # Corrupt: claim STANDALONE_NATIVE_GATE is PASS while step_sh2 is present
    fake_scorecard = copy.deepcopy(scorecard)
    fake_scorecard["gates"]["STANDALONE_NATIVE_GATE"]["status"] = "PASS"

    runtime_src = repo_root / "src" / "runtime" / "standalone_runtime.cpp"
    try:
        audit_d18_guest_removal(runtime_src, fake_scorecard)
        assert False, "Should have raised GateIntegrityError for false STANDALONE_NATIVE_GATE"
    except GateIntegrityError as e:
        assert "falsely claimed PASS" in str(e)
        print("[PASS] Negative control: premature STANDALONE_NATIVE_GATE rejected fail-closed.")


def test_bgm_omission_rejected():
    scorecard_path = repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json"
    scorecard = load_scorecard(scorecard_path)

    # Corrupt: set BGM.BIN with runtime_verified = false, claim PASS
    fake_scorecard = copy.deepcopy(scorecard)
    fake_scorecard["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    for mod in fake_scorecard["modules"]:
        if mod["name"] == "BGM.BIN":
            mod["runtime_verified"] = False

    try:
        audit_full_asm_game_gate(fake_scorecard)
        assert False, "Should have raised GateIntegrityError"
    except GateIntegrityError as e:
        assert "BGM.BIN" in str(e)
        print("[PASS] Negative control: BGM.BIN unverified status rejected.")


def test_missing_module_rejected():
    scorecard_path = repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json"
    scorecard = load_scorecard(scorecard_path)

    # Corrupt: drop SET07.BIN and claim PASS
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    fake["modules"] = [m for m in fake["modules"] if m["name"] != "SET07.BIN"]

    try:
        audit_full_asm_game_gate(fake, repo_root)
        assert False, "Should have raised GateIntegrityError for missing module"
    except GateIntegrityError as e:
        assert "Missing required executable modules" in str(e)
        print("[PASS] Negative control: missing module rejected fail-closed.")


def test_non_byte_exact_rejected():
    scorecard_path = repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json"
    scorecard = load_scorecard(scorecard_path)

    # Corrupt: set 0TH2.BIN reassembly_status to NEEDS_ALIGNMENT
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    fake["modules"][0]["reassembly_status"] = "NEEDS_ALIGNMENT"

    try:
        audit_full_asm_game_gate(fake, repo_root)
        assert False, "Should have raised GateIntegrityError for non-byte-exact module"
    except GateIntegrityError as e:
        assert "expected 'BYTE_EXACT'" in str(e)
        print("[PASS] Negative control: non-byte-exact module rejected fail-closed.")


def _setup_mock_tree():
    import tempfile, shutil
    td = tempfile.TemporaryDirectory()
    tr = Path(td.name)
    shutil.copytree(repo_root / "asm" / "manifests", tr / "asm" / "manifests")
    shutil.copytree(repo_root / "workstreams" / "T2-ASM-CARVER", tr / "workstreams" / "T2-ASM-CARVER")
    return td, tr


def test_nc1_p3_hardcoded_zero_rejected():
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree()
    p3_file = tr / "workstreams" / "T2-ASM-CARVER" / "p3_control_flow_resolution.json"
    p3_data = json.loads(p3_file.read_text(encoding="utf-8"))
    p3_data["unresolved_control_flow_unknown"] = 0
    p3_data["records"][0]["resolved_state"] = "UNRESOLVED_EXECUTABLE_CANDIDATE"
    p3_file.write_text(json.dumps(p3_data), encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed for hardcoded zero with unresolved record"
    except GateIntegrityError as e:
        assert "unresolved but records contain" in str(e) or "UNRESOLVED_EXECUTABLE_CANDIDATE" in str(e)
        print("[PASS] NC1: hard-code P3 summary to zero while unresolved record exists rejected.")
    finally:
        td.cleanup()


def test_nc2_blocked_record_rejected():
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree()
    p3_file = tr / "workstreams" / "T2-ASM-CARVER" / "p3_control_flow_resolution.json"
    p3_data = json.loads(p3_file.read_text(encoding="utf-8"))
    p3_data["records"][0]["resolved_state"] = "BLOCKED_WITH_EXACT_REASON"
    p3_file.write_text(json.dumps(p3_data), encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed for BLOCKED_WITH_EXACT_REASON record"
    except GateIntegrityError as e:
        assert "BLOCKED_WITH_EXACT_REASON" in str(e)
        print("[PASS] NC2: BLOCKED_WITH_EXACT_REASON record rejected fail-closed.")
    finally:
        td.cleanup()


def test_nc3_executed_0600428a_noncode_rejected():
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree()
    p3_file = tr / "workstreams" / "T2-ASM-CARVER" / "p3_control_flow_resolution.json"
    p3_data = json.loads(p3_file.read_text(encoding="utf-8"))
    for r in p3_data["records"]:
        if r.get("runtime_start") == "0x0600428A":
            r["resolved_state"] = "UNKNOWN_NONEXECUTABLE"
    p3_file.write_text(json.dumps(p3_data), encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed when 0x0600428A is non-code"
    except GateIntegrityError as e:
        assert "0x0600428A" in str(e)
        print("[PASS] NC3: historical executed site 0x0600428A marked non-code rejected fail-closed.")
    finally:
        td.cleanup()


def test_nc4_empty_carver_diff_rejected():
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree()
    diff_file = tr / "workstreams" / "T2-ASM-CARVER" / "carver_integrity_diff.json"
    diff_file.write_text("", encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed for empty carver_integrity_diff.json"
    except GateIntegrityError as e:
        assert "carver_integrity_diff.json is empty" in str(e)
        print("[PASS] NC4: empty carver_integrity_diff.json rejected fail-closed.")
    finally:
        td.cleanup()


def test_nc5_probable_data_cfg_overlap_rejected():
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree()
    mf_file = tr / "asm" / "manifests" / "0TH2.BIN.json"
    mf_data = json.loads(mf_file.read_text(encoding="utf-8"))
    mf_data["ranges"].append({
        "offset_start": 100, "offset_end_exclusive": 104, "runtime_start": "0x06004064",
        "byte_length": 4, "evidence_classification": "DATA_PROBABLE", "assembly_representation": "RAW_DATA",
        "evidence_refs": ["EXACT_CFG_TARGET"],
    })
    mf_file.write_text(json.dumps(mf_data), encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed for PROBABLE_DATA overlapping exact CFG target"
    except GateIntegrityError as e:
        assert "PROBABLE_DATA overlaps exact CFG target" in str(e)
        print("[PASS] NC5: PROBABLE_DATA overlapping exact CFG target rejected fail-closed.")
    finally:
        td.cleanup()


def test_nc6_confirmed_code_raw_pending_rejected():
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree()
    mf_file = tr / "asm" / "manifests" / "0TH2.BIN.json"
    mf_data = json.loads(mf_file.read_text(encoding="utf-8"))
    mf_data["ranges"].append({
        "offset_start": 200, "offset_end_exclusive": 216, "runtime_start": "0x060040C8",
        "byte_length": 16, "evidence_classification": "CONFIRMED_CODE",
        "assembly_representation": "RAW_CODE_PENDING",
    })
    mf_file.write_text(json.dumps(mf_data), encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed for confirmed code with RAW_CODE_PENDING"
    except GateIntegrityError as e:
        assert "SH2_RAW_CODE_PENDING" in str(e)
        print("[PASS] NC6: confirmed code represented RAW_CODE_PENDING rejected fail-closed.")
    finally:
        td.cleanup()


def test_nc7_byte_mismatch_rejected():
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    fake["modules"][0]["confirmed_code_bytes"] += 100
    try:
        audit_full_asm_game_gate(fake, repo_root)
        assert False, "Should have failed for confirmed vs proven byte mismatch"
    except GateIntegrityError as e:
        assert "Confirmed vs proven byte mismatch" in str(e)
        print("[PASS] NC7: confirmed/proven byte mismatch rejected fail-closed.")


def test_nc8_unknown_execution_hit_rejected():
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree()
    gap_file = tr / "workstreams" / "T2-ASM-CARVER" / "unknown_gap_report.json"
    gap_data = json.loads(gap_file.read_text(encoding="utf-8"))
    gap_data["gaps_by_priority"]["P1_EXECUTION"] = 5
    gap_file.write_text(json.dumps(gap_data), encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed for unknown execution hit"
    except GateIntegrityError as e:
        assert "UNKNOWN_EXECUTION_HITS" in str(e)
        print("[PASS] NC8: unknown execution hit rejected fail-closed.")
    finally:
        td.cleanup()


def test_premature_overall_complete_rejected():
    scorecard_path = repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json"
    scorecard = load_scorecard(scorecard_path)

    fake_scorecard = copy.deepcopy(scorecard)
    fake_scorecard["overall_status"] = "COMPLETE"

    try:
        run_full_validation(repo_root, fake_scorecard)
        assert False, "Should have raised GateIntegrityError for premature overall COMPLETE"
    except GateIntegrityError as e:
        assert "overall_status COMPLETE" in str(e)
        print("[PASS] Negative control: premature overall COMPLETE rejected fail-closed.")


def main():
    test_honest_scorecard_passes()
    test_premature_full_asm_rejected()
    test_premature_d18_guest_removal_rejected()
    test_bgm_omission_rejected()
    test_missing_module_rejected()
    test_non_byte_exact_rejected()
    test_nc1_p3_hardcoded_zero_rejected()
    test_nc2_blocked_record_rejected()
    test_nc3_executed_0600428a_noncode_rejected()
    test_nc4_empty_carver_diff_rejected()
    test_nc5_probable_data_cfg_overlap_rejected()
    test_nc6_confirmed_code_raw_pending_rejected()
    test_nc7_byte_mismatch_rejected()
    test_nc8_unknown_execution_hit_rejected()
    test_premature_overall_complete_rejected()
    run_all_p3_negative_controls(repo_root)
    run_all_p4_negative_controls(repo_root)
    run_all_p5_negative_controls(repo_root)
    assert run_full_validation(repo_root) is True
    print("All 32 negative controls (8 base + 8 P3 NC-A..NC-H + 8 P4 NC-I..NC-P + 8 P5 NC-Q..NC-X) and gate validator tests passed 100%.")


if __name__ == "__main__":
    main()
