# T2-ASM-CARVER Experiment Evidence: Saturn Recovery Carver & Denominator Re-Audit

## 1. Executive Summary

Task `T2-ASM-CARVER-01` addressed the fundamental denominator integrity problem in the Thor 2 recovery scorecard: while proven mnemonic coverage reported ~96.6%, the denominator excluded large unexamined regions of executable code, leaving ~1,399,886 bytes as unclassified `UNKNOWN`.

By implementing an evidence-driven Saturn Recovery Carver comprising:
1. Canonical Central Interval Database (`IntervalDatabase`);
2. Prioritized Detector Registry (`DetectorRegistry`) with 8 Saturn-specific detectors;
3. Execution Conflict Rule enforcement (fail-closed);
4. R-Studio Style RAM → Disc Signature Carver;
5. Provenance DAG with strictly gated graph expansion;
6. Fixed-point loop convergence;
7. UNKNOWN Gap Auditor & Campaign Engine;

the recovery pipeline reached a deterministic fixed point in 3 passes, discovering **2,842 newly confirmed executable code bytes**, **81,435 bytes of structured data** (literal pools, pointer tables, MMIO pointers, string tables), and **82,562 bytes of alignment padding**, reducing residual `UNKNOWN` by **166,839 bytes** with **0 conflicts**.

The proven mnemonic coverage denominator has been honestly re-audited from 57,266 to 60,108 bytes, adjusting coverage from 96.64% to **92.07%** while maintaining `ASM_90_GATE = PASS`.

---

## 2. Evidence Metrics Table

| Metric | Target | Result | Status |
|---|---|---|---|
| Interval Database Schema | Non-overlapping, exhaustive | 100% byte coverage across all 4 modules | PASS |
| Fixed-Point Convergence | Deterministic termination | Converged in 3 passes (0 diffs on rerun) | PASS |
| Execution Conflict Rule | 0 conflicts / fail-closed | 0 conflicts detected across 21,976 ranges | PASS |
| Graph Expansion Safety | Only CONFIRMED parents expand | 0 unconfirmed parent promotions (Rule 5) | PASS |
| Provenance DAG Tracking | 100% lineage accountability | 13,780 nodes, 3,434 edges fully traceable | PASS |
| P1 Execution Gaps | 0 execution hits in UNKNOWN | **0 remaining P1 execution gaps** | PASS |
| Newly Confirmed Code | > 0 bytes discovered | **+2,842 bytes** (entering denominator) | PASS |
| Classified Data & Padding | > 50,000 bytes | **163,997 bytes** (81,435 data + 82,562 pad) | PASS |
| Audited Mnemonic Coverage | >= 90.00% | **92.07%** (55,342 / 60,108 bytes) | **PASS (HONEST)** |
| Dual-Run Determinism | Bit-identical summary | SHA-256 identical across dual runs | PASS |

---

## 3. Module Breakdown

### `0TH2.BIN` (Main Engine, Master SH-2, VMA `0x06004000`, 535,552 bytes)
- Confirmed Code: **56,628 bytes** (+2,670 bytes discovered)
- Proven Mnemonics: 52,050 bytes
- Classified Data: **43,297 bytes** (Literal Pools: 6,486, Pointer Tables: 33,924, Strings: 2,511, MMIO: 376)
- Alignment Padding: 714 bytes
- Residual UNKNOWN: 434,913 bytes (reduced from 481,594)

### `TH2.LOW` (Secondary Module, Master SH-2, VMA `0x002DA000`, 149,504 bytes)
- Confirmed Code: **3,436 bytes** (+170 bytes discovered)
- Proven Mnemonics: 3,250 bytes
- Classified Data: **19,422 bytes** (Strings: 10,474, Pointer Tables: 8,044, Literal Pools: 636, MMIO: 268)
- Alignment Padding: 10,430 bytes
- Residual UNKNOWN: 116,216 bytes (reduced from 146,238)

### `SET07.BIN` (Stage Overlay, Master SH-2, VMA `0x060D8000`, 98,304 bytes)
- Confirmed Code: **14 bytes** (+2 bytes discovered)
- Proven Mnemonics: 12 bytes
- Classified Data: **3,647 bytes** (Pointer Tables: 2,720, Strings: 675, MMIO: 244, Literal Pools: 8)
- Alignment Padding: 39,598 bytes
- Residual UNKNOWN: 55,045 bytes (reduced from 98,292)

### `BGM.BIN` (Sound Driver, MC68EC000, Sound RAM `0x00000000`, 673,792 bytes)
- Confirmed Code: 30 bytes
- Proven Mnemonics: 30 bytes
- Classified Data: **15,069 bytes** (Strings: 14,060, MMIO: 885, Pointer Tables: 124)
- Alignment Padding: 31,820 bytes
- Residual UNKNOWN: 626,873 bytes (reduced from 673,762)

---

## 4. Residual UNKNOWN Campaigns

The Gap Reporter clustered all remaining UNKNOWN intervals into campaigns:
- **P1 (Execution hits): 0 gaps** (All dynamically executed bytes are now confirmed code).
- **P2 (Provenance chains): 0 gaps**.
- **P3 (Control-flow reachability): 2,259 gaps**.
- **P4 (Data consumer patterns): 1,994 gaps**.
- **P5 (Heuristic gaps): 3,943 gaps**.
Total Campaigns: 43 localized structural campaigns.
