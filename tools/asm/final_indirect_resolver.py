#!/usr/bin/env python3
"""tools/asm/final_indirect_resolver.py — Master Synthesis for Indirect Dispatch & Return Closure.

Synthesizes the complete set of 2,233 indirect sites across 0TH2.BIN, TH2.LOW,
SET07.BIN, and BGM.BIN, reconciling previous constant propagation, struct field
callbacks, final call/jump resolutions, and PR return domains.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


@dataclass
class IndirectSiteEntry:
    site_id: str
    module: str
    runtime_pc: str
    opcode_id: str
    category: str
    resolution_status: str
    target_count: int
    targets: List[str]
    evidence_type: str
    details: str


class FinalIndirectResolver:
    """Synthesizes master indirect site scorecard with closed 2,233 accounting."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.sc_p7 = json.loads((repo_root / "workstreams/T2-ASM-07/struct_callback_scorecard.json").read_text(encoding="utf-8"))
        self.final_cj = json.loads((repo_root / "workstreams/T2-ASM-08/final_call_jump_sites.json").read_text(encoding="utf-8"))
        self.pr_prov = json.loads((repo_root / "workstreams/T2-ASM-08/pr_provenance.json").read_text(encoding="utf-8"))

    def synthesize(self) -> Dict[str, Any]:
        # Index newly resolved call/jump sites
        cj_map = {s["site_id"]: s for s in self.final_cj.get("sites", [])}
        # Index PR provenance records
        pr_map = {r["site_id"]: r for r in self.pr_prov.get("records", [])}

        master_sites: List[IndirectSiteEntry] = []

        # Track accounting
        opcode_counts = {
            "JSR": {"total": 0, "resolved": 0, "unresolved": 0},
            "JMP": {"total": 0, "resolved": 0, "unresolved": 0},
            "BRAF": {"total": 0, "resolved": 0, "unresolved": 0},
            "BSRF": {"total": 0, "resolved": 0, "unresolved": 0},
            "RTS": {"total": 0, "resolved": 0, "unresolved": 0},
        }

        call_jump_total = 0
        call_jump_resolved = 0
        rts_total = 0
        rts_resolved = 0

        for s in self.sc_p7["sites"]:
            site_id = s["site_id"]
            op = s["opcode_id"]
            cat = s["category"]
            opcode_counts[op]["total"] += 1

            if cat == "INDIRECT_CALL_JUMP":
                call_jump_total += 1
            else:
                rts_total += 1

            # Check if this site was already resolved previously
            if s["resolution_status"] in ("RESOLVED_EXACT_SINGLE", "RESOLVED_FINITE_SET"):
                # If it's an RTS, enrich with PR provenance details if available
                if op == "RTS" and site_id in pr_map:
                    pr = pr_map[site_id]
                    entry = IndirectSiteEntry(
                        site_id=site_id,
                        module=s["module"],
                        runtime_pc=s["runtime_pc"],
                        opcode_id=op,
                        category=cat,
                        resolution_status="RESOLVED_FINITE_SET",
                        target_count=pr["return_domain_count"],
                        targets=pr["return_pcs"],
                        evidence_type="RTS_BOUNDED_CALLER_SET",
                        details=pr["details"],
                    )
                else:
                    entry = IndirectSiteEntry(
                        site_id=site_id,
                        module=s["module"],
                        runtime_pc=s["runtime_pc"],
                        opcode_id=op,
                        category=cat,
                        resolution_status=s["resolution_status"],
                        target_count=s.get("target_count", len(s.get("targets", []))),
                        targets=s.get("targets", []),
                        evidence_type=s.get("evidence_type", "UNKNOWN"),
                        details=s.get("details", ""),
                    )
                master_sites.append(entry)
                opcode_counts[op]["resolved"] += 1
                if cat == "INDIRECT_CALL_JUMP":
                    call_jump_resolved += 1
                else:
                    rts_resolved += 1

            elif site_id in cj_map:
                # Newly resolved CALL/JUMP site
                cj = cj_map[site_id]
                entry = IndirectSiteEntry(
                    site_id=site_id,
                    module=cj["module"],
                    runtime_pc=cj["runtime_pc"],
                    opcode_id=op,
                    category=cat,
                    resolution_status=cj["resolution_status"],
                    target_count=cj["target_count"],
                    targets=cj["targets"],
                    evidence_type=cj["evidence_type"],
                    details=cj["details"],
                )
                master_sites.append(entry)
                opcode_counts[op]["resolved"] += 1
                call_jump_resolved += 1

            elif op == "RTS" and site_id in pr_map:
                # Newly bounded RTS site
                pr = pr_map[site_id]
                entry = IndirectSiteEntry(
                    site_id=site_id,
                    module=s["module"],
                    runtime_pc=s["runtime_pc"],
                    opcode_id=op,
                    category=cat,
                    resolution_status="RESOLVED_FINITE_SET",
                    target_count=pr["return_domain_count"],
                    targets=pr["return_pcs"],
                    evidence_type="RTS_BOUNDED_CALLER_SET",
                    details=pr["details"],
                )
                master_sites.append(entry)
                opcode_counts[op]["resolved"] += 1
                rts_resolved += 1

            else:
                # Unresolved fallback
                master_sites.append(
                    IndirectSiteEntry(
                        site_id=site_id,
                        module=s["module"],
                        runtime_pc=s["runtime_pc"],
                        opcode_id=op,
                        category=cat,
                        resolution_status="UNRESOLVED",
                        target_count=0,
                        targets=[],
                        evidence_type="NONE",
                        details="Unresolved indirect control flow",
                    )
                )
                opcode_counts[op]["unresolved"] += 1

        total_sites = len(master_sites)
        resolved_total = call_jump_resolved + rts_resolved
        unresolved_total = total_sites - resolved_total

        return {
            "accounting": {
                "total_sites": total_sites,
                "resolved_total": resolved_total,
                "unresolved_total": unresolved_total,
                "reduction_from_baseline_2231": resolved_total - 2,
                "reduction_from_p7_547": resolved_total - 1686,
            },
            "indirect_call_jump_metrics": {
                "total": call_jump_total,
                "resolved": call_jump_resolved,
                "unresolved": call_jump_total - call_jump_resolved,
                "resolution_ratio": f"{(call_jump_resolved / call_jump_total * 100.0):.2f}%",
            },
            "return_flow_rts_metrics": {
                "total": rts_total,
                "resolved": rts_resolved,
                "unresolved": rts_total - rts_resolved,
                "resolution_ratio": f"{(rts_resolved / rts_total * 100.0):.2f}%",
            },
            "opcode_breakdown": opcode_counts,
            "sites": [asdict(s) for s in master_sites],
        }


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    resolver = FinalIndirectResolver(repo_root)
    result = resolver.synthesize()

    out_file = repo_root / "workstreams" / "T2-ASM-08" / "final_indirect_scorecard.json"
    out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")

    acc = result["accounting"]
    cj = result["indirect_call_jump_metrics"]
    rf = result["return_flow_rts_metrics"]
    print(f"Master scorecard synthesized -> {out_file}")
    print(f"  Total sites: {acc['total_sites']}")
    print(f"  Resolved: {acc['resolved_total']} (Unresolved: {acc['unresolved_total']})")
    print(f"  INDIRECT_CALL_JUMP: {cj['resolved']} / {cj['total']} ({cj['resolution_ratio']})")
    print(f"  RETURN_FLOW (RTS): {rf['resolved']} / {rf['total']} ({rf['resolution_ratio']})")
    print("  Opcode breakdown:")
    for op, cnt in result["opcode_breakdown"].items():
        print(f"    {op}: resolved {cnt['resolved']} / {cnt['total']} (unres: {cnt['unresolved']})")


if __name__ == '__main__':
    main()
