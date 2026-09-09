#!/usr/bin/env python3
"""SaturnRecomp SH-2 Decoder Adapter.

Invokes SaturnRecomp's external decoder to extract normalized decode records
for 16-bit SH-2 opcodes without vendoring or copying external source code.
Pinned external commit: 26c9715e5493054b8a205aa31d73d8f125fdd8f5.
"""

import json
import os
import subprocess
import sys
import tempfile

PINNED_COMMIT = "26c9715e5493054b8a205aa31d73d8f125fdd8f5"


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
        return True
    except Exception as e:
        raise RuntimeError(f"Failed to verify SaturnRecomp commit: {e}") from e


def get_probe_binary(sr_dir):
    exe_name = "sr_probe.exe" if os.name == "nt" else "sr_probe"
    probe_bin = os.path.join(tempfile.gettempdir(), exe_name)

    c_source = r"""#include "external/sh2-recomp-core/common/sh2_isa.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc < 3) {
        printf("{\"error\": \"usage: probe hex_op hex_addr\"}\n");
        return 1;
    }
    uint16_t op = (uint16_t)strtoul(argv[1], NULL, 16);
    uint32_t addr = (uint32_t)strtoul(argv[2], NULL, 16);
    sh2_insn insn;
    char fmt[64] = {0};
    int valid = sh2_decode(op, addr, &insn);
    sh2_format(op, addr, fmt);

    printf("{\n");
    printf("  \"valid\": %d,\n", valid);
    printf("  \"raw_opcode\": \"0x%04X\",\n", (unsigned)insn.raw);
    printf("  \"instruction_address\": \"0x%08X\",\n", (unsigned)insn.addr);
    printf("  \"opcode_id\": %u,\n", (unsigned)insn.op);
    printf("  \"opcode_class\": \"%s\",\n", sh2_op_name(insn.op));
    printf("  \"formatted\": \"%s\",\n", fmt);
    printf("  \"flags\": \"0x%04X\",\n", (unsigned)insn.flags);
    printf("  \"branch_flag\": %s,\n", (insn.flags & SH2F_BRANCH) ? "true" : "false");
    printf("  \"conditional_flag\": %s,\n", (insn.flags & SH2F_COND) ? "true" : "false");
    printf("  \"delay_slot_flag\": %s,\n", (insn.flags & SH2F_DELAY) ? "true" : "false");
    printf("  \"indirect_flag\": %s,\n", (insn.flags & SH2F_INDIRECT) ? "true" : "false");
    printf("  \"load_flag\": %s,\n", (insn.flags & SH2F_LOAD) ? "true" : "false");
    printf("  \"store_flag\": %s,\n", (insn.flags & SH2F_STORE) ? "true" : "false");
    printf("  \"rn\": %u,\n", (unsigned)insn.n);
    printf("  \"rm\": %u,\n", (unsigned)insn.m);
    printf("  \"access_size\": %u,\n", (unsigned)insn.size);
    printf("  \"immediate\": %d,\n", insn.imm);
    printf("  \"displacement\": %d,\n", insn.disp);
    printf("  \"target\": \"0x%08X\"\n", (unsigned)insn.target);
    printf("}\n");
    return 0;
}
"""
    tmp_c = os.path.join(tempfile.gettempdir(), "sr_probe_src.c")
    if not os.path.exists(probe_bin) or (
        os.path.getmtime(probe_bin) < os.path.getmtime(__file__)
    ):
        with open(tmp_c, "w", encoding="utf-8") as f:
            f.write(c_source)
        decoder_c = os.path.join(
            sr_dir, "external", "sh2-recomp-core", "common", "sh2_decoder.c"
        )
        cmd = ["gcc", "-O2", f"-I{sr_dir}", tmp_c, decoder_c, "-o", probe_bin]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Failed to build probe: {res.stderr}")
    return probe_bin


def decode_opcode(op_hex, addr_hex, sr_dir=None):
    if sr_dir is None:
        sr_dir = find_saturnrecomp_dir()
    if not sr_dir:
        raise FileNotFoundError("SaturnRecomp directory not found")
    verify_saturnrecomp_pin(sr_dir)
    probe_bin = get_probe_binary(sr_dir)
    res = subprocess.run(
        [probe_bin, op_hex, addr_hex], capture_output=True, text=True, check=True
    )
    return json.loads(res.stdout)


def main():
    if len(sys.argv) < 3:
        print("Usage: saturnrecomp_adapter.py <hex_op> <hex_addr>")
        sys.exit(1)
    sr_dir = find_saturnrecomp_dir()
    if not sr_dir:
        print("Error: SaturnRecomp directory not found", file=sys.stderr)
        sys.exit(1)
    data = decode_opcode(sys.argv[1], sys.argv[2], sr_dir)
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
