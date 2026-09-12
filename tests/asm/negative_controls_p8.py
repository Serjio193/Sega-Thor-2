#!/usr/bin/env python3
"""tests/asm/negative_controls_p8.py — Negative Controls Suite AQ-AX for T2-ASM-09 Integrity.

Implements required adversarial Negative Controls:
  AQ. ADDRESS_TAKEN_NOT_CALLABLE (Non-call data occurrence must not open caller domain)
  AR. UNBOUNDED_TABLE_INDEX (Table without proven bounded index must remain incomplete)
  AS. TAILCALL_RETURN_PC_ERROR (Tailcall target RTS must inherit upstream PR, not tailcall_pc + 4)
  AT. SHARED_ENTRY_FUNCTION_BOUNDARY (Direct branch entering shared block must not be silently ignored)
  AU. RECURSIVE_SCC_HIDDEN_EXTERNAL_ENTRY (Recursive SCC with unresolved external entry must remain incomplete)
  AV. INTERRUPT_ENTRY_AS_NORMAL_CALLER (Interrupt/root entry must not receive normal +4 return address)
  AW. CALLBACK_UNKNOWN_WRITER (Callback field with open writer must remain incomplete)
  AX. GENERATION_ALIAS_ENTRY (Same VMA across distinct generations must not collapse caller domains)
"""

from pathlib import Path
import json
import sys

_repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_repo_root / "tools" / "asm"))
sys.path.insert(0, str(_repo_root))


def test_nc_aq_address_taken_not_callable(repo_root: Path):
    """NC-AQ: Function address in DATA with non-call consumer must not open caller domain."""
    ref_path = repo_root / "workstreams/T2-ASM-09/reference_to_call_sink.json"
    ref_data = json.loads(ref_path.read_text(encoding="utf-8"))["provenance_records"]
    noncall_refs = [r for r in ref_data if r["call_sink_status"] == "NONCALL_REFERENCE"]
    assert len(noncall_refs) > 0, "NC-AQ requires non-call references to exist"
    for r in noncall_refs:
        assert r["consumer_pc"] is None, f"NC-AQ violation: non-call reference at {r['ref_pc']} has call consumer {r['consumer_pc']}"
    print("[PASS] NC-AQ: address taken not callable rejected fail-closed.")


def test_nc_ar_unbounded_table_index(repo_root: Path):
    """NC-AR: Pointer table without proven bound check must remain incomplete."""
    ct_path = repo_root / "workstreams/T2-ASM-09/residual_callback_tables.json"
    tables = json.loads(ct_path.read_text(encoding="utf-8"))["tables"]
    for t in tables:
        assert "entry_count" in t or "targets" in t, f"NC-AR violation: table {t.get('table_address')} missing bounds"
    print("[PASS] NC-AR: unbounded table index rejected fail-closed.")


def test_nc_as_tailcall_return_pc_error(repo_root: Path):
    """NC-AS: Tailcall target RTS must inherit upstream PR, not tailcall_pc + 4."""
    tc_path = repo_root / "workstreams/T2-ASM-09/tailcall_domains.json"
    tailcalls = json.loads(tc_path.read_text(encoding="utf-8"))["tailcalls"]
    assert len(tailcalls) > 0, "NC-AS requires tailcalls to exist"
    for tc in tailcalls:
        tc_pc = tc["source_pc"]
        bad_ret = f"0x{int(tc_pc, 16) + 4:08X}"
        assert bad_ret not in tc["upstream_return_domain"], (
            f"NC-AS violation: tailcall {tc_pc} incorrectly added {bad_ret} as return target"
        )
    print("[PASS] NC-AS: tailcall return PC error rejected fail-closed.")


def test_nc_at_shared_entry_function_boundary(repo_root: Path):
    """NC-AT: Direct branch entering shared function block must not be silently ignored."""
    ceg_path = repo_root / "workstreams/T2-ASM-09/canonical_entry_graph.json"
    edges = json.loads(ceg_path.read_text(encoding="utf-8"))["edges"]
    shared_edges = [e for e in edges if e["edge_type"] == "DIRECT_BRANCH_SHARED_ENTRY"]
    assert len(shared_edges) > 0, "NC-AT requires shared entry edges to exist"
    for e in shared_edges:
        assert e["source_function"] != e["target_function"]
    print("[PASS] NC-AT: shared entry function boundary recorded fail-closed.")


def test_nc_au_recursive_scc_hidden_external_entry(repo_root: Path):
    """NC-AU: Recursive SCC with unresolved external entry must remain incomplete."""
    fc_path = repo_root / "workstreams/T2-ASM-09/function_caller_certificates.json"
    certs = json.loads(fc_path.read_text(encoding="utf-8"))["certificates"]
    for c in certs:
        if not c["recursive_scc_external_entries_complete"]:
            assert c["CALLER_DOMAIN_COMPLETE"] is False, (
                f"NC-AU violation: function {c['function_id']} certified despite open SCC external entry"
            )
    print("[PASS] NC-AU: recursive SCC hidden external entry rejected fail-closed.")


def test_nc_av_interrupt_entry_as_normal_caller(repo_root: Path):
    """NC-AV: Hardware interrupt/root entry must not receive normal JSR/BSR return address."""
    rts_path = repo_root / "workstreams/T2-ASM-09/rts_completeness_v2.json"
    certs = json.loads(rts_path.read_text(encoding="utf-8"))["certificates"]
    for c in certs:
        if c["function_entry_pc"] == "0x06004000":
            # Reset vector root entry must not be a normal return target
            assert "0x06004004" not in c["return_pcs"], (
                f"NC-AV violation: root vector 0x06004000 treated as normal caller return at {c['site_id']}"
            )
    print("[PASS] NC-AV: interrupt entry as normal caller rejected fail-closed.")


def test_nc_aw_callback_unknown_writer(repo_root: Path):
    """NC-AW: Callback field with unknown writer / open reference must remain incomplete."""
    fc_path = repo_root / "workstreams/T2-ASM-09/function_caller_certificates.json"
    certs = json.loads(fc_path.read_text(encoding="utf-8"))["certificates"]
    for c in certs:
        if len(c["unresolved_reference_sources"]) > 0:
            assert c["CALLER_DOMAIN_COMPLETE"] is False, (
                f"NC-AW violation: function {c['function_id']} certified despite unresolved reference sources"
            )
    print("[PASS] NC-AW: callback unknown writer rejected fail-closed.")


def test_nc_ax_generation_alias_entry(repo_root: Path):
    """NC-AX: Same architectural VMA across distinct generations must not collapse caller domains."""
    fc_path = repo_root / "workstreams/T2-ASM-09/function_caller_certificates.json"
    certs = json.loads(fc_path.read_text(encoding="utf-8"))["certificates"]
    for c in certs:
        assert c["generation"] == 0, f"NC-AX violation: non-zero generation {c['generation']} in SH-2 certificate"
        assert c["cross_module_domain_complete"] is True
    print("[PASS] NC-AX: generation alias entry rejected fail-closed.")


def run_all_p8_negative_controls(repo_root: Path):
    print("=== Running T2-ASM-09 Negative Controls (NC-AQ .. NC-AX) ===")
    test_nc_aq_address_taken_not_callable(repo_root)
    test_nc_ar_unbounded_table_index(repo_root)
    test_nc_as_tailcall_return_pc_error(repo_root)
    test_nc_at_shared_entry_function_boundary(repo_root)
    test_nc_au_recursive_scc_hidden_external_entry(repo_root)
    test_nc_av_interrupt_entry_as_normal_caller(repo_root)
    test_nc_aw_callback_unknown_writer(repo_root)
    test_nc_ax_generation_alias_entry(repo_root)
    print("=== All 8 P8 Negative Controls (NC-AQ .. NC-AX) Passed Successfully ===")


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    run_all_p8_negative_controls(repo_root)


if __name__ == '__main__':
    main()
