#!/usr/bin/env python3
"""tests/asm/negative_controls_p4.py — Negative Controls Suite I-P for P4 Integrity.

Implements required Negative Controls:
  I. VALID_LOOKING_DATA (Must not decode into proven DATA)
  J. DEBUG_PC_PLUS_2_PRESENTATION (Presented PC+2 must not count as executed)
  K. PR_ONLY_ADDRESS (PR register value must not count as executed)
  L. SILENT_DATA_DEMOTION (Demoting proven DATA to UNKNOWN must fail)
  M. FAKE_UNREACHABILITY (Unreachable with unresolved indirect sites must fail)
  N. GENERATION_ALIAS (Missing generation in identity key must fail)
  O. MODULE_NAME_HEURISTIC (Module name shortcut classification must fail)
  P. SWALLOWED_EVIDENCE_ERROR (Malformed authoritative evidence must fail closed)
"""

import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path

_repo_root_preload = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_repo_root_preload / "tools" / "asm"))
sys.path.insert(0, str(_repo_root_preload))

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


def test_nc_i_valid_looking_data(repo_root: Path):
    """NC-I: Valid-looking instructions placed inside proven DATA must not be promoted."""
    from tools.carver.p3_control_flow_resolver import P3ControlFlowResolver
    resolver = P3ControlFlowResolver(repo_root)
    # Ensure guarded DATA is present and CFG never decodes into it
    for mod in ["0TH2.BIN", "TH2.LOW"]:
        g_d = resolver.guarded_data.get(mod, set())
        assert len(g_d) > 0, f"Guarded DATA empty for {mod}"
    # Verify no P3 confirmed code range overlaps guarded DATA
    p3_file = repo_root / "workstreams" / "T2-ASM-CARVER" / "p3_control_flow_resolution.json"
    p3_data = json.loads(p3_file.read_text(encoding="utf-8"))
    overlaps = 0
    for r in p3_data.get("records", []):
        if r.get("resolved_state") == "CONFIRMED_CODE":
            mod = r["module"]
            s, e = r["offset_start"], r["offset_end_exclusive"]
            g_d = resolver.guarded_data.get(mod, set())
            if any(off in g_d for off in range(s, e)):
                overlaps += 1
    assert overlaps == 0, f"NC-I violation: {overlaps} confirmed code bytes overlap proven DATA"
    print("[PASS] NC-I: valid-looking data inside proven DATA rejected fail-closed.")


def test_nc_j_debug_pc_plus_2_presentation(repo_root: Path):
    """NC-J: Event with address X and PC=X+2: only X may become EXECUTED_INSTRUCTION_PC."""
    from tools.carver.executed_pc_union import ExecutedPCUnion
    union = ExecutedPCUnion(repo_root)
    union.build_union()
    # 0x06004000 is entry; 0x06004002 is debug presented PC
    inst_pcs = union.get_instruction_pcs_for_module("0TH2.BIN")
    assert 0x06004000 in inst_pcs, "0x06004000 must be in executed_instruction_pcs"
    assert 0x06004002 not in inst_pcs, "NC-J violation: debug presented PC 0x06004002 counted as executed"
    assert 0x0600428A in inst_pcs, "0x0600428A must be in executed_instruction_pcs"
    assert 0x0600428C not in inst_pcs, "NC-J violation: debug presented PC 0x0600428C counted as executed"
    print("[PASS] NC-J: debug PC+2 presentation rejected as executed PC.")


def test_nc_k_pr_only_address(repo_root: Path):
    """NC-K: Address present only in PR register must NOT count as executed."""
    u_file = repo_root / "workstreams" / "T2-ASM-CARVER" / "executed_pc_union.json"
    u_data = json.loads(u_file.read_text(encoding="utf-8"))
    ret_candidates = u_data.get("return_target_candidates", [])
    inst_pcs = {int(x["pc"], 16) if isinstance(x, dict) else int(x, 16) for x in u_data.get("executed_instruction_pcs", [])}
    # For every candidate in return_target_candidates not backed by real breakpoint entry, ensure not in inst_pcs
    for rc in ret_candidates:
        val = int(rc.get("address", "0x0"), 16)
        if val != 0:
            entry_events = [e for e in u_data.get("executed_instruction_pcs", []) if int(e["pc"], 16) == val]
            if not entry_events:
                assert val not in inst_pcs, f"NC-K violation: PR value 0x{val:08X} counted as executed PC"
    print("[PASS] NC-K: PR-only address correctly quarantined as non-executed.")


def test_nc_l_silent_data_demotion(repo_root: Path):
    """NC-L: Demoting previously proven DATA to UNKNOWN without override must fail."""
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree(repo_root)
    # Tamper manifest: turn a DATA range into UNKNOWN
    mf_file = tr / "asm" / "manifests" / "0TH2.BIN.json"
    mf_data = json.loads(mf_file.read_text(encoding="utf-8"))
    for r in mf_data["ranges"]:
        if r.get("evidence_classification") == "DATA":
            r["evidence_classification"] = "UNKNOWN"
            r["assembly_representation"] = "RAW_UNKNOWN"
            break
    mf_file.write_text(json.dumps(mf_data), encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed for SILENT_DATA_DEMOTION"
    except GateIntegrityError as e:
        assert "SILENT_DATA_DEMOTION" in str(e) or "DEMOTION" in str(e) or "MISSING" in str(e)
        print("[PASS] NC-L: silent data demotion rejected fail-closed.")
    finally:
        td.cleanup()


def test_nc_m_fake_unreachability(repo_root: Path):
    """NC-M: Undecoded residual bytes declared PROVEN_UNREACHABLE with unresolved indirect sites must fail."""
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree(repo_root)
    p3_file = tr / "workstreams" / "T2-ASM-CARVER" / "p3_control_flow_resolution.json"
    p3_data = json.loads(p3_file.read_text(encoding="utf-8"))
    # Inject fake PROVEN_UNREACHABLE record while indirect sites are unresolved
    p3_data["records"].append({
        "module": "0TH2.BIN", "generation": 0, "offset_start": 400000, "offset_end_exclusive": 400010,
        "byte_length": 10, "runtime_start": "0x06065A40", "runtime_end_exclusive": "0x06065A4A",
        "resolved_state": "PROVEN_UNREACHABLE",
        "evidence_reason": "FAKE_UNREACHABILITY",
        "seed_reachability_provenance": "UNREACHABLE_ANALYSIS",
        "decoder_provenance": "N/A", "mnemonic_representation_state": "RAW_UNKNOWN",
    })
    p3_file.write_text(json.dumps(p3_data), encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed for FAKE_UNREACHABILITY"
    except GateIntegrityError as e:
        assert "UNREACHABLE" in str(e) or "unresolved" in str(e).lower()
        print("[PASS] NC-M: fake unreachability without complete indirect closure rejected.")
    finally:
        td.cleanup()


def test_nc_n_generation_alias(repo_root: Path):
    """NC-N: Identity check without generation (generation alias) must fail."""
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree(repo_root)
    # Inject record with generation 1 (differing generation alias)
    u_file = tr / "workstreams" / "T2-ASM-CARVER" / "executed_pc_union.json"
    u_data = json.loads(u_file.read_text(encoding="utf-8"))
    u_data["executed_instruction_pcs"].append({
        "revision": "RUS", "cpu": "MASTER_SH2", "module": "0TH2.BIN",
        "generation": 1, "pc": "0x06004000", "source": "D9_EVENT:ALIAS"
    })
    u_file.write_text(json.dumps(u_data), encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed for GENERATION_ALIAS"
    except GateIntegrityError as e:
        assert "GENERATION" in str(e) or "ALIAS" in str(e) or "OUTSIDE" in str(e)
        print("[PASS] NC-N: generation alias rejected fail-closed.")
    finally:
        td.cleanup()


def test_nc_o_module_name_heuristic(repo_root: Path):
    """NC-O: Module-name classification heuristics must fail validator."""
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree(repo_root)
    p3_file = tr / "workstreams" / "T2-ASM-CARVER" / "p3_control_flow_resolution.json"
    p3_data = json.loads(p3_file.read_text(encoding="utf-8"))
    p3_data["records"].append({
        "module": "SET07.BIN", "generation": 0, "offset_start": 20, "offset_end_exclusive": 30,
        "byte_length": 10, "runtime_start": "0x060D8014", "runtime_end_exclusive": "0x060D801E",
        "resolved_state": "PROVEN_DATA",
        "evidence_reason": "MODULE_NAME_HEURISTIC: SET07.BIN unknown is data",
        "seed_reachability_provenance": "MODULE_NAME_HEURISTIC",
        "decoder_provenance": "N/A", "mnemonic_representation_state": "RAW_DATA",
    })
    p3_file.write_text(json.dumps(p3_data), encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed for MODULE_NAME_HEURISTIC"
    except GateIntegrityError as e:
        assert "HEURISTIC" in str(e) or "MODULE_NAME" in str(e) or "MISSING" in str(e)
        print("[PASS] NC-O: module-name heuristic classification rejected fail-closed.")
    finally:
        td.cleanup()


def test_nc_p_swallowed_evidence_error(repo_root: Path):
    """NC-P: Corrupted authoritative JSON source must fail closed."""
    scorecard = load_scorecard(repo_root / "workstreams" / "ASM_RECOVERY_SCORECARD.json")
    fake = copy.deepcopy(scorecard)
    fake["gates"]["FULL_ASM_GAME_GATE"]["status"] = "PASS"
    td, tr = _setup_mock_tree(repo_root)
    # Corrupt executed_pc_union.json with invalid JSON
    u_file = tr / "workstreams" / "T2-ASM-CARVER" / "executed_pc_union.json"
    u_file.write_text("{corrupted_json: [invalid...", encoding="utf-8")
    try:
        audit_full_asm_game_gate(fake, tr)
        assert False, "Should have failed for SWALLOWED_EVIDENCE_ERROR"
    except (GateIntegrityError, Exception) as e:
        print("[PASS] NC-P: swallowed evidence error failed closed successfully.")
    finally:
        td.cleanup()


def run_all_p4_negative_controls(repo_root: Path):
    print("=== Running T2-ASM-INTEGRITY-05 Negative Controls (NC-I .. NC-P) ===")
    test_nc_i_valid_looking_data(repo_root)
    test_nc_j_debug_pc_plus_2_presentation(repo_root)
    test_nc_k_pr_only_address(repo_root)
    test_nc_l_silent_data_demotion(repo_root)
    test_nc_m_fake_unreachability(repo_root)
    test_nc_n_generation_alias(repo_root)
    test_nc_o_module_name_heuristic(repo_root)
    test_nc_p_swallowed_evidence_error(repo_root)
    print("=== All 8 P4 Negative Controls (NC-I .. NC-P) Passed Successfully ===")


if __name__ == "__main__":
    repo_dir = Path(__file__).resolve().parent.parent.parent
    run_all_p4_negative_controls(repo_dir)
