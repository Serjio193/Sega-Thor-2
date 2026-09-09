# Workstream T2-D7 / V-07B — Shadow Checker Validation

Status:
- **`D7` (Shadow recompilation framework)**: **`BOUNDED_PROOF` for `bb_06004000`**
- **`V-07B` (Shadow comparison validation)**: **`PASS`**
- **`D8` / `V-07C` (Authoritative native promotion)**: **`PROPOSED`** (Do NOT claim DONE)

Target: Thor 2 Master SH-2 Startup Basic Block `bb_06004000` (`0x06004000..0x0600400A`, exit `0x06004012`, module `0TH2.BIN`, CPU `MASTER_SH2`).

---

## 1. Overview

This milestone delivers the production reusable D7 shadow execution comparison framework (`ShadowChecker`) and proves that it detects every required class of divergence without contaminating oracle state:

1. **Reusable Production Architecture**:
   - `include/thor/recomp/shadow_checker.hpp` and `src/recomp/shadow_checker.cpp`.
   - Complete outcome comparator across R0..R15, PC, SR, PR/GBR/VBR/MACH/MACL, ordered memory read/write logs (kind, address, value, width, sequence), and bounded event safety metadata.
   - Built-in fail-closed eligibility guard integration via `check_block_eligibility`.
   - Strict anti-aliasing enforcement preventing candidate or oracle from sharing mutable state references.

2. **V-07B Positive Shadow Proof**:
   - Replayed against 4 independent test vectors: Synthetic Vector A, Sign-Extension Vector B, Zero-Boundary Vector C, and Real Thor 2 cold-boot capture.
   - Zero CPU divergences, zero memory log divergences, and exact match against accepted Mednafen oracle constants.

3. **V-07B Negative Fault Controls**:
   - 100% detection rate across 24 distinct fault injections covering register corruption (R0..R15, PC, SR, PR/GBR/MACH/MACL), memory write divergences (omitted write, added write, wrong address, wrong width, wrong value, reversed order), event safety violations, and block eligibility mismatches.

4. **Pre-State Storage Isolation Proof**:
   - Proves candidate execution cannot mutate oracle execution state or the original captured pre-state.
   - Proves oracle execution cannot contaminate candidate input pre-state.
   - Verifies distinct physical object memory addresses for candidate and oracle execution environments.

---

## 2. Evidence Documents

- [shadow_validation_evidence.md](shadow_validation_evidence.md): Complete differential results, negative fault matrix, and isolation proofs.
