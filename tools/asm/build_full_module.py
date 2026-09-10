#!/usr/bin/env python3
"""SH-2 Full Module Assembly & Link Round-Trip Pipeline.

Assembles mechanically generated assembly container using pinned GNU toolchain,
links at Saturn VMA with linker script assertions, inspects relocations,
extracts raw bytes, and proves byte-exact parity and dual-build determinism.
"""

from typing import Dict, List, Optional, Tuple
import argparse
import hashlib
import json
import os
import subprocess
import sys

from assemble_roundtrip import (
    PINNED_TOOLCHAIN,
    Toolchain,
    assemble_and_link,
    find_pinned_toolchain,
    verify_toolchain_hashes,
)


def get_module_stem(module_name: str) -> str:
    """Return filesystem-friendly identifier for module."""
    if module_name == "0TH2.BIN":
        return "0TH2"
    return module_name.replace(".", "_")


def execute_build(
    repo_root: str,
    s_path: str,
    ld_path: str,
    stem: str,
    build_label: str = "1",
) -> Tuple[bytes, str, str]:
    """Execute a single build and return bytes and relocation reports."""
    out_dir = os.path.join(repo_root, "out", f"asm_{stem}_build_{build_label}")
    raw_bytes, rel_before, rel_after, _ = assemble_and_link(s_path, ld_path, out_dir)
    return raw_bytes, rel_before, rel_after


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and verify full assembly module")
    parser.add_argument("--manifest", default=None, help="Path to module manifest JSON")
    parser.add_argument("--repo-root", default=None, help="Root repository directory")
    args = parser.parse_args()

    repo_root = args.repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    manifest_path = args.manifest or os.path.join(repo_root, "asm", "manifests", "0TH2.BIN.json")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    module_name = manifest["module"]
    stem = get_module_stem(module_name)
    s_path = os.path.join(repo_root, ".private", "asm", stem, f"{stem}.s")
    ld_path = os.path.join(repo_root, "asm", "linker", f"{stem}.ld")

    if not os.path.exists(s_path) or not os.path.exists(ld_path):
        print(f"Assembly source not found at {s_path}. Running generator first...")
        gen_script = os.path.join(repo_root, "tools", "asm", "generate_full_module_asm.py")
        res_gen = subprocess.run([sys.executable, gen_script, "--manifest", manifest_path], cwd=repo_root)
        if res_gen.returncode != 0:
            return res_gen.returncode

    print(f"=== SH-2 FULL MODULE ROUND-TRIP BUILD: {module_name} ===")
    tc = find_pinned_toolchain()
    print("Verifying pinned GNU toolchain integrity...")
    hashes = verify_toolchain_hashes(tc)
    for tool, h in hashes.items():
        print(f"  {tool}: {h} [MATCH]")

    print(f"\nExecuting Build 1 (out/asm_{stem}_build_1)...")
    bytes_1, rel_before_1, rel_after_1 = execute_build(repo_root, s_path, ld_path, stem, "1")
    sha_1 = hashlib.sha256(bytes_1).hexdigest()
    print(f"  Length: {len(bytes_1)} bytes")
    print(f"  SHA256: {sha_1}")

    expected_sha = manifest["expected_output_sha256"]
    expected_size = manifest["module_size"]

    if len(bytes_1) != expected_size:
        print(f"ERROR: Size mismatch: {len(bytes_1)} != {expected_size}")
        return 1

    if sha_1 != expected_sha:
        print(f"ERROR: SHA mismatch: {sha_1} != {expected_sha}")
        return 1
    print(f"  Byte-Exact Match: PASS ({len(bytes_1)} / {expected_size} bytes match original {module_name})")

    print(f"\nExecuting Build 2 (out/asm_{stem}_build_2) for determinism check...")
    bytes_2, _, _ = execute_build(repo_root, s_path, ld_path, stem, "2")
    sha_2 = hashlib.sha256(bytes_2).hexdigest()

    if bytes_1 != bytes_2:
        print("ERROR: Deterministic build check failed!")
        return 1
    print("  Deterministic Build: PASS (0 differing bytes between independent runs)")

    print("\nRelocation Audit:")
    has_rel = "RELOCATION RECORDS FOR" in rel_after_1
    print(f"  Final ELF Relocations: {'NONE (Clean)' if not has_rel else 'ERROR: RELOCATIONS REMAIN'}")
    if has_rel:
        print(rel_after_1)
        return 1

    print(f"\n=== FULL MODULE BUILD: SUCCESS ({module_name}) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
