#!/usr/bin/env python3
"""Reusable Live Guest Code Mutation Harness for SaturnAutoRE (M-02) Fault Injection.

Provides bounded transient guest-code mutations over Mednafen IPC:
- Validates authorized range.
- Reads and verifies expected original bytes before mutation.
- Applies mutation (NOP instruction replacement or arbitrary byte mutation).
- Verifies applied bytes in guest RAM.
- Restores original bytes and verifies restoration.
- Executes bounded negative-control runs and clean baseline non-contamination checks.
"""

import sys
import os
import shutil
import json
import time

sys.path.insert(0, '/mnt/e/Github/SaturnAutoRE/mednafen')
from mednafen_bot import MednafenBot

class LiveGuestMutationHarness:
    def __init__(self, bot, auth_start=0x06004000, auth_size=12):
        self.bot = bot
        self.auth_start = auth_start
        self.auth_size = auth_size

    def validate_spec(self, addr, expected_orig, replacement_bytes):
        if not expected_orig or not replacement_bytes:
            raise ValueError("Mutation spec expected_original and replacement_bytes must be non-empty")
        if len(expected_orig) != len(replacement_bytes):
            raise ValueError(f"Mismatched vector lengths: orig={len(expected_orig)}, repl={len(replacement_bytes)}")
        MAX_ADDRESS_EXCLUSIVE = 0x100000000
        length = len(replacement_bytes)
        if addr >= MAX_ADDRESS_EXCLUSIVE or length > (MAX_ADDRESS_EXCLUSIVE - addr):
            raise ValueError("32-bit address-space overflow / exclusive-end range overflow")
        end_addr = addr + length
        if addr < self.auth_start or end_addr > (self.auth_start + self.auth_size):
            raise ValueError(f"Target address range [0x{addr:08x}, 0x{end_addr:08x}) outside authorized range [0x{self.auth_start:08x}, 0x{self.auth_start + self.auth_size:08x})")

    def read_bytes(self, addr, count):
        ack = self.bot.send_and_wait(f'dump_mem {addr:08x} {count}', 'mem ')
        if not ack:
            raise RuntimeError(f"No response from dump_mem {addr:08x}")
        lines = ack.strip().splitlines()
        hex_tokens = []
        for line in lines[1:]:
            hex_tokens.extend(line.strip().split())
        return [int(h, 16) for h in hex_tokens[:count]]

    def apply_mutation(self, addr, expected_orig, replacement_bytes, desc=""):
        self.validate_spec(addr, expected_orig, replacement_bytes)

        # Verify pre-mutation original bytes
        current = self.read_bytes(addr, len(expected_orig))
        if current != list(expected_orig):
            raise RuntimeError(f"Original byte mismatch at 0x{addr:08x}: expected {expected_orig}, got {current}")

        # Poke replacement bytes
        byte_args = " ".join(f"{b:02x}" for b in replacement_bytes)
        self.bot.send_and_wait(f"poke {addr:08x} {byte_args}", "ok poke")

        # Verify applied bytes
        applied = self.read_bytes(addr, len(replacement_bytes))
        if applied != list(replacement_bytes):
            raise RuntimeError(f"Apply verification failed at 0x{addr:08x}: expected {replacement_bytes}, got {applied}")

        return {
            "address": addr,
            "expected_orig": list(expected_orig),
            "replacement": list(replacement_bytes),
            "description": desc,
            "applied_verified": True
        }

    def restore_mutation(self, addr, expected_orig, replacement_bytes=None):
        if replacement_bytes is None:
            # Default to NOP if 2 bytes
            replacement_bytes = [0x00, 0x09] if len(expected_orig) == 2 else [expected_orig[0] ^ 0x01]
        self.validate_spec(addr, expected_orig, replacement_bytes)

        # Precondition check: verify current bytes match expected mutation replacement
        current = self.read_bytes(addr, len(replacement_bytes))
        if current != list(replacement_bytes):
            raise RuntimeError(f"Restore precondition failed at 0x{addr:08x}: expected {replacement_bytes}, got {current}")

        # Restore original bytes
        byte_args = " ".join(f"{b:02x}" for b in expected_orig)
        self.bot.send_and_wait(f"poke {addr:08x} {byte_args}", "ok poke")

        restored = self.read_bytes(addr, len(expected_orig))
        if restored != list(expected_orig):
            raise RuntimeError(f"Restoration verification failed at 0x{addr:08x}: expected {expected_orig}, got {restored}")

        return True


def setup_bot_env(root_dir):
    if os.path.exists(root_dir):
        shutil.rmtree(root_dir)
    home = os.path.join(root_dir, 'home')
    ipc = os.path.join(root_dir, 'ipc')
    fw = os.path.join(home, 'firmware')
    os.makedirs(home, exist_ok=True)
    os.makedirs(ipc, exist_ok=True)
    os.makedirs(fw, exist_ok=True)
    shutil.copy2('/mnt/e/Github/Sega-Thor-2/mpr-17933.bin', os.path.join(home, 'mpr-17933.bin'))
    shutil.copy2('/mnt/e/Github/Sega-Thor-2/mpr-17933.bin', os.path.join(fw, 'mpr-17933.bin'))
    with open(os.path.join(home, 'mednafen.cfg'), 'w') as f:
        f.write("ss.bios_na_eu mpr-17933.bin\nss.region_autodetect 1\nss.region_default jp\nss.cart backup\n")

    bot = MednafenBot(
        ipc_dir=ipc,
        cue_path='/mnt/e/Github/Sega-Thor-2/The_Story_of_Thor_2_[RUS]_(NTSC).cue',
        show=False,
        sound=False,
        home_dir=home
    )
    started = bot.start(timeout=20)
    assert started, f"Failed to start Mednafen in {root_dir}"
    bot.send_and_wait('deterministic', 'ok deterministic')
    return bot


def parse_stats(stats_str):
    res = {}
    tokens = stats_str.strip().split()
    for tok in tokens:
        if '=' in tok:
            k, v = tok.split('=', 1)
            try:
                res[k] = int(v)
            except ValueError:
                res[k] = v
    return res


def run_live_m02_experiments():
    print("=== T2-POST-D8.1 / M-02 Live Mutation & Non-Contamination Verification ===", flush=True)
    results = {}

    cases = [
        {
            "id": "CASE_1_FIRST_INSTR_NOP",
            "name": "Instruction 0 NOP Replacement (0x06004000: 0x6611 -> 0x0009)",
            "addr": 0x06004000,
            "orig": [0x66, 0x11],
            "repl": [0x00, 0x09]
        },
        {
            "id": "CASE_2_MIDDLE_BLOCK_MUTATION",
            "name": "Instruction 3 Opcode Mutation (0x06004006: 0x6442 -> 0x0009)",
            "addr": 0x06004006,
            "orig": [0x64, 0x42],
            "repl": [0x00, 0x09]
        },
        {
            "id": "CASE_3_BRANCH_NOP",
            "name": "Instruction 4 Branch Mutation (0x06004008: 0xA003 -> 0x0009)",
            "addr": 0x06004008,
            "orig": [0xA0, 0x03],
            "repl": [0x00, 0x09]
        }
    ]

    for c in cases:
        cid = c["id"]
        print(f"\n--- Running Live Mutation: {c['name']} ---", flush=True)
        root_dir = f"/mnt/e/Github/Sega-Thor-2/scratch/m02_live_{cid}"
        bot = setup_bot_env(root_dir)
        try:
            bot.send_and_wait('native_mode 2', 'ok native_mode')
            bot.send_and_wait('breakpoint 06004000', 'ok breakpoint')
            bot.send('run')
            ack_bp = bot.wait_ack(['break pc=', 'break'], timeout=60)
            print(f"  [BREAK] {ack_bp.splitlines()[0]}", flush=True)

            harness = LiveGuestMutationHarness(bot, auth_start=0x06004000, auth_size=12)

            # Apply mutation
            apply_meta = harness.apply_mutation(c["addr"], c["orig"], c["repl"], c["name"])
            print(f"  [APPLY] Mutation verified in RAM at 0x{c['addr']:08x}: {[hex(b) for b in c['repl']]}", flush=True)

            # Clear breakpoint at 06004000 so stepping proceeds
            bot.send_and_wait('breakpoint_clear', 'ok breakpoint_clear')

            # Step 1: Advance into instruction 0 boundary
            ack_st1 = bot.send_and_wait('step 1', 'done step')
            # Step 2: Trigger native hook -> fail-closed rejection -> fallback to interpreter
            ack_st2 = bot.send_and_wait('step 1', 'done step')
            print(f"  [STEP] {ack_st2.splitlines()[0]}", flush=True)

            # Query native stats
            ack_stats = bot.send_and_wait('native_stats', 'ok native_stats')
            st = parse_stats(ack_stats)
            print(f"  [STATS] {ack_stats.strip()}", flush=True)

            # Verification invariants for mutated run:
            assert st.get("attempts", 0) == 1, f"Attempt must be 1! attempts={st.get('attempts')}"
            assert st.get("executed", 0) == 0, f"Mutated block must NOT execute natively! executed={st.get('executed')}"
            assert st.get("fallback", 0) == 1, f"Fallback must be 1! fallback={st.get('fallback')}"
            assert st.get("ineligible", 0) == 1, f"Ineligible must be 1! ineligible={st.get('ineligible')}"
            assert st.get("retirements_in_interval", 0) >= 1, "Interpreter must retire mutated instructions!"

            results[cid] = {
                "name": c["name"],
                "target_addr": hex(c["addr"]),
                "mutation": [hex(b) for b in c["repl"]],
                "attempts": st.get("attempts"),
                "native_executed": st.get("executed"),
                "fallback": st.get("fallback"),
                "ineligible": st.get("ineligible"),
                "retirements_in_interval": st.get("retirements_in_interval"),
                "status": "PASS_FAIL_CLOSED_DETECTED"
            }
            print(f"  >>> PASS: Mutation correctly rejected fail-closed, native execution refused, fallback triggered.", flush=True)

        finally:
            bot.quit()

    # Case 4: Transient Mutation + Exact Restoration + Clean Baseline Run
    print(f"\n--- Running Case 4: Transient Mutation + Exact Restoration + Clean Baseline Run ---", flush=True)
    clean_root = "/mnt/e/Github/Sega-Thor-2/scratch/m02_live_CASE_4_RESTORATION"
    clean_bot = setup_bot_env(clean_root)
    try:
        clean_bot.send_and_wait('native_mode 2', 'ok native_mode')
        clean_bot.send_and_wait('breakpoint 06004000', 'ok breakpoint')
        clean_bot.send('run')
        ack_bp = clean_bot.wait_ack(['break pc=', 'break'], timeout=60)
        print(f"  [BREAK] {ack_bp.splitlines()[0]}", flush=True)

        harness = LiveGuestMutationHarness(clean_bot, auth_start=0x06004000, auth_size=12)

        # Apply transient mutation at 0x06004000
        harness.apply_mutation(0x06004000, [0x66, 0x11], [0x00, 0x09], "Transient NOP test")
        print("  [TRANSIENT] Mutation 0x0009 applied and verified in RAM.", flush=True)

        # Immediately restore original bytes
        harness.restore_mutation(0x06004000, [0x66, 0x11])
        print("  [RESTORE] Original bytes 0x6611 restored and verified in RAM.", flush=True)

        # Clear breakpoint at 06004000
        clean_bot.send_and_wait('breakpoint_clear', 'ok breakpoint_clear')

        # Run to continuation checkpoint 0x06004280
        clean_bot.send_and_wait('breakpoint 06004280', 'ok breakpoint')
        clean_bot.send('run')
        ack_cont = clean_bot.wait_ack(['break pc=', 'break'], timeout=60)
        print(f"  [CHECKPOINT] {ack_cont.splitlines()[0]}", flush=True)

        ack_stats = clean_bot.send_and_wait('native_stats', 'ok native_stats')
        st = parse_stats(ack_stats)
        print(f"  [STATS] {ack_stats.strip()}", flush=True)

        clean_bot.send('dump_regs')
        ack_regs = clean_bot.wait_ack('R0=', timeout=10)

        # Non-contamination invariants:
        assert st.get("executed", 0) == 1, f"Native execution must succeed! executed={st.get('executed')}"
        assert st.get("fallback", 0) == 0, f"Fallback must be 0! fallback={st.get('fallback')}"
        assert st.get("retirements_in_interval", 0) == 0, f"Retirements in interval must be 0! ret={st.get('retirements_in_interval')}"
        assert st.get("shadow_match", 0) == 1, f"Shadow match must be 1! match={st.get('shadow_match')}"
        assert st.get("cycle", 0) == 307090585, f"Cycle must be 307090585! cycle={st.get('cycle')}"

        golden = {
            "R0": "00000001", "R1": "000000F1", "R2": "FFFFFF0F", "R3": "00000001",
            "R4": "FFFFF7FF", "R5": "00000000", "R6": "00006611", "R7": "06000D00",
            "R8": "00000000", "R9": "00000000", "R10": "00000000", "R11": "06096523",
            "R12": "06088708", "R13": "00000001", "R14": "00000000", "R15": "06002EDC",
            "PC": "06004280", "SR": "00000001", "PR": "0600427C", "GBR": "00000000",
            "VBR": "06000000", "MACH": "00000000", "MACL": "00000000"
        }

        divergences = 0
        actual_regs = {}
        for line in ack_regs.strip().split("\n"):
            for tok in line.split():
                if '=' in tok:
                    k, v = tok.split('=', 1)
                    if k in golden:
                        actual_regs[k] = v
                        if v != golden[k]:
                            print(f"  DIVERGENCE in {k}: actual={v} expected={golden[k]}", flush=True)
                            divergences += 1

        assert divergences == 0, f"Divergences detected: {divergences}"
        print(f"  >>> PASS: Exact restoration and zero non-contamination divergence verified across all 23 registers!", flush=True)

        results["CASE_4_CLEAN_RESTORATION_BASELINE"] = {
            "name": "Restoration Non-Contamination Clean Baseline Run",
            "native_executed": st.get("executed"),
            "fallback": st.get("fallback"),
            "retirements_in_interval": st.get("retirements_in_interval"),
            "shadow_match": st.get("shadow_match"),
            "checkpoint": "0x06004280",
            "cycle": st.get("cycle"),
            "cycle_delta": 0,
            "register_divergences": 0,
            "status": "PASS_CLEAN_NON_CONTAMINATED"
        }

    finally:
        clean_bot.quit()

    out_path = "/mnt/e/Github/Sega-Thor-2/scratch/m02_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nAll M-02 Live Experiments Completed Successfully! Results written to {out_path}", flush=True)


if __name__ == "__main__":
    run_live_m02_experiments()
