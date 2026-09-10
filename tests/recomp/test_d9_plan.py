import hashlib
import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if not os.path.isdir(os.path.join(REPO_ROOT, "docs")):
    REPO_ROOT = os.getcwd()

PLAN_DOC = os.path.join(REPO_ROOT, "docs", "D9_INDIRECT_CONTROL_FLOW_PLAN.md")
CANDIDATE_DOC = os.path.join(REPO_ROOT, "workstreams", "T2-D9-indirect", "candidate_06004280.md")
README_DOC = os.path.join(REPO_ROOT, "workstreams", "T2-D9-indirect", "README.md")

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


def validate_plan_content(plan_text, cand_text, readme_text):
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
    if "copy-on-read" not in plan_text and "dependency descriptors" not in plan_text:
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

    return True


def run_negative_controls(base_plan, base_cand, base_readme):
    controls = [
        ("corrupt_cand_sha",
         base_plan,
         base_cand.replace(EXPECTED_CANDIDATE_SHA256, "0000000000000000000000000000000000000000000000000000000000000000"),
         base_readme),
        ("corrupt_plan_sha",
         base_plan.replace(EXPECTED_CANDIDATE_SHA256, "0000000000000000000000000000000000000000000000000000000000000000"),
         base_cand,
         base_readme),
        ("missing_start_pc",
         base_plan.replace("0x06004280", "0x00000000"),
         base_cand,
         base_readme),
        ("missing_end_pc",
         base_plan.replace("0x06004288", "0x00000000"),
         base_cand,
         base_readme),
        ("premature_bounded_proof",
         base_plan + "\nD9 = BOUNDED_PROOF\n",
         base_cand,
         base_readme),
        ("missing_jsr_l0_need",
         base_plan.replace("NEEDS_D3_L0_PROOF", "ALREADY_PROVEN"),
         base_cand,
         base_readme),
        ("missing_m03_trigger",
         base_plan.replace("D9.4", "D9.X_UNKNOWN"),
         base_cand,
         base_readme),
        ("missing_exit_kind",
         base_plan.replace("INDIRECT_CALL", "UNKNOWN_EXIT"),
         base_cand,
         base_readme),
        ("timing_arithmetic_mismatch",
         base_plan.replace("BLOCK_DURATION = 21", "BLOCK_DURATION = 19"),
         base_cand,
         base_readme),
        ("v09a_leak_in_plan",
         base_plan + "\n(V-09A)\n",
         base_cand,
         base_readme),
        ("v09a_leak_in_candidate",
         base_plan,
         base_cand + "\n(V-09A)\n",
         base_readme),
    ]

    print(f"Running {len(controls)} negative controls...")
    for name, p, c, r in controls:
        caught = False
        try:
            validate_plan_content(p, c, r)
        except Exception:
            caught = True

        if not caught:
            print(f"FAILED: Negative control '{name}' was not caught!")
            return False
        print(f"  [OK] Negative control caught: {name}")

    return True


def main():
    print("=== D9 Indirect Control-Flow Plan Validator ===")

    for path, name in [
        (PLAN_DOC, "D9 plan doc"),
        (CANDIDATE_DOC, "D9 candidate doc"),
        (README_DOC, "D9 workstream README")
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

    try:
        validate_plan_content(plan_text, cand_text, readme_text)
        print("Positive validation: PASS (All D9 plan contracts and candidate hashes valid)")
    except Exception as e:
        print(f"FAILED: Positive validation error: {e}")
        sys.exit(1)

    if not run_negative_controls(plan_text, cand_text, readme_text):
        print("FAILED: Negative control suite failed")
        sys.exit(1)

    print("ALL D9 PLAN VALIDATION TESTS PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
