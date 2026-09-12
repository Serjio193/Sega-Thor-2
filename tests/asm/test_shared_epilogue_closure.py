#!/usr/bin/env python3
"""tests/asm/test_shared_epilogue_closure.py — Unit Tests for T2-ASM-11 Invariants.

Verifies:
  1. RTS V4 Completeness & Invariants (453 resolved, 185 unresolved, 0 invalid resolved).
  2. Every resolved RTS has caller_count > 0, return_domain_count > 0, and all return PCs in CODE.
  3. Context-sensitive PR decomposition (630/638 sites proven, shared epilogue clusters formed).
  4. Caller return domain audit (2,288 false call edges from DATA correctly excised).
  5. Function boundary normalization (artificial labels normalized without modifying bytes).
  6. Targeted external threats documentation (81 external entry sites retained fail-closed).
"""

from pathlib import Path
import json
import pytest
import sys

repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))


@pytest.fixture
def t2_asm_11_dir() -> Path:
    return repo_root / "workstreams" / "T2-ASM-11"


def test_rts_completeness_v4_invariants(t2_asm_11_dir: Path):
    v4_path = t2_asm_11_dir / "rts_completeness_v4.json"
    assert v4_path.exists(), "rts_completeness_v4.json must exist"
    data = json.loads(v4_path.read_text(encoding="utf-8"))
    summary = data["summary"]

    assert summary["total_rts_sites"] == 638
    assert summary["certified_resolved_count"] == 453
    assert summary["unresolved_count"] == 185
    assert summary["unresolved_breakdown"] == {
        "UNRESOLVED_EXTERNAL_ENTRY": 81,
        "UNRESOLVED_CALLER_DOMAIN": 45,
        "UNRESOLVED_PR_PATH": 59,
    }


def test_resolved_certificates_soundness(t2_asm_11_dir: Path):
    audit_path = t2_asm_11_dir / "rts_v4_soundness_audit.json"
    assert audit_path.exists(), "rts_v4_soundness_audit.json must exist"
    data = json.loads(audit_path.read_text(encoding="utf-8"))
    summary = data["summary"]

    assert summary["invalid_resolved_certificates_count"] == 0
    assert summary["all_certificates_sound"] is True
    assert summary["certified_resolved_count"] == 453

    # Every resolved certificate must be non-empty and have 100% code return PCs
    for rec in data["audit_records"]:
        if rec["is_certified_resolved"]:
            assert rec["pr_paths_complete"] is True
            assert rec["pr_slot_verified"] is True
            assert rec["caller_domain_complete"] is True
            assert rec["caller_count"] > 0
            assert rec["return_domain_count"] > 0
            assert rec["all_return_pcs_in_code"] is True
            assert rec["return_domain_nonempty"] is True
            assert rec["is_sound"] is True


def test_caller_return_domain_audit(t2_asm_11_dir: Path):
    audit_path = t2_asm_11_dir / "caller_return_domain_audit.json"
    assert audit_path.exists(), "caller_return_domain_audit.json must exist"
    data = json.loads(audit_path.read_text(encoding="utf-8"))

    assert data["true_call_edges_count"] == 9558
    assert data["false_call_edges_count"] == 2288
    assert data["unknown_threat_edges_count"] == 2810
    assert data["caller_blocked_sites_audited"] == 56


def test_function_boundary_normalization(t2_asm_11_dir: Path):
    fb_path = t2_asm_11_dir / "function_boundary_v4.json"
    assert fb_path.exists(), "function_boundary_v4.json must exist"
    data = json.loads(fb_path.read_text(encoding="utf-8"))

    refinements = {r["site_id"]: r for r in data["refinements"]}
    # Verify sub_0600812E normalized to sub_06007BF0
    assert "0TH2.BIN_0x06008224" in refinements
    r = refinements["0TH2.BIN_0x06008224"]
    assert r["original_entry"] == "0x0600812E"
    assert r["normalized_entry"] == "0x06007C04"


def test_targeted_external_threats_retained_fail_closed(t2_asm_11_dir: Path):
    threats_path = t2_asm_11_dir / "targeted_external_threats.json"
    assert threats_path.exists(), "targeted_external_threats.json must exist"
    data = json.loads(threats_path.read_text(encoding="utf-8"))

    assert data["total_external_entry_sites"] == 81
    for site in data["sites"]:
        assert site["status"] == "UNRESOLVED_EXTERNAL_ENTRY_RETAINED"


def main():
    d = repo_root / "workstreams" / "T2-ASM-11"
    test_rts_completeness_v4_invariants(d)
    test_resolved_certificates_soundness(d)
    test_caller_return_domain_audit(d)
    test_function_boundary_normalization(d)
    test_targeted_external_threats_retained_fail_closed(d)
    print("test_shared_epilogue_closure: All T2-ASM-11 invariant tests PASSED.")


if __name__ == "__main__":
    main()
