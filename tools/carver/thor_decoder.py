#!/usr/bin/env python3
"""tools/carver/thor_decoder.py — C++ thor_sh2 Decoder Bridge for Carver.

Eliminates duplicate Python opcode bitmasks by executing the authoritative
C++ thor::sh2::decode_sh2 tool (export_sh2_asm_ir) and querying decoded IR.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import os
import subprocess
import sys


@dataclass
class DecodedInstruction:
    pc: int
    offset: int
    opcode: int
    opcode_id: str
    asm_line: str
    comment: str
    rn: int
    rm: int
    disp: int
    target_vma: int
    flow: str
    has_delay_slot: bool

    @property
    def is_branch(self) -> bool:
        return self.flow in ("BRANCH", "BRANCH_CONDITIONAL")

    @property
    def is_call(self) -> bool:
        return self.flow == "CALL"

    @property
    def is_pc_rel_data(self) -> bool:
        return self.opcode_id in ("MOV_L_PC_REL", "MOV_W_PC_REL", "MOVA")

    @property
    def data_access_size(self) -> int:
        if self.opcode_id in ("MOV_L_PC_REL", "MOVA"):
            return 4
        elif self.opcode_id == "MOV_W_PC_REL":
            return 2
        return 0


def find_exporter_binary(repo_root: Path) -> Path:
    exe_name = "export_sh2_asm_ir.exe" if sys.platform == "win32" else "export_sh2_asm_ir"
    candidates = [
        repo_root / "build" / exe_name,
        repo_root / "build_linux" / exe_name,
        repo_root / "build-linux" / exe_name,
        repo_root / exe_name,
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"Cannot find {exe_name} in candidate paths")


def decode_intervals_with_thor_sh2(
    repo_root: Path,
    module_name: str,
    base_vma: int,
    module_bytes: bytes,
    intervals: List[Any],
) -> List[DecodedInstruction]:
    """Execute C++ export_sh2_asm_ir against intervals and return DecodedInstructions."""
    if not intervals or not module_bytes:
        return []

    exe_path = find_exporter_binary(repo_root)

    # Write temporary binary if needed
    scratch_dir = repo_root / "scratch"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    temp_bin = scratch_dir / f"{module_name}_carver.bin"
    temp_bin.write_bytes(module_bytes)

    temp_rsp = scratch_dir / f"{module_name}_ranges.rsp"
    temp_json = scratch_dir / f"{module_name}_carver_ir.json"

    with open(temp_rsp, "w", encoding="utf-8") as rf:
        for iv in intervals:
            blk_id = getattr(iv, "block_id", None) or f"blk_{iv.offset_start:06X}"
            s_vma = base_vma + iv.offset_start
            e_vma = base_vma + iv.offset_end_exclusive
            rf.write(f"0x{s_vma:08X}:0x{e_vma:08X}:{blk_id}\n")

    try:
        if temp_json.exists():
            temp_json.unlink()
    except OSError:
        pass

    cmd = [
        str(exe_path),
        str(temp_bin),
        f"0x{base_vma:08X}",
        str(temp_json),
        f"@{temp_rsp}",
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not temp_json.exists():
        # If any block fails closed, decode block-by-block to salvage all valid blocks
        return _decode_block_by_block(exe_path, temp_bin, base_vma, temp_json, intervals)

    try:
        with open(temp_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        return _parse_json_instructions(data)
    except Exception:
        return _decode_block_by_block(exe_path, temp_bin, base_vma, temp_json, intervals)


def _decode_block_by_block(
    exe_path: Path,
    temp_bin: Path,
    base_vma: int,
    temp_json: Path,
    intervals: List[Any],
) -> List[DecodedInstruction]:
    results: List[DecodedInstruction] = []
    for iv in intervals:
        blk_id = getattr(iv, "block_id", None) or f"blk_{iv.offset_start:06X}"
        s_vma = base_vma + iv.offset_start
        e_vma = base_vma + iv.offset_end_exclusive
        range_arg = f"0x{s_vma:08X}:0x{e_vma:08X}:{blk_id}"
        cmd = [str(exe_path), str(temp_bin), f"0x{base_vma:08X}", str(temp_json), range_arg]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and temp_json.exists():
            try:
                with open(temp_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                results.extend(_parse_json_instructions(data))
            except Exception:
                pass
    return results


def _make_decoded_instruction(ins: Dict[str, Any]) -> DecodedInstruction:
    return DecodedInstruction(
        pc=int(ins["pc"], 16),
        offset=int(ins["offset"]),
        opcode=int(ins["opcode"], 16),
        opcode_id=ins["opcode_id"],
        asm_line=ins.get("asm_line", ""),
        comment=ins.get("comment", ""),
        rn=int(ins.get("rn", 0)),
        rm=int(ins.get("rm", 0)),
        disp=int(ins.get("disp", 0)),
        target_vma=int(ins.get("target_vma", "0x0"), 16),
        flow=ins.get("flow", "SEQUENTIAL"),
        has_delay_slot=bool(ins.get("has_delay_slot", False)),
    )


def _parse_json_instructions(data: Dict[str, Any]) -> List[DecodedInstruction]:
    instructions: List[DecodedInstruction] = []
    for blk in data.get("blocks", []):
        for ins in blk.get("instructions", []):
            instructions.append(_make_decoded_instruction(ins))
    for ins in data.get("instructions", []):
        instructions.append(_make_decoded_instruction(ins))
    return instructions


def dump_all_valid_with_thor_sh2(
    repo_root: Path,
    module_name: str,
    base_vma: int,
    module_bytes: bytes,
) -> Dict[int, DecodedInstruction]:
    """Execute C++ export_sh2_asm_ir --dump-all-valid and return dict of DecodedInstructions by PC."""
    if not module_bytes:
        return {}
    exe_path = find_exporter_binary(repo_root)
    scratch_dir = repo_root / "scratch"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    temp_bin = scratch_dir / f"{module_name}_all_valid.bin"
    temp_bin.write_bytes(module_bytes)
    temp_json = scratch_dir / f"{module_name}_all_valid.json"
    if temp_json.exists():
        temp_json.unlink()

    cmd = [
        str(exe_path),
        "--dump-all-valid",
        str(temp_bin),
        f"0x{base_vma:08X}",
        str(temp_json),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not temp_json.exists():
        raise RuntimeError(f"export_sh2_asm_ir --dump-all-valid failed for {module_name}: {res.stderr}")

    with open(temp_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    instructions = _parse_json_instructions(data)
    return {ins.pc: ins for ins in instructions}
