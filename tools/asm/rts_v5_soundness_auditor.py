#!/usr/bin/env python3
"""tools/asm/rts_v5_soundness_auditor.py — Independent RTS V5 Soundness Auditor.

T2-ASM-12 Phase 14:
  1. Independently audits all 638 certificates in rts_completeness_v5.json.
  2. Enforces fail-closed soundness contract:
     - No resolved certificate may have empty return domain.
     - No resolved certificate may have return PCs in DATA, PADDING, or UNKNOWN.
     - STACK_RESTORED_PR requires pr_slot_verified == True.
     - Zero metric forcing: INVALID_RESOLVED_CERTIFICATES must be 0.
  3. Emits:
     - workstreams/T2-ASM-12/rts_v5_soundness_audit.json
"""

import bisect
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))


class RTSV5SoundnessAuditor:
    def __init__(self, root: Path):
        self.root = root
        self.out_dir = root / "workstreams" / "T2-ASM-12"
        self.out_dir.mkdir(parents=True, exist_ok=True)

        # Byte ownership v3
        own_p = root / "workstreams/T2-ASM-10/module_byte_ownership_v3.json"
        self.ownership = json.loads(own_p.read_text(encoding="utf-8"))
        self.mod_intervals: Dict[str, Tuple[List[int], List[Dict[str, Any]]]] = {}
        for mod, mdata in self.ownership["modules"].items():
            ivs = mdata.get("intervals", [])
            starts = [int(iv["runtime_start"], 16) for iv in ivs]
            self.mod_intervals[mod] = (starts, ivs)

        # RTS completeness V5
        rts5_p = self.out_dir / "rts_completeness_v5.json"
        self.rts5 = json.loads(rts5_p.read_text(encoding="utf-8"))

    def lookup_iv(self, mod: str, pc: int) -> Optional[Dict[str, Any]]:
        if mod not in self.mod_intervals:
            return None
        starts, ivs = self.mod_intervals[mod]
        idx = bisect.bisect_right(starts, pc) - 1
        if 0 <= idx < len(ivs):
            iv = ivs[idx]
            if int(iv["runtime_start"], 16) <= pc < int(iv["runtime_end_exclusive"], 16):
                return iv
        return None

    def determine_module(self, pc: int) -> str:
        if pc >= 0x060D8000: return "SET07.BIN"
        if pc >= 0x06000000: return "0TH2.BIN"
        if pc >= 0x00200000: return "TH2.LOW"
        return "BGM.BIN"

    def audit(self) -> Dict[str, Any]:
        certs = self.rts5["certificates"]
        total_sites = len(certs)
        violations = []
        resolved_count = 0
        unresolved_count = 0

        for c in certs:
            sid = c["site_id"]
            is_res = c.get("is_certified_resolved", False)

            if is_res:
                resolved_count += 1
                # Check PR completeness
                if not c.get("pr_paths_complete", False):
                    violations.append({"site_id": sid, "rule": "PR_PATHS_INCOMPLETE", "detail": "Resolved site has pr_paths_complete == False"})
                if c.get("pr_mechanism") == "STACK_RESTORED_PR" and not c.get("pr_slot_verified", False):
                    violations.append({"site_id": sid, "rule": "PR_SLOT_UNVERIFIED", "detail": "STACK_RESTORED_PR without verified slot"})
                if c.get("pr_mechanism") == "UNVERIFIED_PR":
                    violations.append({"site_id": sid, "rule": "UNVERIFIED_PR_MECHANISM", "detail": "Resolved site with UNVERIFIED_PR"})

                # Check caller domain
                if not c.get("caller_domain_complete", False):
                    violations.append({"site_id": sid, "rule": "CALLER_DOMAIN_INCOMPLETE", "detail": "Resolved site has caller_domain_complete == False"})
                if c.get("caller_count", 0) <= 0:
                    violations.append({"site_id": sid, "rule": "ZERO_CALLERS", "detail": "Resolved site has caller_count <= 0"})

                # Check return domain
                ret_cnt = c.get("return_domain_count", 0)
                ret_pcs = c.get("return_pcs", [])
                if ret_cnt <= 0 or len(ret_pcs) == 0:
                    violations.append({"site_id": sid, "rule": "EMPTY_RETURN_DOMAIN", "detail": f"return_domain_count={ret_cnt}, return_pcs={ret_pcs}"})
                if len(ret_pcs) != ret_cnt:
                    violations.append({"site_id": sid, "rule": "RETURN_COUNT_MISMATCH", "detail": f"count {ret_cnt} != len {len(ret_pcs)}"})

                # Check return targets ownership
                for r_s in ret_pcs:
                    r = int(r_s, 16)
                    r_mod = self.determine_module(r)
                    iv = self.lookup_iv(r_mod, r)
                    cls = iv["ownership_class"] if iv else "OUT_OF_BOUNDS"
                    if cls != "CODE":
                        violations.append({
                            "site_id": sid,
                            "rule": "NON_CODE_RETURN_TARGET",
                            "detail": f"Return target {r_s} in {r_mod} has ownership {cls} (interval {iv})",
                        })

                # Check status label consistency
                status = c.get("resolution_status", "")
                if status == "RESOLVED_EXACT_RETURN" and ret_cnt != 1:
                    violations.append({"site_id": sid, "rule": "EXACT_COUNT_MISMATCH", "detail": f"RESOLVED_EXACT_RETURN with count {ret_cnt}"})
                elif status == "RESOLVED_FINITE_SET" and ret_cnt <= 1:
                    violations.append({"site_id": sid, "rule": "FINITE_COUNT_MISMATCH", "detail": f"RESOLVED_FINITE_SET with count {ret_cnt}"})
                elif status not in ("RESOLVED_EXACT_RETURN", "RESOLVED_FINITE_SET"):
                    violations.append({"site_id": sid, "rule": "INVALID_RESOLVED_STATUS", "detail": f"Unexpected status: {status}"})
            else:
                unresolved_count += 1
                status = c.get("resolution_status", "")
                if status not in ("UNRESOLVED_EXTERNAL_ENTRY", "UNRESOLVED_CALLER_DOMAIN", "UNRESOLVED_PR_PATH"):
                    violations.append({"site_id": sid, "rule": "INVALID_UNRESOLVED_STATUS", "detail": f"Unexpected unresolved status: {status}"})

        audit_summary = {
            "version": "1.0",
            "total_sites_audited": total_sites,
            "resolved_sites_count": resolved_count,
            "unresolved_sites_count": unresolved_count,
            "invalid_resolved_certificates_count": len(violations),
            "audit_passed": (len(violations) == 0),
            "violations": violations,
        }

        (self.out_dir / "rts_v5_soundness_audit.json").write_text(
            json.dumps(audit_summary, indent=2), encoding="utf-8"
        )
        return audit_summary


def main():
    auditor = RTSV5SoundnessAuditor(repo_root)
    res = auditor.audit()
    print("RTS V5 Soundness Audit complete:")
    print(f"  Total sites audited: {res['total_sites_audited']}")
    print(f"  Resolved sites: {res['resolved_sites_count']}")
    print(f"  Unresolved sites: {res['unresolved_sites_count']}")
    print(f"  INVALID_RESOLVED_CERTIFICATES: {res['invalid_resolved_certificates_count']}")
    print(f"  Audit Passed: {res['audit_passed']}")


if __name__ == "__main__":
    main()
