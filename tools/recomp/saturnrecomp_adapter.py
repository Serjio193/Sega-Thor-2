#!/usr/bin/env python3
"""SaturnRecomp SH-2 Decoder & Semantic Adapter.

Invokes SaturnRecomp's external decoder and execution semantics with strict
source-blob identity verification and cache isolation.
Zero foreign source code is checked into Sega-Thor-2.

Pinned external repository: https://github.com/sonsegajp/SaturnRecomp.git
Pinned commit: 26c9715e5493054b8a205aa31d73d8f125fdd8f5
Pinned decoder blob: 6a5f7e06606c2dab20e84b5c014c014647be70e4
Pinned ISA header blob: 709f92437990a2a0fe6b69d34565cea9d432a844
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile

PINNED_COMMIT = "26c9715e5493054b8a205aa31d73d8f125fdd8f5"
PINNED_DECODER_BLOB = "6a5f7e06606c2dab20e84b5c014c014647be70e4"
PINNED_ISA_BLOB = "709f92437990a2a0fe6b69d34565cea9d432a844"

DECODER_REL_PATH = "external/sh2-recomp-core/common/sh2_decoder.c"
ISA_REL_PATH = "external/sh2-recomp-core/common/sh2_isa.h"

PROBE_C_SOURCE = '#include "sh2_isa.h"\n#include <stdio.h>\n#include <stdlib.h>\n\nint main(int argc, char **argv) {\n    if (argc < 3) {\n        printf("{\\"error\\": \\"usage: probe hex_op hex_addr\\"}\\n");\n        return 1;\n    }\n    uint16_t op = (uint16_t)strtoul(argv[1], NULL, 16);\n    uint32_t addr = (uint32_t)strtoul(argv[2], NULL, 16);\n    sh2_insn insn;\n    char fmt[64] = {0};\n    int valid = sh2_decode(op, addr, &insn);\n    sh2_format(op, addr, fmt);\n\n    printf("{\\n");\n    printf("  \\"valid\\": %d,\\n", valid);\n    printf("  \\"raw_opcode\\": \\"0x%04X\\",\\n", (unsigned)insn.raw);\n    printf("  \\"instruction_address\\": \\"0x%08X\\",\\n", (unsigned)insn.addr);\n    printf("  \\"opcode_id\\": %u,\\n", (unsigned)insn.op);\n    printf("  \\"opcode_class\\": \\"%s\\",\\n", sh2_op_name(insn.op));\n    printf("  \\"formatted\\": \\"%s\\",\\n", fmt);\n    printf("  \\"flags\\": \\"0x%04X\\",\\n", (unsigned)insn.flags);\n    printf("  \\"branch_flag\\": %s,\\n", (insn.flags & SH2F_BRANCH) ? "true" : "false");\n    printf("  \\"conditional_flag\\": %s,\\n", (insn.flags & SH2F_COND) ? "true" : "false");\n    printf("  \\"delay_slot_flag\\": %s,\\n", (insn.flags & SH2F_DELAY) ? "true" : "false");\n    printf("  \\"indirect_flag\\": %s,\\n", (insn.flags & SH2F_INDIRECT) ? "true" : "false");\n    printf("  \\"load_flag\\": %s,\\n", (insn.flags & SH2F_LOAD) ? "true" : "false");\n    printf("  \\"store_flag\\": %s,\\n", (insn.flags & SH2F_STORE) ? "true" : "false");\n    printf("  \\"uses_rn\\": %s,\\n", (insn.flags & SH2F_USES_RN) ? "true" : "false");\n    printf("  \\"uses_rm\\": %s,\\n", (insn.flags & SH2F_USES_RM) ? "true" : "false");\n    printf("  \\"rn\\": %u,\\n", (unsigned)insn.n);\n    printf("  \\"rm\\": %u,\\n", (unsigned)insn.m);\n    printf("  \\"access_size\\": %u,\\n", (unsigned)insn.size);\n    printf("  \\"immediate\\": %d,\\n", insn.imm);\n    printf("  \\"displacement\\": %d,\\n", insn.disp);\n    printf("  \\"target\\": \\"0x%08X\\"\\n", (unsigned)insn.target);\n    printf("}\\n");\n    return 0;\n}\n'

SEMANTIC_PROBE_C_SOURCE = '#include "saturn.h"\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\nint  sh2_step(sh2 *c);\nvoid sh2_reset(sh2 *c, saturn *s, int slave, uint32_t pc, uint32_t sp);\nvoid saturn_init(saturn *s);\n\nstatic saturn g;\n#define CODE 0x06004000u\n\nstatic void emit_json(const char *test, sh2 *c) {\n    printf("{\\n");\n    printf("  \\"test\\": \\"%s\\",\\n", test);\n    printf("  \\"r0\\": \\"0x%08X\\",\\n", (unsigned)c->r[0]);\n    printf("  \\"r1\\": \\"0x%08X\\",\\n", (unsigned)c->r[1]);\n    printf("  \\"r3\\": \\"0x%08X\\",\\n", (unsigned)c->r[3]);\n    printf("  \\"t_bit\\": %d,\\n", (c->sr & 1) ? 1 : 0);\n    printf("  \\"sr\\": \\"0x%08X\\",\\n", (unsigned)c->sr);\n    printf("  \\"pc\\": \\"0x%08X\\"\\n", (unsigned)c->pc);\n    printf("}\\n");\n}\n\nint main(int argc, char **argv) {\n    if (argc < 2) {\n        printf("{\\"error\\": \\"missing test case argument\\"}\\n");\n        return 1;\n    }\n    const char *test = argv[1];\n    saturn_init(&g);\n    sh2 *c = &g.master;\n\n    if (strcmp(test, "cmp_ge_signed") == 0) {\n        /* r0 = -1 (0xFFFFFFFF), r1 = 1; cmp/ge r1, r0 -> -1 >= 1 is false -> T=0 */\n        uint16_t ops[] = { 0xE0FF, 0xE101, 0x3013 };\n        for (int i = 0; i < 3; i++) bus_w16(&g, CODE + i*2, ops[i]);\n        sh2_reset(c, &g, 0, CODE, 0x06020000u);\n        for (int i = 0; i < 3; i++) sh2_step(c);\n        emit_json(test, c);\n        return 0;\n    }\n    if (strcmp(test, "cmp_hs_unsigned") == 0) {\n        /* r0 = 0xFFFFFFFF, r1 = 1; cmp/hs r1, r0 -> 4294967295 >= 1 is true -> T=1 */\n        uint16_t ops[] = { 0xE0FF, 0xE101, 0x3012 };\n        for (int i = 0; i < 3; i++) bus_w16(&g, CODE + i*2, ops[i]);\n        sh2_reset(c, &g, 0, CODE, 0x06020000u);\n        for (int i = 0; i < 3; i++) sh2_step(c);\n        emit_json(test, c);\n        return 0;\n    }\n    if (strcmp(test, "shlr_logical") == 0) {\n        /* r0 = -1 (0xFFFFFFFF); shlr r0 -> 0x7FFFFFFF, T=1 */\n        uint16_t ops[] = { 0xE0FF, 0x4001 };\n        for (int i = 0; i < 2; i++) bus_w16(&g, CODE + i*2, ops[i]);\n        sh2_reset(c, &g, 0, CODE, 0x06020000u);\n        for (int i = 0; i < 2; i++) sh2_step(c);\n        emit_json(test, c);\n        return 0;\n    }\n    if (strcmp(test, "shar_arithmetic") == 0) {\n        /* r0 = -1 (0xFFFFFFFF); shar r0 -> 0xFFFFFFFF, T=1 */\n        uint16_t ops[] = { 0xE0FF, 0x4021 };\n        for (int i = 0; i < 2; i++) bus_w16(&g, CODE + i*2, ops[i]);\n        sh2_reset(c, &g, 0, CODE, 0x06020000u);\n        for (int i = 0; i < 2; i++) sh2_step(c);\n        emit_json(test, c);\n        return 0;\n    }\n    if (strcmp(test, "add_imm_sign_ext") == 0) {\n        /* r0 = 5; add #-1, r0 -> r0 = 4 */\n        uint16_t ops[] = { 0xE005, 0x70FF };\n        for (int i = 0; i < 2; i++) bus_w16(&g, CODE + i*2, ops[i]);\n        sh2_reset(c, &g, 0, CODE, 0x06020000u);\n        for (int i = 0; i < 2; i++) sh2_step(c);\n        emit_json(test, c);\n        return 0;\n    }\n    if (strcmp(test, "bf_delayed_exec") == 0) {\n        /* r0=0, cmp/pl r0 (T=0); bf.s +2 (skips next); add #5, r0 in delay slot */\n        uint16_t ops[] = { 0xE000, 0x4015, 0x8F01, 0x7005, 0x7001, 0x7002 };\n        for (int i = 0; i < 6; i++) bus_w16(&g, CODE + i*2, ops[i]);\n        sh2_reset(c, &g, 0, CODE, 0x06020000u);\n        for (int i = 0; i < 5; i++) sh2_step(c);\n        emit_json(test, c);\n        return 0;\n    }\n    if (strcmp(test, "rotcl_semantics") == 0) {\n        /* r1 = -1 (0xFFFFFFFF), T=0; rotcl r1 -> r1 = 0xFFFFFFFE, T=1 */\n        uint16_t ops[] = { 0xE1FF, 0x4124 };\n        for (int i = 0; i < 2; i++) bus_w16(&g, CODE + i*2, ops[i]);\n        sh2_reset(c, &g, 0, CODE, 0x06020000u);\n        for (int i = 0; i < 2; i++) sh2_step(c);\n        emit_json(test, c);\n        return 0;\n    }\n    if (strcmp(test, "div0s_div1") == 0) {\n        /* r1=4, r3=3; div0s r1, r3; div1 r1, r3 */\n        uint16_t ops[] = { 0xE104, 0xE303, 0x2317, 0x3314 };\n        for (int i = 0; i < 4; i++) bus_w16(&g, CODE + i*2, ops[i]);\n        sh2_reset(c, &g, 0, CODE, 0x06020000u);\n        for (int i = 0; i < 4; i++) sh2_step(c);\n        emit_json(test, c);\n        return 0;\n    }\n    printf("{\\"error\\": \\"unknown semantic test case %s\\"}\\n", test);\n    return 1;\n}\n'

def find_saturnrecomp_dir():
    env_dir = os.environ.get("SATURNRECOMP_DIR")
    if env_dir and os.path.isdir(env_dir):
        return os.path.abspath(env_dir)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "..", "..", "..", "SaturnRecomp"),
        os.path.join(script_dir, "..", "..", "SaturnRecomp"),
        r"e:\Github\SaturnRecomp",
        "/mnt/e/Github/SaturnRecomp",
    ]
    for cand in candidates:
        if os.path.isdir(cand):
            return os.path.abspath(cand)
    return None


def verify_saturnrecomp_pin(sr_dir):
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=sr_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        head = res.stdout.strip()
        if head != PINNED_COMMIT:
            raise RuntimeError(
                f"SaturnRecomp commit mismatch: expected {PINNED_COMMIT}, got {head}"
            )

        res_dec = subprocess.run(
            ["git", "rev-parse", f"{PINNED_COMMIT}:{DECODER_REL_PATH}"],
            cwd=sr_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        dec_blob = res_dec.stdout.strip()
        if dec_blob != PINNED_DECODER_BLOB:
            raise RuntimeError(
                f"Decoder blob mismatch: expected {PINNED_DECODER_BLOB}, got {dec_blob}"
            )

        res_isa = subprocess.run(
            ["git", "rev-parse", f"{PINNED_COMMIT}:{ISA_REL_PATH}"],
            cwd=sr_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        isa_blob = res_isa.stdout.strip()
        if isa_blob != PINNED_ISA_BLOB:
            raise RuntimeError(
                f"ISA blob mismatch: expected {PINNED_ISA_BLOB}, got {isa_blob}"
            )

        return True
    except Exception as e:
        raise RuntimeError(f"Failed to verify SaturnRecomp pinned identity: {e}") from e


def extract_pinned_source(sr_dir, git_path, dest_path):
    cmd = ["git", "show", f"{PINNED_COMMIT}:{git_path}"]
    res = subprocess.run(cmd, cwd=sr_dir, capture_output=True, text=True, check=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(res.stdout)


def get_probe_binary(sr_dir):
    verify_saturnrecomp_pin(sr_dir)
    probe_hash = hashlib.sha256(PROBE_C_SOURCE.encode("utf-8")).hexdigest()[:8]
    cache_tag = f"sr_probe_{PINNED_COMMIT[:8]}_{PINNED_DECODER_BLOB[:8]}_{PINNED_ISA_BLOB[:8]}_{probe_hash}"
    cache_dir = os.path.join(tempfile.gettempdir(), cache_tag)
    os.makedirs(cache_dir, exist_ok=True)

    exe_name = "sr_probe.exe" if os.name == "nt" else "sr_probe"
    probe_bin = os.path.join(cache_dir, exe_name)

    if not os.path.exists(probe_bin):
        tmp_c = os.path.join(cache_dir, "probe.c")
        dec_c = os.path.join(cache_dir, "sh2_decoder.c")
        isa_h = os.path.join(cache_dir, "sh2_isa.h")

        with open(tmp_c, "w", encoding="utf-8") as f:
            f.write(PROBE_C_SOURCE)
        extract_pinned_source(sr_dir, DECODER_REL_PATH, dec_c)
        extract_pinned_source(sr_dir, ISA_REL_PATH, isa_h)

        cmd = ["gcc", "-O2", f"-I{cache_dir}", tmp_c, dec_c, "-o", probe_bin]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Failed to build probe: {res.stderr}")

    return probe_bin


def get_semantic_probe_binary(sr_dir):
    verify_saturnrecomp_pin(sr_dir)
    probe_hash = hashlib.sha256(SEMANTIC_PROBE_C_SOURCE.encode("utf-8")).hexdigest()[:8]
    cache_tag = f"sr_sem_probe_{PINNED_COMMIT[:8]}_{probe_hash}"
    cache_dir = os.path.join(tempfile.gettempdir(), cache_tag)
    os.makedirs(cache_dir, exist_ok=True)

    exe_name = "sr_sem_probe.exe" if os.name == "nt" else "sr_sem_probe"
    probe_bin = os.path.join(cache_dir, exe_name)

    if not os.path.exists(probe_bin):
        tmp_c = os.path.join(cache_dir, "sem_probe.c")
        with open(tmp_c, "w", encoding="utf-8") as f:
            f.write(SEMANTIC_PROBE_C_SOURCE)

        runner_srcs = [
            os.path.join(sr_dir, "runner", "src", s)
            for s in [
                "sh2_interp.c", "bus.c", "scu_dsp.c", "cdblock.c", "smpc.c",
                "vdp1.c", "png.c", "sound.c", "scsp.c", "scsp_dsp.c", "vdp2.c",
                "m68k.c", "m68k_bus.c", "bios.c"
            ]
        ] + [
            os.path.join(sr_dir, "recompiler", "src", "disc.c"),
            os.path.join(sr_dir, "external", "sh2-recomp-core", "common", "sh2_decoder.c")
        ]

        cmd = [
            "gcc", "-O2",
            f"-I{sr_dir}/runner/include",
            f"-I{sr_dir}/recompiler/include",
            f"-I{sr_dir}/external/sh2-recomp-core/common",
            tmp_c
        ] + runner_srcs + ["-lm", "-o", probe_bin]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Failed to build semantic probe: {res.stderr}")

    return probe_bin


def decode_opcode(op_hex, addr_hex, sr_dir=None):
    if sr_dir is None:
        sr_dir = find_saturnrecomp_dir()
    if not sr_dir:
        raise FileNotFoundError("SaturnRecomp directory not found")
    probe_bin = get_probe_binary(sr_dir)
    res = subprocess.run(
        [probe_bin, op_hex, addr_hex], capture_output=True, text=True, check=True
    )
    return json.loads(res.stdout)


def run_semantic_case(case_name, sr_dir=None):
    if sr_dir is None:
        sr_dir = find_saturnrecomp_dir()
    if not sr_dir:
        raise FileNotFoundError("SaturnRecomp directory not found")
    probe_bin = get_semantic_probe_binary(sr_dir)
    res = subprocess.run(
        [probe_bin, case_name], capture_output=True, text=True, check=True
    )
    return json.loads(res.stdout)


def main():
    if len(sys.argv) < 2:
        print("Usage: saturnrecomp_adapter.py decode <hex_op> <hex_addr>")
        print("   or: saturnrecomp_adapter.py semantic <case_name>")
        sys.exit(1)
    sr_dir = find_saturnrecomp_dir()
    if not sr_dir:
        print("Error: SaturnRecomp directory not found", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "decode":
        if len(sys.argv) < 4:
            print("Usage: saturnrecomp_adapter.py decode <hex_op> <hex_addr>", file=sys.stderr)
            sys.exit(1)
        data = decode_opcode(sys.argv[2], sys.argv[3], sr_dir)
        print(json.dumps(data, indent=2))
    elif cmd == "semantic":
        if len(sys.argv) < 3:
            print("Usage: saturnrecomp_adapter.py semantic <case_name>", file=sys.stderr)
            sys.exit(1)
        data = run_semantic_case(sys.argv[2], sr_dir)
        print(json.dumps(data, indent=2))
    elif len(sys.argv) == 3 and not cmd.startswith("-"):
        data = decode_opcode(sys.argv[1], sys.argv[2], sr_dir)
        print(json.dumps(data, indent=2))
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
