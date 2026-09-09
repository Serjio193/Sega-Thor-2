#!/usr/bin/env python3
"""M-07 SaturnRecomp Reference Corpus Verification and Negative Control Test.

Validates:
1. Integrity and completeness of reference_vectors.json manifest.
2. 6 bb_06004000 overlap vectors (zero disagreements across references).
3. 14 future-expansion synthetic probe vectors covering unmodeled classes.
4. Live SaturnRecomp decode cross-check (if SaturnRecomp repo available).
5. Fail-closed negative controls: intentional field corruptions MUST fail.
"""

import copy
import json
import os
import sys

# Add tools/recomp to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "tools", "recomp"))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

try:
    import saturnrecomp_adapter
except ImportError:
    saturnrecomp_adapter = None


def get_manifest_path():
    candidates = [
        os.path.join(
            SCRIPT_DIR,
            "..",
            "..",
            "workstreams",
            "POST-D8-M07-saturnrecomp",
            "reference_vectors.json",
        ),
        os.path.abspath(
            os.path.join(
                os.getcwd(),
                "workstreams",
                "POST-D8-M07-saturnrecomp",
                "reference_vectors.json",
            )
        ),
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    raise FileNotFoundError("Could not find reference_vectors.json")


def validate_vector(v):
    required_keys = [
        "opcode",
        "pc",
        "mnemonic",
        "saturnrecomp_op",
        "saturnrecomp_class",
        "rn",
        "rm",
        "access_size",
        "load",
        "store",
        "branch",
        "conditional",
        "delay_slot",
        "displacement",
        "target",
    ]
    for k in required_keys:
        if k not in v:
            return False, f"Missing required key: {k}"

    pc_int = int(v["pc"], 16)
    if pc_int % 2 != 0:
        return False, f"PC not aligned to 2 bytes: {v['pc']}"

    op_cls = v["saturnrecomp_class"]

    # Branch consistency
    if op_cls in ("bf", "bt", "bf/s", "bt/s", "bra"):
        if not v["branch"]:
            return False, f"Instruction class {op_cls} must have branch=True"
        target_int = int(v["target"], 16)
        if target_int == 0:
            return False, f"Branch vector has zero target address: {v['opcode']}"

    # Conditional consistency
    if op_cls in ("bf", "bt", "bf/s", "bt/s"):
        if not v["conditional"]:
            return False, f"Instruction class {op_cls} must have conditional=True"

    # Delay slot consistency
    if op_cls in ("bf/s", "bt/s", "bra"):
        if not v["delay_slot"]:
            return False, f"Instruction class {op_cls} must have delay_slot=True"
    elif op_cls in ("bf", "bt", "nop"):
        if v["delay_slot"]:
            return False, f"Instruction class {op_cls} must have delay_slot=False"

    # Immediate sign extension consistency for ADD #imm
    if op_cls == "add#":
        if v.get("immediate") != -1 and v.get("opcode") == "0x70FF":
            return False, f"0x70FF must have sign-extended immediate -1, got {v.get('immediate')}"

    return True, "OK"


def validate_manifest(manifest_data):
    if manifest_data.get("schema_version") != "1.0":
        return False, "Invalid schema_version"
    if manifest_data.get("method_id") != "M-07":
        return False, "Invalid method_id"

    meta = manifest_data.get("metadata", {})
    if not meta.get("saturnrecomp_pinned_commit"):
        return False, "Missing saturnrecomp_pinned_commit"

    overlap = manifest_data.get("bb_06004000_overlap_vectors", [])
    if len(overlap) != 6:
        return False, f"Expected 6 overlap vectors, got {len(overlap)}"

    for v in overlap:
        ok, msg = validate_vector(v)
        if not ok:
            return False, f"Overlap vector {v.get('opcode')} failed: {msg}"

    probes = manifest_data.get("future_expansion_probe_vectors", [])
    if len(probes) < 10:
        return False, f"Expected >= 10 probe vectors, got {len(probes)}"

    for v in probes:
        ok, msg = validate_vector(v)
        if not ok:
            return False, f"Probe vector {v.get('opcode')} failed: {msg}"

    classes_found = {v["saturnrecomp_class"] for v in probes}
    required_classes = [
        "bf", "bt", "bf/s", "bt/s", "cmp/ge", "shll", "shar", "add#", "rotcl", "div1", "mac.w"
    ]
    for rc in required_classes:
        if rc not in classes_found:
            return False, f"Missing required probe opcode class: {rc}"

    return True, "Manifest valid"


def run_negative_controls(base_manifest):
    print("Running negative controls...")
    corruptions = [
        ("corrupt_schema", lambda m: m.update({"schema_version": "99.9"})),
        ("corrupt_method", lambda m: m.update({"method_id": "M-99"})),
        ("missing_commit", lambda m: m["metadata"].pop("saturnrecomp_pinned_commit")),
        ("empty_overlap", lambda m: m.update({"bb_06004000_overlap_vectors": []})),
        ("corrupt_target", lambda m: m["future_expansion_probe_vectors"][0].update({"target": "0x00000000"})),
        ("corrupt_branch_flag", lambda m: m["future_expansion_probe_vectors"][0].update({"branch": False})),
        ("corrupt_delay_slot", lambda m: m["future_expansion_probe_vectors"][2].update({"delay_slot": False})),
        ("corrupt_immediate", lambda m: m["future_expansion_probe_vectors"][9].update({"immediate": 255})),
        ("remove_div1_class", lambda m: m.update({
            "future_expansion_probe_vectors": [
                v for v in m["future_expansion_probe_vectors"] if v["saturnrecomp_class"] != "div1"
            ]
        })),
    ]

    for name, mutate_fn in corruptions:
        mutated = copy.deepcopy(base_manifest)
        mutate_fn(mutated)
        ok, msg = validate_manifest(mutated)
        if ok:
            raise AssertionError(f"Negative control '{name}' FAILED to detect corruption! msg: {msg}")
        print(f"  [OK] Negative control caught: {name} ({msg})")


def run_live_crosscheck_if_available(manifest_data):
    if not saturnrecomp_adapter:
        print("SaturnRecomp adapter module unavailable; skipping live decode crosscheck.")
        return
    sr_dir = saturnrecomp_adapter.find_saturnrecomp_dir()
    if not sr_dir:
        print("SaturnRecomp directory not found; skipping live decode crosscheck.")
        return

    print(f"Running live SaturnRecomp crosscheck against {sr_dir}...")
    all_vectors = manifest_data["bb_06004000_overlap_vectors"] + manifest_data["future_expansion_probe_vectors"]
    disagreements = 0

    for v in all_vectors:
        op = v["opcode"]
        pc = v["pc"]
        res = saturnrecomp_adapter.decode_opcode(op, pc, sr_dir)

        if not res.get("valid"):
            print(f"  FAIL: Opcode {op} reported invalid by SaturnRecomp")
            disagreements += 1
            continue

        if res.get("opcode_class") != v["saturnrecomp_class"]:
            print(f"  FAIL {op}: class got {res.get('opcode_class')}, want {v['saturnrecomp_class']}")
            disagreements += 1

        if res.get("branch_flag") != v["branch"]:
            print(f"  FAIL {op}: branch got {res.get('branch_flag')}, want {v['branch']}")
            disagreements += 1

        if res.get("delay_slot_flag") != v["delay_slot"]:
            print(f"  FAIL {op}: delay_slot got {res.get('delay_slot_flag')}, want {v['delay_slot']}")
            disagreements += 1

        if v["branch"] and res.get("target") != v["target"]:
            print(f"  FAIL {op}: target got {res.get('target')}, want {v['target']}")
            disagreements += 1

    if disagreements != 0:
        raise AssertionError(f"Live decode crosscheck had {disagreements} disagreements!")
    print(f"  Live decode crosscheck: {len(all_vectors)} vectors, 0 disagreements. PASS.")


def main():
    manifest_path = get_manifest_path()
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # 1. Positive validation
    ok, msg = validate_manifest(manifest_data)
    if not ok:
        print(f"Manifest validation failed: {msg}", file=sys.stderr)
        sys.exit(1)
    print(f"Positive manifest validation: PASS ({msg})")

    # 2. Negative controls
    run_negative_controls(manifest_data)

    # 3. Live cross-check if external repo is cloned
    run_live_crosscheck_if_available(manifest_data)

    print("ALL M-07 REFERENCE TESTS PASSED.")


if __name__ == "__main__":
    main()
