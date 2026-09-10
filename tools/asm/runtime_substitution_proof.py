#!/usr/bin/env python3
"""Bounded Runtime Substitution Proof.

Runs clean Mednafen oracle (commit 155426661b7ac3152e2c93a98da60ac33002b908)
in pure interpreter mode (native_mode 0) comparing ORIGINAL cold boot vs
ASM_REBUILT substituted cold boot at architectural checkpoints.
"""

from typing import Any, Dict, List, Optional, Tuple
import json
import os
import shutil
import subprocess
import sys
import time

CUE_ORIGINAL = "The_Story_of_Thor_2_[RUS]_(NTSC).cue"
BIN_ORIGINAL = "The_Story_of_Thor_2_[RUS]_(NTSC).bin"
BIOS_PATH = "mpr-17933.bin"

CHECKPOINTS = [
    ("06004000", "entry_06004000"),
    ("06004012", "branch_target_06004012"),
    ("06004280", "checkpoint_06004280"),
]

EXPECTED_ENTRY_CYCLE = 305462360
EXPECTED_TARGET_CYCLE = 305462387
EXPECTED_DURATION = 27

REG_NAMES = [
    "R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7",
    "R8", "R9", "R10", "R11", "R12", "R13", "R14", "R15",
    "PC", "SR", "PR", "GBR", "VBR", "MACH", "MACL"
]


def to_wsl_path(win_path: str) -> str:
    p = os.path.abspath(win_path).replace("\\", "/")
    if len(p) >= 2 and p[1] == ":":
        drive = p[0].lower()
        return f"/mnt/{drive}{p[2:]}"
    return p


def create_substituted_disc(
    repo_root: str,
    scratch_dir: str,
    reassembled_bytes: bytes,
) -> Tuple[str, str]:
    """Create a temporary private disc image with reassembled bytes spliced at LBA 24."""
    os.makedirs(scratch_dir, exist_ok=True)
    orig_bin_path = os.path.join(repo_root, BIN_ORIGINAL)
    rebuilt_bin_path = os.path.join(scratch_dir, "thor2_rebuilt.bin")
    rebuilt_cue_path = os.path.join(scratch_dir, "thor2_rebuilt.cue")

    # Splicing 12 bytes at LBA 24, user data offset +16 inside sector
    splice_offset = 24 * 2352 + 16

    print(f"Creating private substituted disc image in {scratch_dir}...")
    shutil.copyfile(orig_bin_path, rebuilt_bin_path)

    with open(rebuilt_bin_path, "r+b") as f:
        f.seek(splice_offset)
        f.write(reassembled_bytes)

    # Create matching CUE pointing to rebuilt bin
    cue_content = (
        f'FILE "thor2_rebuilt.bin" BINARY\n'
        f'  TRACK 01 MODE1/2352\n'
        f'    INDEX 01 00:00:00\n'
    )
    with open(rebuilt_cue_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(cue_content)

    return rebuilt_cue_path, rebuilt_bin_path


def run_mednafen_session(
    cue_path: str,
    work_dir: str,
    label: str,
) -> Dict[str, Any]:
    """Run an automated cold-boot session in Mednafen via WSL python bot."""
    os.makedirs(work_dir, exist_ok=True)
    home_dir = os.path.join(work_dir, "home")
    ipc_dir = os.path.join(work_dir, "ipc")
    os.makedirs(os.path.join(home_dir, "firmware"), exist_ok=True)
    os.makedirs(ipc_dir, exist_ok=True)

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    bios_src = os.path.join(repo_root, BIOS_PATH)
    shutil.copy2(bios_src, os.path.join(home_dir, "firmware", "mpr-17933.bin"))
    shutil.copy2(bios_src, os.path.join(home_dir, "mpr-17933.bin"))

    cfg_content = (
        "ss.bios_na_eu mpr-17933.bin\n"
        "ss.region_autodetect 1\n"
        "ss.region_default jp\n"
        "ss.cart backup\n"
    )
    with open(os.path.join(home_dir, "mednafen.cfg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(cfg_content)

    cue_wsl = to_wsl_path(cue_path)
    home_wsl = to_wsl_path(home_dir)
    ipc_wsl = to_wsl_path(ipc_dir)
    out_json_wsl = f"{ipc_wsl}/results.json"

    # Inline runner script executed under WSL
    wsl_script = f"""
import sys, os, json
sys.path.insert(0, '/mnt/e/Github/SaturnAutoRE/mednafen')
from mednafen_bot import MednafenBot

bot = MednafenBot(ipc_dir='{ipc_wsl}', cue_path='{cue_wsl}', show=False, sound=False, home_dir='{home_wsl}')
if not bot.start(timeout=45):
    print("FATAL: Failed to start Mednafen")
    sys.exit(1)

bot.send_and_wait("deterministic", "ok deterministic", timeout=10)
bot.send_and_wait("native_mode 0", "ok native_mode", timeout=10)
bot.send_and_wait("native_mask 0x00000000", "ok native_mask", timeout=10)

checkpoints = {CHECKPOINTS!r}
events = {{}}

for addr, cp_label in checkpoints:
    bot.send_and_wait(f"breakpoint {{addr}} once", "ok breakpoint", timeout=10)
    bot.send("run")
    ack = bot.wait_ack(["break pc=", "break"], timeout=60)
    bot.send("dump_regs")
    regs_ack = bot.wait_ack("R0=", timeout=10)
    
    # parse registers
    regs = {{}}
    tokens = regs_ack.replace("regs", "").split()
    for tok in tokens:
        if "=" in tok:
            k, v = tok.split("=", 1)
            regs[k] = v
            
    cycle = int(regs.get("cycle", "0"))
    pc = regs.get("PC", "")
    events[cp_label] = {{
        "checkpoint": cp_label,
        "address": f"0x{{addr}}",
        "pc": f"0x{{pc}}",
        "cycle": cycle,
        "regs": regs
    }}

bot.send("quit")

with open('{out_json_wsl}', 'w') as f:
    json.dump(events, f, indent=2)
"""

    script_path = os.path.join(work_dir, "run_wsl.py")
    with open(script_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(wsl_script)

    script_wsl = to_wsl_path(script_path)
    res = subprocess.run(["wsl", "python3", script_wsl], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"WSL Mednafen run failed for {label}:\n{res.stderr}\n{res.stdout}")

    results_file = os.path.join(ipc_dir, "results.json")
    with open(results_file, "r", encoding="utf-8") as f:
        return json.load(f)


def execute_runtime_parity_proof(
    repo_root: str,
    reassembled_bytes: bytes,
) -> Dict[str, Any]:
    """Execute both cold boot runs and verify complete parity."""
    scratch_root = os.path.join(repo_root, "scratch", "runtime_proof")
    if os.path.exists(scratch_root):
        shutil.rmtree(scratch_root, ignore_errors=True)
    os.makedirs(scratch_root, exist_ok=True)

    try:
        # 1. Run ORIGINAL
        print("\n--- Running Mednafen Cold Boot A: ORIGINAL (clean disc) ---")
        orig_cue = os.path.join(repo_root, CUE_ORIGINAL)
        dir_a = os.path.join(scratch_root, "run_a_original")
        results_a = run_mednafen_session(orig_cue, dir_a, "ORIGINAL")

        # 2. Run ASM_REBUILT
        print("\n--- Running Mednafen Cold Boot B: ASM_REBUILT (substituted slice) ---")
        rebuilt_cue, rebuilt_bin = create_substituted_disc(repo_root, scratch_root, reassembled_bytes)
        dir_b = os.path.join(scratch_root, "run_b_rebuilt")
        results_b = run_mednafen_session(rebuilt_cue, dir_b, "ASM_REBUILT")

        # 3. Compare Parity
        print("\n--- Analyzing Runtime Parity ---")
        comparison = {}
        all_match = True

        for _, label in CHECKPOINTS:
            ev_a = results_a[label]
            ev_b = results_b[label]
            
            cycle_a = ev_a["cycle"]
            cycle_b = ev_b["cycle"]
            cycle_match = (cycle_a == cycle_b)
            
            regs_diff = {}
            for r in REG_NAMES:
                val_a = ev_a["regs"].get(r)
                val_b = ev_b["regs"].get(r)
                if val_a != val_b:
                    regs_diff[r] = {"original": val_a, "rebuilt": val_b}

            reg_match = (len(regs_diff) == 0)
            if not (cycle_match and reg_match):
                all_match = False

            comparison[label] = {
                "address": ev_a["address"],
                "cycle_original": cycle_a,
                "cycle_rebuilt": cycle_b,
                "cycle_match": cycle_match,
                "regs_match": reg_match,
                "differing_regs": regs_diff,
                "regs": ev_b["regs"],
            }
            print(f"  [{label}] Cycle A: {cycle_a} | Cycle B: {cycle_b} | Regs Match: {reg_match}")

        # Check timing invariants
        c_entry = results_b["entry_06004000"]["cycle"]
        c_target = results_b["branch_target_06004012"]["cycle"]
        duration = c_target - c_entry
        print(f"\nBounded Timing Verification:")
        print(f"  Entry 0x06004000 cycle: {c_entry} (expected: {EXPECTED_ENTRY_CYCLE})")
        print(f"  Target 0x06004012 cycle: {c_target} (expected: {EXPECTED_TARGET_CYCLE})")
        print(f"  Block Duration:          {duration} (expected: {EXPECTED_DURATION})")

        timing_ok = (c_entry == EXPECTED_ENTRY_CYCLE and c_target == EXPECTED_TARGET_CYCLE and duration == EXPECTED_DURATION)

        return {
            "all_match": all_match,
            "timing_ok": timing_ok,
            "entry_cycle": c_entry,
            "target_cycle": c_target,
            "duration": duration,
            "comparison": comparison,
            "results_original": results_a,
            "results_rebuilt": results_b,
        }

    finally:
        # Legal hygiene: wipe private substituted binary
        if os.path.exists(scratch_root):
            shutil.rmtree(scratch_root, ignore_errors=True)
            print("Private substituted disc image cleaned up.")


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    bin_path = os.path.join(repo_root, "out", "asm_build_1", "block.bin")
    if not os.path.exists(bin_path):
        print(f"ERROR: Assembled binary not found at {bin_path}. Run assemble_roundtrip.py first.")
        return 1

    with open(bin_path, "rb") as f:
        rebuilt_bytes = f.read()

    proof_data = execute_runtime_parity_proof(repo_root, rebuilt_bytes)

    if not proof_data["all_match"]:
        print("ERROR: Runtime register/cycle divergence detected!")
        return 1
    if not proof_data["timing_ok"]:
        print("ERROR: Runtime timing invariant violation!")
        return 1

    print("\n=== BOUNDED RUNTIME SUBSTITUTION PROOF: PASS ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
