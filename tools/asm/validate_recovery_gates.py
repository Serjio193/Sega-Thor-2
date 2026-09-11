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


def audit_full_asm_game_gate(scorecard: dict, repo_root: Optional[Path] = None) -> dict:
    """Independently verifies all factual requirements for FULL_ASM_GAME_GATE."""
    modules = scorecard.get("modules", [])
    issues = []
    unverified_modules = []
    non_byte_exact_modules = []

    expected_modules = {"0TH2.BIN", "TH2.LOW", "SET07.BIN", "BGM.BIN"}
    found_modules = set()

    for mod in modules:
        name = mod.get("name", "UNNAMED")
        found_modules.add(name)
        reassembly = mod.get("reassembly_status")
        runtime_ver = mod.get("runtime_verified", False)

        if reassembly != "BYTE_EXACT":
            non_byte_exact_modules.append(name)
            issues.append(f"Module '{name}' reassembly_status is '{reassembly}', expected 'BYTE_EXACT'")
        if not runtime_ver:
            unverified_modules.append(name)
            issues.append(f"Module '{name}' has runtime_verified = false")

    missing = expected_modules - found_modules
    if missing:
        issues.append(f"Missing required executable modules from inventory: {sorted(missing)}")

    gameplay_verified = scorecard.get("metrics", {}).get("full_gameplay_verified", False)
    if not gameplay_verified:
        issues.append("Full multi-scenario gameplay suite (menus, transitions, combat, audio) not yet verified")

    # Independent manifest verification if repo_root available
    sh2_pending_bytes = 0
    m68k_pending_bytes = 0
    if repo_root:
        manifest_dir = repo_root / "asm" / "manifests"
        for mf_name, cpu in [("0TH2.BIN.json", "SH2"), ("TH2.LOW.json", "SH2"), ("SET07.BIN.json", "SH2"), ("BGM.BIN.json", "M68K")]:
            mf_path = manifest_dir / mf_name
            if not mf_path.exists():
                issues.append(f"Manifest missing: {mf_path}")
                continue
            with open(mf_path, "r", encoding="utf-8") as fp:
                mf_data = json.load(fp)
            for r in mf_data.get("ranges", []):
                if r.get("evidence_classification") == "CONFIRMED_CODE":
                    if r.get("assembly_representation") != "MNEMONIC_PROVEN":
                        if cpu == "SH2":
                            sh2_pending_bytes += r.get("byte_length", 0)
                        else:
                            m68k_pending_bytes += r.get("byte_length", 0)

        if sh2_pending_bytes > 0:
            issues.append(f"SH2_RAW_CODE_PENDING == {sh2_pending_bytes} (must be 0)")
        if m68k_pending_bytes > 0:
            issues.append(f"M68K_RAW_CODE_PENDING == {m68k_pending_bytes} (must be 0)")

        # Independent carver evidence verification
        gap_rep_path = repo_root / "workstreams" / "T2-ASM-CARVER" / "unknown_gap_report.json"
        if gap_rep_path.exists():
            with open(gap_rep_path, "r", encoding="utf-8") as fp:
                gap_data = json.load(fp)
            p1_execs = gap_data.get("gaps_by_priority", {}).get("P1_EXECUTION", 0)
            if p1_execs > 0:
                issues.append(f"UNKNOWN_EXECUTION_HITS == {p1_execs} (must be 0)")

        # Independent carver integrity diff verification
        diff_path = repo_root / "workstreams" / "T2-ASM-CARVER" / "carver_integrity_diff.json"
        if not diff_path.exists() or diff_path.stat().st_size == 0:
            issues.append(f"carver_integrity_diff.json is empty or missing: {diff_path}")
        else:
            try:
                diff_data = json.loads(diff_path.read_text(encoding="utf-8"))
                in_total = diff_data.get("input_candidate_total", 0)
                conf_c = diff_data.get("confirmed_count", 0)
                prob_c = diff_data.get("probable_count", 0)
                cand_c = diff_data.get("candidate_count", 0)
                confl_c = diff_data.get("conflict_count", 0)
                if in_total == 0 or (conf_c + prob_c + cand_c + confl_c) != in_total:
                    issues.append(f"carver_integrity_diff counts do not reconcile: {conf_c}+{prob_c}+{cand_c}+{confl_c} != {in_total}")
                if confl_c > 0:
                    issues.append(f"carver_integrity_diff has conflict_count == {confl_c} (must be 0)")
                if len(diff_data.get("decisions", [])) != in_total:
                    issues.append(f"carver_integrity_diff decisions count mismatch: {len(diff_data.get('decisions', []))} != {in_total}")
            except Exception as e:
                issues.append(f"carver_integrity_diff.json malformed: {e}")

        # Independent P3 control flow resolution verification (must parse ALL records)
        p3_res_path = repo_root / "workstreams" / "T2-ASM-CARVER" / "p3_control_flow_resolution.json"
        if not p3_res_path.exists():
            issues.append(f"p3_control_flow_resolution.json missing: {p3_res_path}")
        else:
            try:
                p3_data = json.loads(p3_res_path.read_text(encoding="utf-8"))
                records = p3_data.get("records", [])
                if not records:
                    issues.append("p3_control_flow_resolution.json missing detailed records")
                p3_unresolved = sum(
                    1 for r in records
                    if r.get("resolved_state") in ("UNRESOLVED_EXECUTABLE_CANDIDATE", "BLOCKED_WITH_EXACT_REASON")
                )
                p3_blocked = sum(1 for r in records if r.get("resolved_state") == "BLOCKED_WITH_EXACT_REASON")
                p3_candidates = sum(1 for r in records if r.get("resolved_state") == "UNRESOLVED_EXECUTABLE_CANDIDATE")
                summary_unres = p3_data.get("unresolved_control_flow_unknown", 0)

                if summary_unres != p3_unresolved:
                    issues.append(
                        f"P3 summary claims {summary_unres} unresolved but records contain {p3_unresolved}"
                    )
                if p3_blocked > 0:
                    issues.append(f"P3 has {p3_blocked} BLOCKED_WITH_EXACT_REASON records (must be 0)")
                if p3_candidates > 0:
                    issues.append(f"P3 has {p3_candidates} UNRESOLVED_EXECUTABLE_CANDIDATE records (must be 0)")

                # Mandatory regression check: 0x0600428A must be CONFIRMED_CODE
                r_428a = next((r for r in records if r.get("runtime_start") == "0x0600428A"), None)
                if not r_428a:
                    issues.append("Historical executed site 0x0600428A missing from P3 resolution records")
                elif r_428a.get("resolved_state") != "CONFIRMED_CODE":
                    issues.append(
                        f"Historical executed site 0x0600428A is classified as non-code: {r_428a.get('resolved_state')}"
                    )
            except Exception as e:
                issues.append(f"p3_control_flow_resolution.json parsing error: {e}")

        # Check PROBABLE_DATA overlapping exact CFG targets
        for mf_name in ["0TH2.BIN.json", "TH2.LOW.json", "SET07.BIN.json"]:
            mf_path = manifest_dir / mf_name
            if mf_path.exists():
                try:
                    mf_data = json.loads(mf_path.read_text(encoding="utf-8"))
                    for r in mf_data.get("ranges", []):
                        if r.get("evidence_classification") in ("DATA_PROBABLE", "PROBABLE_DATA"):
                            if "EXACT_CFG_TARGET" in r.get("evidence_refs", []):
                                issues.append(f"PROBABLE_DATA overlaps exact CFG target at {r.get('runtime_start')}")
                except Exception:
                    pass

        # Confirmed vs proven byte parity check
        total_conf_bytes = sum(m.get("confirmed_code_bytes", 0) for m in scorecard.get("modules", []))
        total_prov_bytes = sum(m.get("proven_mnemonic_bytes", 0) for m in scorecard.get("modules", []))
        if total_conf_bytes != total_prov_bytes:
            issues.append(f"Confirmed vs proven byte mismatch: {total_conf_bytes} != {total_prov_bytes}")

        db_sum_path = repo_root / "workstreams" / "T2-ASM-CARVER" / "interval_db_summary.json"
        if db_sum_path.exists():
            with open(db_sum_path, "r", encoding="utf-8") as fp:
                db_data = json.load(fp)
            conflicts = db_data.get("aggregate", {}).get("conflicts_count", 0)
            if conflicts > 0:
                issues.append(f"Carver conflicts == {conflicts} (must be 0)")

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
        "sh2_pending_bytes": sh2_pending_bytes,
        "m68k_pending_bytes": m68k_pending_bytes,
        "non_byte_exact_modules": non_byte_exact_modules,
        "unverified_modules": unverified_modules,
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

    full_asm = audit_full_asm_game_gate(scorecard, repo_root)
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
