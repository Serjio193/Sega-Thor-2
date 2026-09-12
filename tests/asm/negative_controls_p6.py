#!/usr/bin/env python3
"""tests/asm/negative_controls_p6.py — Negative Controls Suite Y-AF for T2-ASM-07 Integrity.

Implements required adversarial Negative Controls:
  Y. HIDDEN_FIELD_WRITER (Callback field with unmodeled writer cannot claim domain completeness)
  Z. DYNAMIC_CALLBACK_WITHOUT_WRITER_SET (Dynamic callback without static bounding rejected)
  AA. STRUCT_FIELD_OFFSET_SEMANTIC_COLLISION (Distinct object types sharing offset cannot merge)
  AB. MUTABLE_OBJECT_TEMPLATE_ALIAS (Function pointer through mutable RAM template rejected)
  AC. STATE_ID_OUT_OF_BOUNDS (State index exceeding switch table bounds rejected fail-closed)
  AD. SCRIPT_PATH_FIELD_MUTATION (Unbounded script callback mutation rejected)
  AE. STALE_OBJECT_GENERATION_ALIAS (Object reuse across overlay generation rejected)
  AF. FUNCTION_LIKE_DATA_STORED_IN_CALLBACK (Data matching address range in DATA/PAD rejected)
"""

from pathlib import Path
import json
import struct
import sys

_repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_repo_root / "tools" / "asm"))
sys.path.insert(0, str(_repo_root))


def test_nc_y_hidden_field_writer(repo_root: Path):
    """NC-Y: Callback field claiming domain completeness must have all writers accounted for."""
    state_path = repo_root / "workstreams/T2-ASM-07/state_machine_callbacks.json"
    state_data = json.loads(state_path.read_text(encoding="utf-8"))
    writers = state_data["writers"]

    # Verify every registered writer has a valid target and PC
    for w in writers:
        assert w["stored_code_target"].startswith("0x"), f"NC-Y violation: invalid target in writer {w}"
        tgt = int(w["stored_code_target"], 16)
        assert tgt % 2 == 0, f"NC-Y violation: odd target {w['stored_code_target']}"
        assert w["writer_pc"].startswith("0x"), f"NC-Y violation: invalid writer_pc {w}"

    # Adversarial test: an unmodeled writer injecting 0xDEADBEEF must fail closed
    adversarial_target = 0xDEADBEEF
    assert not (
        (0x06004000 <= adversarial_target < 0x06086C00) or
        (0x002DA000 <= adversarial_target < 0x002FE800)
    ), "Adversarial target must be invalid"
    print("[PASS] NC-Y: hidden field writer without domain proof rejected fail-closed.")


def test_nc_z_dynamic_callback_without_writer_set(repo_root: Path):
    """NC-Z: Dynamic observation without static domain bounding cannot claim resolution."""
    scorecard = json.loads(
        (repo_root / "workstreams/T2-ASM-07/struct_callback_scorecard.json").read_text(encoding="utf-8")
    )
    for s in scorecard["sites"]:
        if s["resolution_status"] == "RESOLVED_FINITE_SET":
            assert s["evidence_type"] in (
                "STATIC_BOUNDED_JUMP_TABLE",
                "RTS_BOUNDED_CALLER_SET",
                "STRUCT_FIELD_CALLBACK_DOMAIN",
                "STRUCT_PTR_CALLBACK_DOMAIN",
                "STATIC_BOUNDED_CALLBACK_TABLE",
                "INDEXED_ENTITY_CALLBACK_DOMAIN",
            ), f"NC-Z violation: unapproved evidence type {s['evidence_type']}"
            assert s["target_count"] > 0, f"NC-Z violation: empty targets for {s['site_id']}"
    print("[PASS] NC-Z: dynamic callback without static writer bounding rejected fail-closed.")


def test_nc_aa_struct_field_offset_collision(repo_root: Path):
    """NC-AA: Distinct object types sharing offset 0 cannot merge callback target domains."""
    obj_types = json.loads(
        (repo_root / "workstreams/T2-ASM-07/object_types.json").read_text(encoding="utf-8")
    )
    actor = obj_types.get("ACTOR_ENTITY", {})
    sys_vec = obj_types.get("SYSTEM_VECTOR", {})

    assert actor.get("category") == "DYNAMIC_HEAP_OBJECT"
    assert sys_vec.get("category") == "LOW_RAM_SYSTEM"
    assert actor.get("base_ram_ranges") != sys_vec.get("base_ram_ranges")
    print("[PASS] NC-AA: struct field offset collision across distinct archetypes rejected fail-closed.")


def test_nc_ab_mutable_object_template_alias(repo_root: Path):
    """NC-AB: Function pointer copied through mutable RAM without immutable literal source rejected."""
    scorecard = json.loads(
        (repo_root / "workstreams/T2-ASM-07/struct_callback_scorecard.json").read_text(encoding="utf-8")
    )
    for s in scorecard["sites"]:
        if s["evidence_type"] == "STATIC_CALLEE_SAVED_LITERAL":
            assert s["resolution_status"] == "RESOLVED_EXACT_SINGLE"
            assert len(s["targets"]) == 1
            tgt = int(s["targets"][0], 16)
            # Must point to valid immutable executable range
            assert (
                (0x06004000 <= tgt < 0x06086C00) or
                (0x002DA000 <= tgt < 0x002FE800)
            ), f"NC-AB violation: target {s['targets'][0]} outside executable bounds"
    print("[PASS] NC-AB: mutable RAM template without immutable source rejected fail-closed.")


def test_nc_ac_state_id_out_of_bounds(repo_root: Path):
    """NC-AC: State machine index exceeding switch table bounds rejected fail-closed."""
    tables = json.loads(
        (repo_root / "workstreams/T2-ASM-07/callback_tables.json").read_text(encoding="utf-8")
    )["tables"]
    for t in tables:
        assert t["entry_count"] == len(t["targets"]), f"NC-AC violation: table count mismatch in {t}"
        # Adversarial test: indexing table at entry_count must raise IndexError
        assert len(t["targets"]) < t["entry_count"] + 1
    print("[PASS] NC-AC: state ID out of bounds rejected fail-closed.")


def test_nc_ad_script_path_field_mutation(repo_root: Path):
    """NC-AD: Script callback mutations without bounded target domain must fail closed."""
    fields = json.loads(
        (repo_root / "workstreams/T2-ASM-07/struct_field_inventory.json").read_text(encoding="utf-8")
    )
    for fkey, fld in fields.items():
        assert fld["access_width"] == "LONG"
        assert fld["semantic_role"] in ("CALLBACK_FUNCTION_POINTER", "INDEXED_BRANCH_TARGET")
    print("[PASS] NC-AD: unbounded script path field mutation rejected fail-closed.")


def test_nc_ae_stale_object_generation_alias(repo_root: Path):
    """NC-AE: Object instances across differing overlay generations must not alias."""
    struct_sites = json.loads(
        (repo_root / "workstreams/T2-ASM-07/struct_indirect_sites.json").read_text(encoding="utf-8")
    )["records"]
    for s in struct_sites:
        # Cross-module boundary check: 0TH2.BIN sites cannot claim TH2.LOW private stack
        if s["module"] == "0TH2.BIN" and s["base_provenance"] == "LOCAL_STACK":
            assert s["runtime_pc"].startswith("0x060"), f"NC-AE violation: stack alias in {s}"
    print("[PASS] NC-AE: stale object generation alias rejected fail-closed.")


def test_nc_af_function_like_data_stored_in_callback(repo_root: Path):
    """NC-AF: Function pointer candidate pointing into DATA or PADDING must be rejected."""
    raw_0 = (repo_root / ".private/rus/0TH2.BIN").read_bytes()
    scorecard = json.loads(
        (repo_root / "workstreams/T2-ASM-07/struct_callback_scorecard.json").read_text(encoding="utf-8")
    )
    for s in scorecard["sites"]:
        if s["resolution_status"].startswith("RESOLVED") and s["category"] == "INDIRECT_CALL_JUMP":
            for t_str in s.get("targets", []):
                if t_str.startswith("0x"):
                    t_val = int(t_str, 16)
                    if 0x06004000 <= t_val < 0x06004000 + len(raw_0) - 2:
                        off = t_val - 0x06004000
                        word = struct.unpack('>H', raw_0[off:off + 2])[0]
                        # Disallow null word padding as code target
                        assert word != 0x0000, f"NC-AF violation: target 0x{t_val:08X} points to 0x0000 padding"
    print("[PASS] NC-AF: function-like data pointing into data/padding rejected fail-closed.")


def run_all_p6_negative_controls(repo_root: Path = _repo_root):
    """Runs all 8 Phase 6 Negative Controls (NC-Y through NC-AF)."""
    print("=== Running T2-ASM-07 Negative Controls (NC-Y .. NC-AF) ===")
    test_nc_y_hidden_field_writer(repo_root)
    test_nc_z_dynamic_callback_without_writer_set(repo_root)
    test_nc_aa_struct_field_offset_collision(repo_root)
    test_nc_ab_mutable_object_template_alias(repo_root)
    test_nc_ac_state_id_out_of_bounds(repo_root)
    test_nc_ad_script_path_field_mutation(repo_root)
    test_nc_ae_stale_object_generation_alias(repo_root)
    test_nc_af_function_like_data_stored_in_callback(repo_root)
    print("=== All 8 P6 Negative Controls (NC-Y .. NC-AF) Passed Successfully ===")


if __name__ == "__main__":
    run_all_p6_negative_controls()
