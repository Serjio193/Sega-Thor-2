# Experiment Evidence: M-02 SaturnAutoRE Mutation Fault Injection

## 1. Pinned Source Audit

- **Repository**: `SaturnAutoRE` (local clone `/mnt/e/Github/SaturnAutoRE`)
- **Pinned Commit**: `4662aad69f95222fe37c5e6b98f2285b1a7e4653`
- **Pinned Mednafen Submodule**: `155426661b7ac3152e2c93a98da60ac33002b908`
- **Audited Components**:
  - `auto_re.py`: lines 360–568, 1380–1430 (`_test_patch`, `_revert_patch`, `_mutation_loop`)
  - Mednafen `src/drivers/automation.cpp`: `poke <patch_addr> <hex_bytes>` command handler

### Mechanism Summary
SaturnAutoRE implements mutation by sending `poke <addr> 00 09` over IPC to replace guest instructions with SH-2 `NOP` (`0x0009`), or writing perturbed immediate values. It advances emulation by a fixed number of frames and compares screenshots or memory state to detect visual/behavioral differences.

### Methodological Limitations Identified
1. **Conflation of Perturbation with Proof**: Observing that a NOP causes a crash or divergence proves only that the mutated instruction was executed and had an effect. It does *not* prove that a candidate native replacement is semantically or architecturally equivalent.
2. **Interactive / Heuristic Verification**: SaturnAutoRE heavily relies on visual frame inspection and loose heuristic timeouts rather than cycle-exact register/memory trace differential checks.
3. **Savestate Contamination Risk**: Relies on reloading bulk savestates rather than verifying exact byte-level restoration in memory.

---

## 2. Thor 2 Mutation Harness Design

To adopt this method safely within the Thor 2 pipeline, we established a strict C++ harness (`MutationHarness` in `thor::recomp`):
- **Bounded Target**: `0x06004000..0x0600400B` (12 bytes). Mutating outside this range is strictly prohibited.
- **Fail-Closed Verification**: The harness captures original bytes, verifies them against `0TH2.BIN` baseline, applies single-byte mutations or NOPs, tests dispatch rejection, and verifies exact post-restoration byte equality.
- **Zero Contamination**: Dispatch under mutation *must* fail closed: 0 native blocks executed, 0 register side effects, 0 scheduler contamination.

---

## 3. Unit Test Verification (C++ Synthetic Matrix)

Executed via `tests/recomp/test_mutation_harness.cpp`:

| Test Case | Description | Expected Result | Observed Result | Status |
|---|---|---|---|---|
| Range Bounds | Out-of-range address rejection | `apply_mutation` returns false | Rejected immediately | PASS |
| Baseline Guard | Original byte mismatch rejection | `apply_mutation` returns false | Rejected immediately | PASS |
| Restoration Validation | Restore byte mismatch detection | `restore_mutation` returns false | Restoration verified | PASS |
| Single-Byte Matrix | 12/12 individual byte mutations (`0x06004000..0x0600400B`) | `is_eligible` false, 0 executions, fallback clean | 12/12 rejected fail-closed, exact bytes restored, clean dispatch | PASS |
| NOP Matrix | 6/6 instruction NOP replacements (`0x0009`) | `is_eligible` false, 0 executions, fallback clean | 6/6 rejected fail-closed, exact bytes restored, clean dispatch | PASS |

---

## 4. Live Mednafen IPC Test Matrix

Executed via `tools/recomp/mutation_harness.py` against live Mednafen debug oracle:

| Case | Mutation Target | Injected Value | Dispatch Behavior | Continuation / Effect | Status |
|---|---|---|---|---|---|
| Case 1: Inst 0 NOP | `0x06004000` (`MOV.W @R1, R6`, `0x6611`) | `0x0009` (NOP) | Native refused (`is_eligible` false, `ineligible=1`, `fallback=1`, `executed=0`). | Interpreter retired mutated instruction (`retirements_in_interval=1`, cycle `305462370`). | PASS |
| Case 2: Mid-Block | `0x06004006` (`MOV.L @R4, R4`, `0x6442`) | `0x0009` (NOP) | Native refused (`is_eligible` false, `ineligible=1`, `fallback=1`, `executed=0`). | Interpreter retired mutated instruction (`retirements_in_interval=1`, cycle `305462370`). | PASS |
| Case 3: Branch NOP | `0x06004008` (`BRA 0x06004012`, `0xA003`) | `0x0009` (NOP) | Native refused (`is_eligible` false, `ineligible=1`, `fallback=1`, `executed=0`). | Interpreter retired mutated instruction (`retirements_in_interval=1`, cycle `305462370`). | PASS |
| Case 4: Restore Check | `0x06004000..0x0600400B` | Transient mutation $\rightarrow$ exact restore | Native accepted (`is_eligible` true, `executed=1`, `fallback=0`, `shadow_match=1`). | Continuation checkpoint `0x06004280` reached at cycle `307090585` (`delta = 0`) with 0 register divergences across all 23 registers. Zero state contamination. | PASS |

---

## 5. Method Evaluation & Disposition

### Axis 1: Evidence Strength — LOW / NON-AUTHORITATIVE FOR POSITIVE PROOF
- **Equivalence**: Mutation testing cannot prove equivalence. Perturbing a byte and seeing a program fail only proves that the program depends on that byte or that the mutated code is broken.
- **Sufficiency**: Mutation fault injection does not satisfy L0..L5 verification requirements for promoting native candidates.

### Axis 2: Workflow Utility — HIGH FOR FALSIFICATION / NEGATIVE CONTROLS
- **Falsification Harness**: Extremely effective at verifying that guards, hashes, and shadow validators fail closed when code changes.
- **Regression Testing**: Provides automated negative-control coverage ensuring that corrupt or patched RAM cannot trigger native dispatch without qualification.
- **Oracle Integrity**: Validates that fallback mechanisms function properly under anomalous guest conditions.

### Final Disposition: `ADOPT_PARTIAL`
- **Assigned Pipeline Role**: `NEGATIVE_CONTROL_HARNESS` / `FAULT_INJECTION_TESTING`.
- **Constraint**: Must never be used as positive evidence for recompilation correctness or semantic recovery.
- **Next Second-Pass Experiment**: `M-07` — SaturnAutoRE SH-2 instruction semantic corpus / opcode coverage audit.
