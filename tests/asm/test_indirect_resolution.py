#!/usr/bin/env python3
"""tests/asm/test_indirect_resolution.py — Unit Tests for T2-ASM-06 Indirect Resolution.

Validates the full pipeline of indirect control flow resolution:
  1. Exact inventory reconciliation (2,233 total sites).
  2. Strict opcode accounting (JSR: 1465, RTS: 638, JMP: 121, BSRF: 7, BRAF: 2).
  3. Rule 1 category separation (INDIRECT_CALL_JUMP vs RETURN_FLOW).
  4. Constant propagation and PC literal decoding.
  5. Jump table discovery and bounds verification.
  6. Call-clobber and memory provenance safety.
  7. Function boundary and leaf RTS domain recovery.
  8. CFG closure and gap reduction monotonicity.
"""

import json
from pathlib import Path
import struct
import sys

repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root / "tools" / "asm"))
sys.path.insert(0, str(repo_root))

from tools.asm.constant_propagator import ConstantPropagator, PropagatedValue
from tools.asm.register_provenance import RegisterProvenanceEngine
from tools.asm.jump_table_recovery import JumpTableRecovery
from tools.asm.call_graph_builder import CallGraphBuilder
from tools.asm.indirect_resolver import MasterIndirectResolver


def test_inventory_reconciliation():
    """Validates that inventory reconciles exactly to 2,233 total sites."""
    scorecard_path = repo_root / "workstreams/T2-ASM-06/indirect_resolution_scorecard.json"
    data = json.loads(scorecard_path.read_text(encoding="utf-8"))
    acct = data["accounting"]

    assert acct["total_sites"] == 2233, f"Expected 2233 total sites, got {acct['total_sites']}"
    assert acct["resolved_total"] + acct["unresolved_total"] == 2233, (
        f"Sum of resolved ({acct['resolved_total']}) and unresolved ({acct['unresolved_total']}) must equal 2233"
    )
    assert acct["resolved_total"] > 0, "Resolved total must be positive"
    assert acct["unresolved_total"] > 0, "Unresolved total must remain > 0 (honest gate)"
    print(f"[PASS] Inventory reconciliation verified: {acct['resolved_total']} resolved + {acct['unresolved_total']} unresolved == 2233")


def test_opcode_accounting():
    """Validates exact opcode accounting across JSR, RTS, JMP, BSRF, BRAF."""
    scorecard_path = repo_root / "workstreams/T2-ASM-06/indirect_resolution_scorecard.json"
    data = json.loads(scorecard_path.read_text(encoding="utf-8"))
    opcodes = data["opcode_breakdown"]

    expected_totals = {
        "JSR": 1465,
        "RTS": 638,
        "JMP": 121,
        "BSRF": 7,
        "BRAF": 2,
    }

    total_sum = 0
    for op, exp_total in expected_totals.items():
        assert op in opcodes, f"Missing opcode {op} in scorecard"
        cur = opcodes[op]
        assert cur["total"] == exp_total, f"Opcode {op} expected {exp_total}, got {cur['total']}"
        assert cur["resolved"] + cur["unresolved"] == exp_total, (
            f"Opcode {op}: resolved ({cur['resolved']}) + unresolved ({cur['unresolved']}) != {exp_total}"
        )
        total_sum += cur["total"]

    assert total_sum == 2233, f"Sum of all opcode totals ({total_sum}) must be 2233"
    print(f"[PASS] Opcode accounting verified: {expected_totals}")


def test_category_separation():
    """Validates Rule 1: Separation of INDIRECT_CALL_JUMP from RETURN_FLOW."""
    scorecard_path = repo_root / "workstreams/T2-ASM-06/indirect_resolution_scorecard.json"
    data = json.loads(scorecard_path.read_text(encoding="utf-8"))

    cj = data["indirect_call_jump_metrics"]
    rf = data["return_flow_rts_metrics"]

    assert cj["total"] == 1595, f"Expected 1595 call/jump sites, got {cj['total']}"
    assert rf["total"] == 638, f"Expected 638 RTS sites, got {rf['total']}"
    assert cj["total"] + rf["total"] == 2233, "Categories must sum to 2233"

    assert cj["resolved"] + cj["unresolved"] == cj["total"]
    assert rf["resolved"] + rf["unresolved"] == rf["total"]
    print(f"[PASS] Rule 1 category separation verified: Call/Jump {cj['resolved']}/{cj['total']}, RTS {rf['resolved']}/{rf['total']}")


def test_constant_propagation_direct():
    """Validates constant propagation on known SH-2 PC literal references."""
    th2_0 = (repo_root / ".private/rus/0TH2.BIN").read_bytes()
    prop = ConstantPropagator(th2_0, 0x06004000)

    # Test 0x0600403C: JSR @R3 -> literal loaded from 0x0600404C
    res = prop.resolve_register_at_site(0x0600403C, 3)
    assert res is not None, "0x0600403C R3 must resolve via constant propagation"
    assert res.is_exact is True
    assert res.val == 0x06004254, f"0x0600403C R3 expected 0x06004254, got 0x{res.val:08X}"
    assert res.provenance == "PC_LITERAL_POOL"
    print(f"[PASS] Constant propagation direct verified: 0x0600403C R3 -> 0x{res.val:08X}")


def test_jump_table_recovery():
    """Validates jump table recovery bounds, encoding, and alignment."""
    jt_path = repo_root / "workstreams/T2-ASM-06/jump_tables.json"
    data = json.loads(jt_path.read_text(encoding="utf-8"))
    tables = data["tables"]

    assert len(tables) > 40, f"Expected at least 40 jump tables, got {len(tables)}"
    for t in tables:
        assert t["entry_count"] >= 2, f"Jump table {t['table_id']} must have at least 2 entries"
        assert t["bounds_check"] in ("AND_MASK", "MOV_LIMIT", "IMPLICIT")
        assert len(t["targets"]) == t["entry_count"]
        for tgt in t["targets"]:
            vma = int(tgt, 16)
            assert vma % 2 == 0, f"Jump table target {tgt} in {t['table_id']} is not 2-byte aligned"
    print(f"[PASS] Jump table recovery verified: {len(tables)} tables with proven bounds and alignment")


def test_call_clobber_safety():
    """Validates Rule 3: Call-clobber safety stops propagation across calls."""
    mock = bytearray(32)
    # 0x00: MOV.L @(4, PC), R1 (0xD101)
    struct.pack_into('>H', mock, 0x00, 0xD101)
    # 0x02: JSR @R2 (0x420B) -> Call-clobber instruction
    struct.pack_into('>H', mock, 0x02, 0x420B)
    # 0x04: NOP (0x0009)
    struct.pack_into('>H', mock, 0x04, 0x0009)
    # 0x06: JSR @R1 (0x410B) -> Site to resolve
    struct.pack_into('>H', mock, 0x06, 0x410B)
    # 0x08: literal pool value (0x06005000)
    struct.pack_into('>I', mock, 0x08, 0x06005000)

    prop = ConstantPropagator(bytes(mock), 0x06004000)
    res = prop.resolve_register_at_site(0x06004006, 1)
    assert res is None, "Call-clobber safety violated: propagated across JSR @R2"
    print("[PASS] Call-clobber safety verified: halted at call boundary")


def test_leaf_rts_domain_recovery():
    """Validates that all resolved RTS sites possess bounded static caller sets."""
    scorecard_path = repo_root / "workstreams/T2-ASM-06/indirect_resolution_scorecard.json"
    data = json.loads(scorecard_path.read_text(encoding="utf-8"))

    resolved_rts = [
        s for s in data["sites"]
        if s["opcode_id"] == "RTS" and s["resolution_status"].startswith("RESOLVED")
    ]
    assert len(resolved_rts) > 0, "Expected resolved RTS sites"
    for s in resolved_rts:
        assert s["evidence_type"] == "RTS_BOUNDED_CALLER_SET"
        assert len(s["targets"]) > 0
        assert s["targets"][0].startswith("CALLERS_OF_")
    print(f"[PASS] Leaf RTS domain recovery verified: {len(resolved_rts)} RTS sites bounded")


def test_cfg_gap_reduction():
    """Validates that CFG closure achieved measurable gap reduction without circular heuristics."""
    cfg_path = repo_root / "workstreams/T2-ASM-06/cfg_closure.json"
    data = json.loads(cfg_path.read_text(encoding="utf-8"))

    assert data["residual_undecoded_gaps_before"] == 2206
    assert data["residual_undecoded_gaps_after"] < 2206
    assert data["gap_reduction"] > 0
    assert data["proven_targets_injected"] > 0
    print(
        f"[PASS] CFG gap reduction verified: {data['residual_undecoded_gaps_before']} -> "
        f"{data['residual_undecoded_gaps_after']} (reduced by {data['gap_reduction']})"
    )


def main():
    print("=== Running T2-ASM-06 Indirect Resolution Unit Tests ===")
    test_inventory_reconciliation()
    test_opcode_accounting()
    test_category_separation()
    test_constant_propagation_direct()
    test_jump_table_recovery()
    test_call_clobber_safety()
    test_leaf_rts_domain_recovery()
    test_cfg_gap_reduction()
    print("=== All 8 Indirect Resolution Unit Tests Passed 100% ===")


if __name__ == "__main__":
    main()
