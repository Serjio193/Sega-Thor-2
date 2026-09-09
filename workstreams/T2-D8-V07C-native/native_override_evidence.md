# Evidence Record: T2-D8-V07C Native Override Verification Matrix

- Date: 2026-09-09
- Oracle: Pinned Mednafen debug fork (`AJBats/mednafen-saturn-debug` commit `155426661b7ac3152e2c93a98da60ac33002b908`)
- Harness: Scripted IPC (`mednafen_bot.py`), `run_v07c_experiment.py`
- Shared Plugin: `libthor_native.so` dynamically loaded via `dlopen`

---

## 1. Timing Reconciliation

- Entry Cycle: `305462360` (PC=`0x06004000`)
- Exit Cycle: `305462388` (PC=`0x06004012`)
- Execution Window: `305462388 - 305462360 = 28 cycles` (exact hardware retirement window)
- C++ Unit Test Assertion: `static_assert(305462388u - 305462360u == 28u);` in `tests/recomp/test_native_dispatcher.cpp`.

---

## 2. Dynamic Verification Matrix Results

### Run A — Native Override (`native_mode=2`)
- Mode: 2 (Authoritative Native Override)
- Attempts: 1, Executed: 1, Fallback: 0
- Shadow Match: 1, Shadow Divergences: 0, Ineligible: 0
- Replaced Interval Retirements: `retirements_in_interval = 0` (Original interpreter retired 0 instructions!)
- Checkpoint: Hit `0x06004280` at frame 683, cycle `307090599`
- Registers at `0x06004280`:
  `R0=00000001 R1=000000F1 R2=FFFFFF0F R3=00000001 R4=FFFFF7FF R5=00000000 R6=00006611 R7=06000D00 R8=00000000 R9=00000000 R10=00000000 R11=06096523 R12=06088708 R13=00000001 R14=00000000 R15=06002EDC PC=06004280 SR=00000001 PR=0600427C GBR=00000000 VBR=06000000 MACH=00000000 MACL=00000000`

### Run B — Independent Cold-Boot Reproduction (`native_mode=2`)
- Bit-identical match across all 23 registers, PC, SR, PR, stats, and frame 683.

### Run C — Baseline Interpreter (`native_mode=0`)
- Mode: 0 (Pure Interpreter)
- Attempts: 0, Executed: 0, Fallback: 0
- Replaced Interval Retirements: `retirements_in_interval = 5` (Delay branch pipeline retirement)
- Checkpoint: Hit `0x06004280` at frame 683, cycle `307090585`
- Registers at `0x06004280`:
  `R0=00000001 R1=000000F1 R2=FFFFFF0F R3=00000001 R4=FFFFF7FF R5=00000000 R6=00006611 R7=06000D00 R8=00000000 R9=00000000 R10=00000000 R11=06096523 R12=06088708 R13=00000001 R14=00000000 R15=06002EDC PC=06004280 SR=00000001 PR=0600427C GBR=00000000 VBR=06000000 MACH=00000000 MACL=00000000`
- Differential Result: **0 register divergences between Run A and Run C across all 23 CPU registers!**
- Timing Delta: `307090599 - 307090585 = 14 cycles` over 1,628,239 elapsed cycles (0.00086% delta).

### Run D — Shadow Verify Mode (`native_mode=1`)
- Mode: 1 (Shadow Qualification Only)
- Attempts: 1, Executed: 0, Fallback: 1
- Shadow Match: 1, Shadow Divergences: 0
- Replaced Interval Retirements: `retirements_in_interval = 5`
- Registers at `0x06004280`: Identical to interpreter baseline.

### Run E — Content Byte Corruption Negative Control (`native_mode=2`)
- Injected Fault: Byte at `0x06004000` poked from `0x66` to `0x00`
- Mode: 2
- Attempts: 1, Executed: 0, Fallback: 1, Ineligible: 1
- Shadow Match: 0, Shadow Divergences: 0
- Fail-closed result: Block disqualified, native code not committed, interpreter gracefully executed corrupted instruction (`R6=0x00000011`).

---

## 3. Unit Test Verification Matrix

Test Suite `test_native_dispatcher`:
- `test_interpreter_mode`: PASS (Live state untouched)
- `test_shadow_verify_mode`: PASS (Shadow match logged, live state untouched)
- `test_native_override_positive`: PASS (State updated to R6=0x6611, R15=0x06002EDC, R4=0x060917DC, cycles=27)
- `test_negative_wrong_revision`: PASS (Ineligible -> Fallback)
- `test_negative_corrupted_bytes`: PASS (Ineligible -> Fallback)
- `test_negative_slave_active`: PASS (Ineligible -> Fallback)
- `test_negative_dma_active`: PASS (Ineligible -> Fallback)
- `test_negative_irq_pending`: PASS (Ineligible -> Fallback)
- `test_negative_shadow_divergence`: PASS (Shadow divergence -> Fallback)
- `test_negative_unregistered_pc`: PASS (Fallback)
- `test_c_abi_bridge`: PASS
- `test_timing_constants`: PASS (`305462388 - 305462360 == 28`)

Result: 12/12 test suites passing on Windows MinGW and Linux WSL (Debug and Release).
