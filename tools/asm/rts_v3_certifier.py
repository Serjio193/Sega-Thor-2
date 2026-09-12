#!/usr/bin/env python3
"""tools/asm/rts_v3_certifier.py — Residual RTS Threat Correlation & RTS Completeness V3.

Phases 15, 16, 17 & Mandatory Correction 6 of T2-ASM-10:
  1. Correlates all 182 residual RTS sites from T2-ASM-09 against PR refinements and decarved regions.
  2. Emits workstreams/T2-ASM-10/rts_gap_correlation.json.
  3. Re-evaluates RTS completeness certificates V3:
     - Discharges PR-path refined sites where caller domain is complete.
     - Discharges external-entry threatened sites where threats were proven in DATA/CODE/PADDING.
     - Retains residual sites fail-closed with exact blocker taxonomy.
  4. Emits workstreams/T2-ASM-10/rts_completeness_v3.json.
  5. Reports exact before/after distribution by the three baseline classes:
     - UNRESOLVED_EXTERNAL_ENTRY: 81 -> ?
     - UNRESOLVED_PR_PATH: 81 -> ?
     - UNRESOLVED_CALLER_DOMAIN: 20 -> ?
"""

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import sys

repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.asm.call_sink_and_pointer_tracer import CallSinkAndPointerTracer


class RTSV3Certifier:
    """Evaluates RTS completeness V3 using PR refinements and true UNKNOWN threat status."""

    def __init__(self, root: Path):
        self.repo_root = root
        self.out_dir = root / "workstreams" / "T2-ASM-10"
        self.out_dir.mkdir(parents=True, exist_ok=True)

        # Ingest RTS completeness V2
        rts_v2_p = root / "workstreams/T2-ASM-09/rts_completeness_v2.json"
        self.rts_v2 = json.loads(rts_v2_p.read_text(encoding="utf-8"))

        # Ingest PR path refinements
        pr_ref_p = self.out_dir / "pr_path_refinements.json"
        self.pr_ref = json.loads(pr_ref_p.read_text(encoding="utf-8"))
        self.pr_ref_by_site = {r["site_id"]: r for r in self.pr_ref.get("refinements", [])}

        # Ingest ownership V3
        own_p = self.out_dir / "module_byte_ownership_v3.json"
        self.ownership_v3 = json.loads(own_p.read_text(encoding="utf-8"))

        # Ingest function caller certificates V2
        fc_p = root / "workstreams/T2-ASM-09/function_caller_certificates.json"
        self.fc_certs = json.loads(fc_p.read_text(encoding="utf-8")).get("certificates", [])
        self.fc_by_entry: Dict[str, Dict[str, Any]] = {}
        for c in self.fc_certs:
            for e in c["entries"]:
                self.fc_by_entry[e] = c

        # Threat audit
        self.tracer = CallSinkAndPointerTracer(root)
        self.all_threats = self.tracer.audit_unknown_caller_threats()

        # Build byte class lookup from V3
        self.byte_class_v3: Dict[str, Dict[int, str]] = {}
        for mod_name, mod_info in self.ownership_v3["modules"].items():
            classes: Dict[int, str] = {}
            for iv in mod_info["intervals"]:
                st = int(iv["runtime_start"], 16)
                en = int(iv["runtime_end_exclusive"], 16)
                cls = iv["ownership_class"]
                for addr in range(st, en):
                    classes[addr] = cls
            self.byte_class_v3[mod_name] = classes

    def run_certification(self) -> Dict[str, Any]:
        # 1. Build correlation report
        correlation_records = []
        for cert in self.rts_v2["certificates"]:
            status = cert["resolution_status"]
            if not status.startswith("RESOLVED"):
                site_id = cert["site_id"]
                fn_pc = cert["function_entry_pc"]
                pr_info = self.pr_ref_by_site.get(site_id, {})
                fc_info = self.fc_by_entry.get(fn_pc, {})

                # Check true UNKNOWN threats for this function under V3
                th = self.all_threats.get(fn_pc, {})
                true_unknown_threats = []
                for pt in th.get("pointer_threats", []):
                    addr = int(pt["pc"], 16)
                    m = pt.get("module", "0TH2.BIN")
                    if self.byte_class_v3.get(m, {}).get(addr) == "UNKNOWN":
                        true_unknown_threats.append(pt)
                for bt in th.get("direct_branch_threats", []):
                    addr = int(bt["pc"], 16)
                    m = bt.get("module", "0TH2.BIN")
                    if self.byte_class_v3.get(m, {}).get(addr) == "UNKNOWN":
                        true_unknown_threats.append(bt)

                correlation_records.append({
                    "site_id": site_id,
                    "runtime_pc": cert["runtime_pc"],
                    "function_entry_pc": fn_pc,
                    "module": cert["module"],
                    "baseline_blocker_class": status,
                    "pr_path_status": pr_info.get("pr_path_status", "PR_PATH_COMPLETE"),
                    "is_pr_path_resolved": pr_info.get("is_pr_path_resolved", cert["pr_paths_complete"]),
                    "caller_domain_complete": cert["caller_domain_complete"],
                    "true_unknown_threat_count": len(true_unknown_threats),
                    "true_unknown_threats": true_unknown_threats,
                })

        corr_path = self.out_dir / "rts_gap_correlation.json"
        corr_path.write_text(json.dumps({"total_records": len(correlation_records), "records": correlation_records}, indent=2), encoding="utf-8")

        # 2. Derive RTS completeness V3 certificates
        new_certs = []
        baseline_counts = {"UNRESOLVED_EXTERNAL_ENTRY": 0, "UNRESOLVED_PR_PATH": 0, "UNRESOLVED_CALLER_DOMAIN": 0}
        v3_counts = {"UNRESOLVED_EXTERNAL_ENTRY": 0, "UNRESOLVED_PR_PATH": 0, "UNRESOLVED_CALLER_DOMAIN": 0}

        corr_by_site = {r["site_id"]: r for r in correlation_records}

        for cert in self.rts_v2["certificates"]:
            site_id = cert["site_id"]
            old_status = cert["resolution_status"]

            if old_status in baseline_counts:
                baseline_counts[old_status] += 1

            if old_status.startswith("RESOLVED"):
                new_certs.append(dict(cert))
            else:
                corr = corr_by_site[site_id]
                pr_resolved = corr["is_pr_path_resolved"]
                true_threats = corr["true_unknown_threat_count"]
                caller_complete = corr["caller_domain_complete"]

                fc = self.fc_by_entry.get(fn_pc, {})
                other_entry_unres = [
                    e for e in fc.get("unresolved_entry_sources", [])
                    if not e.startswith("UNKNOWN_REGION")
                ]
                ref_unres = fc.get("unresolved_reference_sources", [])
                caller_domain_proven = (len(other_entry_unres) == 0 and len(ref_unres) == 0 and true_threats == 0)

                new_cert = dict(cert)

                if old_status == "UNRESOLVED_PR_PATH":
                    if pr_resolved and caller_complete:
                        new_cert["pr_paths_complete"] = True
                        new_cert["is_certified_resolved"] = True
                        new_cert["resolution_status"] = "RESOLVED_EXACT_RETURN" if cert["return_domain_count"] == 1 else "RESOLVED_FINITE_SET"
                    else:
                        new_cert["pr_paths_complete"] = False
                        new_cert["is_certified_resolved"] = False
                        new_cert["resolution_status"] = "UNRESOLVED_PR_PATH"
                        v3_counts["UNRESOLVED_PR_PATH"] += 1

                elif old_status == "UNRESOLVED_EXTERNAL_ENTRY":
                    if caller_domain_proven and pr_resolved:
                        new_cert["caller_domain_complete"] = True
                        new_cert["is_certified_resolved"] = True
                        new_cert["resolution_status"] = "RESOLVED_EXACT_RETURN" if cert["return_domain_count"] == 1 else "RESOLVED_FINITE_SET"
                    else:
                        new_cert["caller_domain_complete"] = False
                        new_cert["is_certified_resolved"] = False
                        new_cert["resolution_status"] = "UNRESOLVED_EXTERNAL_ENTRY"
                        v3_counts["UNRESOLVED_EXTERNAL_ENTRY"] += 1

                elif old_status == "UNRESOLVED_CALLER_DOMAIN":
                    # Retain fail-closed as caller domain incomplete
                    new_cert["is_certified_resolved"] = False
                    new_cert["resolution_status"] = "UNRESOLVED_CALLER_DOMAIN"
                    v3_counts["UNRESOLVED_CALLER_DOMAIN"] += 1

                new_certs.append(new_cert)

        total_rts = len(new_certs)
        resolved_count = sum(1 for c in new_certs if c["is_certified_resolved"])
        unresolved_count = total_rts - resolved_count
        res_pct = f"{(resolved_count / total_rts) * 100:.2f}%"

        status_dist = Counter(c["resolution_status"] for c in new_certs)

        summary = {
            "total_rts_sites": total_rts,
            "certified_resolved": resolved_count,
            "honest_unresolved": unresolved_count,
            "resolution_percentage": res_pct,
            "baseline_unresolved": 182,
            "unresolved_reduction": 182 - unresolved_count,
            "baseline_blocker_distribution": baseline_counts,
            "v3_blocker_distribution": v3_counts,
            "status_distribution": dict(status_dist),
        }

        output = {
            "summary": summary,
            "certificates": new_certs,
        }

        out_path = self.out_dir / "rts_completeness_v3.json"
        out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        return summary


def main():
    certifier = RTSV3Certifier(repo_root)
    res = certifier.run_certification()
    print("=== RTS Completeness V3 Certification Completed ===")
    print(f"Total RTS: {res['total_rts_sites']}")
    print(f"Certified Resolved: {res['certified_resolved']} ({res['resolution_percentage']})")
    print(f"Honest Unresolved: {res['honest_unresolved']} (reduced by {res['unresolved_reduction']})")
    print("\nMandatory Before / After Blocker Distribution:")
    b_dist = res["baseline_blocker_distribution"]
    v_dist = res["v3_blocker_distribution"]
    for k in ["UNRESOLVED_EXTERNAL_ENTRY", "UNRESOLVED_PR_PATH", "UNRESOLVED_CALLER_DOMAIN"]:
        print(f"  {k:<28}: {b_dist[k]} -> {v_dist[k]}")


if __name__ == "__main__":
    main()
