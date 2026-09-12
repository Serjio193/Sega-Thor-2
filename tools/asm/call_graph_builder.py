#!/usr/bin/env python3
"""tools/asm/call_graph_builder.py — Thor 2 Call Graph & Function Boundary Recovery.

Constructs an inter-procedural call graph from direct calls (BSR) and resolved
indirect calls (JSR/JMP), identifying function entry points, epilogues,
and caller/callee relationships across 0TH2.BIN and TH2.LOW.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
import json
import struct


@dataclass
class CallEdge:
    source_pc: str
    target_pc: str
    opcode: str
    call_type: str
    module: str
    evidence: str


@dataclass
class FunctionBoundaryRecord:
    function_id: str
    module: str
    entry_pc: str
    exit_pc: Optional[str]
    byte_length: int
    has_pr_spill: bool
    is_leaf: bool
    incoming_callers_count: int
    outgoing_callees_count: int
    rts_sites: List[str]


class CallGraphBuilder:
    """Builds call graph and refines function boundaries."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.th2_0 = (repo_root / ".private/rus/0TH2.BIN").read_bytes()
        self.th2_low = (repo_root / ".private/rus/TH2.LOW").read_bytes()
        self.edges: List[CallEdge] = []
        self.functions: Dict[str, FunctionBoundaryRecord] = {}

    def extract_direct_calls(self, mod_name: str, vma_base: int, raw: bytes):
        raw_len = len(raw)
        for off in range(0, raw_len - 2, 2):
            pc = vma_base + off
            w = struct.unpack('>H', raw[off : off + 2])[0]
            if (w & 0xF000) == 0xB000: # BSR disp12
                disp = w & 0x0FFF
                if disp & 0x0800:
                    disp -= 0x1000
                target = pc + 4 + disp * 2
                if vma_base <= target < vma_base + raw_len:
                    self.edges.append(
                        CallEdge(
                            source_pc=f"0x{pc:08X}",
                            target_pc=f"0x{target:08X}",
                            opcode="BSR",
                            call_type="DIRECT_NEAR",
                            module=mod_name,
                            evidence="BSR_DISPLACEMENT_EXACT",
                        )
                    )

    def import_resolved_indirect(self, reg_prov_path: Path):
        data = json.loads(reg_prov_path.read_text())
        for r in data["records"]:
            if r["is_resolved_target"] and r["exact_value"] and r["opcode_id"] == "JSR":
                self.edges.append(
                    CallEdge(
                        source_pc=r["runtime_pc"],
                        target_pc=r["exact_value"],
                        opcode="JSR",
                        call_type="INDIRECT_RESOLVED",
                        module=r["module"],
                        evidence=f"REGISTER_PROVENANCE_{r['origin']}",
                    )
                )

    def recover_boundaries(self, mod_name: str, vma_base: int, raw: bytes):
        call_targets: Set[int] = {
            int(e.target_pc, 16) for e in self.edges if e.module == mod_name
        }
        if mod_name == "0TH2.BIN":
            call_targets.add(0x06004000)
        elif mod_name == "TH2.LOW":
            call_targets.add(0x002E9910)

        raw_len = len(raw)
        # Scan for function entry heuristics: targets of calls, STS.L PR, @-R15
        entries = sorted(list(call_targets))
        for i, entry in enumerate(entries):
            off = entry - vma_base
            if not (0 <= off < raw_len):
                continue

            # Look forward up to next entry or RTS
            next_entry = entries[i + 1] if i + 1 < len(entries) else vma_base + raw_len
            cur_pc = entry
            rts_list: List[str] = []
            has_pr = False
            last_rts = None

            while cur_pc < next_entry and cur_pc - vma_base + 2 <= raw_len:
                c_off = cur_pc - vma_base
                w = struct.unpack('>H', raw[c_off : c_off + 2])[0]
                if w == 0x4F22: # STS.L PR, @-R15
                    has_pr = True
                elif w == 0x000B: # RTS
                    rts_list.append(f"0x{cur_pc:08X}")
                    last_rts = cur_pc + 2 # include delay slot
                cur_pc += 2

            exit_pc = f"0x{last_rts:08X}" if last_rts else None
            length = (last_rts - entry) if last_rts else (next_entry - entry)

            func_id = f"sub_{entry:08X}"
            self.functions[func_id] = FunctionBoundaryRecord(
                function_id=func_id,
                module=mod_name,
                entry_pc=f"0x{entry:08X}",
                exit_pc=exit_pc,
                byte_length=max(2, length),
                has_pr_spill=has_pr,
                is_leaf=len(rts_list) > 0 and not has_pr,
                incoming_callers_count=sum(1 for e in self.edges if e.target_pc == f"0x{entry:08X}"),
                outgoing_callees_count=sum(1 for e in self.edges if entry <= int(e.source_pc, 16) < (last_rts or next_entry)),
                rts_sites=rts_list,
            )

    def build_all(self):
        self.extract_direct_calls("0TH2.BIN", 0x06004000, self.th2_0)
        self.extract_direct_calls("TH2.LOW", 0x002DA000, self.th2_low)
        self.import_resolved_indirect(self.repo_root / "workstreams/T2-ASM-06/register_provenance.json")
        self.recover_boundaries("0TH2.BIN", 0x06004000, self.th2_0)
        self.recover_boundaries("TH2.LOW", 0x002DA000, self.th2_low)


def main():
    repo_root = Path(".")
    builder = CallGraphBuilder(repo_root)
    builder.build_all()

    cg_out = repo_root / "workstreams/T2-ASM-06/call_graph.json"
    cg_out.write_text(json.dumps({
        "total_nodes": len(builder.functions),
        "total_edges": len(builder.edges),
        "edges": [asdict(e) for e in builder.edges],
    }, indent=2))

    fb_out = repo_root / "workstreams/T2-ASM-06/function_boundaries.json"
    fb_out.write_text(json.dumps({
        "total_functions": len(builder.functions),
        "functions": [asdict(f) for f in builder.functions.values()],
    }, indent=2))

    print(f"Call Graph: {len(builder.functions)} nodes, {len(builder.edges)} edges saved to {cg_out}")
    print(f"Function Boundaries: {len(builder.functions)} functions saved to {fb_out}")


if __name__ == '__main__':
    main()
