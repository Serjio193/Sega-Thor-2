# RTS V3 Certificate Soundness Audit & Fail-Closed Reconciliation Report (T2-ASM-10.1)

**Task**: `T2-ASM-10.1 — RTS V3 Certificate Soundness Audit, Per-Function Caller Binding Repair, and Fail-Closed Reconciliation`  
**Date**: 2026-09-12  
**Baseline Commit**: `24f8fe68f3efc48e03930f86f9535901a2b296d6`  
**Classification**: CORRECTIVE AUDIT / SOUNDNESS RESTORATION  

---

## 1. Executive Summary & Audit Motivation

Following the push of milestone `T2-ASM-10`, an audit of the control-flow artifacts revealed that the reported RTS V3 completeness metrics (**552 / 638 resolved**, **86 unresolved**) were compromised by two implementation defects in `tools/asm/rts_v3_certifier.py`:
1. **Defect #1 (Stale `fn_pc` Caller-Certificate Binding)**: Loop variable leakage across Python loops caused caller certificate lookup in loop 2 to evaluate all unresolved RTS sites against the single function entry PC left behind by loop 1 (`TH2.LOW` function `0x002EA15C`).
2. **Defect #2 (Zero-Element Return Domain & Unverified PR Promotion)**: The promotion logic in `rts_v3_certifier.py` flipped `is_certified_resolved = True` and set `resolution_status = "RESOLVED_FINITE_SET"` without populating `callers` or `return_pcs`, and without verifying `pr_slot_verified` or prohibiting `UNVERIFIED_PR`. This created invalid certificates such as `0TH2.BIN RTS 0x0600467E` (`pr_mechanism: UNVERIFIED_PR`, `return_domain_count: 0`, `caller_count: 0`, `is_certified_resolved: True`).

In accordance with project rules (Fail-Closed Evidence, Historical Preservation, No Continuity-Forcing), task `T2-ASM-10.1` was executed to:
- Conduct an independent, non-mutating audit of all 638 RTS certificates using `tools/asm/rts_certificate_auditor.py`;
- Re-architect `rts_v3_certifier.py` around a pure `certify_site` function enforcing exact `(module, generation, entry_pc)` binding and the Mandatory Resolved RTS Contract;
- Individually re-audit the 96 claimed promotions from T2-ASM-10;
- Re-audit all 456 pre-existing resolved V2 certificates;
- Implement 8 new negative controls (NC-BG through NC-BN, raising total to 74);
- Recompute canonical indirect metrics without metric-forcing;
- Formally document the corrected baseline.

---

## 2. Root Cause Analysis

### Defect #1: Stale `fn_pc` Loop Variable Leakage

In `tools/asm/rts_v3_certifier.py` (lines 79-112), loop 1 built the gap correlation records:
```python
for cert in self.rts_v2["certificates"]:
    status = cert["resolution_status"]
    if not status.startswith("RESOLVED"):
        site_id = cert["site_id"]
        fn_pc = cert["function_entry_pc"]
        ...
```
At loop termination, `fn_pc` remained in function scope holding `"0x002EA15C"` (the last unresolved certificate in `TH2.LOW`).

In loop 2 (lines 124-177), the code iterated over certificates to derive V3 certificates:
```python
for cert in self.rts_v2["certificates"]:
    site_id = cert["site_id"]
    old_status = cert["resolution_status"]
    ...
    else:
        corr = corr_by_site[site_id]
        pr_resolved = corr["is_pr_path_resolved"]
        true_threats = corr["true_unknown_threat_count"]
        caller_complete = corr["caller_domain_complete"]

        fc = self.fc_by_entry.get(fn_pc, {})  # <-- CRITICAL BUG: fn_pc was never rebound!
```
Because `fn_pc` was not assigned from `cert["function_entry_pc"]`, every single RTS site being evaluated in loop 2 queried the caller certificate of `0x002EA15C`.

### Defect #2: Missing Promotion Invariants & Empty Return Domains

When evaluating promotions, `rts_v3_certifier.py` executed:
```python
if old_status == "UNRESOLVED_PR_PATH":
    if pr_resolved and caller_complete:
        new_cert["pr_paths_complete"] = True
        new_cert["is_certified_resolved"] = True
        new_cert["resolution_status"] = "RESOLVED_EXACT_RETURN" if cert["return_domain_count"] == 1 else "RESOLVED_FINITE_SET"
```
This omitted:
- Checking `cert["pr_mechanism"] != "UNVERIFIED_PR"`
- Checking `cert["pr_slot_verified"] == True` for `STACK_RESTORED_PR`
- Checking `cert["return_domain_count"] >= 1`
- Checking `len(cert["return_pcs"]) == cert["return_domain_count"]`
- Checking that all return PCs reside in confirmed `CODE`

As a result, 96 sites were promoted to `RESOLVED_FINITE_SET` while possessing `return_domain_count: 0`, `return_pcs: []`, `caller_count: 0`, `callers: []`, and in 37 cases `pr_mechanism: "UNVERIFIED_PR"`.

---

## 3. Independent Certificate Soundness Audit Results

Tool: `tools/asm/rts_certificate_auditor.py`  
Output: `workstreams/T2-ASM-10-1/rts_v3_soundness_audit.json`  

Auditing all 638 certificates in `workstreams/T2-ASM-10/rts_completeness_v3.json` against the Mandatory Resolved RTS Contract yielded:

```
=== RTS V3 Certificate Soundness Audit Complete ===
Total audited:                 638
Claimed resolved in T2-ASM-10: 552
Sound resolved:                420
Violating resolved:            132

Breakdown by violation:
  wrong_caller_certificate:   95
  UNVERIFIED_PR:               37
  unverified_stack_pr_slot:    0
  empty_return_domain:         96
  invalid_return_pc:           36
  other:                       0
```

### Breakdown of the 132 Invalid Resolved Certificates
1. **The 96 T2-ASM-10 Promotions**:
   - 95 sites evaluated against wrong caller certificate (`0x002EA15C`).
   - 37 sites had `pr_mechanism == "UNVERIFIED_PR"`.
   - All 96 sites had empty return domains (`return_domain_count: 0`, `return_pcs: []`).
   - 1 site belonged to `0x002EA15C` (`TH2.LOW_0x002EA1B0`), but still violated the contract due to `return_domain_count: 0`.
2. **The 36 Pre-Existing V2 Certificates**:
   - 36 certificates originally marked resolved in V2 had return PCs pointing to addresses like `0x06007C3E`.
   - In T2-ASM-10, interval `0x06007C28..0x06007C48` was proven to be `DATA_LITERAL_POOL`.
   - Because return PCs reside in `DATA` rather than `CODE`, their caller domains were based on false caller decodes inside literal pools. Under fail-closed reconciliation, all 36 sites must be demoted.

---

## 4. Re-Audit of T2-ASM-10 Promotions

Tool: `tools/asm/rts_promotion_auditor.py`  
Output: `workstreams/T2-ASM-10-1/t2_asm_10_rts_promotion_audit.json`  

Individually auditing each of the 96 sites claimed as promoted in T2-ASM-10:
- **Total promotions audited**: 96
- **Valid promotions**: 0
- **Revoked promotions**: 96
- **Classification breakdown**:
  - `PROMOTION_VALID`: 0
  - `PROMOTION_REVOKED_PR_UNPROVEN`: 37 (unverified PR mechanism)
  - `PROMOTION_REVOKED_EMPTY_RETURN_DOMAIN`: 59 (valid PR mechanism, but empty return domain)
  - `PROMOTION_REVOKED_WRONG_CALLER_CERT`: 0 (prioritized under PR/domain failure)
  - `PROMOTION_REVOKED_OTHER`: 0

**Result**: 100% of the 96 promotions claimed in T2-ASM-10 are revoked.

---

## 5. Pre-Existing V2 Certificate Audit & Edge/Ownership Impact

Auditing all 456 pre-existing resolved V2 certificates against confirmed CODE intervals:
- **Sound resolved certificates**: 420
- **Demoted certificates**: 36 (all due to `RETURN_PC_NOT_CODE`)
- **Revoked return target edges**: 43 edges across 28 unique addresses in DATA literal pools.
- **CODE bytes dependent on revoked edges**: 0 bytes (the addresses were confirmed DATA; no code was disassembled from them).
- **Ownership demotions**: 0 bytes (Partition V3 remains 100% stable: 156,694 code, 68,980 data, 59,324 padding, 1,172,154 unknown).

---

## 6. Corrected RTS V3.1 Certification

Tool: `tools/asm/rts_v3_certifier.py`  
Output: `workstreams/T2-ASM-10-1/rts_completeness_v3_1.json`  

The certifier was refactored with a pure `certify_site(cert, correlation, function_certificate, pr_refinement, code_intervals)` function. All ambient loop variables were eliminated, and caller binding is keyed strictly by `(module, generation, entry_pc)`.

### Corrected RTS Metrics:
- **Total RTS Sites**: 638
- **Certified Resolved**: **420 / 638 (65.83%)**
  - `RESOLVED_EXACT_RETURN`: 229
  - `RESOLVED_FINITE_SET`: 191
- **Honest Unresolved**: **218 / 638 (34.17%)**
  - `UNRESOLVED_EXTERNAL_ENTRY`: 81
  - `UNRESOLVED_PR_PATH`: 81
  - `UNRESOLVED_CALLER_DOMAIN`: 56 (20 original + 36 demoted)

---

## 7. Control-Flow Scorecard Reconciliation

Canonical indirect resolution recomputed in `workstreams/ASM_RECOVERY_SCORECARD.json`:
- **Indirect Calls / Jumps**: 1,588 / 1,588 resolved (100.0%)
- **RTS Return Sites**: 420 / 638 resolved (65.83%), 218 unresolved (34.17%)
- **Canonical Indirect Denominator**: 2,226
- **Total Indirect Resolved**: **2,008 / 2,226 (90.21%)**
- **Total Indirect Unresolved**: **218 / 2,226 (9.79%)**

### Gate Evaluation:
- `ASM_90_GATE`: **PASS** (90.21% >= 90.00%)
- `FULL_ASM_GAME_GATE`: **NOT_YET_REPROVEN** (factually honest; blocked by 218 unresolved RTS sites and 498,392 SH-2 UNKNOWN bytes)
- `STANDALONE_NATIVE_GATE`: **FROZEN_BY_ASM_FIRST_ARCHITECTURE**

---

## 8. Adversarial Negative Controls Suite P10

File: `tests/asm/negative_controls_p10.py` (272 lines, <= 500)  
Eight new negative controls implemented:
1. `NC-BG: STALE_FUNCTION_CERT_BINDING` — Certifying function A with caller certificate of function B asserts/rejects fail-closed.
2. `NC-BH: UNVERIFIED_PR_MARKED_RESOLVED` — `UNVERIFIED_PR` rejected from resolution fail-closed.
3. `NC-BI: EMPTY_FINITE_RETURN_SET` — `return_domain_count == 0` rejected from `RESOLVED_FINITE_SET`.
4. `NC-BJ: WRONG_FUNCTION_CERTIFICATE` — Caller certificate with wrong module/generation asserts/fails closed.
5. `NC-BK: STACK_PR_SLOT_UNVERIFIED` — `STACK_RESTORED_PR` with `pr_slot_verified == False` rejected fail-closed.
6. `NC-BL: METRIC_TARGET_FORCING` — Individual site certification is independent of aggregate target variables.
7. `NC-BM: RETURN_PC_NOT_CODE` — Return PC pointing to DATA/PADDING demoted to unresolved fail-closed.
8. `NC-BN: CALLER_RETURN_CARDINALITY_MISMATCH` — `return_domain_count != len(return_pcs)` rejected fail-closed.

Total repository negative controls: **74 / 74 (100% PASS)**.  
All 26 CTests under WSL Linux: **26 / 26 (100% PASS)**.  
All 53 pytest tests: **53 / 53 (100% PASS)**.  
Byte-exact reassembly: **4/4 modules byte-exact (0 diff bytes), disc SHA-256 exact, 6 Mednafen scenarios 0 divergence**.  
Source file limit: **All human-maintained files <= 500 lines**.  
Repository hygiene: **Zero commercial bytes committed**.
