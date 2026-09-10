#!/usr/bin/env python3
"""M-07 SaturnRecomp Reference Corpus Verification and Negative Control Test.

Validates:
1. Integrity and completeness of reference_vectors.json manifest.
2. 6 bb_06004000 overlap vectors (full-field decode cross-check).
3. 14 future-expansion synthetic probe vectors covering unmodeled classes.
4. 8 semantic execution vectors verifying SaturnRecomp transition states.
5. Strict external reproduction mode (--require-external / THOR_M07_REQUIRE_EXTERNAL).
6. Fail-closed negative controls: 18 intentional field corruptions MUST fail.
"""

import copy
import json
import os
import sys

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
        "opcode", "pc", "mnemonic", "saturnrecomp_op", "saturnrecomp_class",
        "uses_rn", "rn", "uses_rm", "rm", "access_size", "load", "store",
        "branch", "conditional", "delay_slot", "indirect", "immediate_used",
        "immediate", "displacement_used", "displacement", "target"
    ]
    for k in required_keys:
        if k not in v:
            return False, f"Missing required key: {k}"

    pc_int = int(v["pc"], 16)
    if pc_int % 2 != 0:
        return False, f"PC not aligned to 2 bytes: {v['pc']}"

    op_cls = v["saturnrecomp_class"]

    if op_cls in ("bf", "bt", "bf/s", "bt/s", "bra"):
        if not v["branch"]:
            return False, f"Instruction class {op_cls} must have branch=True"
        target_int = int(v["target"], 16)
        if target_int == 0:
            return False, f"Branch vector has zero target address: {v['opcode']}"
        if not v["displacement_used"]:
            return False, f"Branch vector must have displacement_used=True: {v['opcode']}"

    if op_cls in ("bf", "bt", "bf/s", "bt/s"):
        if not v["conditional"]:
            return False, f"Instruction class {op_cls} must have conditional=True"

    if op_cls in ("bf/s", "bt/s", "bra"):
        if not v["delay_slot"]:
            return False, f"Instruction class {op_cls} must have delay_slot=True"
    elif op_cls in ("bf", "bt", "nop"):
        if v["delay_slot"]:
            return False, f"Instruction class {op_cls} must have delay_slot=False"

    if op_cls.endswith("@ld") or op_cls.endswith("@pc"):
        if not v["load"]:
            return False, f"{op_cls} must have load=True"
        if v["store"]:
            return False, f"{op_cls} must have store=False"

    if op_cls == "nop":
        if v["load"] or v["store"] or v["branch"] or v["conditional"]:
            return False, "nop cannot have memory or branch flags"

    if v["load"] or v["store"]:
        if v["access_size"] not in (1, 2, 4):
            return False, f"Memory operation has invalid access_size: {v['access_size']}"
    else:
        if v["access_size"] != 0:
            return False, f"Non-memory operation has non-zero access_size: {v['access_size']}"

    if v["immediate_used"]:
        if v.get("opcode") == "0x70FF" and v.get("immediate") != -1:
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
    if not meta.get("saturnrecomp_decoder_blob"):
        return False, "Missing saturnrecomp_decoder_blob"
    if not meta.get("saturnrecomp_isa_blob"):
        return False, "Missing saturnrecomp_isa_blob"

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

    sems = manifest_data.get("semantic_execution_vectors", [])
    if len(sems) < 7:
        return False, f"Expected >= 7 semantic execution vectors, got {len(sems)}"

    for sv in sems:
        if not sv.get("case_name") or not sv.get("expected_output"):
            return False, f"Semantic vector missing case_name or expected_output: {sv}"

    return True, "Manifest valid"


def run_negative_controls(base_manifest):
    print("Running negative controls (18 corruption checks)...")
    corruptions = [
        ("corrupt_schema", lambda m: m.update({"schema_version": "99.9"})),
        ("corrupt_method", lambda m: m.update({"method_id": "M-99"})),
        ("missing_commit", lambda m: m["metadata"].pop("saturnrecomp_pinned_commit")),
        ("missing_decoder_blob", lambda m: m["metadata"].pop("saturnrecomp_decoder_blob")),
        ("missing_isa_blob", lambda m: m["metadata"].pop("saturnrecomp_isa_blob")),
        ("empty_overlap", lambda m: m.update({"bb_06004000_overlap_vectors": []})),
        ("corrupt_target", lambda m: m["future_expansion_probe_vectors"][0].update({"target": "0x00000000"})),
        ("corrupt_branch_flag", lambda m: m["future_expansion_probe_vectors"][0].update({"branch": False})),
        ("corrupt_delay_slot", lambda m: m["future_expansion_probe_vectors"][2].update({"delay_slot": False})),
        ("corrupt_immediate", lambda m: m["future_expansion_probe_vectors"][9].update({"immediate": 255})),
        ("corrupt_access_size", lambda m: m["bb_06004000_overlap_vectors"][0].update({"access_size": 3})),
        ("corrupt_load_flag", lambda m: m["bb_06004000_overlap_vectors"][0].update({"load": False})),
        ("corrupt_store_flag", lambda m: m["bb_06004000_overlap_vectors"][0].update({"store": True})),
        ("corrupt_conditional", lambda m: m["future_expansion_probe_vectors"][0].update({"conditional": False})),
        ("corrupt_displacement_used", lambda m: m["bb_06004000_overlap_vectors"][4].update({"displacement_used": False})),
        ("remove_div1_class", lambda m: m.update({
            "future_expansion_probe_vectors": [
                v for v in m["future_expansion_probe_vectors"] if v["saturnrecomp_class"] != "div1"
            ]
        })),
        ("corrupt_semantic_empty", lambda m: m.update({"semantic_execution_vectors": []})),
        ("corrupt_semantic_missing_expected", lambda m: m["semantic_execution_vectors"][0].pop("expected_output")),
    ]

    for name, mutate_fn in corruptions:
        mutated = copy.deepcopy(base_manifest)
        mutate_fn(mutated)
        ok, msg = validate_manifest(mutated)
        if ok:
            raise AssertionError(f"Negative control '{name}' FAILED to detect corruption! msg: {msg}")
        print(f"  [OK] Negative control caught: {name}")


def run_live_decode_and_semantic_crosschecks(manifest_data, require_external=False):
    if not saturnrecomp_adapter:
        if require_external:
            raise RuntimeError("CRITICAL: saturnrecomp_adapter unavailable in strict mode!")
        print("SaturnRecomp adapter module unavailable; skipping live crosscheck.")
        return

    sr_dir = saturnrecomp_adapter.find_saturnrecomp_dir()
    if not sr_dir:
        if require_external:
            raise RuntimeError("CRITICAL: SaturnRecomp directory not found in strict mode!")
        print("SaturnRecomp directory not found; skipping live crosscheck.")
        return

    print(f"Running live SaturnRecomp crosscheck against {sr_dir}...")
    saturnrecomp_adapter.verify_saturnrecomp_pin(sr_dir)

    all_vectors = manifest_data["bb_06004000_overlap_vectors"] + manifest_data["future_expansion_probe_vectors"]
    disagreements = 0

    # 1. Full-field decode verification
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

        if res.get("conditional_flag") != v["conditional"]:
            print(f"  FAIL {op}: conditional got {res.get('conditional_flag')}, want {v['conditional']}")
            disagreements += 1

        if res.get("delay_slot_flag") != v["delay_slot"]:
            print(f"  FAIL {op}: delay_slot got {res.get('delay_slot_flag')}, want {v['delay_slot']}")
            disagreements += 1

        if res.get("indirect_flag") != v["indirect"]:
            print(f"  FAIL {op}: indirect got {res.get('indirect_flag')}, want {v['indirect']}")
            disagreements += 1

        if res.get("load_flag") != v["load"]:
            print(f"  FAIL {op}: load got {res.get('load_flag')}, want {v['load']}")
            disagreements += 1

        if res.get("store_flag") != v["store"]:
            print(f"  FAIL {op}: store got {res.get('store_flag')}, want {v['store']}")
            disagreements += 1

        if res.get("access_size") != v["access_size"]:
            print(f"  FAIL {op}: access_size got {res.get('access_size')}, want {v['access_size']}")
            disagreements += 1

        if v["uses_rn"] and res.get("rn") != v["rn"]:
            print(f"  FAIL {op}: rn got {res.get('rn')}, want {v['rn']}")
            disagreements += 1

        if v["uses_rm"] and res.get("rm") != v["rm"]:
            print(f"  FAIL {op}: rm got {res.get('rm')}, want {v['rm']}")
            disagreements += 1

        if v["immediate_used"] and res.get("immediate") != v["immediate"]:
            print(f"  FAIL {op}: immediate got {res.get('immediate')}, want {v['immediate']}")
            disagreements += 1

        if v["displacement_used"] and res.get("displacement") != v["displacement"]:
            print(f"  FAIL {op}: displacement got {res.get('displacement')}, want {v['displacement']}")
            disagreements += 1

        if (v["branch"] or v.get("target") != "0x00000000") and res.get("target") != v["target"]:
            print(f"  FAIL {op}: target got {res.get('target')}, want {v['target']}")
            disagreements += 1

    if disagreements != 0:
        raise AssertionError(f"Live decode crosscheck had {disagreements} disagreements!")
    print(f"  [PASS] Live decode crosscheck: {len(all_vectors)} vectors, 0 disagreements.")

    # 2. Semantic execution verification
    sem_vectors = manifest_data.get("semantic_execution_vectors", [])
    sem_disagreements = 0
    for sv in sem_vectors:
        case_name = sv["case_name"]
        expected = sv["expected_output"]
        res = saturnrecomp_adapter.run_semantic_case(case_name, sr_dir)

        if "t_bit" in expected and res.get("t_bit") != expected["t_bit"]:
            print(f"  FAIL semantic {case_name}: t_bit got {res.get('t_bit')}, want {expected['t_bit']}")
            sem_disagreements += 1

        if "pc" in expected and res.get("pc") != expected["pc"]:
            print(f"  FAIL semantic {case_name}: pc got {res.get('pc')}, want {expected['pc']}")
            sem_disagreements += 1

        for reg in ("r0", "r1", "r3"):
            if reg in expected and res.get(reg) != expected[reg]:
                print(f"  FAIL semantic {case_name}: {reg} got {res.get(reg)}, want {expected[reg]}")
                sem_disagreements += 1

    if sem_disagreements != 0:
        raise AssertionError(f"Live semantic crosscheck had {sem_disagreements} disagreements!")
    print(f"  [PASS] Live semantic crosscheck: {len(sem_vectors)} cases, 0 disagreements.")


def main():
    require_external = ("--require-external" in sys.argv) or (os.environ.get("THOR_M07_REQUIRE_EXTERNAL") == "1")

    manifest_path = get_manifest_path()
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    # 1. Positive manifest validation
    ok, msg = validate_manifest(manifest_data)
    if not ok:
        print(f"Manifest validation failed: {msg}", file=sys.stderr)
        sys.exit(1)
    print(f"Positive manifest validation: PASS ({msg})")

    # 2. Negative controls (18 checks)
    run_negative_controls(manifest_data)

    # 3. Live decode & semantic crosschecks
    run_live_decode_and_semantic_crosschecks(manifest_data, require_external=require_external)

    print("ALL M-07 REFERENCE TESTS PASSED.")


if __name__ == "__main__":
    main()
