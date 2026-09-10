import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if not os.path.isdir(os.path.join(REPO_ROOT, "docs")):
    REPO_ROOT = os.getcwd()

CLOSURE_DOC = os.path.join(REPO_ROOT, "docs", "POST_D8_SECOND_PASS_CLOSURE.md")

REQUIRED_METHODS = [
    "M-01", "M-02", "M-03", "M-04", "M-05", "M-06",
    "M-07A", "M-07B", "M-08", "M-09", "M-10"
]

CANONICAL_PINS = {
    "SaturnAutoRE": "4662aad69f95222fe37c5e6b98f2285b1a7e4653",
    "MednafenDebug": "155426661b7ac3152e2c93a98da60ac33002b908",
    "DaytonaCCE": "bf2ea285e0dc699b659c4d2cdd0a59d07f92d276",
    "SaturnRecomp": "26c9715e5493054b8a205aa31d73d8f125fdd8f5",
    "SaturnRecomp_dec_blob": "6a5f7e06606c2dab20e84b5c014c014647be70e4",
    "SaturnRecomp_isa_blob": "709f92437990a2a0fe6b69d34565cea9d432a844",
}

FORBIDDEN_HASHES = [
    "ca88cf23b2c6d7d51944daaa2d41571214041a99"
]

ALLOWED_EVIDENCE_STRENGTH = {"LOW", "MEDIUM", "HIGH", "N/A"}
ALLOWED_WORKFLOW_UTILITY = {"LOW", "MEDIUM", "HIGH", "N/A"}
ALLOWED_DISPOSITIONS = {
    "ADOPT", "ADOPT_PARTIAL", "REJECT", "DEFER",
    "NOT_PRESENT_AT_PIN", "REJECT_MAINTAINED"
}


def clean_enum(val):
    if not val:
        return ""
    cleaned = re.sub(r"[`*]", "", val).strip()
    return cleaned.split()[0].rstrip(";").strip()


def parse_closure(content):
    methods = {}
    current_m = None
    current_lines = []

    for line in content.splitlines():
        m_match = re.match(r"^###\s+(M-\d+[AB]?)\s+.*", line)
        if m_match:
            if current_m:
                methods[current_m] = "\n".join(current_lines)
            current_m = m_match.group(1)
            current_lines = [line]
        elif current_m:
            if line.startswith("## "):
                methods[current_m] = "\n".join(current_lines)
                current_m = None
                current_lines = []
            else:
                current_lines.append(line)

    if current_m:
        methods[current_m] = "\n".join(current_lines)

    return methods


def extract_field(section_text, field_name):
    pattern = rf"-\s+\*\*{re.escape(field_name)}\*\*:\s*(.*)"
    match = re.search(pattern, section_text)
    return match.group(1).strip() if match else None


def validate_closure_text(content, repo_root):
    for f_hash in FORBIDDEN_HASHES:
        if f_hash in content:
            return False, f"Forbidden/stale hash detected in closure: {f_hash}"

    parsed_sections = parse_closure(content)
    found_methods = list(parsed_sections.keys())

    for req in REQUIRED_METHODS:
        count = found_methods.count(req)
        if count == 0:
            return False, f"Missing required method: {req}"
        if count > 1:
            return False, f"Duplicate method section: {req}"

    table_lines = [line for line in content.splitlines() if line.startswith("| **M-")]
    if len(table_lines) != len(REQUIRED_METHODS):
        return False, f"Expected {len(REQUIRED_METHODS)} summary table rows, found {len(table_lines)}"

    for row in table_lines:
        cols = [c.strip() for c in row.split("|")[1:-1]]
        m_id = clean_enum(cols[0])
        strength = clean_enum(cols[4])
        utility = clean_enum(cols[5])
        if strength not in ALLOWED_EVIDENCE_STRENGTH:
            return False, f"Summary table {m_id}: Invalid Evidence Strength enum: '{strength}'"
        if utility not in ALLOWED_WORKFLOW_UTILITY:
            return False, f"Summary table {m_id}: Invalid Workflow Utility enum: '{utility}'"

    for m_id, sec in parsed_sections.items():
        strength_raw = extract_field(sec, "Evidence Strength")
        if not strength_raw:
            return False, f"{m_id}: Missing Evidence Strength"
        strength_val = clean_enum(strength_raw)
        if strength_val not in ALLOWED_EVIDENCE_STRENGTH:
            return False, f"{m_id}: Invalid Evidence Strength enum: '{strength_val}'"

        utility_raw = extract_field(sec, "Workflow Utility")
        if not utility_raw:
            return False, f"{m_id}: Missing Workflow Utility"
        utility_val = clean_enum(utility_raw)
        if utility_val not in ALLOWED_WORKFLOW_UTILITY:
            return False, f"{m_id}: Invalid Workflow Utility enum: '{utility_val}'"

        disp_raw = extract_field(sec, "Final Disposition")
        if not disp_raw:
            return False, f"{m_id}: Missing Final Disposition"
        disp_val = clean_enum(disp_raw)
        if disp_val not in ALLOWED_DISPOSITIONS:
            return False, f"{m_id}: Invalid Final Disposition enum: '{disp_val}'"

        gate = extract_field(sec, "Prerequisite / Future Gate")
        if not gate:
            return False, f"{m_id}: Missing Prerequisite / Future Gate"
        if disp_val == "DEFER":
            if "D" not in gate:
                return False, f"{m_id}: Deferred method must declare an explicit D-milestone gate in: '{gate}'"

        ev_paths_str = extract_field(sec, "Evidence Path")
        if not ev_paths_str:
            return False, f"{m_id}: Missing Evidence Path"
        paths = re.findall(r"`([^`]+)`", ev_paths_str)
        if not paths:
            return False, f"{m_id}: No backticked evidence paths found in: '{ev_paths_str}'"
        for p in paths:
            full_p = os.path.join(repo_root, p)
            if not os.path.isfile(full_p):
                return False, f"{m_id}: Nonexistent evidence path: '{p}' (full: {full_p})"

        if m_id in ("M-01", "M-02", "M-03", "M-04"):
            pin_text = extract_field(sec, "Pinned Artifact / Commit") or ""
            if CANONICAL_PINS["SaturnAutoRE"] not in pin_text:
                return False, f"{m_id}: Missing canonical SaturnAutoRE pin {CANONICAL_PINS['SaturnAutoRE']}"

        if m_id == "M-01":
            pin_text = extract_field(sec, "Pinned Artifact / Commit") or ""
            if re.search(r"SaturnAutoRE`?\s+commit\s+`155426", pin_text):
                return False, "M-01 must not identify Mednafen submodule commit as SaturnAutoRE pin"

        if m_id == "M-05":
            if "Ghidra" in sec or "GDT" in sec:
                return False, "M-05 must not contain invented Ghidra or GDT claims"

    return True, "OK"


def run_negative_controls(base_content, repo_root):
    print("Running negative controls (9 corruption checks)...")
    controls = [
        (
            "wrong_saturnautore_hash",
            lambda c: c.replace(CANONICAL_PINS["SaturnAutoRE"], "ca88cf23b2c6d7d51944daaa2d41571214041a99"),
        ),
        (
            "missing_evidence_file",
            lambda c: c.replace("workstreams/POST-D8-M02-mutation/README.md", "workstreams/nonexistent/README.md"),
        ),
        (
            "invalid_evidence_strength",
            lambda c: c.replace("- **Evidence Strength**: `LOW`", "- **Evidence Strength**: `CONFIRMED`"),
        ),
        (
            "missing_future_gate",
            lambda c: c.replace("Blocked until multi-block candidate/CFG/indirect-control substrate is available at `D9 (Multi-Block Expansion Architecture)`.", "None."),
        ),
        (
            "missing_method_id",
            lambda c: re.sub(r"### M-04[\s\S]*?(?=### M-05)", "", c),
        ),
        (
            "duplicate_method_id",
            lambda c: c.replace("### M-02", "### M-01"),
        ),
        (
            "invalid_disposition",
            lambda c: c.replace("- **Final Disposition**: `ADOPT_PARTIAL`", "- **Final Disposition**: `UNKNOWN_DISP`", 1),
        ),
        (
            "invented_ghidra_in_m05",
            lambda c: c.replace("Module RAM layout and byte identity", "Module RAM layout, Ghidra 11.2.1 types and byte identity"),
        ),
        (
            "m01_mednafen_confusion",
            lambda c: c.replace("`AJBats/SaturnAutoRE` commit `4662aad69f95222fe37c5e6b98f2285b1a7e4653`", "`AJBats/SaturnAutoRE` commit `155426661b7ac3152e2c93a98da60ac33002b908`"),
        ),
    ]

    for name, mutate_fn in controls:
        mutated = mutate_fn(base_content)
        ok, msg = validate_closure_text(mutated, repo_root)
        if ok:
            raise AssertionError(f"Negative control '{name}' FAILED to detect corruption! Validated as OK.")
        print(f"  [OK] Negative control caught: {name} -> {msg}")


def main():
    if not os.path.isfile(CLOSURE_DOC):
        print(f"FAIL: Closure document not found at {CLOSURE_DOC}")
        sys.exit(1)

    with open(CLOSURE_DOC, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"Validating {CLOSURE_DOC}...")
    ok, msg = validate_closure_text(content, REPO_ROOT)
    if not ok:
        print(f"FAIL: Positive closure validation failed: {msg}")
        sys.exit(1)
    print("Positive closure validation: PASS")

    run_negative_controls(content, REPO_ROOT)
    print("ALL POST-D8 CLOSURE AUDIT VALIDATIONS PASSED.")


if __name__ == "__main__":
    main()
