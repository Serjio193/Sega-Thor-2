import hashlib
import json
import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if not os.path.isdir(os.path.join(REPO_ROOT, "docs")):
    REPO_ROOT = os.getcwd()

PLAN_DOC = os.path.join(REPO_ROOT, "docs", "D9_INDIRECT_CONTROL_FLOW_PLAN.md")
CANDIDATE_DOC = os.path.join(REPO_ROOT, "workstreams", "T2-D9-indirect", "candidate_06004280.md")
README_DOC = os.path.join(REPO_ROOT, "workstreams", "T2-D9-indirect", "README.md")
CANDIDATE_JSON = os.path.join(REPO_ROOT, "workstreams", "T2-D9-indirect", "candidate_06004280.json")
DECODE_MANIFEST_JSON = os.path.join(REPO_ROOT, "workstreams", "T2-D3-sh2-decode", "reference_decode_manifest.json")

EXPECTED_CANDIDATE_BYTES = bytes([0xD5, 0x36, 0xD4, 0x37, 0xD3, 0x37, 0x43, 0x0B, 0x00, 0x09])
EXPECTED_CANDIDATE_SHA256 = "8879cbe14f58a5fbc4eb9545e1cc41b3593e306cab114769a94f814a18bcb770"
EXPECTED_START_PC = 0x06004280
EXPECTED_END_PC = 0x06004288
EXPECTED_INS_COUNT = 5
EXPECTED_BYTE_LENGTH = 10

REQUIRED_EXIT_KINDS = [
    "DIRECT", "CONDITIONAL", "INDIRECT_JUMP",
    "INDIRECT_CALL", "RETURN", "FALLBACK_UNSUPPORTED"
]


def validate_plan_content(plan_text, cand_text, readme_text, cand_json_text, decode_manifest_text):
    # 1. SHA256 matches actual byte computation
    calc_sha = hashlib.sha256(EXPECTED_CANDIDATE_BYTES).hexdigest()
    if calc_sha != EXPECTED_CANDIDATE_SHA256:
        raise ValueError(f"Internal SHA mismatch: {calc_sha} vs {EXPECTED_CANDIDATE_SHA256}")

    if EXPECTED_CANDIDATE_SHA256 not in cand_text:
        raise ValueError("Candidate SHA256 missing from candidate_06004280.md")
    if EXPECTED_CANDIDATE_SHA256 not in plan_text:
        raise ValueError("Candidate SHA256 missing from D9 plan")

    # 2. Block boundaries
    for text, name in [(cand_text, "candidate_06004280.md"), (plan_text, "D9 plan")]:
        if "0x06004280" not in text:
            raise ValueError(f"Start PC 0x06004280 missing from {name}")
        if "0x06004288" not in text:
            raise ValueError(f"End PC 0x06004288 missing from {name}")

    # 3. Instruction classification
    if "NEEDS_D3_L0_PROOF" not in plan_text or "JSR @R3" not in plan_text:
        raise ValueError("JSR @R3 not classified as NEEDS_D3_L0_PROOF in D9 plan")
    if "ALREADY_D3_L0_PROVEN" not in plan_text:
        raise ValueError("ALREADY_D3_L0_PROVEN classification missing from D9 plan")

    # 4. M-03 Re-entry Trigger
    if "D9.4" not in plan_text or "M-03" not in plan_text:
        raise ValueError("M-03 re-entry trigger at D9.4 not properly specified in D9 plan")

    # 5. Exit kinds
    for kind in REQUIRED_EXIT_KINDS:
        if kind not in plan_text:
            raise ValueError(f"Required BlockExitKind '{kind}' missing from D9 plan")

    # 6. Status check: must be READY_FOR_BOUNDED_TEST, NOT BOUNDED_PROOF
    if "READY_FOR_BOUNDED_TEST" not in plan_text:
        raise ValueError("Status READY_FOR_BOUNDED_TEST missing from D9 plan")
    if "D9 = BOUNDED_PROOF" in plan_text:
        raise ValueError("Plan prematurely claims D9 = BOUNDED_PROOF")

    # 7. Anti-hardcoding invariant
    clean_plan = plan_text.replace("*", "")
    if not re.search(r"must\s+(not|never)\s+be\s+hardcoded", clean_plan, re.IGNORECASE):
        raise ValueError("Anti-hardcoding dynamic target invariant missing from D9 plan")

    # 8. Memory generalization
    if "copy-on-read" not in plan_text and "dependency descriptors" not in plan_text and "BlockMemoryContract" not in plan_text:
        raise ValueError("Memory generalization architecture missing from D9 plan")

    # 9. Timing reconciliation: entry + duration == exit (316309168 + 21 == 316309189)
    entry_m = re.search(r"BLOCK_ENTRY_CYCLE\s*=\s*(\d+)", plan_text)
    duration_m = re.search(r"BLOCK_DURATION\s*=\s*(\d+)", plan_text)
    exit_m = re.search(r"BLOCK_EXIT_TARGET_ENTRY_CYCLE\s*=\s*(\d+)", plan_text)

    if not entry_m or not duration_m or not exit_m:
        raise ValueError("Missing structured timing cycle definitions in D9 plan")

    entry_cyc = int(entry_m.group(1))
    duration_cyc = int(duration_m.group(1))
    exit_cyc = int(exit_m.group(1))

    if entry_cyc != 316309168:
        raise ValueError(f"Incorrect entry cycle {entry_cyc} (expected 316309168)")
    if duration_cyc != 21:
        raise ValueError(f"Incorrect duration cycles {duration_cyc} (expected 21)")
    if exit_cyc != 316309189:
        raise ValueError(f"Incorrect exit cycle {exit_cyc} (expected 316309189)")
    if entry_cyc + duration_cyc != exit_cyc:
        raise ValueError(f"Timing arithmetic failure: {entry_cyc} + {duration_cyc} != {exit_cyc}")

    # Also check candidate text has duration 21
    if "21 cycles" not in cand_text:
        raise ValueError("Candidate document missing 21 cycles duration")

    # 10. No V-09A anywhere (V-09 is canonically reserved for D13)
    for doc_name, doc_text in [("D9 plan", plan_text), ("Candidate doc", cand_text), ("README", readme_text)]:
        if "V-09A" in doc_text:
            raise ValueError(f"Invalid non-canonical gate label 'V-09A' found in {doc_name}")

    # 11. Stale timing detection: out_cycles_advanced = 19 must NOT be in D9 plan
    if re.search(r"out_cycles_advanced\s*=\s*19", plan_text):
        raise ValueError("Stale 'out_cycles_advanced = 19' found in D9 plan (must be 21)")

    # 12. Stale timing equation: 1 + 2 + 1 + 15 = 19
    if "1 + 2 + 1 + 15 = 19" in plan_text:
        raise ValueError("Stale timing equation equating total cycles to 19")

    # 13. Stale candidate duration claim of 19 cycles in prose
    if re.search(r"exact timing \(19 cycles\)", plan_text):
        raise ValueError("Stale claim of 'exact timing (19 cycles)' found in D9 plan")

    # 14. Target-entry observation recorded as 316309187
    if re.search(r'"last_observed_cycle"\s*:\s*316309187', plan_text):
        raise ValueError("Ambiguous 'last_observed_cycle: 316309187' found in D9 plan observation schema")

    # 15. Stale statement that 0x06004280..0x06004289 is not CONFIRMED_CODE
    if re.search(r"not\s+promoted\s+to.*CONFIRMED_CODE", plan_text, re.IGNORECASE):
        raise ValueError("Stale statement that candidate block is not promoted to CONFIRMED_CODE in D9 plan")

    # 16. Conflicting frame 701/702 claims: candidate doc must not contain bare un-annotated 'frame 702'
    if re.search(r"Hit 2 at frame [`']?702[`']?(?!nd)", cand_text):
        raise ValueError("Contradictory un-annotated frame 702 claim found in candidate_06004280.md")

    # 17. Machine-readable candidate metadata validation (candidate_06004280.json)
    cand_data = json.loads(cand_json_text)
    if cand_data.get("block_start") != "0x06004280" or cand_data.get("block_end") != "0x06004288":
        raise ValueError("Candidate JSON boundaries mismatch")
    if cand_data.get("sha256") != EXPECTED_CANDIDATE_SHA256:
        raise ValueError("Candidate JSON SHA256 mismatch")
    if cand_data.get("block_duration") != 21 or cand_data.get("delay_slot_entry_delta") != 19:
        raise ValueError("Candidate JSON timing mismatch")
    if cand_data.get("source_entry_cycle") != 316309168 or cand_data.get("target_entry_cycle") != 316309189:
        raise ValueError("Candidate JSON entry/target cycles mismatch")
    if cand_data.get("ownership_state") != "CONFIRMED_CODE / EXECUTED":
        raise ValueError("Candidate JSON ownership state mismatch")

    # 18. Reference decode manifest scope validation
    manifest_data = json.loads(decode_manifest_text)
    target_slice = manifest_data.get("target_slice", "")
    if "bb_06004280" not in target_slice and "0x06004280" not in target_slice:
        raise ValueError("reference_decode_manifest.json target_slice excludes bb_06004280 while carrying its vector")

    roles = manifest_data.get("reference_projects", {})
    if roles.get("hardware_manual", {}).get("role") != "ARCHITECTURE_AUTHORITY":
        raise ValueError("Hardware manual must be labeled ARCHITECTURE_AUTHORITY in decode manifest")
    if roles.get("mednafen", {}).get("role") != "BEHAVIORAL_DYNAMIC_ORACLE":
        raise ValueError("Mednafen must be labeled BEHAVIORAL_DYNAMIC_ORACLE in decode manifest")
    if roles.get("catherine", {}).get("role") != "INDEPENDENT_STATIC_DECODER_CROSS_CHECK":
        raise ValueError("Catherine must be labeled INDEPENDENT_STATIC_DECODER_CROSS_CHECK in decode manifest")

    return True


def run_negative_controls(base_plan, base_cand, base_readme, base_cand_json, base_manifest):
    controls = [
        ("corrupt_cand_sha",
         base_plan,
         base_cand.replace(EXPECTED_CANDIDATE_SHA256, "0000000000000000000000000000000000000000000000000000000000000000"),
         base_readme, base_cand_json, base_manifest),
        ("corrupt_plan_sha",
         base_plan.replace(EXPECTED_CANDIDATE_SHA256, "0000000000000000000000000000000000000000000000000000000000000000"),
         base_cand, base_readme, base_cand_json, base_manifest),
        ("missing_start_pc",
         base_plan.replace("0x06004280", "0x00000000"),
         base_cand, base_readme, base_cand_json, base_manifest),
        ("missing_end_pc",
         base_plan.replace("0x06004288", "0x00000000"),
         base_cand, base_readme, base_cand_json, base_manifest),
        ("premature_bounded_proof",
         base_plan + "\nD9 = BOUNDED_PROOF\n",
         base_cand, base_readme, base_cand_json, base_manifest),
        ("missing_jsr_l0_need",
         base_plan.replace("NEEDS_D3_L0_PROOF", "ALREADY_PROVEN"),
         base_cand, base_readme, base_cand_json, base_manifest),
        ("missing_m03_trigger",
         base_plan.replace("D9.4", "D9.X_UNKNOWN"),
         base_cand, base_readme, base_cand_json, base_manifest),
        ("missing_exit_kind",
         base_plan.replace("INDIRECT_CALL", "UNKNOWN_EXIT"),
         base_cand, base_readme, base_cand_json, base_manifest),
        ("timing_arithmetic_mismatch",
         base_plan.replace("BLOCK_DURATION = 21", "BLOCK_DURATION = 19"),
         base_cand, base_readme, base_cand_json, base_manifest),
        ("v09a_leak_in_plan",
         base_plan + "\n(V-09A)\n",
         base_cand, base_readme, base_cand_json, base_manifest),
        ("v09a_leak_in_candidate",
         base_plan,
         base_cand + "\n(V-09A)\n",
         base_readme, base_cand_json, base_manifest),
        ("stale_out_cycles_advanced_19",
         base_plan + "\nout_cycles_advanced = 19\n",
         base_cand, base_readme, base_cand_json, base_manifest),
        ("stale_timing_equation_19",
         base_plan + "\n1 + 2 + 1 + 15 = 19\n",
         base_cand, base_readme, base_cand_json, base_manifest),
        ("stale_exact_timing_prose_19",
         base_plan + "\nexact timing (19 cycles)\n",
         base_cand, base_readme, base_cand_json, base_manifest),
        ("stale_last_observed_cycle_316309187",
         base_plan + '\n"last_observed_cycle": 316309187\n',
         base_cand, base_readme, base_cand_json, base_manifest),
        ("stale_not_confirmed_code_claim",
         base_plan + "\nIt is not promoted to CONFIRMED_CODE until D9.4\n",
         base_cand, base_readme, base_cand_json, base_manifest),
        ("conflicting_frame_claim_cand",
         base_plan,
         base_cand.replace("Hit 2 at frame 701", "Hit 2 at frame 702"),
         base_readme, base_cand_json, base_manifest),
        ("manifest_excludes_bb_06004280",
         base_plan, base_cand, base_readme, base_cand_json,
         base_manifest.replace("and bb_06004280 (0x06004280..0x06004288)", "")),
        ("cand_json_corrupt_duration",
         base_plan, base_cand, base_readme,
         base_cand_json.replace('"block_duration": 21', '"block_duration": 19'),
         base_manifest),
    ]

    print(f"Running {len(controls)} negative controls...")
    for name, p, c, r, j, m in controls:
        caught = False
        try:
            validate_plan_content(p, c, r, j, m)
        except Exception:
            caught = True

        if not caught:
            print(f"FAILED: Negative control '{name}' was not caught!")
            return False
        print(f"  [OK] Negative control caught: {name}")

    return True


def main():
    print("=== D9 Indirect Control-Flow Plan & Artifacts Validator ===")

    for path, name in [
        (PLAN_DOC, "D9 plan doc"),
        (CANDIDATE_DOC, "D9 candidate doc"),
        (README_DOC, "D9 workstream README"),
        (CANDIDATE_JSON, "D9 candidate metadata JSON"),
        (DECODE_MANIFEST_JSON, "D3 reference decode manifest JSON")
    ]:
        if not os.path.exists(path):
            print(f"FAILED: {name} not found at {path}")
            sys.exit(1)

    with open(PLAN_DOC, "r", encoding="utf-8") as f:
        plan_text = f.read()
    with open(CANDIDATE_DOC, "r", encoding="utf-8") as f:
        cand_text = f.read()
    with open(README_DOC, "r", encoding="utf-8") as f:
        readme_text = f.read()
    with open(CANDIDATE_JSON, "r", encoding="utf-8") as f:
        cand_json_text = f.read()
    with open(DECODE_MANIFEST_JSON, "r", encoding="utf-8") as f:
        decode_manifest_text = f.read()

    try:
        validate_plan_content(plan_text, cand_text, readme_text, cand_json_text, decode_manifest_text)
        print("Positive validation: PASS (All D9 plan contracts, candidate metadata, and decode scope valid)")
    except Exception as e:
        print(f"FAILED: Positive validation error: {e}")
        sys.exit(1)

    if not run_negative_controls(plan_text, cand_text, readme_text, cand_json_text, decode_manifest_text):
        print("FAILED: Negative control suite failed")
        sys.exit(1)

    print("ALL D9 PLAN & ARTIFACT VALIDATION TESTS PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
