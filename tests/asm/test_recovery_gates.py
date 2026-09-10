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
    assert not full_asm["can_pass"], "FULL_ASM_GAME_GATE should not be able to pass yet"
    assert full_asm["claimed_status"] == "NOT_SATISFIED"

    runtime_src = repo_root / "src" / "runtime" / "standalone_runtime.cpp"
    d18 = audit_d18_guest_removal(runtime_src, scorecard)
    assert d18["has_guest_fallback"] is True, "step_sh2 should be detected in production runtime"
    assert d18["claimed_status"] == "NOT_SATISFIED"

    print("[PASS] Current honest scorecard passes validation.")


def test_premature_full_asm_rejected():
    scorecard_path = repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json"
    scorecard = load_scorecard(scorecard_path)

    # Corrupt: claim FULL_ASM_GAME_GATE is PASS while BGM.BIN is incomplete
    fake_scorecard = copy.deepcopy(scorecard)
    fake_scorecard["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"

    try:
        audit_full_asm_game_gate(fake_scorecard)
        assert False, "Should have raised GateIntegrityError for false FULL_ASM_GAME_GATE"
    except GateIntegrityError as e:
        assert "falsely claimed PASS" in str(e)
        print("[PASS] Negative control: premature FULL_ASM_GAME_GATE rejected fail-closed.")


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

    # Corrupt: keep BGM.BIN with runtime_verified = false, claim PASS
    fake_scorecard = copy.deepcopy(scorecard)
    fake_scorecard["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"

    try:
        audit_full_asm_game_gate(fake_scorecard)
        assert False, "Should have raised GateIntegrityError"
    except GateIntegrityError as e:
        assert "BGM.BIN" in str(e)
        print("[PASS] Negative control: BGM.BIN unverified status rejected.")


def main():
    test_honest_scorecard_passes()
    test_premature_full_asm_rejected()
    test_premature_d18_guest_removal_rejected()
    test_bgm_omission_rejected()
    print("All gate validator tests and negative controls passed 100%.")


if __name__ == "__main__":
    main()
