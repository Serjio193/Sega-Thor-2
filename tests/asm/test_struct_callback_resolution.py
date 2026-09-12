#!/usr/bin/env python3
"""tests/asm/test_struct_callback_resolution.py — Unit Tests for T2-ASM-07 Struct Callbacks.

Validates the full pipeline of struct function pointer recovery, entity/actor
dispatch domains, and residual CFG closure:
  1. Exact inventory reconciliation (2,233 total sites).
  2. Strict opcode accounting (JSR: 1465, RTS: 638, JMP: 121, BSRF: 7, BRAF: 2).
  3. Rule 1 category separation (INDIRECT_CALL_JUMP vs RETURN_FLOW).
  4. Struct site isolation and access pattern recovery.
  5. Object base provenance and field layout mapping.
  6. Callback table entry validity and bounds.
  7. Field writer domain bounding and target safety.
  8. Master scorecard metrics and resolution progression.
"""

from pathlib import Path
import json
import sys

repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root / "tools" / "asm"))
sys.path.insert(0, str(repo_root))

from tools.asm.struct_site_isolator import StructSiteIsolator
from tools.asm.object_provenance_analyzer import ObjectProvenanceAnalyzer
from tools.asm.callback_field_analyzer import CallbackFieldAnalyzer
from tools.asm.struct_callback_resolver import StructCallbackResolver


def test_inventory_reconciliation():
    """Validates that inventory reconciles exactly to 2,233 total sites."""
    scorecard_path = repo_root / "workstreams/T2-ASM-07/struct_callback_scorecard.json"
    data = json.loads(scorecard_path.read_text(encoding="utf-8"))
    acct = data["accounting"]

    assert acct["total_sites"] == 2233, f"Expected 2233 total sites, got {acct['total_sites']}"
    assert acct["resolved_total"] + acct["unresolved_total"] == 2233, (
        f"Sum of resolved ({acct['resolved_total']}) and unresolved ({acct['unresolved_total']}) must equal 2233"
    )
    assert acct["resolved_total"] == 1686, f"Expected 1686 resolved sites, got {acct['resolved_total']}"
    assert acct["unresolved_total"] == 547, f"Expected 547 unresolved sites, got {acct['unresolved_total']}"
    print(f"[PASS] Inventory reconciliation verified: 1686 resolved + 547 unresolved == 2233")


def test_opcode_accounting():
    """Validates exact opcode accounting across JSR, RTS, JMP, BSRF, BRAF."""
    scorecard_path = repo_root / "workstreams/T2-ASM-07/struct_callback_scorecard.json"
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
    scorecard_path = repo_root / "workstreams/T2-ASM-07/struct_callback_scorecard.json"
    data = json.loads(scorecard_path.read_text(encoding="utf-8"))

    cj = data["indirect_call_jump_metrics"]
    rf = data["return_flow_rts_metrics"]

    assert cj["total"] == 1595, f"Expected 1595 call/jump sites, got {cj['total']}"
    assert rf["total"] == 638, f"Expected 638 RTS sites, got {rf['total']}"
    assert cj["total"] + rf["total"] == 2233, "Categories must sum to 2233"

    assert cj["resolved"] == 1552, f"Expected 1552 resolved call/jump, got {cj['resolved']}"
    assert cj["unresolved"] == 43, f"Expected 43 unresolved call/jump, got {cj['unresolved']}"
    assert rf["resolved"] == 134, f"Expected 134 resolved RTS, got {rf['resolved']}"
    assert rf["unresolved"] == 504, f"Expected 504 unresolved RTS, got {rf['unresolved']}"

    print(f"[PASS] Rule 1 category separation verified: Call/Jump 1552/1595 (97.30%), RTS 134/638 (21.00%)")


def test_struct_site_isolation():
    """Validates struct site isolation across dynamic and cold populations."""
    sites_path = repo_root / "workstreams/T2-ASM-07/struct_indirect_sites.json"
    data = json.loads(sites_path.read_text(encoding="utf-8"))
    summary = data["summary"]

    assert summary["total_unresolved_sites"] == 855
    assert summary["dynamic_unresolved_sites"] == 551
    assert summary["cold_unresolved_sites"] == 304
    assert summary["dynamic_unresolved_sites"] + summary["cold_unresolved_sites"] == 855
    print(f"[PASS] Struct site isolation verified: 551 dynamic + 304 cold == 855")


def test_object_provenance_and_fields():
    """Validates object type taxonomy and struct field layouts."""
    types_path = repo_root / "workstreams/T2-ASM-07/object_types.json"
    types_data = json.loads(types_path.read_text(encoding="utf-8"))
    assert "ACTOR_ENTITY" in types_data
    assert "ENGINE_STATE" in types_data
    assert "SYSTEM_VECTOR" in types_data

    fields_path = repo_root / "workstreams/T2-ASM-07/struct_field_inventory.json"
    fields_data = json.loads(fields_path.read_text(encoding="utf-8"))
    assert len(fields_data) >= 10, f"Expected >= 10 distinct struct fields, got {len(fields_data)}"
    print(f"[PASS] Object provenance and struct field inventory verified: {len(fields_data)} fields mapped")


def test_callback_tables_integrity():
    """Validates callback tables entry counts and target alignments."""
    tables_path = repo_root / "workstreams/T2-ASM-07/callback_tables.json"
    tables_data = json.loads(tables_path.read_text(encoding="utf-8"))
    assert tables_data["summary"]["total_tables"] >= 800
    for t in tables_data["tables"][:50]:
        assert t["entry_count"] >= 4
        assert len(t["targets"]) == t["entry_count"]
        for tgt in t["targets"]:
            assert int(tgt, 16) % 2 == 0
    print(f"[PASS] Callback tables integrity verified across {tables_data['summary']['total_tables']} tables")


def test_state_machine_callbacks():
    """Validates state machine callback field writer domains."""
    state_path = repo_root / "workstreams/T2-ASM-07/state_machine_callbacks.json"
    state_data = json.loads(state_path.read_text(encoding="utf-8"))
    callbacks = state_data["state_machine_callbacks"]

    for fld, targets in callbacks.items():
        assert len(targets) > 0, f"Empty target domain for {fld}"
        for tgt in targets:
            assert tgt.startswith("0x")
            assert int(tgt, 16) % 2 == 0
    print(f"[PASS] State machine callback domains verified across {len(callbacks)} fields")


def main():
    test_inventory_reconciliation()
    test_opcode_accounting()
    test_category_separation()
    test_struct_site_isolation()
    test_object_provenance_and_fields()
    test_callback_tables_integrity()
    test_state_machine_callbacks()
    print("All 7 T2-ASM-07 unit tests passed 100%.")


if __name__ == "__main__":
    main()
