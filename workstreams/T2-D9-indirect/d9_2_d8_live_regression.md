# D8 Live Production Regression Record (T2-D9.3)

Date: 2026-09-10
Baseline: 3aa1ee249774eb63a46f10b9459c023cfed8e116
Tested Working Tree: Uncommitted working tree implementing T2-D9.3 changes on top of 3aa1ee, subsequently committed and pushed as 32ebc5a4ffc42882d6b6d891167a29956fe0e9a6 (commit 3aa1ee alone did not contain D9.3 changes).
External Pins:
- SaturnAutoRE harness: 4662aad69f95222fe37c5e6b98f2285b1a7e4653
- Mednafen debug submodule: 155426661b7ac3152e2c93a98da60ac33002b908
Environment: Windows MinGW-w64 / MSYS2 pinned SaturnAutoRE test harness running pinned Mednafen debug submodule
Target Block: bb_06004000 (0x06004000 .. 0x0600400A)
Continuation Checkpoint: 0x06004280 (Hit 1 cold boot, cycle 307090585)

---

## 1. Regression Objective

Verify that all architectural changes introduced in D9.2 and D9.3 (dynamic exit descriptor, runtime memory contracts, delayed-transfer state checks, and fail-closed registration validation) preserve existing D8 native override production behavior with zero divergence.

---

## 2. Live Execution Protocol (run_v07c_experiment.py)

Harness command:
python tools/recomp/run_v07c_experiment.py

### Run Results Matrix

| Run | Configuration / Mode | Native Executed | Fallback | Shadow Matches | Register Match % | Checkpoint PC | Checkpoint Cycle | Result |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Run A** | Native Override | 1 | 0 | 1 | 100% (23/23) | 0x06004280 | 307090585 | **PASS** |
| **Run B** | Determinism Repeat | 1 | 0 | 1 | 100% (23/23) | 0x06004280 | 307090585 | **PASS (Bit-Identical to Run A)** |
| **Run C** | Pure Interpreter Reference | 0 | 1 | 0 | 100% (23/23) | 0x06004280 | 307090585 | **PASS (Identical to Runs A & B)** |
| **Run D** | Shadow Verify Mode | 0 | 1 | 1 | 100% (23/23) | 0x06004280 | 307090585 | **PASS (Shadow Proved, Fallback=1)** |
| **Run E** | Injected Corruption | 0 | 1 | 0 | 100% (23/23) | 0x06004280 | 307090585 | **PASS (Fail-Closed Rejection)** |

---

## 3. Register State Verification at 0x06004280

All 23 SH-2 architectural registers matched 100% identically between native override (Run A/B) and pure interpreter baseline (Run C) at the first execution of 0x06004280:

- R0..R15: exact match
- PC: 0x06004280
- SR: exact match
- PR: exact match
- GBR, VBR: exact match
- MACH, MACL: exact match
- Live cycle counter: 307090585

---

## 4. Conclusion

The D9.2/D9.3 contract hardening and registration validation did not perturb D8 production execution. The native override for bb_06004000 remains bit-identical and fully verified against the hardware oracle.
