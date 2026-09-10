#!/usr/bin/env python3
"""CTest integration test for SH-2 full TH2.LOW module round-trip verification."""

import os
import subprocess
import sys


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Ensure full TH2.LOW module assembly is generated
    s_path = os.path.join(repo_root, ".private", "asm", "TH2_LOW", "TH2_LOW.s")
    manifest_path = os.path.join(repo_root, "asm", "manifests", "TH2.LOW.json")
    if not os.path.exists(s_path):
        gen_script = os.path.join(repo_root, "tools", "asm", "generate_full_module_asm.py")
        res_gen = subprocess.run([sys.executable, gen_script, "--manifest", manifest_path], cwd=repo_root)
        if res_gen.returncode != 0:
            return res_gen.returncode

    script = os.path.join(repo_root, "tools", "asm", "verify_full_module.py")
    res = subprocess.run([sys.executable, script, "--manifest", manifest_path], cwd=repo_root)
    return res.returncode


if __name__ == "__main__":
    sys.exit(main())
