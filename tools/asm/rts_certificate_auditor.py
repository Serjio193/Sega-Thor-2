#!/usr/bin/env python3
"""tools/asm/rts_certificate_auditor.py — RTS V3 Certificate Soundness Auditor.

Phase 1 of T2-ASM-10.1:
  Independently audits all 638 RTS certificates in rts_completeness_v3.json
  against the Mandatory Resolved RTS Contract without mutating state.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import sys

repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))


class RTSCertificateAuditor:
    """Audits RTS certificates against the strict fail-closed contract."""

    def __init__(self, root: Path):
        self.repo_root = root
        self.out_dir = root / "workstreams" / "T2-ASM-10-1"
        self.out_dir.mkdir(parents=True, exist_ok=True)

        # Ingest RTS completeness V3
        rts_v3_path = root / "workstreams" / "T2-ASM-10" / "rts_completeness_v3.json"
        self.rts_v3 = json.loads(rts_v3_path.read_text(encoding="utf-8"))

        # Ingest RTS completeness V2 to identify T2-ASM-10 promotions
        rts_v2_path = root / "workstreams" / "T2-ASM-09" / "rts_completeness_v2.json"
        self.rts_v2 = json.loads(rts_v2_path.read_text(encoding="utf-8"))
        self.v2_by_site = {c["site_id"]: c for c in self.rts_v2["certificates"]}

        # Ingest module byte ownership V3 for code intervals
        own_path = root / "workstreams" / "T2-ASM-10" / "module_byte_ownership_v3.json"
        self.ownership_v3 = json.loads(own_path.read_text(encoding="utf-8"))
        self.code_intervals: Dict[str, List[Tuple[int, int]]] = {}
        for m_name, m_info in self.ownership_v3["modules"].items():
            self.code_intervals[m_name] = [
                (int(iv["runtime_start"], 16), int(iv["runtime_end_exclusive"], 16))
                for iv in m_info["intervals"]
                if iv["ownership_class"] == "CODE"
            ]

        # Ingest function caller certificates V2 (T2-ASM-09)
        fc_path = root / "workstreams" / "T2-ASM-09" / "function_caller_certificates.json"
        self.fc_data = json.loads(fc_path.read_text(encoding="utf-8"))
        self.fc_map: Dict[Tuple[str, int, str], Dict[str, Any]] = {}
        for fc in self.fc_data.get("certificates", []):
            mod = fc["module"]
            gen = fc.get("generation", 0)
            for entry in fc["entries"]:
                self.fc_map[(mod, gen, entry)] = fc

        # Ingest T2-ASM-08 RTS certificates for pre-existing leaf functions
        c08_path = root / "workstreams" / "T2-ASM-08" / "rts_completeness_certificates.json"
        if c08_path.exists():
            c08_data = json.loads(c08_path.read_text(encoding="utf-8"))
            self.c08_by_site = {c["site_id"]: c for c in c08_data.get("certificates", [])}
        else:
            self.c08_by_site = {}

    def is_in_confirmed_code(self, module: str, addr: int) -> bool:
        """Checks if a runtime address is within confirmed CODE intervals."""
        for st, en in self.code_intervals.get(module, []):
            if st <= addr < en:
                return True
        return False

    def audit_certificate(self, cert: Dict[str, Any]) -> Dict[str, Any]:
        """Audits a single certificate against the soundness contract."""
        site_id = cert["site_id"]
        module = cert["module"]
        runtime_pc = cert["runtime_pc"]
        fn_entry_pc = cert["function_entry_pc"]
        gen = cert.get("generation", 0)

        res_status = cert.get("resolution_status", "")
        is_resolved = cert.get("is_certified_resolved", False)

        pr_mech = cert.get("pr_mechanism", "UNVERIFIED_PR")
        pr_paths_complete = cert.get("pr_paths_complete", False)
        pr_slot_verified = cert.get("pr_slot_verified", False)

        caller_domain_complete = cert.get("caller_domain_complete", False)
        caller_count = cert.get("caller_count", 0)
        callers = cert.get("callers", [])

        return_domain_count = cert.get("return_domain_count", 0)
        return_pcs = cert.get("return_pcs", [])

        # Check function caller certificate binding
        fc_key = (module, gen, fn_entry_pc)
        fc = self.fc_map.get(fc_key)
        fc_entry = fc.get("function_id") if fc else None

        v2_cert = self.v2_by_site.get(site_id, {})
        was_v2_resolved = v2_cert.get("is_certified_resolved", False)
        is_t2_asm_10_promotion = is_resolved and not was_v2_resolved

        # If it was a T2-ASM-10 promotion, it evaluated against 0x002EA15C due to the loop variable bug
        used_wrong_caller_cert = is_t2_asm_10_promotion and (fn_entry_pc != "0x002EA15C")

        # Function certificate presence check
        c08_cert = self.c08_by_site.get(site_id, {})
        has_provenance = (fc is not None) or (was_v2_resolved and c08_cert.get("is_certified_resolved", False))
        fc_matches = has_provenance and not used_wrong_caller_cert

        # Check return domain nonempty
        return_domain_nonempty = (return_domain_count >= 1) and (len(return_pcs) >= 1)

        # Check all return PCs in code
        all_return_pcs_in_code = True
        invalid_return_pcs = []
        for rpc in return_pcs:
            rpc_int = int(rpc, 16) if isinstance(rpc, str) else rpc
            if not self.is_in_confirmed_code(module, rpc_int):
                all_return_pcs_in_code = False
                invalid_return_pcs.append(rpc)

        contract_failures: List[str] = []

        if is_resolved:
            if used_wrong_caller_cert:
                contract_failures.append("WRONG_CALLER_CERTIFICATE")

            # Rule 1: pr_mechanism != UNVERIFIED_PR
            if pr_mech == "UNVERIFIED_PR":
                contract_failures.append("UNVERIFIED_PR")

            # Rule 2: pr_paths_complete == True
            if not pr_paths_complete:
                contract_failures.append("PR_PATHS_INCOMPLETE")

            # Rule 3: STACK_RESTORED_PR requires pr_slot_verified == True
            if pr_mech == "STACK_RESTORED_PR" and not pr_slot_verified:
                contract_failures.append("UNVERIFIED_STACK_PR_SLOT")

            # Rule 4: caller_domain_complete == True
            if not caller_domain_complete:
                contract_failures.append("CALLER_DOMAIN_INCOMPLETE")

            # Rule 5: Empty return domain prohibited
            if not return_domain_nonempty:
                contract_failures.append("EMPTY_RETURN_DOMAIN")

            # Rule 6: Cardinality check
            if return_domain_count != len(return_pcs):
                contract_failures.append("RETURN_DOMAIN_CARDINALITY_MISMATCH")

            if caller_count != len(callers):
                contract_failures.append("CALLER_COUNT_CARDINALITY_MISMATCH")

            # Rule 7: All return PCs must be confirmed CODE
            if not all_return_pcs_in_code:
                contract_failures.append(f"INVALID_RETURN_PC:{','.join(invalid_return_pcs)}")

            # Rule 8: EXACT_RETURN must have exactly 1 return PC
            if res_status == "RESOLVED_EXACT_RETURN" and return_domain_count != 1:
                contract_failures.append("EXACT_RETURN_CARDINALITY_MISMATCH")

            # Rule 9: Function caller provenance
            if not fc_matches and not used_wrong_caller_cert:
                contract_failures.append("NO_MATCHING_FUNCTION_CERTIFICATE")
        else:
            if res_status.startswith("RESOLVED_"):
                contract_failures.append("UNRESOLVED_CLAIMING_RESOLVED_STATUS")

        contract_valid = len(contract_failures) == 0

        return {
            "site_id": site_id,
            "module": module,
            "runtime_pc": runtime_pc,
            "function_entry_pc": fn_entry_pc,
            "resolution_status": res_status,
            "is_certified_resolved": is_resolved,
            "is_t2_asm_10_promotion": is_t2_asm_10_promotion,
            "was_v2_resolved": was_v2_resolved,
            "pr_mechanism": pr_mech,
            "pr_paths_complete": pr_paths_complete,
            "pr_slot_verified": pr_slot_verified,
            "caller_domain_complete": caller_domain_complete,
            "caller_count": caller_count,
            "callers": callers,
            "return_domain_count": return_domain_count,
            "return_pcs": return_pcs,
            "function_certificate_entry": fc_entry,
            "function_certificate_matches_site": fc_matches,
            "all_return_pcs_in_code": all_return_pcs_in_code,
            "return_domain_nonempty": return_domain_nonempty,
            "contract_valid": contract_valid,
            "contract_failures": contract_failures,
        }

    def run_audit(self) -> Dict[str, Any]:
        """Runs audit on all 638 certificates and saves report."""
        records = []
        failure_counts: Dict[str, int] = {
            "wrong_caller_certificate": 0,
            "UNVERIFIED_PR": 0,
            "unverified_stack_pr_slot": 0,
            "empty_return_domain": 0,
            "invalid_return_pc": 0,
            "other": 0,
        }
        claimed_resolved_count = 0
        sound_resolved_count = 0
        violating_resolved_count = 0
        violating_resolved_pcs: List[str] = []

        for cert in self.rts_v3.get("certificates", []):
            rec = self.audit_certificate(cert)
            records.append(rec)

            if rec["is_certified_resolved"]:
                claimed_resolved_count += 1
                if rec["contract_valid"]:
                    sound_resolved_count += 1
                else:
                    violating_resolved_count += 1
                    violating_resolved_pcs.append(rec["runtime_pc"])

                    fails = rec["contract_failures"]
                    if "WRONG_CALLER_CERTIFICATE" in fails:
                        failure_counts["wrong_caller_certificate"] += 1
                    if "UNVERIFIED_PR" in fails:
                        failure_counts["UNVERIFIED_PR"] += 1
                    if "UNVERIFIED_STACK_PR_SLOT" in fails:
                        failure_counts["unverified_stack_pr_slot"] += 1
                    if "EMPTY_RETURN_DOMAIN" in fails:
                        failure_counts["empty_return_domain"] += 1
                    if any(f.startswith("INVALID_RETURN_PC") for f in fails):
                        failure_counts["invalid_return_pc"] += 1
                    other_fails = [
                        f for f in fails
                        if f not in ("WRONG_CALLER_CERTIFICATE", "UNVERIFIED_PR", "UNVERIFIED_STACK_PR_SLOT", "EMPTY_RETURN_DOMAIN")
                        and not f.startswith("INVALID_RETURN_PC")
                    ]
                    if other_fails:
                        failure_counts["other"] += 1

        summary = {
            "total_certificates_audited": len(records),
            "claimed_resolved_count": claimed_resolved_count,
            "sound_resolved_count": sound_resolved_count,
            "violating_resolved_count": violating_resolved_count,
            "claimed_unresolved_count": len(records) - claimed_resolved_count,
            "failure_breakdown": failure_counts,
            "violating_resolved_pcs_count": len(violating_resolved_pcs),
            "violating_resolved_pcs": violating_resolved_pcs,
        }

        audit_report = {
            "version": "1.0",
            "summary": summary,
            "records": records,
        }

        out_file = self.out_dir / "rts_v3_soundness_audit.json"
        out_file.write_text(json.dumps(audit_report, indent=2), encoding="utf-8")
        return audit_report


if __name__ == "__main__":
    auditor = RTSCertificateAuditor(repo_root)
    res = auditor.run_audit()
    print("=== RTS V3 Certificate Soundness Audit Complete ===")
    print(f"Total audited: {res['summary']['total_certificates_audited']}")
    print(f"Claimed resolved: {res['summary']['claimed_resolved_count']}")
    print(f"Sound resolved: {res['summary']['sound_resolved_count']}")
    print(f"Violating resolved: {res['summary']['violating_resolved_count']}")
    print("\nBreakdown by violation:")
    for k, v in res["summary"]["failure_breakdown"].items():
        print(f"  {k}: {v}")
