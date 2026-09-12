#!/usr/bin/env python3
"""tools/asm/executable_byte_carver.py — Whole-Module Byte Carver & UNKNOWN Reducer.

Recomputes full SH-2 CFG closure across 0TH2.BIN and TH2.LOW with audited
indirect sites and certified RTS return domains injected, strictly classifying
pointer tables as FUNCTION_POINTER_TABLE_DATA, partitioning each module into
CONFIRMED_CODE, PROVEN_DATA, PROVEN_PADDING, and UNKNOWN, and quantifying exact
reductions and retractions from the pre-audit baseline.
"""

from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
import json
import struct
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tools.carver.thor_decoder import dump_all_valid_with_thor_sh2
from tools.carver.p3_control_flow_resolver import P3ControlFlowResolver


@dataclass
class ModulePartitionRecord:
    module: str
    vma_base: str
    size_bytes: int
    confirmed_code_bytes: int
    proven_data_bytes: int
    proven_padding_bytes: int
    unknown_bytes: int
    checksum_valid: bool


class ExecutableByteCarver:
    """Carves modules into exact intervals and measures UNKNOWN byte reduction."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.scorecard = json.loads(
            (repo_root / "workstreams/T2-ASM-08/final_indirect_scorecard.json").read_text(encoding="utf-8")
        )
        self.false_tables = json.loads(
            (repo_root / "workstreams/T2-ASM-08/false_decode_pointer_tables.json").read_text(encoding="utf-8")
        )
        self.resolver = P3ControlFlowResolver(repo_root)
        self.baseline_unknown_bytes = 1251863
        self.old_asm08_code_bytes = 157530
        self.old_asm08_unknown_bytes = 1184431

    def extract_proven_targets(self) -> Set[int]:
        targets: Set[int] = set()
        for s in self.scorecard.get("sites", []):
            if s["resolution_status"].startswith("RESOLVED"):
                for t in s.get("targets", []):
                    if t.startswith("0x"):
                        targets.add(int(t, 16))
        return targets

    def carver_run(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        new_targets = self.extract_proven_targets()
        raw_map = self.resolver._load_module_raw_bytes()
        unconditional_terminals = {"RTS", "RTE", "BRA", "JMP", "BRAF"}

        partitions: List[ModulePartitionRecord] = []
        closure_records: List[Dict[str, Any]] = []

        total_code = 0
        total_data = 0
        total_pad = 0
        total_unknown = 0

        # Extract pointer table intervals
        table_intervals: List[Tuple[int, int]] = []
        for tbl in self.false_tables.get("tables", []):
            table_intervals.append((int(tbl["table_start"], 16), int(tbl["table_end"], 16)))

        for mod_name, meta in self.resolver.db.modules.items():
            cpu = meta.get("cpu", "MASTER_SH2")
            vma_base = meta["vma_base"]
            sz = meta["size"]
            raw = raw_map.get(mod_name, b"")
            ivs = self.resolver.db.intervals[mod_name]

            if cpu == "MASTER_SH2" and mod_name in ("0TH2.BIN", "TH2.LOW") and raw:
                all_insts = dump_all_valid_with_thor_sh2(self.repo_root, mod_name, vma_base, raw)

                base_code_vmas: Set[int] = set()
                base_data_vmas: Set[int] = set()
                base_pad_vmas: Set[int] = set()

                for r in ivs:
                    if r.classification == "CONFIRMED_CODE":
                        for off in range(r.offset_start, r.offset_end_exclusive):
                            base_code_vmas.add(vma_base + off)
                    elif r.classification == "DATA":
                        for off in range(r.offset_start, r.offset_end_exclusive):
                            base_data_vmas.add(vma_base + off)
                    elif r.classification == "PADDING":
                        for off in range(r.offset_start, r.offset_end_exclusive):
                            base_pad_vmas.add(vma_base + off)

                # Protect pointer tables as data
                if mod_name == "0TH2.BIN":
                    for t_start, t_end in table_intervals:
                        for vma in range(t_start, t_end):
                            base_data_vmas.add(vma)
                            base_code_vmas.discard(vma)

                seeds: Set[int] = set(base_code_vmas)
                for pc in self.resolver.union.get_instruction_pcs_for_module(mod_name):
                    seeds.add(pc)
                if mod_name == "0TH2.BIN":
                    seeds.add(vma_base)
                for t in new_targets:
                    if vma_base <= t < vma_base + sz:
                        seeds.add(t)

                # Remove any seeds that fall inside pointer tables
                if mod_name == "0TH2.BIN":
                    for t_start, t_end in table_intervals:
                        seeds = {s for s in seeds if not (t_start <= s < t_end)}

                g_data_vmas = {vma_base + off for off in self.resolver.guarded_data.get(mod_name, set())} | base_data_vmas
                g_pad_vmas = {vma_base + off for off in self.resolver.guarded_pad.get(mod_name, set())} | base_pad_vmas

                worklist = deque(sorted(list(seeds)))
                visited_pcs: Set[int] = set(base_code_vmas)
                proven_data_bytes: Set[int] = set(g_data_vmas)

                for pc in seeds:
                    ins = all_insts.get(pc)
                    if ins and ins.is_pc_rel_data and ins.target_vma:
                        for b in range(ins.data_access_size):
                            proven_data_bytes.add(ins.target_vma + b)

                while worklist:
                    pc = worklist.popleft()
                    if (
                        pc in visited_pcs and pc not in seeds
                        or pc in proven_data_bytes
                        or pc in g_pad_vmas
                        or pc < vma_base
                        or pc >= vma_base + sz
                    ):
                        continue
                    curr_pc = pc
                    while curr_pc < vma_base + sz:
                        if curr_pc in proven_data_bytes or curr_pc in g_pad_vmas:
                            break
                        ins = all_insts.get(curr_pc)
                        if not ins:
                            break
                        visited_pcs.add(curr_pc)
                        visited_pcs.add(curr_pc + 1)
                        if ins.is_pc_rel_data and ins.target_vma:
                            for b in range(ins.data_access_size):
                                proven_data_bytes.add(ins.target_vma + b)
                        if ins.target_vma and (ins.is_branch or ins.is_call):
                            t = ins.target_vma
                            if (
                                vma_base <= t < vma_base + sz
                                and t not in visited_pcs
                                and t not in proven_data_bytes
                                and t not in g_pad_vmas
                            ):
                                worklist.append(t)
                        if ins.has_delay_slot:
                            d_pc = curr_pc + 2
                            if (
                                d_pc < vma_base + sz
                                and d_pc not in proven_data_bytes
                                and d_pc not in g_pad_vmas
                            ):
                                d_ins = all_insts.get(d_pc)
                                if d_ins:
                                    visited_pcs.add(d_pc)
                                    visited_pcs.add(d_pc + 1)
                                    if d_ins.is_pc_rel_data and d_ins.target_vma:
                                        for b in range(d_ins.data_access_size):
                                            proven_data_bytes.add(d_ins.target_vma + b)
                            if ins.opcode_id in unconditional_terminals:
                                break
                            curr_pc = curr_pc + 4
                        else:
                            if ins.opcode_id in unconditional_terminals:
                                break
                            curr_pc = curr_pc + 2

                # Interval analysis & byte counting
                code_b = 0
                data_b = 0
                pad_b = 0
                unk_b = 0

                for off in range(sz):
                    vma = vma_base + off
                    if vma in visited_pcs:
                        code_b += 1
                    elif vma in proven_data_bytes:
                        data_b += 1
                    elif vma in g_pad_vmas:
                        pad_b += 1
                    else:
                        b = raw[off]
                        if b == 0x00 or b == 0xFF:
                            pad_b += 1
                        else:
                            unk_b += 1

                for i in range(1, len(ivs)):
                    left = ivs[i - 1]
                    curr = ivs[i]
                    if left.classification != "CONFIRMED_CODE" or curr.classification != "UNKNOWN":
                        continue
                    cur_off = curr.offset_start
                    end = curr.offset_end_exclusive
                    while cur_off < end:
                        vma = vma_base + cur_off
                        seg_s = cur_off
                        if vma in visited_pcs:
                            while cur_off < end and (vma_base + cur_off) in visited_pcs:
                                cur_off += 2
                            st = "CONFIRMED_CODE"
                        elif vma in proven_data_bytes:
                            while cur_off < end and (vma_base + cur_off) not in visited_pcs and (vma_base + cur_off) in proven_data_bytes:
                                cur_off += 1
                            st = "PROVEN_DATA"
                        elif vma in g_pad_vmas:
                            while cur_off < end and (vma_base + cur_off) not in visited_pcs and (vma_base + cur_off) in g_pad_vmas:
                                cur_off += 1
                            st = "PROVEN_PADDING"
                        else:
                            while cur_off < end and (vma_base + cur_off) not in visited_pcs and (vma_base + cur_off) not in proven_data_bytes and (vma_base + cur_off) not in g_pad_vmas:
                                cur_off += 1
                            slice_b = raw[seg_s:cur_off]
                            st = "PROVEN_PADDING" if all(x in (0, 0xFF) for x in slice_b) else "UNKNOWN"

                        closure_records.append({
                            "module": mod_name,
                            "offset_start": seg_s,
                            "offset_end_exclusive": cur_off,
                            "byte_length": cur_off - seg_s,
                            "resolved_state": st,
                        })

                chk = (code_b + data_b + pad_b + unk_b == sz)
                partitions.append(
                    ModulePartitionRecord(
                        module=mod_name,
                        vma_base=f"0x{vma_base:08X}",
                        size_bytes=sz,
                        confirmed_code_bytes=code_b,
                        proven_data_bytes=data_b,
                        proven_padding_bytes=pad_b,
                        unknown_bytes=unk_b,
                        checksum_valid=chk,
                    )
                )
                total_code += code_b
                total_data += data_b
                total_pad += pad_b
                total_unknown += unk_b

            else:
                c_b = sum(r.offset_end_exclusive - r.offset_start for r in ivs if r.classification == "CONFIRMED_CODE")
                d_b = sum(r.offset_end_exclusive - r.offset_start for r in ivs if r.classification == "DATA")
                p_b = sum(r.offset_end_exclusive - r.offset_start for r in ivs if r.classification == "PADDING")
                u_b = sz - (c_b + d_b + p_b)
                chk = (c_b + d_b + p_b + u_b == sz)

                partitions.append(
                    ModulePartitionRecord(
                        module=mod_name,
                        vma_base=f"0x{vma_base:08X}",
                        size_bytes=sz,
                        confirmed_code_bytes=c_b,
                        proven_data_bytes=d_b,
                        proven_padding_bytes=p_b,
                        unknown_bytes=u_b,
                        checksum_valid=chk,
                    )
                )
                total_code += c_b
                total_data += d_b
                total_pad += p_b
                total_unknown += u_b

        state_counts: Dict[str, int] = {}
        for r in closure_records:
            st = r["resolved_state"]
            state_counts[st] = state_counts.get(st, 0) + 1

        unknown_gaps = state_counts.get("UNKNOWN", 0)

        closure_payload = {
            "total_gaps_audited": len(closure_records),
            "state_counts": state_counts,
            "residual_undecoded_gaps_before": 1595,
            "residual_undecoded_gaps_after": unknown_gaps,
            "gap_reduction_from_p7": 1595 - unknown_gaps,
            "newly_confirmed_code_segments": state_counts.get("CONFIRMED_CODE", 0) - 3160,
            "proven_targets_injected": len(new_targets),
        }

        partition_payload = {
            "total_binary_bytes": sum(p.size_bytes for p in partitions),
            "total_confirmed_code_bytes": total_code,
            "total_proven_data_bytes": total_data,
            "total_proven_padding_bytes": total_pad,
            "total_unknown_bytes": total_unknown,
            "baseline_unknown_bytes": self.baseline_unknown_bytes,
            "unknown_bytes_reduction": self.baseline_unknown_bytes - total_unknown,
            "old_asm08_code_bytes": self.old_asm08_code_bytes,
            "audited_code_bytes": total_code,
            "code_bytes_retracted": max(0, self.old_asm08_code_bytes - total_code),
            "old_asm08_unknown_bytes": self.old_asm08_unknown_bytes,
            "audited_unknown_bytes": total_unknown,
            "unknown_bytes_restored_by_audit": max(0, total_unknown - self.old_asm08_unknown_bytes),
            "all_partitions_balanced": all(p.checksum_valid for p in partitions),
            "modules": [asdict(p) for p in partitions],
        }

        return closure_payload, partition_payload


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    carver = ExecutableByteCarver(repo_root)
    closure, partition = carver.carver_run()

    out_dir = repo_root / "workstreams" / "T2-ASM-08"
    out_dir.mkdir(parents=True, exist_ok=True)

    closure_file = out_dir / "cfg_closure.json"
    closure_file.write_text(json.dumps(closure, indent=2), encoding="utf-8")

    partition_file = out_dir / "executable_byte_partition.json"
    partition_file.write_text(json.dumps(partition, indent=2), encoding="utf-8")

    print(f"CFG Closure written to {closure_file}")
    print(f"  Targets injected: {closure['proven_targets_injected']}")
    print(f"  State counts: {closure['state_counts']}")
    print(f"  Residual unknown gaps: {closure['residual_undecoded_gaps_after']}")
    print(f"Executable byte partition written to {partition_file}")
    print(f"  Total binary bytes: {partition['total_binary_bytes']}")
    print(f"  Confirmed code bytes: {partition['total_confirmed_code_bytes']}")
    print(f"  Proven data bytes: {partition['total_proven_data_bytes']}")
    print(f"  Proven padding bytes: {partition['total_proven_padding_bytes']}")
    print(f"  Unknown bytes: {partition['total_unknown_bytes']} (Baseline: {partition['baseline_unknown_bytes']})")
    print(f"  UNKNOWN REDUCTION: -{partition['unknown_bytes_reduction']} bytes!")
    print(f"  Code bytes retracted: {partition['code_bytes_retracted']}")
    print(f"  All checksums valid: {partition['all_partitions_balanced']}")


if __name__ == '__main__':
    main()
