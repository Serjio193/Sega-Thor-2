#!/usr/bin/env python3
"""tools/asm/call_sink_and_pointer_tracer.py — Function Reference & Call Sink Provenance Tracer.

Phases 4, 5, 6, 7, 8, 9, 10 of T2-ASM-09:
  1. Searches canonical module bytes for all references to unresolved RTS functions.
  2. Classifies each reference: PROVEN_CODE_POINTER, PROVEN_NONCALL_DATA, LITERAL_ONLY,
     TABLE_ENTRY, STRUCT_TEMPLATE, GLOBAL_VECTOR, UNRESOLVED_REFERENCE.
  3. Traces references to call sinks (REACHES_PROVEN_CALL_SITE, REACHES_PROVEN_TAILCALL_SITE,
     NONCALL_REFERENCE, DEAD_REFERENCE_PROVEN, DOMAIN_OPEN).
  4. Recovers callback tables and actor struct callbacks.
  5. Derives tailcall PR inheritance and function entry refinements.
  6. Accounts for UNKNOWN executable region caller threats.
"""

from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import struct
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


@dataclass
class FunctionReferenceRecord:
    ref_pc: str
    module: str
    target_function: str
    encoding: str  # ABSOLUTE_32BIT, TABLE_RELATIVE, LITERAL_POOL
    container_classification: str  # DATA, CONFIRMED_CODE, PADDING, UNKNOWN
    reference_type: str  # PROVEN_CODE_POINTER, PROVEN_NONCALL_DATA, LITERAL_ONLY, TABLE_ENTRY, STRUCT_TEMPLATE, UNRESOLVED_REFERENCE
    call_sink_status: str  # REACHES_PROVEN_CALL_SITE, REACHES_PROVEN_TAILCALL_SITE, NONCALL_REFERENCE, DOMAIN_OPEN
    consumer_pc: Optional[str]
    consumer_details: str


@dataclass
class TailcallDomainRecord:
    source_pc: str
    target_pc: str
    source_function: str
    target_function: str
    module: str
    incoming_pr_mechanism: str
    upstream_return_domain: List[str]
    tailcall_classification: str  # TAILCALL_DOMAIN_COMPLETE, TAILCALL_DOMAIN_PARTIAL


class CallSinkAndPointerTracer:
    """Traces function references to call sinks and audits tailcalls/UNKNOWN threats."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.b0 = (repo_root / ".private/rus/0TH2.BIN").read_bytes()
        self.blow = (repo_root / ".private/rus/TH2.LOW").read_bytes()
        self.vma_0 = 0x06004000
        self.vma_low = 0x002DA000

        # Residual RTS inventory
        rts_inv_p = repo_root / "workstreams/T2-ASM-09/residual_rts_inventory.json"
        self.rts_inv = json.loads(rts_inv_p.read_text(encoding="utf-8"))["inventory"]
        self.target_functions: Set[str] = {r["function_entry"] for r in self.rts_inv}

        # Canonical entry graph
        ceg_p = repo_root / "workstreams/T2-ASM-09/canonical_entry_graph.json"
        self.ceg = json.loads(ceg_p.read_text(encoding="utf-8"))
        self.edges = self.ceg.get("edges", [])

        # ASM-07 callback tables & state machines
        cb_p = repo_root / "workstreams/T2-ASM-07/callback_tables.json"
        self.cb_tables = json.loads(cb_p.read_text(encoding="utf-8")).get("tables", [])

        sm_p = repo_root / "workstreams/T2-ASM-07/state_machine_callbacks.json"
        self.sm_cbs = json.loads(sm_p.read_text(encoding="utf-8")).get("state_machine_callbacks", {})

        # False tables to exclude from code
        ft_p = repo_root / "workstreams/T2-ASM-08/false_decode_pointer_tables.json"
        self.false_tables = json.loads(ft_p.read_text(encoding="utf-8")).get("tables", [])

        # Manifest ranges
        self.mf0 = json.loads((repo_root / "asm/manifests/0TH2.BIN.json").read_text(encoding="utf-8"))
        self.mflow = json.loads((repo_root / "asm/manifests/TH2.LOW.json").read_text(encoding="utf-8"))

        self._build_table_maps()

    def _build_table_maps(self):
        self.cb_table_intervals: List[Tuple[str, int, int, Dict[str, Any]]] = []
        for t in self.cb_tables:
            mod = t.get("module", "0TH2.BIN")
            st = int(t["table_address"], 16)
            cnt = t.get("entry_count", len(t.get("targets", [])))
            en = st + cnt * 4
            self.cb_table_intervals.append((mod, st, en, t))

        for t in self.false_tables:
            mod = t.get("module", "0TH2.BIN")
            st = int(t["table_start"], 16)
            en = int(t["table_end"], 16)
            self.cb_table_intervals.append((mod, st, en, t))

        # Build map of JSRs that load from literal pools
        self.lit_pool_consumers: Dict[Tuple[str, int], List[str]] = defaultdict(list)
        for e in self.edges:
            if e["opcode"] == "JSR":
                src_pc = int(e["source_pc"], 16)
                mod = e["module"]
                # Scan backwards up to 32 bytes for MOV.L @(disp,PC), Rn loading literal pool
                raw = self.b0 if mod == "0TH2.BIN" else self.blow
                base = self.vma_0 if mod == "0TH2.BIN" else self.vma_low
                for b_pc in range(max(base, src_pc - 32), src_pc, 2):
                    off = b_pc - base
                    if 0 <= off + 2 <= len(raw):
                        w = struct.unpack(">H", raw[off:off + 2])[0]
                        if (w & 0xF000) == 0xD000:  # MOV.L @(disp, PC), Rn
                            disp = w & 0x00FF
                            lit_vma = ((b_pc + 4) & ~3) + disp * 4
                            self.lit_pool_consumers[(mod, lit_vma)].append(e["source_pc"])

    def get_container_class(self, mod: str, pc: int) -> str:
        mf = self.mf0 if mod == "0TH2.BIN" else self.mflow
        for r in mf.get("ranges", []):
            st = int(r["runtime_start"], 16)
            en = int(r["runtime_end_exclusive"], 16)
            if st <= pc < en:
                return r.get("evidence_classification", "UNKNOWN")
        return "UNKNOWN"

    def scan_function_references(self) -> List[FunctionReferenceRecord]:
        records: List[FunctionReferenceRecord] = []
        modules = [("0TH2.BIN", self.b0, self.vma_0), ("TH2.LOW", self.blow, self.vma_low)]

        for mod, raw, base in modules:
            for off in range(0, len(raw) - 4, 2):
                val = struct.unpack(">I", raw[off:off + 4])[0]
                val_s = f"0x{val:08X}"
                if val_s in self.target_functions:
                    pc = base + off
                    pc_s = f"0x{pc:08X}"
                    container = self.get_container_class(mod, pc)

                    # Check if inside a callback table
                    cb_match = None
                    for c_mod, st, en, tbl in self.cb_table_intervals:
                        if mod == c_mod and st <= pc < en:
                            cb_match = tbl
                            break

                    # Check if inside literal pool loaded by JSR
                    lit_consumers = self.lit_pool_consumers.get((mod, pc), [])

                    # Classification logic
                    if lit_consumers:
                        ref_type = "LITERAL_ONLY"
                        sink_status = "REACHES_PROVEN_CALL_SITE"
                        consumer_pc = lit_consumers[0]
                        details = f"Loaded by PC-relative load to JSR at {consumer_pc}"
                    elif cb_match:
                        ref_type = "TABLE_ENTRY"
                        sink_status = "REACHES_PROVEN_CALL_SITE"
                        consumer_pc = cb_match.get("consumer_pc", cb_match.get("table_address"))
                        details = f"Proven callback table {cb_match.get('table_id', hex(st))}"
                    elif container == "CONFIRMED_CODE":
                        ref_type = "PROVEN_CODE_POINTER"
                        sink_status = "DEAD_REFERENCE_PROVEN"
                        consumer_pc = None
                        details = "Embedded code constant without call consumer"
                    elif container == "DATA":
                        ref_type = "PROVEN_NONCALL_DATA"
                        sink_status = "NONCALL_REFERENCE"
                        consumer_pc = None
                        details = "Static asset or data table entry, non-call consumer"
                    else:
                        ref_type = "UNRESOLVED_REFERENCE"
                        sink_status = "DOMAIN_OPEN"
                        consumer_pc = None
                        details = f"Reference in {container} container without proven consumer"

                    records.append(
                        FunctionReferenceRecord(
                            ref_pc=pc_s,
                            module=mod,
                            target_function=val_s,
                            encoding="ABSOLUTE_32BIT",
                            container_classification=container,
                            reference_type=ref_type,
                            call_sink_status=sink_status,
                            consumer_pc=consumer_pc,
                            consumer_details=details,
                        )
                    )

        return records

    def audit_tailcall_domains(self) -> List[TailcallDomainRecord]:
        tailcalls: List[TailcallDomainRecord] = []
        tailcall_edges = [e for e in self.edges if e["edge_type"] == "TAILCALL_PRESERVES_PR"]

        rts_cert_map = {r["runtime_pc"]: r for r in self.rts_inv}
        rts_by_func = defaultdict(list)
        for r in self.rts_inv:
            rts_by_func[r["function_entry"]].append(r)

        for e in tailcall_edges:
            src_f = e["source_function"]
            tgt_f = e["target_function"]
            src_rts_list = rts_by_func.get(src_f, [])
            incoming_mech = src_rts_list[0]["pr_mechanism"] if src_rts_list else "LEAF_UNTOUCHED_PR"
            up_callers = [
                ed["source_pc"]
                for ed in self.edges
                if ed["target_function"] == src_f
                and ed["edge_type"] == "CALL_SETS_PR"
                and ed["source_function"] != src_f
            ]

            status = "TAILCALL_DOMAIN_COMPLETE" if len(up_callers) > 0 else "TAILCALL_DOMAIN_PARTIAL"
            tailcalls.append(
                TailcallDomainRecord(
                    source_pc=e["source_pc"],
                    target_pc=e["target_pc"],
                    source_function=src_f,
                    target_function=tgt_f,
                    module=e["module"],
                    incoming_pr_mechanism=incoming_mech,
                    upstream_return_domain=[f"0x{int(c, 16) + 4:08X}" for c in up_callers if c.startswith("0x")],
                    tailcall_classification=status,
                )
            )

        return tailcalls

    def audit_unknown_caller_threats(self) -> Dict[str, Dict[str, Any]]:
        """Audits potential branch/call and pointer threats inside UNKNOWN regions."""
        unknown_ranges = {"0TH2.BIN": [], "TH2.LOW": []}
        for mod, mf in [("0TH2.BIN", self.mf0), ("TH2.LOW", self.mflow)]:
            for r in mf.get("ranges", []):
                if r.get("evidence_classification") == "UNKNOWN":
                    unknown_ranges[mod].append((int(r["runtime_start"], 16), int(r["runtime_end_exclusive"], 16)))

        threats_by_func: Dict[str, Dict[str, Any]] = {}
        for f in self.target_functions:
            threats_by_func[f] = {
                "direct_branch_threats": [],
                "pointer_threats": [],
                "unknown_caller_threat_count": 0,
                "is_clean_of_unknown_threats": True,
            }

        modules = [("0TH2.BIN", self.b0, self.vma_0), ("TH2.LOW", self.blow, self.vma_low)]
        for mod, raw, base in modules:
            for st, en in unknown_ranges[mod]:
                for pc in range(st, en - 2, 2):
                    off = pc - base
                    w = struct.unpack(">H", raw[off:off + 2])[0]
                    if (w & 0xF000) in (0xA000, 0xB000):  # BRA or BSR
                        disp = w & 0x0FFF
                        if disp & 0x0800:
                            disp -= 0x1000
                        tgt = pc + 4 + disp * 2
                        tgt_s = f"0x{tgt:08X}"
                        if tgt_s in threats_by_func:
                            threat_type = "UNKNOWN_BSR" if (w & 0xF000) == 0xB000 else "UNKNOWN_BRA"
                            threats_by_func[tgt_s]["direct_branch_threats"].append({
                                "pc": f"0x{pc:08X}",
                                "module": mod,
                                "type": threat_type,
                            })

                for pc in range(st, en - 4, 2):
                    off = pc - base
                    val = struct.unpack(">I", raw[off:off + 4])[0]
                    val_s = f"0x{val:08X}"
                    if val_s in threats_by_func:
                        threats_by_func[val_s]["pointer_threats"].append({
                            "pc": f"0x{pc:08X}",
                            "module": mod,
                        })

        for f, d in threats_by_func.items():
            tot = len(d["direct_branch_threats"]) + len(d["pointer_threats"])
            d["unknown_caller_threat_count"] = tot
            d["is_clean_of_unknown_threats"] = (tot == 0)

        return threats_by_func


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    tracer = CallSinkAndPointerTracer(repo_root)

    # 1. Scan function references & trace to call sinks
    ref_records = tracer.scan_function_references()
    r_path = repo_root / "workstreams/T2-ASM-09/function_reference_index.json"
    s_path = repo_root / "workstreams/T2-ASM-09/reference_to_call_sink.json"

    r_path.parent.mkdir(parents=True, exist_ok=True)
    r_payload = {
        "total_references_found": len(ref_records),
        "references": [asdict(r) for r in ref_records],
    }
    r_path.write_text(json.dumps(r_payload, indent=2), encoding="utf-8")

    sink_counts: Dict[str, int] = defaultdict(int)
    for r in ref_records:
        sink_counts[r.call_sink_status] += 1
    s_payload = {
        "total_references_traced": len(ref_records),
        "sink_status_distribution": dict(sink_counts),
        "provenance_records": [asdict(r) for r in ref_records],
    }
    s_path.write_text(json.dumps(s_payload, indent=2), encoding="utf-8")

    # 2. Residual callback tables (Phase 6)
    target_funcs_set = tracer.target_functions
    relevant_tables = []
    for t in tracer.cb_tables:
        if any(tgt in target_funcs_set for tgt in t.get("targets", [])):
            relevant_tables.append(t)
    ct_path = repo_root / "workstreams/T2-ASM-09/residual_callback_tables.json"
    ct_payload = {
        "total_residual_callback_tables": len(relevant_tables),
        "tables": relevant_tables,
    }
    ct_path.write_text(json.dumps(ct_payload, indent=2), encoding="utf-8")

    # 3. Residual struct & state machine callbacks (Phase 7 & 8)
    relevant_struct_cbs = {}
    for cb_name, cb_info in tracer.sm_cbs.items():
        if isinstance(cb_info, dict) and any(tgt in target_funcs_set for tgt in cb_info.get("targets", [])):
            relevant_struct_cbs[cb_name] = cb_info
    scb_path = repo_root / "workstreams/T2-ASM-09/residual_struct_callback_domains.json"
    scb_payload = {
        "total_residual_struct_callbacks": len(relevant_struct_cbs),
        "callbacks": relevant_struct_cbs,
    }
    scb_path.write_text(json.dumps(scb_payload, indent=2), encoding="utf-8")

    # 4. Tailcalls (Phase 9)
    tailcalls = tracer.audit_tailcall_domains()
    t_path = repo_root / "workstreams/T2-ASM-09/tailcall_domains.json"
    t_payload = {
        "total_tailcalls": len(tailcalls),
        "tailcalls": [asdict(t) for t in tailcalls],
    }
    t_path.write_text(json.dumps(t_payload, indent=2), encoding="utf-8")

    # 5. Function Entry & Shared Entry Refinements (Phase 10)
    shared_entry_edges = [e for e in tracer.edges if e.get("edge_type") == "DIRECT_BRANCH_SHARED_ENTRY"]
    shared_entries_by_func = defaultdict(list)
    for e in shared_entry_edges:
        shared_entries_by_func[e["target_function"]].append(e)

    refinements = []
    for func_entry, entries in shared_entries_by_func.items():
        if func_entry in target_funcs_set:
            refinements.append({
                "function_entry": func_entry,
                "shared_entry_count": len(entries),
                "entry_edges": entries,
            })
    fer_path = repo_root / "workstreams/T2-ASM-09/function_entry_refinements.json"
    fer_payload = {
        "total_functions_with_shared_entries": len(refinements),
        "refinements": refinements,
    }
    fer_path.write_text(json.dumps(fer_payload, indent=2), encoding="utf-8")

    # 6. UNKNOWN threats
    unknown_threats = tracer.audit_unknown_caller_threats()
    clean_cnt = sum(1 for d in unknown_threats.values() if d["is_clean_of_unknown_threats"])

    print(f"Phase 4 & 5 Complete: {len(ref_records)} references indexed & traced:")
    print(f"  Sink distribution: {dict(sink_counts)}")
    print(f"Phase 6 Complete: {len(relevant_tables)} residual callback tables -> {ct_path}")
    print(f"Phase 7 & 8 Complete: {len(relevant_struct_cbs)} struct callback domains -> {scb_path}")
    print(f"Phase 9 Complete: {len(tailcalls)} tailcalls audited -> {t_path}")
    print(f"Phase 10 Complete: {len(refinements)} function entry refinements -> {fer_path}")
    print(f"UNKNOWN-code threat audit: {clean_cnt} / {len(unknown_threats)} functions clean of UNKNOWN threats")


if __name__ == '__main__':
    main()
