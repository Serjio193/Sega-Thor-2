# T2-ASM-04 Experiment Evidence: Secondary Modules & Executable Inventory

## 1. Executive Summary

Task `T2-ASM-04` conducted an exhaustive census across all 33 files on the retail Saturn disc to identify all executable modules, overlays, sound programs, and co-processor code lifetimes, and expanded the lossless assembly container coverage to secondary executable modules.

Key Results:
1. **Identified Executable Modules:**
   - `0TH2.BIN` (535,552 bytes, VMA `0x06004000`): Master SH-2 main engine.
   - `TH2.LOW` (149,504 bytes, VMA `0x002DA000`): Master SH-2 secondary module.
   - `SET07.BIN` (98,304 bytes, VMA `0x060D8000`): Master SH-2 stage/gameplay overlay.
   - `BGM.BIN` (673,792 bytes, Sound RAM `0x00000000` / `0x05A00000`): Motorola 68EC000 sound driver.
   - `MAP.BIN` (4,036,608 bytes): Contains SCU DSP microcode header (`DSP<`).
2. **Co-Processor Life Cycle Verification:**
   - Master SH-2: 100% active code ownership across boot and gameplay.
   - Slave SH-2: Verified dormant/uninitialized (`PC=0x00000000`, `SR=0x000000F0` at frame 1201).
   - 68EC000: SCSP sound driver starts at offset `0x1000` with `MOVE #$2700, SR`.
3. **SET07.BIN Lossless Assembly Container:**
   - Reassembled byte-exact (98,304 / 98,304 bytes, SHA-256 `bb6072222e19f8cb68934cbdb94e7d187c67680bb9e167524f85579ee6bc0af6`).
   - Proved dual-build determinism (0 byte diffs).
   - Verified sector-by-sector private disc splice at LBA 52040.
   - 9/9 fail-closed negative controls pass.
4. **SH-2 Decoder & Semantics Expansion:**
   - Added `MOV_L_WRITE_PREDEC` (`0x2nm6`, `MOV.L Rm, @-Rn`) and `RTS` (`0x000B`) to `thor_sh2`.
   - Promoted `0x002E9910` in `TH2.LOW` to `MNEMONIC_PROVEN` (`mov.l r14, @-r15`).

---

## 2. Evidence Metrics

| Metric | Target | Result | Status |
|---|---|---|---|
| SET07.BIN Byte Exactness | 98,304 bytes | 98,304 bytes (0 diffs) | PASS |
| SET07.BIN SHA-256 | `bb607222...` | `bb607222...` | PASS |
| Dual-Build Determinism | 0 byte diff | 0 byte diff | PASS |
| Disc Splice Match | `fe11d2fb...` | `fe11d2fb...` | PASS |
| TH2.LOW Promoted Mnemonic | `mov.l r14, @-r15` | Verified L0 semantics | PASS |
| SET07 Negative Controls | 9 fail-closed | 9/9 PASS | PASS |
| TH2.LOW Negative Controls | 10 fail-closed | 10/10 PASS | PASS |
| 0TH2.BIN Negative Controls | 20 fail-closed | 20/20 PASS | PASS |
| Schema Negative Controls | 9 fail-closed | 9/9 PASS | PASS |
| CTests (MinGW & WSL) | 24/24 | 24/24 PASS | PASS |
