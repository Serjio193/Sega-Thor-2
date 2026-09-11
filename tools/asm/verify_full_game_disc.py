#!/usr/bin/env python3
"""FULL_ASM_GAME_GATE: Full Saturn Disc Game Verification.

Builds and splices all 3 reassembled SH-2 modules (0TH2.BIN, TH2.LOW, SET07.BIN)
simultaneously into a single private disc image, asserts bit-identical disc SHA-256,
and executes occurrence-aware runtime parity checks across all checkpoints in clean Mednafen.
"""

from typing import Any, Dict, List, Tuple
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

CANONICAL_DISC_SHA = "fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8"
CANONICAL_BIOS_SHA = "96e106f740ab448cf89f0dd49dfbac7fe5391cb6bd6e14ad5e3061c13330266f"
DEFAULT_CUE = "The_Story_of_Thor_2_[RUS]_(NTSC).cue"
DEFAULT_BIN = "The_Story_of_Thor_2_[RUS]_(NTSC).bin"
DEFAULT_BIOS = "mpr-17933.bin"

MODULE_SPECS = [
    ("0TH2.BIN", "asm/manifests/0TH2.BIN.json", 24, 535552, "c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64"),
    ("TH2.LOW", "asm/manifests/TH2.LOW.json", 52123, 149504, "781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224"),
    ("SET07.BIN", "asm/manifests/SET07.BIN.json", 52040, 98304, "bb6072222e19f8cb68934cbdb94e7d187c67680bb9e167524f85579ee6bc0af6"),
    ("BGM.BIN", "asm/manifests/BGM.BIN.json", 353, 673792, "c1d11d5386eaffbd4ca6443c3de615312a71cc678ba4d76c2c9d6035acf9a8f6"),
]

CHECKPOINTS = [
    ("06004000", "entry_06004000", 0, 305462360),
    ("06004012", "branch_target_06004012", 0, 305462387),
    ("06004280", "checkpoint_06004280_occ0", 0, 307090585),
    ("06004280", "checkpoint_06004280_occ1", 1, 316309168),
    ("0600A0F8", "checkpoint_0600A0F8_load_th2_low", 2, 316309189),
    ("002E9910", "checkpoint_002E9910_th2_low_exec", 0, 387459915),
]

REG_NAMES = [
    "R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7",
    "R8", "R9", "R10", "R11", "R12", "R13", "R14", "R15",
    "PC", "SR", "PR", "GBR", "VBR", "MACH", "MACL"
]


def to_wsl_path(win_path: str) -> str:
    if sys.platform != "win32":
        return os.path.abspath(win_path)
    p = os.path.abspath(win_path).replace("\\", "/")
    if len(p) >= 2 and p[1] == ":":
        drive = p[0].lower()
        return f"/mnt/{drive}{p[2:]}"
    return p


def build_module_if_needed(repo_root: str, manifest_rel: str) -> bytes:
    m_path = os.path.join(repo_root, manifest_rel)
    with open(m_path) as f:
        m = json.load(f)
    module_name = m["module"]
    stem = module_name[:-4] if module_name.endswith(".BIN") else module_name.replace(".", "_")
    bin_path = os.path.join(repo_root, "out", f"asm_{stem}_build_1", "block.bin")
    if not os.path.exists(bin_path):
        build_py = os.path.join(repo_root, "tools", "asm", "build_full_module.py")
        subprocess.run([sys.executable, build_py, "--manifest", m_path], check=True, cwd=repo_root)
    with open(bin_path, "rb") as f:
        b = f.read()
    assert hashlib.sha256(b).hexdigest() == m["expected_output_sha256"]
    return b


def create_full_rebuilt_disc(repo_root: str, scratch_dir: str) -> Tuple[str, str]:
    os.makedirs(scratch_dir, exist_ok=True)
    orig_bin = os.environ.get("THOR_DISC_IMAGE", os.path.join(repo_root, DEFAULT_BIN))
    rebuilt_bin = os.path.join(scratch_dir, "thor2_full_rebuilt.bin")
    rebuilt_cue = os.path.join(scratch_dir, "thor2_full_rebuilt.cue")

    shutil.copyfile(orig_bin, rebuilt_bin)

    with open(rebuilt_bin, "r+b") as f:
        for name, m_path, lba, size, exp_sha in MODULE_SPECS:
            b = build_module_if_needed(repo_root, m_path)
            num_sectors = (size + 2047) // 2048
            for sec_idx in range(num_sectors):
                chunk = b[sec_idx * 2048 : (sec_idx + 1) * 2048]
                sec_off = (lba + sec_idx) * 2352 + 16
                f.seek(sec_off)
                f.write(chunk)

    cue_content = (
        'FILE "thor2_full_rebuilt.bin" BINARY\n'
        '  TRACK 01 MODE1/2352\n'
        '    INDEX 01 00:00:00\n'
    )
    with open(rebuilt_cue, "w", encoding="utf-8", newline="\n") as f:
        f.write(cue_content)

    with open(rebuilt_bin, "rb") as f:
        disc_sha = hashlib.sha256(f.read()).hexdigest()
    assert disc_sha == CANONICAL_DISC_SHA, f"Full rebuilt disc SHA mismatch: {disc_sha}"
    return rebuilt_cue, rebuilt_bin


def run_mednafen_session(repo_root: str, cue_path: str, work_dir: str, label: str) -> Dict[str, Any]:
    os.makedirs(work_dir, exist_ok=True)
    home_dir = os.path.join(work_dir, "home")
    ipc_dir = os.path.join(work_dir, "ipc")
    os.makedirs(os.path.join(home_dir, "firmware"), exist_ok=True)
    os.makedirs(ipc_dir, exist_ok=True)

    bios_src = os.environ.get("THOR_BIOS_IMAGE", os.path.join(repo_root, DEFAULT_BIOS))
    shutil.copy2(bios_src, os.path.join(home_dir, "firmware", "mpr-17933.bin"))
    shutil.copy2(bios_src, os.path.join(home_dir, "mpr-17933.bin"))

    with open(os.path.join(home_dir, "mednafen.cfg"), "w", newline="\n") as f:
        f.write("ss.bios_na_eu mpr-17933.bin\nss.region_autodetect 1\nss.region_default jp\nss.cart backup\n")

    cue_wsl = to_wsl_path(cue_path)
    home_wsl = to_wsl_path(home_dir)
    ipc_wsl = to_wsl_path(ipc_dir)
    out_json = f"{ipc_wsl}/results.json"

    saturn_dir = os.environ.get("THOR_SATURNAUTORE_DIR", os.path.join(repo_root, "..", "SaturnAutoRE"))
    saturn_med = to_wsl_path(os.path.join(saturn_dir, "mednafen"))

    wsl_code = f"""
import sys, os, json
sys.path.insert(0, '{saturn_med}')
from mednafen_bot import MednafenBot

bot = MednafenBot(ipc_dir='{ipc_wsl}', cue_path='{cue_wsl}', show=False, sound=False, home_dir='{home_wsl}')
if not bot.start(timeout=45):
    print("FATAL: Mednafen failed to launch")
    sys.exit(1)

bot.send_and_wait("deterministic", "ok deterministic", timeout=10)
bot.send_and_wait("native_mode 0", "ok native_mode", timeout=10)
bot.send_and_wait("native_mask 0x00000000", "ok native_mask", timeout=10)

sequence = {CHECKPOINTS!r}
events = {{}}

for addr, label, occ, exp_c in sequence:
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

    events[label] = {{
        "checkpoint": label,
        "address": f"0x{{addr}}",
        "occurrence": occ,
        "cycle": int(regs.get("cycle", "0")),
        "regs": regs
    }}

bot.send("quit")
with open('{out_json}', 'w') as f:
    json.dump(events, f, indent=2)
"""
    script_path = os.path.join(work_dir, "run_wsl.py")
    with open(script_path, "w", newline="\n") as f:
        f.write(wsl_code)

    cmd = [sys.executable, to_wsl_path(script_path)] if sys.platform != "win32" else ["wsl", "python3", to_wsl_path(script_path)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Mednafen run failed for {label}:\n{res.stderr}\n{res.stdout}")

    with open(os.path.join(ipc_dir, "results.json")) as f:
        return json.load(f)


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    scratch_name = "full_game_proof_win" if sys.platform == "win32" else "full_game_proof_linux"
    scratch = os.path.join(repo_root, "scratch", scratch_name)
    shutil.rmtree(scratch, ignore_errors=True)
    os.makedirs(scratch, exist_ok=True)

    try:
        print("=== FULL_ASM_GAME_GATE: VERIFYING REBUILT SATURN DISC ===")
        rebuilt_cue, rebuilt_bin = create_full_rebuilt_disc(repo_root, scratch)
        print(f"  All {len(MODULE_SPECS)} modules spliced into rebuilt disc: {rebuilt_bin}")
        print("  Disc SHA-256 verification: PASS (fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8)")

        print("\n--- Running Baseline Retail Cold Boot in Mednafen ---")
        orig_cue = os.environ.get("THOR_DISC_CUE", os.path.join(repo_root, DEFAULT_CUE))
        results_orig = run_mednafen_session(repo_root, orig_cue, os.path.join(scratch, "run_orig"), "ORIGINAL")

        print("\n--- Running Rebuilt Full Disc Cold Boot in Mednafen ---")
        results_rebuilt = run_mednafen_session(repo_root, rebuilt_cue, os.path.join(scratch, "run_rebuilt"), "REBUILT")

        print("\n--- Comparing Architectural Parity Across Cold Boot ---")
        all_match = True
        for addr, label, occ, exp_c in CHECKPOINTS:
            c_orig = results_orig[label]["cycle"]
            c_rebuilt = results_rebuilt[label]["cycle"]
            c_match = (c_orig == c_rebuilt == exp_c)

            regs_diff = {}
            for r in REG_NAMES:
                v_o = results_orig[label]["regs"].get(r)
                v_r = results_rebuilt[label]["regs"].get(r)
                if v_o != v_r:
                    regs_diff[r] = (v_o, v_r)

            reg_match = (len(regs_diff) == 0)
            if not (c_match and reg_match):
                all_match = False

            print(f"  [{label}] Cycle: {c_rebuilt} (exp: {exp_c}) | Regs Match: {reg_match}")

        if not all_match:
            print("\nERROR: Full game disc divergence detected!")
            return 1

        print("\n=== FULL_ASM_GAME_GATE: PASS (Zero Divergence on Full Rebuilt Disc) ===")
        return 0

    finally:
        shutil.rmtree(scratch, ignore_errors=True)
        print("Cleaned up private test disc images.")


if __name__ == "__main__":
    sys.exit(main())
