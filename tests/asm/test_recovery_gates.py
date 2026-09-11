#!/usr/bin/env python3
"""
tests/asm/test_recovery_gates.py ? Unit Tests & Negative Controls for Gate Validators
"""

import copy
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


def test_honest_scorecard_passes():
    scorecard_path = repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json"
    scorecard = load_scorecard(scorecard_path)

    full_asm = audit_full_asm_game_gate(scorecard)
    assert full_asm["can_pass"] is True, f"FULL_ASM_GAME_GATE should pass: {full_asm['issues']}"
    assert full_asm["claimed_status"] == "PASS"
    assert len(full_asm["issues"]) == 0

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


def test_premature_overall_complete_rejected():
    scorecard_path = repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json"
    scorecard = load_scorecard(scorecard_path)

    # Corrupt: claim overall_status = COMPLETE while guest fallback is present
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
    test_premature_overall_complete_rejected()
    assert run_full_validation(repo_root) is True
    print("All gate validator tests and negative controls passed 100%.")


if __name__ == "__main__":
    main()
