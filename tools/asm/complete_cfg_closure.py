#!/usr/bin/env python3
"""tools/asm/complete_cfg_closure.py — Full CFG Closure & Gap Reduction Engine.

Re-injects all newly proven indirect targets (callee-saved literals, struct
callback domains, callback tables) into the SH-2 CFG worklist to reduce
residual undecoded gaps across 0TH2.BIN and TH2.LOW.
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

from tools.carver.interval_db import IntervalDatabase, MemoryInterval
from tools.carver.thor_decoder import dump_all_valid_with_thor_sh2, DecodedInstruction
from tools.carver.executed_pc_union import ExecutedPCUnion
from tools.carver.p3_control_flow_resolver import P3ControlFlowResolver


class CompleteCFGClosure:
    """Computes CFG closure using proven indirect targets."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.scorecard = json.loads(
            (repo_root / "workstreams/T2-ASM-07/struct_callback_scorecard.json").read_text(encoding="utf-8")
        )
        self.resolver = P3ControlFlowResolver(repo_root)

    def extract_proven_targets(self) -> Set[int]:
        targets = set()
        for s in self.scorecard["sites"]:
            if s["resolution_status"].startswith("RESOLVED") and s["category"] == "INDIRECT_CALL_JUMP":
                for t in s.get("targets", []):
                    if t.startswith("0x"):
                        targets.add(int(t, 16))
        return targets

    def recompute_closure(self) -> Dict[str, Any]:
        new_targets = self.extract_proven_targets()
        raw_map = self.resolver._load_module_raw_bytes()
        all_resolved: List[Dict[str, Any]] = []

        unconditional_terminals = {"RTS", "RTE", "BRA", "JMP", "BRAF"}

        for mod_name, meta in self.resolver.db.modules.items():
            cpu = meta.get("cpu", "MASTER_SH2")
            vma_base = meta["vma_base"]
            sz = meta["size"]
            raw = raw_map.get(mod_name, b"")
            ivs = self.resolver.db.intervals[mod_name]

            if cpu == "MASTER_SH2" and mod_name in ("0TH2.BIN", "TH2.LOW") and raw:
                all_insts = dump_all_valid_with_thor_sh2(self.repo_root, mod_name, vma_base, raw)

                seeds = set()
                for r in self.resolver.db.intervals[mod_name]:
                    if r.classification == "CONFIRMED_CODE":
                        for pc in range(r.runtime_start, r.runtime_end_exclusive, 2):
                            seeds.add(pc)
                for pc in self.resolver.union.get_instruction_pcs_for_module(mod_name):
                    seeds.add(pc)
                if mod_name == "0TH2.BIN":
                    seeds.add(vma_base)
                for t in new_targets:
                    if vma_base <= t < vma_base + sz:
                        seeds.add(t)

                g_data_vmas = {vma_base + off for off in self.resolver.guarded_data.get(mod_name, set())}
                g_pad_vmas = {vma_base + off for off in self.resolver.guarded_pad.get(mod_name, set())}

                worklist = deque(sorted(list(seeds)))
                visited_pcs: Set[int] = set()
                proven_data_bytes: Set[int] = set()

                for pc in seeds:
                    ins = all_insts.get(pc)
                    if ins and ins.is_pc_rel_data and ins.target_vma:
                        for b in range(ins.data_access_size):
                            proven_data_bytes.add(ins.target_vma + b)

                while worklist:
                    pc = worklist.popleft()
                    if (
                        pc in visited_pcs
                        or pc in proven_data_bytes
                        or pc in g_data_vmas
                        or pc in g_pad_vmas
                        or pc < vma_base
                        or pc >= vma_base + sz
                    ):
                        continue
                    curr_pc = pc
                    while curr_pc < vma_base + sz:
                        if (
                            curr_pc in visited_pcs
                            or curr_pc in proven_data_bytes
                            or curr_pc in g_data_vmas
                            or curr_pc in g_pad_vmas
                        ):
                            break
                        ins = all_insts.get(curr_pc)
                        if not ins:
                            break
                        visited_pcs.add(curr_pc)
                        if ins.is_pc_rel_data and ins.target_vma:
                            for b in range(ins.data_access_size):
                                proven_data_bytes.add(ins.target_vma + b)
                        if ins.target_vma and (ins.is_branch or ins.is_call):
                            t = ins.target_vma
                            if (
                                vma_base <= t < vma_base + sz
                                and t not in visited_pcs
                                and t not in proven_data_bytes
                                and t not in g_data_vmas
                                and t not in g_pad_vmas
                            ):
                                worklist.append(t)
                        if ins.has_delay_slot:
                            d_pc = curr_pc + 2
                            if (
                                d_pc < vma_base + sz
                                and d_pc not in proven_data_bytes
                                and d_pc not in g_data_vmas
                                and d_pc not in g_pad_vmas
                            ):
                                d_ins = all_insts.get(d_pc)
                                if d_ins:
                                    visited_pcs.add(d_pc)
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

                # Interval partitioning
                for i in range(1, len(ivs)):
                    left = ivs[i - 1]
                    curr = ivs[i]
                    if left.classification != "CONFIRMED_CODE" or curr.classification != "UNKNOWN":
                        continue

                    start = curr.offset_start
                    end = curr.offset_end_exclusive
                    cur_off = start
                    while cur_off < end:
                        vma = vma_base + cur_off
                        if vma in visited_pcs:
                            seg_s = cur_off
                            while cur_off < end and (vma_base + cur_off) in visited_pcs:
                                cur_off += 2
                            res_state = "CONFIRMED_CODE"
                        elif vma in proven_data_bytes or cur_off in self.resolver.guarded_data.get(mod_name, set()):
                            seg_s = cur_off
                            while (
                                cur_off < end
                                and (vma_base + cur_off) not in visited_pcs
                                and (
                                    (vma_base + cur_off) in proven_data_bytes
                                    or cur_off in self.resolver.guarded_data.get(mod_name, set())
                                )
                            ):
                                cur_off += 1
                            res_state = "PROVEN_DATA"
                        elif cur_off in self.resolver.guarded_pad.get(mod_name, set()):
                            seg_s = cur_off
                            while (
                                cur_off < end
                                and (vma_base + cur_off) not in visited_pcs
                                and (vma_base + cur_off) not in proven_data_bytes
                                and cur_off not in self.resolver.guarded_data.get(mod_name, set())
                                and cur_off in self.resolver.guarded_pad.get(mod_name, set())
                            ):
                                cur_off += 1
                            res_state = "PROVEN_PADDING"
                        else:
                            seg_s = cur_off
                            while (
                                cur_off < end
                                and (vma_base + cur_off) not in visited_pcs
                                and (vma_base + cur_off) not in proven_data_bytes
                                and cur_off not in self.resolver.guarded_data.get(mod_name, set())
                                and cur_off not in self.resolver.guarded_pad.get(mod_name, set())
                            ):
                                cur_off += 1
                            slice_b = raw[seg_s:cur_off]
                            if all(b == 0 for b in slice_b) or all(b == 0xFF for b in slice_b):
                                res_state = "PROVEN_PADDING"
                            else:
                                res_state = "UNKNOWN"

                        blen = cur_off - seg_s
                        all_resolved.append(
                            {
                                "module": mod_name,
                                "offset_start": seg_s,
                                "offset_end_exclusive": cur_off,
                                "byte_length": blen,
                                "resolved_state": res_state,
                            }
                        )

        state_counts: Dict[str, int] = {}
        for r in all_resolved:
            st = r["resolved_state"]
            state_counts[st] = state_counts.get(st, 0) + 1

        unknown_gaps = state_counts.get("UNKNOWN", 0)

        return {
            "total_gaps_audited": len(all_resolved),
            "state_counts": state_counts,
            "residual_undecoded_gaps_before": 1561,
            "residual_undecoded_gaps_after": unknown_gaps,
            "gap_reduction_from_p6": 1561 - unknown_gaps,
            "gap_reduction_from_p3_baseline": 2206 - unknown_gaps,
            "newly_confirmed_code_segments": state_counts.get("CONFIRMED_CODE", 0) - 3046,
            "proven_targets_injected": len(new_targets),
        }


def main():
    repo_root = Path(".")
    closure = CompleteCFGClosure(repo_root)
    result = closure.recompute_closure()

    out_path = repo_root / "workstreams/T2-ASM-07/cfg_closure.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"CFG Closure written to {out_path}")
    print(f"  Proven targets injected: {result['proven_targets_injected']}")
    print(f"  Total gaps audited: {result['total_gaps_audited']}")
    print(f"  State counts: {result['state_counts']}")
    print(f"  Residual unknown gaps: {result['residual_undecoded_gaps_after']} (down from 1561 in P6 and 2206 in P3)")
    print(f"  Gap reduction from P6: {result['gap_reduction_from_p6']}")


if __name__ == "__main__":
    main()
