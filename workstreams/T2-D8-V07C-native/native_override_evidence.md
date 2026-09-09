# Evidence Record: T2-D8-V07C Native Override Verification Matrix

- Date: 2026-09-09
- Oracle: Pinned Mednafen debug fork (`AJBats/mednafen-saturn-debug` commit `155426661b7ac3152e2c93a98da60ac33002b908`)
- Harness: Scripted IPC (`mednafen_bot.py`), `run_v07c_experiment.py`
- Shared Plugin: `libthor_native.so` dynamically loaded via `dlopen`

---

## 1. Timing Reconciliation & Architectural Derivation

- Entry Cycle: `305462360` (PC=`0x06004000`, local frame ts `19307`)
- Instruction 0 (`0x06004000: MOV.W @R1, R6`): +1 cycle -> `305462361` (ts `19308`)
- Instruction 1 (`0x06004002: MOV R0, R15`): +1 cycle -> `305462362` (ts `19309`)
- Instruction 2 (`0x06004004: MOV.L @(disp,PC), R4`): +1 cycle -> `305462363` (ts `19317`, literal read from `0x06004064`, cache fill line `0x06004060..0x0600406F`)
- Instruction 3 (`0x06004006: MOV.L @R4, R4`): +8 cycles -> `305462371` (ts `19318`, SDRAM bus wait from `0x06081C10`, cache fill line `0x06081C10..0x06081C1F`)
- Instruction 4 (`0x06004008: BRA 0x06004012`): +1 cycle -> `305462372` (ts `19333`)
- Instruction 5 (`0x0600400A: NOP` delay slot): +15 cycles -> `305462387` (ts `19334`, branch target fetch + pipeline refill)
- Architectural Exit Cycle: `305462387` (PC=`0x06004012`, ts `19334`)
- Duration of basic block `bb_06004000`: `305462387 - 305462360 = 27 cycles`.
- (Cycle `305462388` / ts `19335` is post-completion of `0x06004012`, belonging to the subsequent block).
- Root cause of initial +14 cycle drift at continuation checkpoint `0x06004280`: Bypassing SH-2 cache during native memory reads left lines `0x06004060` and `0x06081C10` cold, incurring two +7 cycle SDRAM bus miss penalties at `0x06004012` and `0x06004014` in the first BSS loop iteration. Routing memory access through `CPU[0].MRFP/MWFP` eliminated the drift completely.

---

## 2. Dynamic Verification Matrix Results

### Run A — Native Override (`native_mode=2`)
- Mode: 2 (Authoritative Native Override)
- Attempts: 1, Executed: 1, Fallback: 0
- Shadow Match: 1, Shadow Divergences: 0, Ineligible: 0
- Replaced Interval Retirements: `retirements_in_interval = 0` (Original interpreter retired 0 instructions!)
- Checkpoint: Hit `0x06004280` at frame 683, cycle `307090585`
- Registers at `0x06004280`:
  `R0=00000001 R1=000000F1 R2=FFFFFF0F R3=00000001 R4=FFFFF7FF R5=00000000 R6=00006611 R7=06000D00 R8=00000000 R9=00000000 R10=00000000 R11=06096523 R12=06088708 R13=00000001 R14=00000000 R15=06002EDC PC=06004280 SR=00000001 PR=0600427C GBR=00000000 VBR=06000000 MACH=00000000 MACL=00000000 cycle=307090585`

### Run B — Independent Cold-Boot Reproduction (`native_mode=2`)
- Bit-identical match across all 23 registers, cycle (`307090585`), PC, SR, PR, stats, and frame 683.

### Run C — Baseline Interpreter (`native_mode=0`)
- Mode: 0 (Pure Interpreter)
- Attempts: 0, Executed: 0, Fallback: 0
- Replaced Interval Retirements: `retirements_in_interval = 6` (Exact 6 architectural instructions)
- Checkpoint: Hit `0x06004280` at frame 683, cycle `307090585`
- Registers at `0x06004280`:
  `R0=00000001 R1=000000F1 R2=FFFFFF0F R3=00000001 R4=FFFFF7FF R5=00000000 R6=00006611 R7=06000D00 R8=00000000 R9=00000000 R10=00000000 R11=06096523 R12=06088708 R13=00000001 R14=00000000 R15=06002EDC PC=06004280 SR=00000001 PR=0600427C GBR=00000000 VBR=06000000 MACH=00000000 MACL=00000000 cycle=307090585`
- Differential Result: **0 register divergences between Run A and Run C across all 23 CPU registers!**
- Timing Delta: `307090585 - 307090585 = 0 cycles` (Exact 100% cycle parity over 1,628,225 elapsed cycles).

### Run D — Shadow Verify Mode (`native_mode=1`)
- Mode: 1 (Shadow Qualification Only)
- Attempts: 1, Executed: 0, Fallback: 1
- Shadow Match: 1, Shadow Divergences: 0
- Replaced Interval Retirements: `retirements_in_interval = 6`
- Registers at `0x06004280`: Identical to interpreter baseline.

### Run E — Content Byte Corruption Negative Control (`native_mode=2`)
- Injected Fault: Byte at `0x06004000` poked from `0x66` to `0x00`
- Mode: 2
- Attempts: 1, Executed: 0, Fallback: 1, Ineligible: 1
- Shadow Match: 0, Shadow Divergences: 0
- Replaced Interval Retirements: `retirements_in_interval = 6`
- Fail-closed result: Block disqualified, native code not committed, interpreter gracefully executed corrupted instruction (`R6=0x00000011`). Zero partial commit.

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
- `test_timing_constants`: PASS (`BLOCK_DURATION == 27`, `NEXT_INSTRUCTION_COMPLETION_BOUNDARY_DELTA == 28`)

Result: 12/12 test suites passing on Windows MinGW and Linux WSL (Debug and Release).
