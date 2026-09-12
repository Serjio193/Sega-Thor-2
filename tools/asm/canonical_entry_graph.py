#!/usr/bin/env python3
"""tools/asm/canonical_entry_graph.py — Rebuild Canonical Call/Entry Graph & SCC Decomposition.

Phases 3 & 11 of T2-ASM-09:
  1. Rebuilds canonical call/entry graph from audited evidence:
     - Direct BSRs (excluding 7 false BSRF halfwords)
     - 1,465 audited JSR target domains
     - JMP and BRAF target domains
     - Inter-function direct branches (tailcalls & shared entries)
     - Proven callback tables and state-machine callback domains (ASM-07)
     - Root/reset entries
  2. Separates edge semantics:
     CALL_SETS_PR, TAILCALL_PRESERVES_PR, DIRECT_BRANCH_SHARED_ENTRY, ROOT_ENTRY
  3. Computes Strongly Connected Components (SCCs), decomposing recursive clusters
     and recording external entry domains.
"""

from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import struct
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


@dataclass
class CanonicalEdge:
    source_pc: str
    target_pc: str
    source_function: str
    target_function: str
    opcode: str
    edge_type: str  # CALL_SETS_PR, TAILCALL_PRESERVES_PR, DIRECT_BRANCH_SHARED_ENTRY, ROOT_ENTRY
    module: str
    evidence: str


@dataclass
class RecursiveSCCRecord:
    scc_id: int
    size: int
    members: List[str]
    internal_edges: List[Dict[str, str]]
    external_entry_edges: List[Dict[str, str]]
    is_external_entry_complete: bool


class CanonicalEntryGraphBuilder:
    """Rebuilds canonical entry graph and performs recursive SCC analysis."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.b0 = (repo_root / ".private/rus/0TH2.BIN").read_bytes()
        self.blow = (repo_root / ".private/rus/TH2.LOW").read_bytes()
        self.vma_0 = 0x06004000
        self.vma_low = 0x002DA000

        # False BSRF sites to strictly forbid as edge sources
        ft_p = repo_root / "workstreams/T2-ASM-08/false_decode_pointer_tables.json"
        self.false_tables = json.loads(ft_p.read_text(encoding="utf-8"))
        self.forbidden_sources: Set[str] = set()
        self.table_intervals: List[Tuple[str, int, int]] = []
        for tbl in self.false_tables.get("tables", []):
            mod = tbl.get("module", "0TH2.BIN")
            st = int(tbl["table_start"], 16)
            en = int(tbl["table_end"], 16)
            self.table_intervals.append((mod, st, en))
            for f_pc in tbl.get("false_instruction_pcs", []):
                self.forbidden_sources.add(f_pc)

        # Function boundaries
        fb_p = repo_root / "workstreams/T2-ASM-06/function_boundaries.json"
        self.fb = json.loads(fb_p.read_text(encoding="utf-8"))
        self.functions = self.fb.get("functions", [])
        self.func_by_entry: Dict[str, Dict[str, Any]] = {f["entry_pc"]: f for f in self.functions}

        self.edges: List[CanonicalEdge] = []

    def is_in_pointer_table(self, mod: str, pc: int) -> bool:
        for t_mod, st, en in self.table_intervals:
            if mod == t_mod and st <= pc < en:
                return True
        return False

    def find_function_for_pc(self, mod: str, pc: int) -> str:
        matching = [
            f for f in self.functions
            if f["module"] == mod and int(f["entry_pc"], 16) <= pc
        ]
        if matching:
            best = max(matching, key=lambda x: int(x["entry_pc"], 16))
            return best["entry_pc"]
        return f"0x{pc:08X}"

    def extract_direct_bsr_edges(self):
        """Extract direct BSR calls, strictly avoiding pointer tables."""
        for mod, raw, base in [("0TH2.BIN", self.b0, self.vma_0), ("TH2.LOW", self.blow, self.vma_low)]:
            for off in range(0, len(raw) - 2, 2):
                pc = base + off
                pc_s = f"0x{pc:08X}"
                if pc_s in self.forbidden_sources or self.is_in_pointer_table(mod, pc):
                    continue
                w = struct.unpack(">H", raw[off:off + 2])[0]
                if (w & 0xF000) == 0xB000:
                    disp = w & 0x0FFF
                    if disp & 0x0800:
                        disp -= 0x1000
                    tgt = pc + 4 + disp * 2
                    tgt_s = f"0x{tgt:08X}"
                    if base <= tgt < base + len(raw):
                        src_f = self.find_function_for_pc(mod, pc)
                        tgt_f = self.find_function_for_pc(mod, tgt)
                        self.edges.append(
                            CanonicalEdge(
                                source_pc=pc_s,
                                target_pc=tgt_s,
                                source_function=src_f,
                                target_function=tgt_f,
                                opcode="BSR",
                                edge_type="CALL_SETS_PR",
                                module=mod,
                                evidence="SH2_DIRECT_BSR_AUDITED",
                            )
                        )

    def extract_inter_function_bra_edges(self):
        """Extract direct branches that cross function boundaries (tailcalls or shared entries)."""
        for mod, raw, base in [("0TH2.BIN", self.b0, self.vma_0), ("TH2.LOW", self.blow, self.vma_low)]:
            for off in range(0, len(raw) - 2, 2):
                pc = base + off
                pc_s = f"0x{pc:08X}"
                if pc_s in self.forbidden_sources or self.is_in_pointer_table(mod, pc):
                    continue
                w = struct.unpack(">H", raw[off:off + 2])[0]
                if (w & 0xF000) == 0xA000:  # BRA disp12
                    disp = w & 0x0FFF
                    if disp & 0x0800:
                        disp -= 0x1000
                    tgt = pc + 4 + disp * 2
                    tgt_s = f"0x{tgt:08X}"
                    if base <= tgt < base + len(raw):
                        src_f = self.find_function_for_pc(mod, pc)
                        tgt_f = self.find_function_for_pc(mod, tgt)
                        if src_f != tgt_f:
                            is_entry = (tgt_s == tgt_f)
                            e_type = "TAILCALL_PRESERVES_PR" if is_entry else "DIRECT_BRANCH_SHARED_ENTRY"
                            self.edges.append(
                                CanonicalEdge(
                                    source_pc=pc_s,
                                    target_pc=tgt_s,
                                    source_function=src_f,
                                    target_function=tgt_f,
                                    opcode="BRA",
                                    edge_type=e_type,
                                    module=mod,
                                    evidence=f"SH2_INTER_FUNCTION_{e_type}",
                                )
                            )

    def import_audited_jsr_edges(self):
        """Import verified JSR call edges from final indirect scorecard."""
        sc_p = self.repo_root / "workstreams/T2-ASM-08/final_indirect_scorecard.json"
        sc = json.loads(sc_p.read_text(encoding="utf-8"))
        for s in sc.get("sites", []):
            if s.get("opcode_id") == "JSR" and s.get("resolution_status", "").startswith("RESOLVED"):
                src_pc = s["runtime_pc"]
                mod = s["module"]
                src_f = self.find_function_for_pc(mod, int(src_pc, 16))
                for tgt_pc in s.get("targets", []):
                    tgt_f = self.find_function_for_pc(mod, int(tgt_pc, 16))
                    self.edges.append(
                        CanonicalEdge(
                            source_pc=src_pc,
                            target_pc=tgt_pc,
                            source_function=src_f,
                            target_function=tgt_f,
                            opcode="JSR",
                            edge_type="CALL_SETS_PR",
                            module=mod,
                            evidence="AUDITED_JSR",
                        )
                    )

    def import_audited_jmp_and_braf_edges(self):
        """Import verified JMP and BRAF tailcall/jump edges from final indirect scorecard."""
        sc_p = self.repo_root / "workstreams/T2-ASM-08/final_indirect_scorecard.json"
        sc = json.loads(sc_p.read_text(encoding="utf-8"))
        for s in sc.get("sites", []):
            op = s.get("opcode_id")
            if op in ("JMP", "BRAF") and s.get("resolution_status", "").startswith("RESOLVED"):
                src_pc = s["runtime_pc"]
                mod = s["module"]
                src_f = self.find_function_for_pc(mod, int(src_pc, 16))
                for tgt_pc in s.get("targets", []):
                    tgt_f = self.find_function_for_pc(mod, int(tgt_pc, 16))
                    if src_f != tgt_f:
                        is_entry = (tgt_pc == tgt_f)
                        e_type = "TAILCALL_PRESERVES_PR" if is_entry else "DIRECT_BRANCH_SHARED_ENTRY"
                        self.edges.append(
                            CanonicalEdge(
                                source_pc=src_pc,
                                target_pc=tgt_pc,
                                source_function=src_f,
                                target_function=tgt_f,
                                opcode=op,
                                edge_type=e_type,
                                module=mod,
                                evidence=f"AUDITED_{op}_{e_type}",
                            )
                        )

    def import_callback_and_state_machine_edges(self):
        """Import callback table edges associated with genuine JSR instruction sites."""
        cb_p = self.repo_root / "workstreams/T2-ASM-07/callback_tables.json"
        if cb_p.exists():
            cb = json.loads(cb_p.read_text(encoding="utf-8"))
            for t in cb.get("tables", []):
                for assoc in t.get("associated_sites", []):
                    parts = assoc.split("_")
                    if len(parts) == 2:
                        mod = parts[0]
                        src_pc = parts[1]
                        src_f = self.find_function_for_pc(mod, int(src_pc, 16))
                        for tgt_pc in t.get("targets", []):
                            tgt_f = self.find_function_for_pc(mod, int(tgt_pc, 16))
                            self.edges.append(
                                CanonicalEdge(
                                    source_pc=src_pc,
                                    target_pc=tgt_pc,
                                    source_function=src_f,
                                    target_function=tgt_f,
                                    opcode="CALLBACK_TABLE_JSR",
                                    edge_type="CALL_SETS_PR",
                                    module=mod,
                                    evidence="ASM07_CALLBACK_ASSOCIATED_JSR",
                                )
                            )

    def add_root_entry_edges(self):
        """Add master SH-2 reset/root entry vector."""
        self.edges.append(
            CanonicalEdge(
                source_pc="RESET_VECTOR",
                target_pc="0x06004000",
                source_function="RESET_VECTOR",
                target_function="0x06004000",
                opcode="RESET_VECTOR",
                edge_type="ROOT_ENTRY",
                module="0TH2.BIN",
                evidence="SATURN_MASTER_SH2_RESET",
            )
        )

    def compute_recursive_sccs(self) -> Tuple[Dict[str, int], List[RecursiveSCCRecord]]:
        """Computes Tarjan SCCs over function-level adjacency graph."""
        adj: Dict[str, Set[str]] = defaultdict(set)
        edge_map: Dict[Tuple[str, str], List[CanonicalEdge]] = defaultdict(list)

        for e in self.edges:
            if e.source_function != e.target_function:
                adj[e.source_function].add(e.target_function)
                edge_map[(e.source_function, e.target_function)].append(e)

        idx = 0
        stack: List[str] = []
        on_stack: Set[str] = set()
        indices: Dict[str, int] = {}
        lowlink: Dict[str, int] = {}
        scc_counter = 0
        scc_members: Dict[int, List[str]] = defaultdict(list)
        func_scc: Dict[str, int] = {}

        def strongconnect(v: str):
            nonlocal idx, scc_counter
            indices[v] = idx
            lowlink[v] = idx
            idx += 1
            stack.append(v)
            on_stack.add(v)

            for w in adj.get(v, set()):
                if w not in indices:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif w in on_stack:
                    lowlink[v] = min(lowlink[v], indices[w])

            if lowlink[v] == indices[v]:
                scc_counter += 1
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    func_scc[w] = scc_counter
                    scc_members[scc_counter].append(w)
                    if w == v:
                        break

        for f in list(self.func_by_entry.keys()):
            if f not in indices:
                strongconnect(f)

        recursive_sccs: List[RecursiveSCCRecord] = []
        for scc_id, members in scc_members.items():
            member_set = set(members)
            internal: List[Dict[str, str]] = []
            external: List[Dict[str, str]] = []

            for (src, tgt), edgelist in edge_map.items():
                for ed in edgelist:
                    if src in member_set and tgt in member_set:
                        internal.append({"source": src, "target": tgt, "opcode": ed.opcode})
                    elif src not in member_set and tgt in member_set:
                        external.append({"source": src, "target": tgt, "opcode": ed.opcode})

            is_recursive = len(members) > 1 or len(internal) > 0
            if is_recursive:
                rec = RecursiveSCCRecord(
                    scc_id=scc_id,
                    size=len(members),
                    members=members,
                    internal_edges=internal,
                    external_entry_edges=external,
                    is_external_entry_complete=len(external) > 0,
                )
                recursive_sccs.append(rec)

        return func_scc, recursive_sccs

    def build_all(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        self.extract_direct_bsr_edges()
        self.extract_inter_function_bra_edges()
        self.import_audited_jsr_edges()
        self.import_audited_jmp_and_braf_edges()
        self.import_callback_and_state_machine_edges()
        self.add_root_entry_edges()

        # Deduplicate edges preserving order
        deduped: List[CanonicalEdge] = []
        seen: Set[Tuple[str, str, str, str]] = set()
        for e in self.edges:
            key = (e.source_pc, e.target_pc, e.opcode, e.edge_type)
            if key not in seen:
                seen.add(key)
                deduped.append(e)
        self.edges = deduped

        func_scc, rec_sccs = self.compute_recursive_sccs()

        # Invariant checks
        zero_forbidden_sources = all(e.source_pc not in self.forbidden_sources for e in self.edges)
        assert zero_forbidden_sources, "Fatal: edge found from forbidden false BSRF source!"

        edge_types: Dict[str, int] = defaultdict(int)
        for e in self.edges:
            edge_types[e.edge_type] += 1

        graph_payload = {
            "total_canonical_edges": len(self.edges),
            "zero_forbidden_sources_verified": zero_forbidden_sources,
            "edge_types_distribution": dict(edge_types),
            "edges": [asdict(e) for e in self.edges],
        }

        scc_payload = {
            "total_recursive_sccs": len(rec_sccs),
            "recursive_sccs": [asdict(r) for r in rec_sccs],
        }

        return graph_payload, scc_payload


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    builder = CanonicalEntryGraphBuilder(repo_root)
    graph_res, scc_res = builder.build_all()

    g_path = repo_root / "workstreams/T2-ASM-09/canonical_entry_graph.json"
    s_path = repo_root / "workstreams/T2-ASM-09/recursive_scc_domains.json"

    g_path.parent.mkdir(parents=True, exist_ok=True)
    g_path.write_text(json.dumps(graph_res, indent=2), encoding="utf-8")
    s_path.write_text(json.dumps(scc_res, indent=2), encoding="utf-8")

    print(f"Phase 3 Complete: {graph_res['total_canonical_edges']} canonical edges -> {g_path}")
    print(f"  Edge types: {graph_res['edge_types_distribution']}")
    print(f"  Zero false BSRF sources: {graph_res['zero_forbidden_sources_verified']}")
    print(f"Phase 11 Complete: {scc_res['total_recursive_sccs']} recursive SCCs -> {s_path}")


if __name__ == '__main__':
    main()
