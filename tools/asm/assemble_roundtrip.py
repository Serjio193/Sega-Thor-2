#!/usr/bin/env python3
"""SH-2 Assembly & Link Round-Trip Pipeline.

Assembles mechanically generated SH-2 assembly using the pinned GNU toolchain,
links at the original Saturn VMA, inspects relocations, and extracts raw bytes.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import hashlib
import json
import os
import subprocess
import sys

PINNED_TOOLCHAIN = {
    "target": "sh-elf",
    "binutils_version": "2.40+2",
    "as_sha256": "fd3ddc347d0f83521b98e039e30acf93380930dd521d5031682767e822c074e5",
    "ld_sha256": "e369cd410424715b549f2e61fc12f1f93f525f656ff3f60f2fdc22f689c8472d",
    "objcopy_sha256": "1da83e2a6bbabe453a0fe12a37dd57a262135fc9cb769413655cdfc5e54aaea2",
    "objdump_sha256": "ee13a67c88f386a388cf10eb4710d13f05691ac008af103b84329276bc41eb35",
}

PINNED_M68K_TOOLCHAIN = {
    "target": "m68k-linux-gnu",
    "binutils_version": "2.42",
    "as_sha256": "c52857325edf2697b7434a0c053c3952b31a8698f8d57f6bc6cd1dec7aa1c6d9",
    "ld_sha256": "ad520eb42f75b6bd9d3d72bd7e518ca8c506f0d48e660020a2649da8b0bb4e4f",
    "objcopy_sha256": "b34601a02ddb1be3cdc363f67ccf9587c5c2554098e6ff83566252f196fb89b3",
    "objdump_sha256": "240d1acf1e8f1e3a09498300e8ca4f23076df5f3f7c16af48d534efcc03feded",
}


@dataclass
class Toolchain:
    as_cmd: str
    ld_cmd: str
    objcopy_cmd: str
    objdump_cmd: str
    use_wsl: bool


def find_pinned_toolchain() -> Toolchain:
    """Discover pinned GNU toolchain in local path or WSL."""
    if sys.platform.startswith("linux"):
        base = os.path.expanduser("~/.local/share/toolchains/sh-elf/usr/bin")
        if os.path.exists(os.path.join(base, "sh-elf-as")):
            return Toolchain(
                as_cmd=os.path.join(base, "sh-elf-as"),
                ld_cmd=os.path.join(base, "sh-elf-ld"),
                objcopy_cmd=os.path.join(base, "sh-elf-objcopy"),
                objdump_cmd=os.path.join(base, "sh-elf-objdump"),
                use_wsl=False,
            )

    check_script = (
        'if [ -x ~/.local/share/toolchains/sh-elf/usr/bin/sh-elf-as ]; then '
        'echo ~/.local/share/toolchains/sh-elf/usr/bin; fi'
    )
    try:
        res = subprocess.run(["wsl", "bash", "-c", check_script], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            base = res.stdout.strip()
            return Toolchain(
                as_cmd=f"{base}/sh-elf-as",
                ld_cmd=f"{base}/sh-elf-ld",
                objcopy_cmd=f"{base}/sh-elf-objcopy",
                objdump_cmd=f"{base}/sh-elf-objdump",
                use_wsl=True,
            )
    except FileNotFoundError:
        pass

    import shutil
    as_path = shutil.which("sh-elf-as")
    if as_path:
        base = os.path.dirname(as_path)
        return Toolchain(
            as_cmd=os.path.join(base, "sh-elf-as"),
            ld_cmd=os.path.join(base, "sh-elf-ld"),
            objcopy_cmd=os.path.join(base, "sh-elf-objcopy"),
            objdump_cmd=os.path.join(base, "sh-elf-objdump"),
            use_wsl=False,
        )

    raise RuntimeError("GNU SH-2 cross-toolchain (binutils-sh-elf) not found")


def find_pinned_m68k_toolchain() -> Toolchain:
    """Discover pinned GNU M68K toolchain in local path or WSL."""
    import shutil
    if sys.platform.startswith("linux"):
        as_path = shutil.which("m68k-linux-gnu-as")
        if as_path:
            base = os.path.dirname(as_path)
            return Toolchain(
                as_cmd=os.path.join(base, "m68k-linux-gnu-as"),
                ld_cmd=os.path.join(base, "m68k-linux-gnu-ld"),
                objcopy_cmd=os.path.join(base, "m68k-linux-gnu-objcopy"),
                objdump_cmd=os.path.join(base, "m68k-linux-gnu-objdump"),
                use_wsl=False,
            )
    try:
        res = subprocess.run(["wsl", "bash", "-c", "which m68k-linux-gnu-as"], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            return Toolchain(
                as_cmd="/usr/bin/m68k-linux-gnu-as",
                ld_cmd="/usr/bin/m68k-linux-gnu-ld",
                objcopy_cmd="/usr/bin/m68k-linux-gnu-objcopy",
                objdump_cmd="/usr/bin/m68k-linux-gnu-objdump",
                use_wsl=True,
            )
    except FileNotFoundError:
        pass
    raise RuntimeError("GNU M68K cross-toolchain (binutils-m68k-linux-gnu) not found")



def to_wsl_path(win_path: str) -> str:
    """Convert Windows path to WSL unix path."""
    if sys.platform.startswith("linux"):
        return os.path.abspath(win_path)
    p = os.path.abspath(win_path).replace("\\", "/")
    if len(p) >= 2 and p[1] == ":":
        drive = p[0].lower()
        return f"/mnt/{drive}{p[2:]}"
    return p



def run_tool_cmd(tc: Toolchain, cmd_str: str) -> subprocess.CompletedProcess:
    """Run a tool command natively or via WSL."""
    if tc.use_wsl:
        return subprocess.run(["wsl", "bash", "-c", cmd_str], capture_output=True, text=True)
    return subprocess.run(cmd_str, shell=True, capture_output=True, text=True)


def verify_toolchain_hashes(tc: Toolchain, target_arch: str = "sh2") -> Dict[str, str]:
    """Verify toolchain binaries against pinned SHA-256 hashes."""
    hashes = {}
    pinned = PINNED_M68K_TOOLCHAIN if target_arch == "m68k" else PINNED_TOOLCHAIN
    prefix = "m68k-linux-gnu" if target_arch == "m68k" else "sh-elf"
    tools = [
        (f"{prefix}-as", tc.as_cmd, pinned["as_sha256"]),
        (f"{prefix}-ld", tc.ld_cmd, pinned["ld_sha256"]),
        (f"{prefix}-objcopy", tc.objcopy_cmd, pinned["objcopy_sha256"]),
        (f"{prefix}-objdump", tc.objdump_cmd, pinned["objdump_sha256"]),
    ]

    for name, path, expected in tools:
        cmd = f"sha256sum {path}"
        res = run_tool_cmd(tc, cmd)
        if res.returncode != 0:
            raise RuntimeError(f"Failed to hash {name}: {res.stderr}")
        actual = res.stdout.strip().split()[0]
        hashes[name] = actual
        if actual.lower() != expected.lower():
            raise ValueError(f"Toolchain hash mismatch for {name}: {actual} != {expected}")

    return hashes


def assemble_and_link(
    s_file: str,
    ld_file: str,
    out_dir: str,
    endian_mode: str = "big",
    extra_as_args: Optional[List[str]] = None,
    target_arch: str = "sh2",
) -> Tuple[bytes, str, str, str]:
    """Assemble and link assembly into raw binary bytes."""
    tc = find_pinned_m68k_toolchain() if target_arch == "m68k" else find_pinned_toolchain()
    os.makedirs(out_dir, exist_ok=True)

    if tc.use_wsl:
        s_unix = to_wsl_path(s_file)
        ld_unix = to_wsl_path(ld_file)
        out_unix = to_wsl_path(out_dir)
    else:
        s_unix = os.path.abspath(s_file)
        ld_unix = os.path.abspath(ld_file)
        out_unix = os.path.abspath(out_dir)

    o_unix = f"{out_unix}/block.o"
    elf_unix = f"{out_unix}/block.elf"
    bin_unix = f"{out_unix}/block.bin"

    endian_flag = "-big" if endian_mode == "big" else "-little"
    ld_endian_flag = "-EB" if endian_mode == "big" else "-EL"

    extra = " ".join(extra_as_args) if extra_as_args else ""
    if target_arch == "m68k":
        as_cmd = f"{tc.as_cmd} -m68000 {extra} {s_unix} -o {o_unix}"
    else:
        as_cmd = f"{tc.as_cmd} -isa=sh2 {endian_flag} {extra} {s_unix} -o {o_unix}"
    res = run_tool_cmd(tc, as_cmd)
    if res.returncode != 0:
        raise RuntimeError(f"Assembly failed:\n{res.stderr}")

    res_reloc_o = run_tool_cmd(tc, f"{tc.objdump_cmd} -r {o_unix}")
    relocs_before = res_reloc_o.stdout

    if target_arch == "m68k":
        ld_cmd = f"{tc.ld_cmd} -T {ld_unix} {o_unix} -o {elf_unix}"
    else:
        ld_cmd = f"{tc.ld_cmd} {ld_endian_flag} -T {ld_unix} {o_unix} -o {elf_unix}"
    res = run_tool_cmd(tc, ld_cmd)
    if res.returncode != 0:
        raise RuntimeError(f"Link failed:\n{res.stderr}")

    res_reloc_elf = run_tool_cmd(tc, f"{tc.objdump_cmd} -r {elf_unix}")
    relocs_after = res_reloc_elf.stdout

    objcopy_cmd = f"{tc.objcopy_cmd} -O binary -j .text {elf_unix} {bin_unix}"
    res = run_tool_cmd(tc, objcopy_cmd)
    if res.returncode != 0:
        raise RuntimeError(f"Objcopy failed:\n{res.stderr}")

    bin_local = os.path.join(out_dir, "block.bin")
    with open(bin_local, "rb") as f:
        raw_bytes = f.read()

    return raw_bytes, relocs_before, relocs_after, elf_unix


def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    s_path = os.path.join(repo_root, "asm", "generated", "bb_06004000.s")
    ld_path = os.path.join(repo_root, "asm", "linker", "bb_06004000.ld")
    manifest_path = os.path.join(repo_root, "asm", "manifests", "bb_06004000.json")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    tc = find_pinned_toolchain()
    print("Verifying pinned toolchain integrity...")
    hashes = verify_toolchain_hashes(tc)
    for tool, h in hashes.items():
        print(f"  {tool}: {h} [MATCH]")

    print("\nExecuting Build 1 (out/asm_build_1)...")
    out_dir_1 = os.path.join(repo_root, "out", "asm_build_1")
    bytes_1, rel_before_1, rel_after_1, _ = assemble_and_link(s_path, ld_path, out_dir_1)
    sha_1 = hashlib.sha256(bytes_1).hexdigest()
    print(f"  Length: {len(bytes_1)} bytes")
    print(f"  Hex:    {bytes_1.hex()}")
    print(f"  SHA256: {sha_1}")

    print("\nExecuting Build 2 (out/asm_build_2) for determinism check...")
    out_dir_2 = os.path.join(repo_root, "out", "asm_build_2")
    bytes_2, _, _, _ = assemble_and_link(s_path, ld_path, out_dir_2)
    sha_2 = hashlib.sha256(bytes_2).hexdigest()

    if bytes_1 != bytes_2:
        print("ERROR: Deterministic build check failed!")
        return 1
    print("  Deterministic Build: PASS (0 differing bytes between independent runs)")

    expected_sha = manifest["expected_output_sha256"]
    if sha_1 != expected_sha:
        print(f"ERROR: SHA mismatch: {sha_1} != {expected_sha}")
        return 1

    print("\nRelocation Audit:")
    print(f"  Object relocations count: {len(rel_before_1.strip().splitlines())}")
    print(f"  Final ELF relocations:    {'NONE (Clean)' if not rel_after_1.strip() or 'RELOCATION RECORDS FOR' not in rel_after_1 else 'WARNING'}")

    print("\n=== ASM ROUND-TRIP BUILD: SUCCESS ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
