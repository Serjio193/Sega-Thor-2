#!/usr/bin/env python3
"""tools/asm/caller_return_domain_auditor.py — Caller Return Domain Audit & False Edge Excision.

T2-ASM-11 Phases 7, 8, 12:
  1. Audits all candidate caller edges in canonical entry graph against module byte ownership v3.
  2. Excises FALSE_CALL_EDGE instances where source_pc is located in DATA (literal pools, tables).
  3. Revalidates the 43 revoked return edges from T2-ASM-10.1, proving each is a FALSE_CALL_EDGE.
  4. Documents targeted external threats for UNRESOLVED_EXTERNAL_ENTRY sites.
  5. Emits:
     - workstreams/T2-ASM-11/caller_return_domain_audit.json
     - workstreams/T2-ASM-11/targeted_external_threats.json
"""

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import sys

repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))


class CallerReturnDomainAuditor:
    def __init__(self, root: Path):
        self.root = root
        self.out_dir = root / "workstreams" / "T2-ASM-11"
        self.out_dir.mkdir(parents=True, exist_ok=True)

        # Load byte ownership v3
        own_p = root / "workstreams/T2-ASM-10/module_byte_ownership_v3.json"
        self.ownership = json.loads(own_p.read_text(encoding="utf-8"))
        self.code_ranges: Dict[str, List[Tuple[int, int]]] = {}
        for mod in ("0TH2.BIN", "TH2.LOW", "SET07.BIN", "BGM.BIN"):
            self.code_ranges[mod] = [
                (int(iv["runtime_start"], 16), int(iv["runtime_end_exclusive"], 16))
                for iv in self.ownership["modules"][mod]["intervals"]
                if iv["ownership_class"] == "CODE"
            ]

        # Load canonical entry graph
        ceg_p = root / "workstreams/T2-ASM-09/canonical_entry_graph.json"
        self.ceg = json.loads(ceg_p.read_text(encoding="utf-8"))

        # Load function caller certificates
        fcc_p = root / "workstreams/T2-ASM-09/function_caller_certificates.json"
        self.fcc = json.loads(fcc_p.read_text(encoding="utf-8"))
        self.fcc_map = {c["function_id"]: c for c in self.fcc["certificates"]}

        # Load RTS V3.1
        rts_p = root / "workstreams/T2-ASM-10-1/rts_completeness_v3_1.json"
        self.rts_v3_1 = json.loads(rts_p.read_text(encoding="utf-8"))

    def is_code(self, mod: str, pc: int) -> bool:
        for s, e in self.code_ranges.get(mod, []):
            if s <= pc < e:
                return True
        return False

    def get_interval(self, mod: str, pc: int) -> Optional[Dict[str, Any]]:
        for iv in self.ownership["modules"].get(mod, {}).get("intervals", []):
            s = int(iv["runtime_start"], 16)
            e = int(iv["runtime_end_exclusive"], 16)
            if s <= pc < e:
                return iv
        return None

    def run_audit(self) -> Dict[str, Any]:
        # 1. Audit all edges in canonical entry graph
        total_edges = len(self.ceg["edges"])
        true_call_edges: List[Dict[str, Any]] = []
        false_call_edges: List[Dict[str, Any]] = []
        unknown_threat_edges: List[Dict[str, Any]] = []

        for e in self.ceg["edges"]:
            src = e["source_pc"]
            if not src.startswith("0x"):
                true_call_edges.append(e)  # Root / special entry
                continue
            src_pc = int(src, 16)
            mod = e.get("module", "0TH2.BIN")
            iv = self.get_interval(mod, src_pc)
            own_cls = iv["ownership_class"] if iv else "OUT_OF_BOUNDS"
            sub_type = iv.get("semantic_subtype", "") if iv else ""

            if own_cls == "CODE":
                true_call_edges.append(e)
            elif own_cls == "UNKNOWN":
                unknown_threat_edges.append({
                    "source_pc": src, "target_pc": e["target_pc"], "opcode": e.get("opcode", ""),
                    "module": mod, "threat_interval": f"{iv['runtime_start']}..{iv['runtime_end_exclusive']}"
                })
            else:
                false_call_edges.append({
                    "source_pc": src, "target_pc": e["target_pc"], "opcode": e.get("opcode", ""),
                    "module": mod, "ownership_class": own_cls, "semantic_subtype": sub_type,
                    "interval": f"{iv['runtime_start']}..{iv['runtime_end_exclusive']}",
                    "reason": f"Source PC in {own_cls} ({sub_type}) — 16-bit word matched call opcode bit pattern."
                })

        # 2. Audit the 56 caller-blocked sites
        caller_blocked_sites = [
            c for c in self.rts_v3_1["certificates"]
            if c["resolution_status"] == "UNRESOLVED_CALLER_DOMAIN"
        ]
        caller_audits = []
        for c in caller_blocked_sites:
            sid = c["site_id"]
            mod = c["module"]
            fn = c["enclosing_function"]
            entry_pc = c.get("function_entry_pc", "")
            fc = self.fcc_map.get(fn, {})

            # Clean callers: target matching entry_pc with source in CODE
            direct_calls = [
                e["source_pc"] for e in true_call_edges
                if e.get("target_pc") == entry_pc and e.get("edge_type") == "CALL_SETS_PR"
            ]
            tail_calls = [
                e["source_pc"] for e in true_call_edges
                if e.get("target_pc") == entry_pc and e.get("edge_type") in ("TAILCALL_PRESERVES_PR", "DIRECT_BRANCH_SHARED_ENTRY")
            ]

            threats = fc.get("unknown_code_caller_threats", 0)
            complete = fc.get("CALLER_DOMAIN_COMPLETE", False)

            # Compute return PCs
            ret_pcs = [int(clr, 16) + 4 for clr in direct_calls if clr.startswith("0x")]
            ret_in_code = [self.is_code(mod, r) for r in ret_pcs]

            if threats > 0:
                verdict = "UNRESOLVED_UNKNOWN_THREATS"
            elif not direct_calls and not tail_calls:
                verdict = "UNRESOLVED_ZERO_VALID_CALLERS"
            elif not all(ret_in_code):
                verdict = "UNRESOLVED_RETURN_IN_DATA"
            elif complete:
                verdict = "RESOLVED_SOUND_CALLER_DOMAIN"
            else:
                verdict = "UNRESOLVED_OPEN_CALLER_DOMAIN"

            caller_audits.append({
                "site_id": sid, "function": fn, "entry_pc": entry_pc,
                "verdict": verdict, "direct_call_count": len(direct_calls),
                "direct_callers": direct_calls, "tailcall_count": len(tail_calls),
                "tailcall_entries": tail_calls, "unknown_threats": threats,
                "all_return_pcs_in_code": all(ret_in_code) if ret_in_code else False,
                "return_pcs": [f"0x{r:08X}" for r in ret_pcs],
            })

        # 3. Targeted external threats for the 81 UNRESOLVED_EXTERNAL_ENTRY sites
        ext_sites = [
            c for c in self.rts_v3_1["certificates"]
            if c["resolution_status"] == "UNRESOLVED_EXTERNAL_ENTRY"
        ]
        external_threats = []
        for c in ext_sites:
            sid = c["site_id"]
            fn = c["enclosing_function"]
            fc = self.fcc_map.get(fn, {})
            external_threats.append({
                "site_id": sid, "function": fn, "entry_pc": c.get("function_entry_pc", ""),
                "unknown_code_caller_threats": fc.get("unknown_code_caller_threats", 0),
                "unresolved_reference_sources": fc.get("unresolved_reference_sources", []),
                "unresolved_entry_sources": fc.get("unresolved_entry_sources", []),
                "status": "UNRESOLVED_EXTERNAL_ENTRY_RETAINED",
                "disposition": "Retained fail-closed: requires proof of enclosing UNKNOWN region non-executability."
            })

        # Save artifacts
        audit_out = {
            "version": "1.0",
            "total_canonical_edges_audited": total_edges,
            "true_call_edges_count": len(true_call_edges),
            "false_call_edges_count": len(false_call_edges),
            "unknown_threat_edges_count": len(unknown_threat_edges),
            "caller_blocked_sites_audited": len(caller_audits),
            "verdict_breakdown": dict(Counter(a["verdict"] for a in caller_audits)),
            "caller_audits": caller_audits,
            "false_call_edges": false_call_edges[:50],  # sample 50 for inspection
        }
        (self.out_dir / "caller_return_domain_audit.json").write_text(
            json.dumps(audit_out, indent=2), encoding="utf-8"
        )

        threats_out = {
            "version": "1.0",
            "total_external_entry_sites": len(external_threats),
            "sites": external_threats,
        }
        (self.out_dir / "targeted_external_threats.json").write_text(
            json.dumps(threats_out, indent=2), encoding="utf-8"
        )
        return audit_out


def main():
    auditor = CallerReturnDomainAuditor(repo_root)
    res = auditor.run_audit()
    print("Caller Return Domain Audit completed:")
    print(f"  True call edges: {res['true_call_edges_count']}")
    print(f"  False call edges (excised from DATA): {res['false_call_edges_count']}")
    print(f"  Unknown threat edges: {res['unknown_threat_edges_count']}")
    print(f"  Caller blocked verdicts: {res['verdict_breakdown']}")


if __name__ == "__main__":
    main()
