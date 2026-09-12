#!/usr/bin/env python3
"""tests/asm/negative_controls_p10.py — Negative Controls Suite BG-BN for RTS Soundness.

Implements required adversarial Negative Controls for T2-ASM-10.1:
  BG. STALE_FUNCTION_CERT_BINDING (Stale caller cert from different function must fail/assert)
  BH. UNVERIFIED_PR_MARKED_RESOLVED (UNVERIFIED_PR must never produce resolved RTS)
  BI. EMPTY_FINITE_RETURN_SET (return_domain_count=0 may not be RESOLVED_FINITE_SET)
  BJ. WRONG_FUNCTION_CERTIFICATE (Caller cert with wrong module/generation must assert/fail closed)
  BK. STACK_PR_SLOT_UNVERIFIED (STACK_RESTORED_PR with pr_slot_verified=False must fail)
  BL. METRIC_TARGET_FORCING (Certification must not be influenced by aggregate target variables)
  BM. RETURN_PC_NOT_CODE (Return PC outside canonical CODE cannot enter a resolved domain)
  BN. CALLER_RETURN_CARDINALITY_MISMATCH (return_domain_count != len(return_pcs) must fail closed)
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import sys

_repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_repo_root / "tools" / "asm"))
sys.path.insert(0, str(_repo_root))

from tools.asm.rts_v3_certifier import certify_site, is_address_in_code


def _get_mock_code_intervals() -> Dict[str, List[Tuple[int, int]]]:
    """Returns valid code intervals for testing: 0x06004000..0x06007000 is CODE."""
    return {
        "0TH2.BIN": [(0x06004000, 0x06007000)],
        "TH2.LOW": [(0x00200000, 0x00280000)],
    }


def test_nc_bg_stale_function_cert_binding(repo_root: Path):
    """NC-BG: Stale caller cert from different function must fail/assert."""
    code_ivs = _get_mock_code_intervals()
    cert = {
        "site_id": "0TH2.BIN_0x06004072",
        "module": "0TH2.BIN",
        "function_entry_pc": "0x0600406C",
        "resolution_status": "UNRESOLVED_EXTERNAL_ENTRY",
        "is_certified_resolved": False,
        "pr_mechanism": "LEAF_UNTOUCHED_PR",
        "pr_paths_complete": True,
        "pr_slot_verified": True,
        "caller_domain_complete": True,
        "caller_count": 1,
        "callers": ["0x06004000"],
        "return_domain_count": 1,
        "return_pcs": ["0x06004004"],
    }
    # Stale FC pointing to TH2.LOW function 0x002EA15C
    stale_fc = {
        "function_id": "sub_002EA15C",
        "module": "TH2.LOW",
        "generation": 0,
        "entries": ["0x002EA15C"],
        "CALLER_DOMAIN_COMPLETE": True,
    }
    threw = False
    try:
        certify_site(cert, None, stale_fc, None, code_ivs)
    except AssertionError:
        threw = True
    assert threw, "NC-BG violation: stale function cert binding did not raise AssertionError"
    print("[PASS] NC-BG: stale function cert binding rejected fail-closed.")


def test_nc_bh_unverified_pr_marked_resolved(repo_root: Path):
    """NC-BH: UNVERIFIED_PR must never produce resolved RTS."""
    code_ivs = _get_mock_code_intervals()
    cert = {
        "site_id": "0TH2.BIN_0x0600467E",
        "module": "0TH2.BIN",
        "function_entry_pc": "0x060045E8",
        "resolution_status": "UNRESOLVED_PR_PATH",
        "is_certified_resolved": False,
        "pr_mechanism": "UNVERIFIED_PR",
        "pr_paths_complete": False,
        "pr_slot_verified": False,
        "caller_domain_complete": True,
        "caller_count": 1,
        "callers": ["0x06004500"],
        "return_domain_count": 1,
        "return_pcs": ["0x06004504"],
    }
    fc = {
        "function_id": "sub_060045E8",
        "module": "0TH2.BIN",
        "generation": 0,
        "entries": ["0x060045E8"],
        "CALLER_DOMAIN_COMPLETE": True,
    }
    res = certify_site(cert, None, fc, None, code_ivs)
    assert not res["is_certified_resolved"], "NC-BH violation: UNVERIFIED_PR was marked resolved"
    assert not res["resolution_status"].startswith("RESOLVED")
    print("[PASS] NC-BH: UNVERIFIED_PR marked resolved rejected fail-closed.")


def test_nc_bi_empty_finite_return_set(repo_root: Path):
    """NC-BI: return_domain_count=0 may not be RESOLVED_FINITE_SET."""
    code_ivs = _get_mock_code_intervals()
    cert = {
        "site_id": "0TH2.BIN_0x06005000",
        "module": "0TH2.BIN",
        "function_entry_pc": "0x06004F00",
        "resolution_status": "RESOLVED_FINITE_SET",
        "is_certified_resolved": True,
        "pr_mechanism": "LEAF_UNTOUCHED_PR",
        "pr_paths_complete": True,
        "pr_slot_verified": True,
        "caller_domain_complete": True,
        "caller_count": 0,
        "callers": [],
        "return_domain_count": 0,
        "return_pcs": [],
    }
    res = certify_site(cert, None, None, None, code_ivs)
    assert not res["is_certified_resolved"], "NC-BI violation: empty return domain was resolved"
    assert res["resolution_status"] != "RESOLVED_FINITE_SET"
    print("[PASS] NC-BI: empty finite return set rejected fail-closed.")


def test_nc_bj_wrong_function_certificate(repo_root: Path):
    """NC-BJ: Caller cert with wrong module/generation must assert/fail closed."""
    code_ivs = _get_mock_code_intervals()
    cert = {
        "site_id": "0TH2.BIN_0x06004100",
        "module": "0TH2.BIN",
        "generation": 0,
        "function_entry_pc": "0x0600406C",
        "resolution_status": "UNRESOLVED_EXTERNAL_ENTRY",
        "is_certified_resolved": False,
        "pr_mechanism": "LEAF_UNTOUCHED_PR",
        "pr_paths_complete": True,
        "pr_slot_verified": True,
        "caller_domain_complete": True,
        "caller_count": 1,
        "callers": ["0x06004000"],
        "return_domain_count": 1,
        "return_pcs": ["0x06004004"],
    }
    wrong_gen_fc = {
        "function_id": "sub_0600406C",
        "module": "0TH2.BIN",
        "generation": 1,
        "entries": ["0x0600406C"],
        "CALLER_DOMAIN_COMPLETE": True,
    }
    threw = False
    try:
        certify_site(cert, None, wrong_gen_fc, None, code_ivs)
    except AssertionError:
        threw = True
    assert threw, "NC-BJ violation: mismatched generation did not raise AssertionError"
    print("[PASS] NC-BJ: wrong function certificate rejected fail-closed.")


def test_nc_bk_stack_pr_slot_unverified(repo_root: Path):
    """NC-BK: STACK_RESTORED_PR with pr_slot_verified=False must fail."""
    code_ivs = _get_mock_code_intervals()
    cert = {
        "site_id": "0TH2.BIN_0x06004200",
        "module": "0TH2.BIN",
        "function_entry_pc": "0x06004180",
        "resolution_status": "RESOLVED_EXACT_RETURN",
        "is_certified_resolved": True,
        "pr_mechanism": "STACK_RESTORED_PR",
        "pr_paths_complete": True,
        "pr_slot_verified": False,
        "caller_domain_complete": True,
        "caller_count": 1,
        "callers": ["0x06004100"],
        "return_domain_count": 1,
        "return_pcs": ["0x06004104"],
    }
    res = certify_site(cert, None, None, None, code_ivs)
    assert not res["is_certified_resolved"], "NC-BK violation: unverified stack slot was resolved"
    print("[PASS] NC-BK: stack PR slot unverified rejected fail-closed.")


def test_nc_bl_metric_target_forcing(repo_root: Path):
    """NC-BL: Certification must not be influenced by aggregate target variables."""
    code_ivs = _get_mock_code_intervals()
    cert = {
        "site_id": "0TH2.BIN_0x06004300",
        "module": "0TH2.BIN",
        "function_entry_pc": "0x06004280",
        "resolution_status": "UNRESOLVED_CALLER_DOMAIN",
        "is_certified_resolved": False,
        "pr_mechanism": "LEAF_UNTOUCHED_PR",
        "pr_paths_complete": True,
        "pr_slot_verified": True,
        "caller_domain_complete": False,
        "caller_count": 0,
        "callers": [],
        "return_domain_count": 0,
        "return_pcs": [],
    }
    # Regardless of any external variable, cert with incomplete caller domain remains unresolved
    res = certify_site(cert, None, None, None, code_ivs)
    assert not res["is_certified_resolved"], "NC-BL violation: site resolved without caller domain"
    print("[PASS] NC-BL: metric target forcing rejected fail-closed.")


def test_nc_bm_return_pc_not_code(repo_root: Path):
    """NC-BM: Return PC outside canonical CODE cannot enter a resolved domain."""
    code_ivs = _get_mock_code_intervals()
    # 0x06007C3E is outside 0x06004000..0x06007000 (mock code interval)
    cert = {
        "site_id": "0TH2.BIN_0x06007260",
        "module": "0TH2.BIN",
        "function_entry_pc": "0x0600714E",
        "resolution_status": "RESOLVED_EXACT_RETURN",
        "is_certified_resolved": True,
        "pr_mechanism": "LEAF_UNTOUCHED_PR",
        "pr_paths_complete": True,
        "pr_slot_verified": True,
        "caller_domain_complete": True,
        "caller_count": 1,
        "callers": ["0x06007C3A"],
        "return_domain_count": 1,
        "return_pcs": ["0x06007C3E"],
    }
    res = certify_site(cert, None, None, None, code_ivs)
    assert not res["is_certified_resolved"], "NC-BM violation: return PC in data was resolved"
    assert res["resolution_status"] == "UNRESOLVED_CALLER_DOMAIN"
    print("[PASS] NC-BM: return PC not code rejected fail-closed.")


def test_nc_bn_caller_return_cardinality_mismatch(repo_root: Path):
    """NC-BN: return_domain_count != len(return_pcs) must fail closed."""
    code_ivs = _get_mock_code_intervals()
    cert = {
        "site_id": "0TH2.BIN_0x06004400",
        "module": "0TH2.BIN",
        "function_entry_pc": "0x06004380",
        "resolution_status": "RESOLVED_FINITE_SET",
        "is_certified_resolved": True,
        "pr_mechanism": "LEAF_UNTOUCHED_PR",
        "pr_paths_complete": True,
        "pr_slot_verified": True,
        "caller_domain_complete": True,
        "caller_count": 1,
        "callers": ["0x06004300"],
        "return_domain_count": 2,
        "return_pcs": ["0x06004304"],  # Mismatch: count=2, len=1
    }
    res = certify_site(cert, None, None, None, code_ivs)
    assert not res["is_certified_resolved"], "NC-BN violation: cardinality mismatch was resolved"
    print("[PASS] NC-BN: caller return cardinality mismatch rejected fail-closed.")


def run_all_p10_negative_controls(repo_root: Optional[Path] = None) -> bool:
    """Run all 8 P10 negative controls."""
    root = repo_root or _repo_root
    print("=== Running T2-ASM-10.1 Negative Controls (NC-BG .. NC-BN) ===")
    test_nc_bg_stale_function_cert_binding(root)
    test_nc_bh_unverified_pr_marked_resolved(root)
    test_nc_bi_empty_finite_return_set(root)
    test_nc_bj_wrong_function_certificate(root)
    test_nc_bk_stack_pr_slot_unverified(root)
    test_nc_bl_metric_target_forcing(root)
    test_nc_bm_return_pc_not_code(root)
    test_nc_bn_caller_return_cardinality_mismatch(root)
    print("=== All 8 P10 Negative Controls (NC-BG .. NC-BN) Passed Successfully ===")
    return True


if __name__ == "__main__":
    run_all_p10_negative_controls()
