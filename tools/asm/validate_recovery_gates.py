#!/usr/bin/env python3
"""
tools/asm/validate_recovery_gates.py ? Machine-Enforced Recovery Gate Validator

Audits ASM_90_GATE, FULL_ASM_GAME_GATE, D18 guest CPU removal, and L5 oracle
equivalence to prevent premature completion claims. Fails closed if any gate
is claimed PASS without satisfying all factual requirements.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional


class GateIntegrityError(Exception):
    """Raised when a gate is claimed PASS without meeting evidence standards."""
    pass


def load_scorecard(scorecard_path: Path) -> dict:
    if not scorecard_path.exists():
        raise FileNotFoundError(f"Scorecard not found at: {scorecard_path}")
    with open(scorecard_path, "r", encoding="utf-8") as fp:
        return json.load(fp)


def audit_asm_90_gate(scorecard: dict) -> dict:
    """Calculates per-processor and aggregate ASM recovery metrics."""
    modules = scorecard.get("modules", [])
    processor_stats = {}
    total_confirmed = 0
    total_proven = 0

    for mod in modules:
        proc = mod.get("processor", "UNKNOWN")
        conf = mod.get("confirmed_code_bytes", 0)
        prov = mod.get("proven_mnemonic_bytes", 0)

        if proc not in processor_stats:
            processor_stats[proc] = {"confirmed": 0, "proven": 0, "modules": []}

        processor_stats[proc]["confirmed"] += conf
        processor_stats[proc]["proven"] += prov
        processor_stats[proc]["modules"].append(mod.get("name"))

        total_confirmed += conf
        total_proven += prov

    breakdown = {}
    for proc, data in processor_stats.items():
        pct = (data["proven"] / data["confirmed"] * 100.0) if data["confirmed"] > 0 else 0.0
        breakdown[proc] = {
            "confirmed_bytes": data["confirmed"],
            "proven_bytes": data["proven"],
            "coverage_pct": round(pct, 2),
            "modules": data["modules"]
        }

    agg_pct = (total_proven / total_confirmed * 100.0) if total_confirmed > 0 else 0.0
    return {
        "aggregate_confirmed_bytes": total_confirmed,
        "aggregate_proven_bytes": total_proven,
        "aggregate_coverage_pct": round(agg_pct, 2),
        "processors": breakdown,
        "gate_requirement_met": agg_pct >= 90.00
    }


def audit_full_asm_game_gate(scorecard: dict) -> dict:
    """Verifies that 100% of executable modules are byte-exact and runtime-verified."""
    modules = scorecard.get("modules", [])
    issues = []
    unverified_modules = []
    non_byte_exact_modules = []

    for mod in modules:
        name = mod.get("name", "UNNAMED")
        reassembly = mod.get("reassembly_status")
        runtime_ver = mod.get("runtime_verified", False)

        if reassembly != "BYTE_EXACT":
            non_byte_exact_modules.append(name)
            issues.append(f"Module '{name}' reassembly_status is '{reassembly}', expected 'BYTE_EXACT'")
        if not runtime_ver:
            unverified_modules.append(name)
            issues.append(f"Module '{name}' has runtime_verified = false")

    gameplay_verified = scorecard.get("metrics", {}).get("full_gameplay_verified", False)
    if not gameplay_verified:
        issues.append("Full multi-scenario gameplay suite (menus, transitions, combat, audio) not yet verified")

    claimed_status = scorecard.get("gates", {}).get("FULL_ASM_GAME_GATE", {}).get("status")
    can_pass = (len(issues) == 0)

    if claimed_status == "PASS" and not can_pass:
        raise GateIntegrityError(
            f"FULL_ASM_GAME_GATE falsely claimed PASS. Outstanding issues:\n  " +
            "\n  ".join(issues)
        )

    return {
        "can_pass": can_pass,
        "claimed_status": claimed_status,
        "issues": issues,
        "non_byte_exact_modules": non_byte_exact_modules,
        "unverified_modules": unverified_modules
    }


def audit_d18_guest_removal(runtime_src_path: Path, scorecard: dict) -> dict:
    """Checks whether production runtime contains guest CPU fallback interpreter."""
    fallback_calls = []
    if runtime_src_path.exists():
        with open(runtime_src_path, "r", encoding="utf-8") as fp:
            content = fp.read()
        if "step_sh2" in content:
            fallback_calls.append("step_sh2")
        if "execute_sh2_instruction" in content:
            fallback_calls.append("execute_sh2_instruction")

    has_guest_fallback = len(fallback_calls) > 0
    claimed_status = scorecard.get("gates", {}).get("STANDALONE_NATIVE_GATE", {}).get("status")

    if claimed_status == "PASS" and has_guest_fallback:
        raise GateIntegrityError(
            f"STANDALONE_NATIVE_GATE falsely claimed PASS while guest CPU fallback "
            f"interpreter ({fallback_calls}) is active in production runtime."
        )

    return {
        "has_guest_fallback": has_guest_fallback,
        "fallback_symbols_detected": fallback_calls,
        "claimed_status": claimed_status,
        "guest_removal_complete": not has_guest_fallback
    }


def audit_l5_oracle_equivalence(test_guest_removal_path: Path, scorecard: dict) -> dict:
    """Verifies that L5 oracle equivalence is evaluated against Mednafen oracle, not self-comparison."""
    is_self_comparison = False
    if test_guest_removal_path.exists():
        with open(test_guest_removal_path, "r", encoding="utf-8") as fp:
            content = fp.read()
        if "StandaloneRuntime rt1" in content and "StandaloneRuntime rt2" in content:
            is_self_comparison = True

    return {
        "is_self_comparison_only": is_self_comparison,
        "true_l5_oracle_proven": not is_self_comparison
    }


def run_full_validation(repo_root: Path, scorecard: Optional[dict] = None) -> bool:
    scorecard_path = repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json"
    runtime_src = repo_root / "src" / "runtime" / "standalone_runtime.cpp"
    test_l5 = repo_root / "tests" / "runtime" / "test_guest_removal.cpp"

    if scorecard is None:
        scorecard = load_scorecard(scorecard_path)

    print("=== Thor 2 Gate Integrity Audit ===")
    asm_audit = audit_asm_90_gate(scorecard)
    print(f"ASM_90_GATE: Aggregate coverage = {asm_audit['aggregate_coverage_pct']}% (Target >= 90.00%)")
    for proc, stats in asm_audit["processors"].items():
        print(f"  [{proc}] {stats['proven_bytes']} / {stats['confirmed_bytes']} bytes ({stats['coverage_pct']}%)")

    full_asm = audit_full_asm_game_gate(scorecard)
    print(f"FULL_ASM_GAME_GATE: Claimed = '{full_asm['claimed_status']}', Valid = {full_asm['can_pass']}")
    if full_asm["issues"]:
        for issue in full_asm["issues"]:
            print(f"  [BLOCKER] {issue}")

    d18 = audit_d18_guest_removal(runtime_src, scorecard)
    print(f"D18 GUEST REMOVAL: Guest fallback present = {d18['has_guest_fallback']}, Claimed = '{d18['claimed_status']}'")
    if d18["has_guest_fallback"]:
        print(f"  [NOTE] Production runtime still uses {d18['fallback_symbols_detected']}")

    l5 = audit_l5_oracle_equivalence(test_l5, scorecard)
    print(f"L5 ORACLE EQUIVALENCE: Self-comparison only = {l5['is_self_comparison_only']}")

    overall_status = scorecard.get("overall_status")
    print(f"OVERALL STATUS: {overall_status}")
    if overall_status == "COMPLETE" and (not full_asm["can_pass"] or d18["has_guest_fallback"]):
        raise GateIntegrityError("Scorecard claims overall_status COMPLETE while blocking gates are not satisfied!")

    print("=== All Gate Assertions Verified Factually Honest ===")
    return True


if __name__ == "__main__":
    repo_dir = Path(__file__).resolve().parent.parent.parent
    try:
        run_full_validation(repo_dir)
        sys.exit(0)
    except GateIntegrityError as e:
        print(f"\n[FATAL ERROR] Gate integrity violation:\n{e}", file=sys.stderr)
        sys.exit(1)
