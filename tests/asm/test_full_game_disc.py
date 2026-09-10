#!/usr/bin/env python3
"""CTest integration test for FULL_ASM_GAME_GATE full Saturn disc verification."""

import os
import subprocess
import sys


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    script = os.path.join(repo_root, "tools", "asm", "verify_full_game_disc.py")
    res = subprocess.run([sys.executable, script], cwd=repo_root)
    return res.returncode


if __name__ == "__main__":
    sys.exit(main())
