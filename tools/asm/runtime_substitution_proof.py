#!/usr/bin/env python3
"""Occurrence-Aware Bounded Runtime Substitution Proof.

Runs clean Mednafen oracle (commit 155426661b7ac3152e2c93a98da60ac33002b908)
in pure interpreter mode (native_mode 0) comparing ORIGINAL cold boot vs
ASM_REBUILT substituted cold boot at architectural checkpoints.
"""

from typing import Any, Dict, List, Optional, Tuple
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

PINNED_SATURNAUTORE_COMMIT = "4662aad69f95222fe37c5e6b98f2285b1a7e4653"
PINNED_MEDNAFEN_COMMIT = "155426661b7ac3152e2c93a98da60ac33002b908"
PINNED_MEDNAFEN_BIN_SHA256 = "4d877df4a36b9e29a77e00c51f33ca45178d0756a57cb8ec976c8e26928d04c6"
VALID_MEDNAFEN_BIN_HASHES = {
    PINNED_MEDNAFEN_BIN_SHA256,
    "861f03f36882ac2cff9334e3bdb54c8a29991f711ff81cb1132183ade9828c49",
}
CANONICAL_DISC_SHA = "fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8"
CANONICAL_BIOS_SHA = "96e106f740ab448cf89f0dd49dfbac7fe5391cb6bd6e14ad5e3061c13330266f"

DEFAULT_CUE = "The_Story_of_Thor_2_[RUS]_(NTSC).cue"
DEFAULT_BIN = "The_Story_of_Thor_2_[RUS]_(NTSC).bin"
DEFAULT_BIOS = "mpr-17933.bin"

CHECKPOINTS_SPEC = [
    ("06004000", "entry_06004000", 0, 305462360, None),
    ("06004012", "branch_target_06004012", 0, 305462387, None),
    ("06004280", "checkpoint_06004280_occ0", 0, 307090585, None),
    ("06004280", "checkpoint_06004280_occ1", 1, 316309168, None),
    ("0600A0F8", "checkpoint_0600A0F8_load_th2_low", 2, 316309189, "0600428A"),
    ("002E9910", "checkpoint_002E9910_th2_low_exec", 0, 387459915, "060042E4"),
]

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


def verify_environment_integrity(repo_root: str) -> None:
    """Verify git commits and binary hashes of emulator and assets."""
    saturn_dir = os.environ.get("THOR_SATURNAUTORE_DIR", os.path.join(repo_root, "..", "SaturnAutoRE"))
    mednafen_dir = os.environ.get("THOR_MEDNAFEN_DIR", os.path.join(saturn_dir, "mednafen"))
    disc_bin = os.environ.get("THOR_DISC_IMAGE", os.path.join(repo_root, DEFAULT_BIN))
    bios_path = os.environ.get("THOR_BIOS_IMAGE", os.path.join(repo_root, DEFAULT_BIOS))

    # 1. Disc hash
    with open(disc_bin, "rb") as f:
        disc_sha = hashlib.sha256(f.read()).hexdigest()
    assert disc_sha == CANONICAL_DISC_SHA, f"Disc SHA mismatch: {disc_sha} != {CANONICAL_DISC_SHA}"

    # 2. BIOS hash
    with open(bios_path, "rb") as f:
        bios_sha = hashlib.sha256(f.read()).hexdigest()
    assert bios_sha == CANONICAL_BIOS_SHA, f"BIOS SHA mismatch: {bios_sha} != {CANONICAL_BIOS_SHA}"

    # 3. SaturnAutoRE commit
    res_sat = subprocess.run(["git", "rev-parse", "HEAD"], cwd=saturn_dir, capture_output=True, text=True)
    assert res_sat.returncode == 0 and res_sat.stdout.strip() == PINNED_SATURNAUTORE_COMMIT, \
        f"SaturnAutoRE commit mismatch: {res_sat.stdout.strip()}"

    # 4. Mednafen commit
    res_med = subprocess.run(["git", "rev-parse", "HEAD"], cwd=mednafen_dir, capture_output=True, text=True)
    assert res_med.returncode == 0 and res_med.stdout.strip() == PINNED_MEDNAFEN_COMMIT, \
        f"Mednafen commit mismatch: {res_med.stdout.strip()}"

    # 5. Mednafen binary hash
    med_bin = os.path.join(mednafen_dir, "src", "mednafen.exe")
    if not os.path.exists(med_bin):
        med_bin = os.path.join(mednafen_dir, "src", "mednafen")
    with open(med_bin, "rb") as f:
        med_sha = hashlib.sha256(f.read()).hexdigest()
    assert med_sha in VALID_MEDNAFEN_BIN_HASHES, f"Mednafen binary SHA mismatch: {med_sha}"


def create_substituted_disc(
    repo_root: str,
    scratch_dir: str,
    manifest: Dict[str, Any],
    reassembled_bytes: bytes,
) -> Tuple[str, str]:
    """Create temporary private disc image with reassembled module spliced."""
    os.makedirs(scratch_dir, exist_ok=True)
    orig_bin_path = os.environ.get("THOR_DISC_IMAGE", os.path.join(repo_root, DEFAULT_BIN))
    rebuilt_bin_path = os.path.join(scratch_dir, "thor2_rebuilt.bin")
    rebuilt_cue_path = os.path.join(scratch_dir, "thor2_rebuilt.cue")

    shutil.copyfile(orig_bin_path, rebuilt_bin_path)

    iso_lba = manifest["iso_sector_start"]
    expected_size = manifest["module_size"]
    num_sectors = (expected_size + 2047) // 2048

    with open(rebuilt_bin_path, "r+b") as f:
        for sec_idx in range(num_sectors):
            chunk = reassembled_bytes[sec_idx * 2048 : (sec_idx + 1) * 2048]
            sec_offset = (iso_lba + sec_idx) * 2352 + 16
            f.seek(sec_offset)
            f.write(chunk)

    cue_content = (
        'FILE "thor2_rebuilt.bin" BINARY\n'
        '  TRACK 01 MODE1/2352\n'
        '    INDEX 01 00:00:00\n'
    )
    with open(rebuilt_cue_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(cue_content)

    return rebuilt_cue_path, rebuilt_bin_path


def run_mednafen_session(
    repo_root: str,
    cue_path: str,
    work_dir: str,
    label: str,
) -> Dict[str, Any]:
    """Run automated cold-boot session in Mednafen via WSL python bot."""
    os.makedirs(work_dir, exist_ok=True)
    home_dir = os.path.join(work_dir, "home")
    ipc_dir = os.path.join(work_dir, "ipc")
    os.makedirs(os.path.join(home_dir, "firmware"), exist_ok=True)
    os.makedirs(ipc_dir, exist_ok=True)

    bios_src = os.environ.get("THOR_BIOS_IMAGE", os.path.join(repo_root, DEFAULT_BIOS))
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

    saturn_dir = os.environ.get("THOR_SATURNAUTORE_DIR", os.path.join(repo_root, "..", "SaturnAutoRE"))
    saturn_med_wsl = to_wsl_path(os.path.join(saturn_dir, "mednafen"))

    wsl_script = f"""
import sys, os, json
sys.path.insert(0, '{saturn_med_wsl}')
from mednafen_bot import MednafenBot

bot = MednafenBot(ipc_dir='{ipc_wsl}', cue_path='{cue_wsl}', show=False, sound=False, home_dir='{home_wsl}')
if not bot.start(timeout=45):
    print("FATAL: Failed to start Mednafen")
    sys.exit(1)

bot.send_and_wait("deterministic", "ok deterministic", timeout=10)
bot.send_and_wait("native_mode 0", "ok native_mode", timeout=10)
bot.send_and_wait("native_mask 0x00000000", "ok native_mask", timeout=10)

sequence = {CHECKPOINTS_SPEC!r}
events = {{}}

for addr, cp_label, occ, exp_cycle, exp_pr in sequence:
    bot.send_and_wait(f"breakpoint {{addr}} once", "ok breakpoint", timeout=10)
    bot.send("run")
    ack = bot.wait_ack(["break pc=", "break"], timeout=60)
    bot.send("dump_regs")
    regs_ack = bot.wait_ack("R0=", timeout=10)
    
    regs = {{}}
    tokens = regs_ack.replace("regs", "").split()
    for tok in tokens:
        if "=" in tok:
            k, v = tok.split("=", 1)
            regs[k] = v
            
    cycle = int(regs.get("cycle", "0"))
    pc = regs.get("PC", "")
    pr = regs.get("PR", "")
    events[cp_label] = {{
        "checkpoint": cp_label,
        "address": f"0x{{addr}}",
        "occurrence": occ,
        "pc": f"0x{{pc}}",
        "pr": f"0x{{pr}}",
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
    manifest: Dict[str, Any],
    reassembled_bytes: bytes,
) -> Dict[str, Any]:
    """Execute cold boot runs and verify occurrence-aware parity."""
    scratch_root = os.path.join(repo_root, "scratch", "runtime_proof")
    shutil.rmtree(scratch_root, ignore_errors=True)
    os.makedirs(scratch_root, exist_ok=True)

    try:
        # Pre-run verification
        print("Verifying environment and asset integrity...")
        verify_environment_integrity(repo_root)
        print("  SaturnAutoRE commit, Mednafen binary, BIOS, Disc: [ALL VERIFIED]")

        # Run ORIGINAL
        print("\n--- Running Mednafen Cold Boot A: ORIGINAL (clean disc) ---")
        orig_cue = os.environ.get("THOR_DISC_CUE", os.path.join(repo_root, DEFAULT_CUE))
        dir_a = os.path.join(scratch_root, "run_a_original")
        results_a = run_mednafen_session(repo_root, orig_cue, dir_a, "ORIGINAL")

        # Run ASM_REBUILT
        print("\n--- Running Mednafen Cold Boot B: ASM_REBUILT (substituted module) ---")
        rebuilt_cue, _ = create_substituted_disc(repo_root, scratch_root, manifest, reassembled_bytes)
        dir_b = os.path.join(scratch_root, "run_b_rebuilt")
        results_b = run_mednafen_session(repo_root, rebuilt_cue, dir_b, "ASM_REBUILT")

        print("\n--- Analyzing Occurrence-Aware Runtime Parity ---")
        comparison = {}
        all_match = True

        for _, label, occ, exp_c, exp_pr in CHECKPOINTS_SPEC:
            ev_a = results_a[label]
            ev_b = results_b[label]
            
            cycle_a = ev_a["cycle"]
            cycle_b = ev_b["cycle"]
            cycle_match = (cycle_a == cycle_b == exp_c)
            
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
                "occurrence": occ,
                "cycle_original": cycle_a,
                "cycle_rebuilt": cycle_b,
                "cycle_match": cycle_match,
                "regs_match": reg_match,
                "differing_regs": regs_diff,
                "regs": ev_b["regs"],
            }
            print(f"  [{label} | occ={occ}] Cycle: {cycle_a} (exp: {exp_c}) | Regs Match: {reg_match}")

        timing_ok = all_match
        return {
            "all_match": all_match,
            "timing_ok": timing_ok,
            "comparison": comparison,
            "results_original": results_a,
            "results_rebuilt": results_b,
        }

    finally:
        shutil.rmtree(scratch_root, ignore_errors=True)
        print("Private substituted disc image cleaned up.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Occurrence-aware runtime substitution proof")
    parser.add_argument("--manifest", default=None, help="Path to module manifest")
    parser.add_argument("--repo-root", default=None, help="Root repository directory")
    args = parser.parse_args()

    repo_root = args.repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    manifest_path = args.manifest or os.path.join(repo_root, "asm", "manifests", "0TH2.BIN.json")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    module_name = manifest["module"]
    stem = "0TH2" if module_name == "0TH2.BIN" else module_name.replace(".", "_")

    bin_path = os.path.join(repo_root, "out", f"asm_{stem}_build_1", "block.bin")
    if not os.path.exists(bin_path):
        build_script = os.path.join(repo_root, "tools", "asm", "build_full_module.py")
        subprocess.run([sys.executable, build_script, "--manifest", manifest_path], check=True, cwd=repo_root)

    print(f"Running occurrence-aware runtime proof for {module_name} using: {bin_path}")
    with open(bin_path, "rb") as f:
        rebuilt_bytes = f.read()

    proof_data = execute_runtime_parity_proof(repo_root, manifest, rebuilt_bytes)

    if not proof_data["all_match"]:
        print("ERROR: Runtime register/cycle divergence detected!")
        return 1

    print(f"\n=== OCCURRENCE-AWARE RUNTIME SUBSTITUTION PROOF: PASS ({module_name}) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
