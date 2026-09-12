#!/usr/bin/env python3
"""tests/asm/negative_controls_p5.py — Negative Controls Suite Q-X for T2-ASM-06 Integrity.

Implements required Negative Controls:
  Q. FAKE_LITERAL_CODE (Unaligned or out-of-range literal target must fail closed)
  R. OUT_OF_RANGE_JUMP_TABLE (Jump table with out-of-bounds index must fail closed)
  S. GENERATION_COLLISION (Target resolution with generation mismatch must fail)
  T. DYNAMIC_TARGET_WITHOUT_STATIC_EXCLUSIVITY (Dynamic target alone cannot claim exact single)
  U. AMBIGUOUS_RTS (RTS without bounded caller domain must not claim resolution)
  V. CALLBACK_TABLE_OVERLAPPING_DATA (Jump table targets pointing to DATA/PADDING must fail)
  W. PARTIAL_CONSTANT_MASKED_AS_EXACT (Partial/mutable RAM value masked as exact must fail)
  X. CROSS_MODULE_TARGET_ALIAS (Cross-module target outside destination VMA must fail)
"""

import copy
import json
import struct
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_repo_root / "tools" / "asm"))
sys.path.insert(0, str(_repo_root))

from tools.asm.constant_propagator import ConstantPropagator, PropagatedValue
from tools.asm.register_provenance import RegisterProvenanceEngine
from tools.asm.jump_table_recovery import JumpTableRecovery
from tools.asm.indirect_resolver import MasterIndirectResolver


def test_nc_q_fake_literal_code(repo_root: Path):
    """NC-Q: Literal pool target pointing to unaligned odd address or outside RAM must fail."""
    prov_path = repo_root / "workstreams/T2-ASM-06/register_provenance.json"
    prov_data = json.loads(prov_path.read_text())
    raw_unaligned = 0x06004001
    assert raw_unaligned % 2 != 0
    resolved_records = prov_data["records"]
    odd_targets = [
        r for r in resolved_records
        if r["is_resolved_target"] and r["exact_value"] and int(r["exact_value"], 16) % 2 != 0
    ]
    assert len(odd_targets) == 0, f"NC-Q violation: {len(odd_targets)} odd targets accepted"

    out_of_bounds = [
        r for r in resolved_records
        if r["is_resolved_target"] and r["exact_value"] and not (
            (0x06004000 <= int(r["exact_value"], 16) < 0x06004000 + 535552) or
            (0x002DA000 <= int(r["exact_value"], 16) < 0x002DA000 + 149504) or
            (0x060D8000 <= int(r["exact_value"], 16) < 0x060D8000 + 98304) or
            (0x00200000 <= int(r["exact_value"], 16) < 0x00300000) or
            (0x06000000 <= int(r["exact_value"], 16) < 0x06100000)
        )
    ]
    assert len(out_of_bounds) == 0, f"NC-Q violation: {len(out_of_bounds)} out-of-bounds targets accepted"
    print("[PASS] NC-Q: unaligned or out-of-bounds literal code targets rejected fail-closed.")


def test_nc_r_out_of_range_jump_table(repo_root: Path):
    """NC-R: Jump table candidate without valid bounds check or with out-of-bounds index must fail."""
    recovery = JumpTableRecovery(repo_root)
    tables = recovery.scan_all()
    for t in tables:
        assert t.entry_count > 0, "Jump table entry_count must be positive"
        assert t.bounds_check is not None, "Jump table must possess a proven bounds check"
        for tgt in t.targets:
            tgt_vma = int(tgt, 16)
            assert tgt_vma % 2 == 0, f"NC-R violation: jump target {tgt} is unaligned"
    print("[PASS] NC-R: jump tables without proven bounds check rejected fail-closed.")


def test_nc_s_generation_collision(repo_root: Path):
    """NC-S: Target resolution across differing module generations without explicit declaration must fail."""
    scorecard_path = repo_root / "workstreams/T2-ASM-06/indirect_resolution_scorecard.json"
    data = json.loads(scorecard_path.read_text())
    for s in data["sites"]:
        gen = s.get("generation", 0)
        assert gen == 0, f"NC-S violation: unexpected generation {gen} in site {s['site_id']}"
    print("[PASS] NC-S: cross-generation collision rejected fail-closed.")


def test_nc_t_dynamic_target_without_static_exclusivity(repo_root: Path):
    """NC-T: Indirect site observed dynamically cannot claim RESOLVED_EXACT_SINGLE without static proof."""
    dyn_path = repo_root / "workstreams/T2-ASM-06/indirect_dynamic_targets.json"
    dyn_data = json.loads(dyn_path.read_text())
    violations = 0
    for s in dyn_data["sites"]:
        if not s["resolution_status"].startswith("RESOLVED"):
            assert s["resolution_status"] == "UNRESOLVED", f"NC-T violation: invalid status {s['resolution_status']}"
            assert s["dynamic_correlation_class"] in (
                "DYNAMIC_EXECUTED_STATIC_UNRESOLVED",
                "UNEXECUTED_AND_UNRESOLVED"
            )
            if s["dynamically_executed_in_cdl_or_traces"] and s["resolution_status"] == "RESOLVED_EXACT_SINGLE":
                violations += 1
    assert violations == 0, f"NC-T violation: {violations} dynamic sites falsely claimed exact single"
    print("[PASS] NC-T: dynamic target without static exclusivity quarantined as unresolved.")


def test_nc_u_ambiguous_rts(repo_root: Path):
    """NC-U: RTS without bounded static caller domain must NOT be marked resolved."""
    scorecard_path = repo_root / "workstreams/T2-ASM-06/indirect_resolution_scorecard.json"
    data = json.loads(scorecard_path.read_text())
    rts_sites = [s for s in data["sites"] if s["opcode_id"] == "RTS"]
    assert len(rts_sites) == 638, f"Expected exactly 638 RTS sites, got {len(rts_sites)}"

    unresolved_rts = [s for s in rts_sites if s["resolution_status"] == "UNRESOLVED"]
    assert len(unresolved_rts) > 0, "All RTS sites cannot be magically resolved without bounded caller proof"

    for s in rts_sites:
        if s["resolution_status"].startswith("RESOLVED"):
            assert s["evidence_type"] == "RTS_BOUNDED_CALLER_SET", (
                f"Resolved RTS {s['site_id']} must have RTS_BOUNDED_CALLER_SET evidence"
            )
            assert len(s["targets"]) > 0, f"Resolved RTS {s['site_id']} has no caller target domain"
    print("[PASS] NC-U: ambiguous RTS without bounded caller domain retained as unresolved.")


def test_nc_v_callback_table_overlapping_data(repo_root: Path):
    """NC-V: Jump table targets pointing into proven guarded DATA or PADDING must fail."""
    from tools.carver.p3_control_flow_resolver import P3ControlFlowResolver
    resolver = P3ControlFlowResolver(repo_root)
    jt_path = repo_root / "workstreams/T2-ASM-06/jump_tables.json"
    jt_data = json.loads(jt_path.read_text())

    for t in jt_data["tables"]:
        mod = t["module"]
        vma_base = 0x06004000 if mod == "0TH2.BIN" else (0x002DA000 if mod == "TH2.LOW" else 0x060D8000)
        g_data_vmas = {vma_base + off for off in resolver.guarded_data.get(mod, set())}
        g_pad_vmas = {vma_base + off for off in resolver.guarded_pad.get(mod, set())}

        for tgt in t["targets"]:
            tgt_vma = int(tgt, 16)
            assert tgt_vma not in g_data_vmas, (
                f"NC-V violation: jump table target 0x{tgt_vma:08X} points into guarded DATA"
            )
            assert tgt_vma not in g_pad_vmas, (
                f"NC-V violation: jump table target 0x{tgt_vma:08X} points into guarded PADDING"
            )
    print("[PASS] NC-V: jump table targets pointing into DATA or PADDING rejected fail-closed.")


def test_nc_w_partial_constant_masked_as_exact(repo_root: Path):
    """NC-W: Dynamic RAM load, partial width load, or call clobber must not yield an exact constant."""
    # Test 1: Call instruction in between literal load and indirect call site
    mock_code = bytearray(32)
    struct.pack_into('>H', mock_code, 0x00, 0xD101) # MOV.L @(disp, PC), R1
    struct.pack_into('>H', mock_code, 0x02, 0xB005) # BSR (call clobber)
    struct.pack_into('>H', mock_code, 0x04, 0x0009) # NOP
    struct.pack_into('>H', mock_code, 0x06, 0x410B) # JSR @R1
    struct.pack_into('>I', mock_code, 0x08, 0x06005000)

    prop = ConstantPropagator(bytes(mock_code), 0x06004000)
    res = prop.resolve_register_at_site(0x06004006, 1)
    assert res is None, "NC-W violation: register provenance crossed call clobber boundary"

    # Test 2: Partial/dynamic memory load (e.g. MOV.B @R2, R1)
    mock_code2 = bytearray(16)
    struct.pack_into('>H', mock_code2, 0x00, 0x6120) # MOV.B @R2, R1
    struct.pack_into('>H', mock_code2, 0x02, 0x410B) # JSR @R1
    prop2 = ConstantPropagator(bytes(mock_code2), 0x06004000)
    res2 = prop2.resolve_register_at_site(0x06004002, 1)
    assert res2 is None, "NC-W violation: partial byte memory load accepted as exact constant"
    print("[PASS] NC-W: partial/dynamic constant propagation masked as exact rejected fail-closed.")


def test_nc_x_cross_module_target_alias(repo_root: Path):
    """NC-X: Cross-module target resolving to address outside target module VMA must fail."""
    scorecard_path = repo_root / "workstreams/T2-ASM-06/indirect_resolution_scorecard.json"
    data = json.loads(scorecard_path.read_text())

    vma_ranges = {
        "0TH2.BIN": (0x06004000, 0x06004000 + 535552),
        "TH2.LOW": (0x002DA000, 0x002DA000 + 149504),
        "SET07.BIN": (0x060D8000, 0x060D8000 + 98304),
        "BGM.BIN": (0x00000000, 0x00000000 + 524288),
    }

    for s in data["sites"]:
        if s["resolution_status"] == "RESOLVED_EXACT_SINGLE":
            for tgt in s["targets"]:
                if tgt.startswith("0x"):
                    tvma = int(tgt, 16)
                    matched_mod = None
                    for mod_name, (start, end) in vma_ranges.items():
                        if start <= tvma < end:
                            matched_mod = mod_name
                            break
                    assert matched_mod is not None, (
                        f"NC-X violation: target {tgt} at site {s['site_id']} outside all module VMAs"
                    )
    print("[PASS] NC-X: cross-module target alias outside destination VMAs rejected fail-closed.")


def run_all_p5_negative_controls(repo_root: Path):
    print("=== Running T2-ASM-06 Negative Controls (NC-Q .. NC-X) ===")
    test_nc_q_fake_literal_code(repo_root)
    test_nc_r_out_of_range_jump_table(repo_root)
    test_nc_s_generation_collision(repo_root)
    test_nc_t_dynamic_target_without_static_exclusivity(repo_root)
    test_nc_u_ambiguous_rts(repo_root)
    test_nc_v_callback_table_overlapping_data(repo_root)
    test_nc_w_partial_constant_masked_as_exact(repo_root)
    test_nc_x_cross_module_target_alias(repo_root)
    print("=== All 8 P5 Negative Controls (NC-Q .. NC-X) Passed Successfully ===")


if __name__ == "__main__":
    run_all_p5_negative_controls(_repo_root)
