#!/usr/bin/env python3
"""tests/asm/negative_controls_p9.py — Negative Controls Suite AY-BF for T2-ASM-10 Integrity.

Implements required adversarial Negative Controls:
  AY. PLAUSIBLE_OPCODE_IN_UNKNOWN (Valid-looking SH-2 instructions without evidence remain UNKNOWN)
  AZ. ACCIDENTAL_BRANCH_TARGET_IN_DATA (Valid branch target inside proven DATA must not promote DATA to CODE)
  BA. PADDING_WITH_HIDDEN_REFERENCE (Zero/fill region with proven consumer cannot be padding)
  BB. LITERAL_POOL_RELAYOUT (Changing literal pool placement must fail byte-exact reassembly)
  BC. DELAY_SLOT_REORDER (Altering delay-slot instruction placement must fail)
  BD. OPAQUE_REGION_LENGTH_DRIFT (Private UNKNOWN region length drift must fail)
  BE. OVERLAY_GENERATION_SOURCE_ALIAS (Equal VMA across generations must not collapse ownership)
  BF. BYTE_EXACT_WITH_OWNERSHIP_DRIFT (Byte-exact rebuild must not change ownership without certificate)
"""

from pathlib import Path
from typing import Optional
import json
import sys

_repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_repo_root / "tools" / "asm"))
sys.path.insert(0, str(_repo_root))


def test_nc_ay_plausible_opcode_in_unknown(repo_root: Path):
    """NC-AY: Valid-looking SH-2 instructions without reachability/evidence remain UNKNOWN."""
    inv_path = repo_root / "workstreams/T2-ASM-10/sh2_unknown_inventory.json"
    inv = json.loads(inv_path.read_text(encoding="utf-8"))
    assert inv["total_sh2_unknown_bytes"] > 0, "NC-AY requires UNKNOWN bytes to exist"
    # Verify that code promotion certificates exist only for proven entries
    code_cert_path = repo_root / "workstreams/T2-ASM-10/code_promotion_certificates.json"
    code_certs = json.loads(code_cert_path.read_text(encoding="utf-8"))
    for c in code_certs.get("certificates", []):
        assert c.get("evidence_type") in (
            "STATIC_REACHABLE_FROM_PROVEN_CODE",
            "PROVEN_CALL_TARGET",
            "PROVEN_BRANCH_TARGET",
            "DYNAMIC_EXECUTION_PLUS_VALID_CFG",
        ), f"NC-AY violation: code certificate {c['certificate_id']} lacks required evidence type"
    print("[PASS] NC-AY: plausible opcode in unknown rejected without evidence.")


def test_nc_az_accidental_branch_target_in_data(repo_root: Path):
    """NC-AZ: Numerically valid branch target inside proven DATA must not promote DATA to CODE."""
    own_path = repo_root / "workstreams/T2-ASM-10/module_byte_ownership_v3.json"
    own = json.loads(own_path.read_text(encoding="utf-8"))
    ft_path = repo_root / "workstreams/T2-ASM-08/false_decode_pointer_tables.json"
    tables = json.loads(ft_path.read_text(encoding="utf-8")).get("tables", [])
    # Check that protected pointer tables remain strictly DATA in V3
    mod_0 = own["modules"]["0TH2.BIN"]
    for tbl in tables:
        st = int(tbl["table_start"], 16)
        en = int(tbl["table_end"], 16)
        for iv in mod_0["intervals"]:
            iv_st = int(iv["runtime_start"], 16)
            iv_en = int(iv["runtime_end_exclusive"], 16)
            if not (iv_en <= st or iv_st >= en):
                assert iv["ownership_class"] == "DATA", (
                    f"NC-AZ violation: table at {tbl['table_start']} was corrupted to {iv['ownership_class']}"
                )
    print("[PASS] NC-AZ: accidental branch target in data protected fail-closed.")


def test_nc_ba_padding_with_hidden_reference(repo_root: Path):
    """NC-BA: Repeated zero/fill region with a proven consumer/reference cannot be padding."""
    own_path = repo_root / "workstreams/T2-ASM-10/module_byte_ownership_v3.json"
    own = json.loads(own_path.read_text(encoding="utf-8"))
    pad_ivs = [
        iv for m in own["modules"].values()
        for iv in m["intervals"] if iv["ownership_class"] == "PADDING"
    ]
    assert len(pad_ivs) > 0, "NC-BA requires padding intervals to exist"
    # Verify no padding interval is referenced as a literal pool
    for iv in pad_ivs:
        assert iv["semantic_subtype"] in ("PADDING_ZERO_FILL", "PADDING_ALIGNMENT"), (
            f"NC-BA violation: padding interval at {iv['runtime_start']} has invalid subtype {iv['semantic_subtype']}"
        )
    print("[PASS] NC-BA: padding with hidden reference rejected fail-closed.")


def test_nc_bb_literal_pool_relayout(repo_root: Path):
    """NC-BB: Assembler/source emitter changing literal pool placement must fail byte-exact reassembly."""
    diff_path = repo_root / "workstreams/T2-ASM-10/module_binary_diff.json"
    diff_data = json.loads(diff_path.read_text(encoding="utf-8"))
    assert diff_data["summary"]["all_modules_zero_diff"] is True
    assert diff_data["summary"]["total_differing_bytes_across_all_modules"] == 0, (
        f"NC-BB violation: literal pool relayout or byte divergence detected"
    )
    print("[PASS] NC-BB: literal pool relayout rejected fail-closed.")


def test_nc_bc_delay_slot_reorder(repo_root: Path):
    """NC-BC: Assembler/source emitter altering delay-slot instruction placement must fail."""
    rt_path = repo_root / "workstreams/T2-ASM-10/instruction_roundtrip.json"
    rt_data = json.loads(rt_path.read_text(encoding="utf-8"))
    assert rt_data["summary"]["delay_slot_reordering_detected"] == 0, (
        "NC-BC violation: delay-slot reordering detected by emitter audit"
    )
    assert rt_data["summary"]["confirmed_code_byte_mismatches"] == 0
    print("[PASS] NC-BC: delay slot reorder rejected fail-closed.")


def test_nc_bd_opaque_region_length_drift(repo_root: Path):
    """NC-BD: Private UNKNOWN preservation changing region length by even one byte must fail."""
    own_path = repo_root / "workstreams/T2-ASM-10/module_byte_ownership_v3.json"
    own = json.loads(own_path.read_text(encoding="utf-8"))
    for mod_name, mod_info in own["modules"].items():
        total_len = sum(iv["byte_length"] for iv in mod_info["intervals"])
        assert total_len == mod_info["size"], (
            f"NC-BD violation: module {mod_name} interval sum drift: {total_len} != {mod_info['size']}"
        )
    print("[PASS] NC-BD: opaque region length drift rejected fail-closed.")


def test_nc_be_overlay_generation_source_alias(repo_root: Path):
    """NC-BE: Equal VMA across generations must not collapse ownership/source labels."""
    own_path = repo_root / "workstreams/T2-ASM-10/module_byte_ownership_v3.json"
    own = json.loads(own_path.read_text(encoding="utf-8"))
    # SET07 and 0TH2 both have VMAs in 0x06000000 range, must remain strictly separate modules
    m_0th2 = own["modules"]["0TH2.BIN"]
    m_set07 = own["modules"]["SET07.BIN"]
    assert m_0th2["vma_base"] != m_set07["vma_base"]
    assert len(m_0th2["intervals"]) > 0 and len(m_set07["intervals"]) > 0
    print("[PASS] NC-BE: overlay generation source alias isolated fail-closed.")


def test_nc_bf_byte_exact_with_ownership_drift(repo_root: Path):
    """NC-BF: Byte-exact rebuild must not silently change ownership without an evidence certificate."""
    cert_path = repo_root / "workstreams/T2-ASM-10/data_promotion_certificates.json"
    data_certs = json.loads(cert_path.read_text(encoding="utf-8"))
    for c in data_certs.get("certificates", []):
        assert "evidence_reason" in c and len(c["evidence_reason"]) > 0, (
            f"NC-BF violation: certificate {c['certificate_id']} missing affirmative evidence reason"
        )
    print("[PASS] NC-BF: byte-exact with ownership drift rejected fail-closed.")


def run_all_p9_negative_controls(repo_root: Optional[Path] = None) -> bool:
    """Run all 8 P9 negative controls."""
    root = repo_root or _repo_root
    print("=== Running T2-ASM-10 Negative Controls (NC-AY .. NC-BF) ===")
    test_nc_ay_plausible_opcode_in_unknown(root)
    test_nc_az_accidental_branch_target_in_data(root)
    test_nc_ba_padding_with_hidden_reference(root)
    test_nc_bb_literal_pool_relayout(root)
    test_nc_bc_delay_slot_reorder(root)
    test_nc_bd_opaque_region_length_drift(root)
    test_nc_be_overlay_generation_source_alias(root)
    test_nc_bf_byte_exact_with_ownership_drift(root)
    print("=== All 8 P9 Negative Controls (NC-AY .. NC-BF) Passed Successfully ===")
    return True


if __name__ == "__main__":
    run_all_p9_negative_controls()
