#!/usr/bin/env python3
"""Validation and fail-closed testing for module manifest schema and partition invariants."""

from typing import Any, Dict, List
import copy
import json
import os
import sys


def validate_manifest(manifest: Dict[str, Any]) -> None:
    """Validate manifest structure, required fields, and partition invariants."""
    required_top = [
        "module", "revision", "module_runtime_base", "module_size",
        "confirmed_code_bytes", "raw_unknown_bytes", "ranges",
        "expected_output_sha256", "assembler_tool_identity",
        "linker_tool_identity", "provenance_identity"
    ]
    for key in required_top:
        if key not in manifest:
            raise ValueError(f"Missing required manifest field: {key}")

    mod_size = manifest["module_size"]
    ranges = manifest["ranges"]
    if not ranges:
        raise ValueError("Ranges list must not be empty")

    expected_off = 0
    code_bytes = 0
    unknown_bytes = 0

    valid_classifications = {"CONFIRMED_CODE", "PROBABLE_CODE", "DATA", "PADDING", "UNKNOWN"}
    valid_representations = {"MNEMONIC_PROVEN", "RAW_CODE_PENDING_DECODE", "RAW_DATA", "RAW_UNKNOWN"}

    for idx, r in enumerate(ranges):
        for req in ["offset_start", "offset_end_exclusive", "runtime_start", "runtime_end_exclusive",
                    "byte_length", "evidence_classification", "assembly_representation"]:
            if req not in r:
                raise ValueError(f"Range {idx} missing required field {req}")

        off_start = r["offset_start"]
        off_end = r["offset_end_exclusive"]
        length = r["byte_length"]
        e_class = r["evidence_classification"]
        a_repr = r["assembly_representation"]

        if e_class not in valid_classifications:
            raise ValueError(f"Range {idx} has invalid evidence_classification: {e_class}")
        if a_repr not in valid_representations:
            raise ValueError(f"Range {idx} has invalid assembly_representation: {a_repr}")

        if off_end <= off_start:
            raise ValueError(f"Range {idx} is inverted or empty: [{off_start}, {off_end})")

        if (off_end - off_start) != length:
            raise ValueError(f"Range {idx} length mismatch: {off_end - off_start} != {length}")

        if off_start != expected_off:
            raise ValueError(f"Range {idx} partition violation: expected {expected_off}, got {off_start}")

        if e_class == "CONFIRMED_CODE":
            code_bytes += length
        elif e_class == "UNKNOWN":
            unknown_bytes += length

        expected_off = off_end

    if expected_off != mod_size:
        raise ValueError(f"Partition does not cover entire module: {expected_off} != {mod_size}")

    if code_bytes != manifest["confirmed_code_bytes"]:
        raise ValueError(f"Confirmed code bytes mismatch: {code_bytes} != {manifest['confirmed_code_bytes']}")

    if unknown_bytes != manifest["raw_unknown_bytes"]:
        raise ValueError(f"Raw unknown bytes mismatch: {unknown_bytes} != {manifest['raw_unknown_bytes']}")


def run_positive_manifest_tests(repo_root: str) -> None:
    """Validate all committed manifests against invariants."""
    manifest_dir = os.path.join(repo_root, "asm", "manifests")
    for name in ["0TH2.BIN.json", "TH2.LOW.json", "SET07.BIN.json", "BGM.BIN.json"]:
        path = os.path.join(manifest_dir, name)
        with open(path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        validate_manifest(manifest)
        print(f"Positive validation passed: {name}")


def run_negative_manifest_tests(repo_root: str) -> None:
    """Verify that schema and partition violations fail closed."""
    path = os.path.join(repo_root, "asm", "manifests", "0TH2.BIN.json")
    with open(path, "r", encoding="utf-8") as f:
        base = json.load(f)

    def assert_fails(mutation_name: str, mut_fn) -> None:
        m = copy.deepcopy(base)
        mut_fn(m)
        try:
            validate_manifest(m)
            raise AssertionError(f"Negative control FAILED: {mutation_name} unexpectedly passed!")
        except (ValueError, AssertionError) as e:
            if "unexpectedly passed" in str(e):
                raise
            print(f"Negative control PASS (failed closed): {mutation_name}")

    # 1. Missing required top-level key
    assert_fails("missing_module_size", lambda m: m.pop("module_size"))
    # 2. Inverted range
    assert_fails("inverted_range", lambda m: m["ranges"][0].update({"offset_start": 20, "offset_end_exclusive": 10}))
    # 3. Partition gap
    assert_fails("partition_gap", lambda m: m["ranges"][1].update({"offset_start": 20}))
    # 4. Partition overlap
    assert_fails("partition_overlap", lambda m: m["ranges"][1].update({"offset_start": 8}))
    # 5. Incomplete module span
    assert_fails("incomplete_span", lambda m: m.update({"module_size": m["module_size"] + 100}))
    # 6. Invalid classification
    assert_fails("invalid_classification", lambda m: m["ranges"][0].update({"evidence_classification": "SPECULATIVE_CODE"}))
    # 7. Invalid representation
    assert_fails("invalid_representation", lambda m: m["ranges"][0].update({"assembly_representation": "EMULATED_INTERPRETER"}))
    # 8. Mismatched code byte count
    assert_fails("mismatched_code_bytes", lambda m: m.update({"confirmed_code_bytes": m["confirmed_code_bytes"] + 2}))
    # 9. Mismatched unknown byte count
    assert_fails("mismatched_unknown_bytes", lambda m: m.update({"raw_unknown_bytes": m["raw_unknown_bytes"] - 2}))


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    print("=== 1. MANIFEST POSITIVE VALIDATION ===")
    run_positive_manifest_tests(repo_root)

    print("\n=== 2. MANIFEST NEGATIVE CONTROLS (FAIL-CLOSED) ===")
    run_negative_manifest_tests(repo_root)

    print("\n=== ALL MANIFEST SCHEMA TESTS PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
