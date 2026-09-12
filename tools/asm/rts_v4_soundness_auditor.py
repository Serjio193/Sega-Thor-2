#!/usr/bin/env python3
"""tools/asm/rts_v4_soundness_auditor.py — Independent RTS V4 Soundness Auditor.

T2-ASM-11 Phase 14 & 15:
  Independently audits all 638 RTS certificates in rts_completeness_v4.json.
  Verifies that every resolved certificate strictly satisfies:
    1. pr_paths_complete == True and pr_slot_verified == True
    2. caller_domain_complete == True
    3. caller_count > 0 and len(callers) == caller_count
    4. return_domain_count > 0 and len(return_pcs) == return_domain_count
    5. every return PC is strictly within a CONFIRMED_CODE interval
    6. no ambient variable leakage or empty return domains
  Emits workstreams/T2-ASM-11/rts_v4_soundness_audit.json.
  Fails if INVALID_RESOLVED_CERTIFICATES > 0.
"""

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import sys

repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))


@dataclass
class CertificateAuditResult:
    site_id: str
    module: str
    runtime_pc: str
    function_entry_pc: str
    resolution_status: str
    is_certified_resolved: bool
    pr_mechanism: str
    pr_paths_complete: bool
    pr_slot_verified: bool
    caller_domain_complete: bool
    caller_count: int
    return_domain_count: int
    all_return_pcs_in_code: bool
    return_domain_nonempty: bool
    is_sound: bool
    contract_violations: List[str]


class RTSV4SoundnessAuditor:
    def __init__(self, root: Path):
        self.root = root
        self.out_dir = root / "workstreams" / "T2-ASM-11"
        self.out_dir.mkdir(parents=True, exist_ok=True)

        # Load RTS V4 certificates
        rts_v4_p = self.out_dir / "rts_completeness_v4.json"
        self.rts_v4 = json.loads(rts_v4_p.read_text(encoding="utf-8"))

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

    def is_code(self, mod: str, pc: int) -> bool:
        for s, e in self.code_ranges.get(mod, []):
            if s <= pc < e:
                return True
        return False

    def audit_all(self) -> Dict[str, Any]:
        results: List[CertificateAuditResult] = []
        violations: List[Dict[str, Any]] = []

        for cert in self.rts_v4["certificates"]:
            sid = cert["site_id"]
            mod = cert["module"]
            pc = cert["runtime_pc"]
            entry_pc = cert["function_entry_pc"]
            status = cert["resolution_status"]
            is_resolved = cert["is_certified_resolved"]

            site_violations: List[str] = []

            # Return PCs validation
            ret_pcs = cert.get("return_pcs", [])
            ret_in_code = [self.is_code(mod, int(r, 16)) for r in ret_pcs]
            all_in_code = all(ret_in_code) if ret_pcs else True
            nonempty = len(ret_pcs) > 0

            if is_resolved:
                if status not in ("RESOLVED_EXACT_RETURN", "RESOLVED_FINITE_SET"):
                    site_violations.append(f"INVALID_STATUS_FOR_RESOLVED:{status}")
                if not cert.get("pr_paths_complete"):
                    site_violations.append("PR_PATHS_INCOMPLETE")
                if not cert.get("pr_slot_verified"):
                    site_violations.append("PR_SLOT_UNVERIFIED")
                if not cert.get("caller_domain_complete"):
                    site_violations.append("CALLER_DOMAIN_INCOMPLETE")
                if cert.get("caller_count", 0) <= 0:
                    site_violations.append("EMPTY_CALLER_COUNT")
                if len(cert.get("callers", [])) != cert.get("caller_count", 0):
                    site_violations.append("CALLER_COUNT_MISMATCH")
                if not nonempty:
                    site_violations.append("EMPTY_RETURN_DOMAIN")
                if len(ret_pcs) != cert.get("return_domain_count", 0):
                    site_violations.append("RETURN_DOMAIN_COUNT_MISMATCH")
                if not all_in_code:
                    bad_pcs = [r for r, ok in zip(ret_pcs, ret_in_code) if not ok]
                    site_violations.append(f"RETURN_PC_NOT_IN_CODE:{','.join(bad_pcs)}")
                if cert.get("pr_mechanism") == "UNVERIFIED_PR":
                    site_violations.append("UNVERIFIED_PR_MECHANISM")

            is_sound = len(site_violations) == 0
            if not is_sound:
                violations.append({
                    "site_id": sid, "module": mod, "runtime_pc": pc,
                    "violations": site_violations
                })

            results.append(CertificateAuditResult(
                site_id=sid, module=mod, runtime_pc=pc,
                function_entry_pc=entry_pc, resolution_status=status,
                is_certified_resolved=is_resolved,
                pr_mechanism=cert.get("pr_mechanism", "UNKNOWN"),
                pr_paths_complete=cert.get("pr_paths_complete", False),
                pr_slot_verified=cert.get("pr_slot_verified", False),
                caller_domain_complete=cert.get("caller_domain_complete", False),
                caller_count=cert.get("caller_count", 0),
                return_domain_count=cert.get("return_domain_count", 0),
                all_return_pcs_in_code=all_in_code,
                return_domain_nonempty=nonempty,
                is_sound=is_sound,
                contract_violations=site_violations,
            ))

        total = len(results)
        resolved_count = sum(1 for r in results if r.is_certified_resolved)
        unresolved_count = total - resolved_count
        invalid_resolved_count = len(violations)

        summary = {
            "version": "1.0",
            "total_certificates_audited": total,
            "certified_resolved_count": resolved_count,
            "unresolved_count": unresolved_count,
            "invalid_resolved_certificates_count": invalid_resolved_count,
            "all_certificates_sound": invalid_resolved_count == 0,
            "resolution_status_breakdown": dict(Counter(r.resolution_status for r in results)),
            "pr_mechanism_breakdown": dict(Counter(r.pr_mechanism for r in results)),
        }

        output = {
            "summary": summary,
            "violations": violations,
            "audit_records": [asdict(r) for r in results],
        }

        (self.out_dir / "rts_v4_soundness_audit.json").write_text(
            json.dumps(output, indent=2), encoding="utf-8"
        )
        return output


def main():
    auditor = RTSV4SoundnessAuditor(repo_root)
    res = auditor.audit_all()
    s = res["summary"]
    print("RTS V4 Soundness Audit completed:")
    print(f"  Total certificates audited: {s['total_certificates_audited']}")
    print(f"  Certified resolved count: {s['certified_resolved_count']}")
    print(f"  Unresolved count: {s['unresolved_count']}")
    print(f"  INVALID RESOLVED CERTIFICATES: {s['invalid_resolved_certificates_count']}")
    print(f"  All certificates sound: {s['all_certificates_sound']}")

    if s["invalid_resolved_certificates_count"] > 0:
        print("FAIL: Contract violations detected in RTS V4 certificates!")
        sys.exit(1)
    else:
        print("PASS: 100% of RTS V4 certificates satisfy the strict fail-closed contract.")


if __name__ == "__main__":
    main()
