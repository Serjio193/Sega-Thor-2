# M-07 Experiment Evidence — SaturnRecomp SH-2 Reference Corpus

- **Experiment Date**: 2026-09-10
- **Upstream Git Pin**: `26c9715e5493054b8a205aa31d73d8f125fdd8f5`
- **Pinned Git Blobs**:
  - `external/sh2-recomp-core/common/sh2_decoder.c`: `6a5f7e06606c2dab20e84b5c014c014647be70e4`
  - `external/sh2-recomp-core/common/sh2_isa.h`: `709f92437990a2a0fe6b69d34565cea9d432a844`
- **Authority Standard**: Hitachi SH-1/SH-2 Programming Manual Rev. 4.0 (Sept 2004)
- **Dynamic Oracle**: AJBats/mednafen-saturn-debug (`155426661b7ac3152e2c93a98da60ac33002b908`)
- **Status**: **PASS (0 unexplained decode or semantic disagreements across 20 decode vectors and 8 live semantic cases)**

---

## 1. Startup Block Overlap Cross-Check (bb_06004000)

The six instructions forming `0TH2.BIN` startup basic block 0 (`0x06004000..0x0600400A`) were evaluated against SaturnRecomp's decoder and compared against the Thor 2 reference manifest:

| Opcode | Address | Mnemonic | Thor 2 Decoder | SaturnRecomp Decoder | Hitachi Manual | Mednafen Oracle | Disagreement |
|---|---|---|---|---|---|---|---|
| `0x6611` | `0x06004000` | `MOV.W @R1, R6` | `MOV_W_READ_MEM`, R1->R6, READ_S16 | `op=6 (mov.w@ld)`, n=6, m=1, size=2, load=1 | Sec 5.25 | `OP_MOV_W_REGINDIR_REG` | **0** |
| `0x6F03` | `0x06004002` | `MOV R0, R15` | `MOV_REG`, R0->R15, NONE | `op=1 (mov)`, n=15, m=0, size=0 | Sec 5.23 | `OP_MOV_REG_REG` | **0** |
| `0xD417` | `0x06004004` | `MOV.L @(0x5C, PC), R4` | `MOV_L_PC_REL`, disp=0x17, target `0x06004064` | `op=4 (mov.l@pc)`, n=4, disp=92, target `0x06004064` | Sec 5.22 | `OP_MOV_L_PCREL_REG` | **0** |
| `0x6442` | `0x06004006` | `MOV.L @R4, R4` | `MOV_L_READ_MEM`, R4->R4, READ_U32 | `op=7 (mov.l@ld)`, n=4, m=4, size=4, load=1 | Sec 5.26 | `OP_MOV_L_REGINDIR_REG` | **0** |
| `0xA003` | `0x06004008` | `BRA 0x06004012` | `BRA`, disp=3, target `0x06004012`, delay slot | `op=105 (bra)`, disp=6, target `0x06004012`, delay=1 | Sec 5.10 | `OP_BRA` | **0** |
| `0x0009` | `0x0600400A` | `NOP` | `NOP`, sequential, NONE | `op=126 (nop)`, sequential, flags=0 | Sec 5.34 | `OP_NOP` | **0** |

**Overlap Disagreements: 0.**

---

## 2. Future-Expansion Synthetic Probe Corpus

A synthetic corpus of 14 instructions covering unmodeled classes was evaluated across Hitachi hardware authority, Mednafen, and SaturnRecomp:

| Opcode | Address | Instruction Form | Architectural Semantic Properties | SaturnRecomp Decode Result | Agreement |
|---|---|---|---|---|---|
| `0x8B04` | `0x06001000` | `BF 0x0600100C` | Conditional branch if T==0, no delay slot, target = PC+4+(4*2) | `op=101 (bf)`, cond=1, branch=1, delay=0, target `0x0600100C` | **MATCH** |
| `0x8904` | `0x06001000` | `BT 0x0600100C` | Conditional branch if T==1, no delay slot, target = PC+4+(4*2) | `op=103 (bt)`, cond=1, branch=1, delay=0, target `0x0600100C` | **MATCH** |
| `0x8F04` | `0x06001000` | `BF/S 0x0600100C` | Delayed conditional branch if T==0, delay slot executes | `op=102 (bf/s)`, cond=1, branch=1, delay=1, target `0x0600100C` | **MATCH** |
| `0x8D04` | `0x06001000` | `BT/S 0x0600100C` | Delayed conditional branch if T==1, delay slot executes | `op=104 (bt/s)`, cond=1, branch=1, delay=1, target `0x0600100C` | **MATCH** |
| `0x3013` | `0x06001000` | `CMP/GE R1, R0` | Signed compare: (int32)R0 >= (int32)R1 -> T | `op=47 (cmp/ge)`, n=0, m=1, flags=0x0300 | **MATCH** |
| `0x3017` | `0x06001000` | `CMP/GT R1, R0` | Signed compare: (int32)R0 > (int32)R1 -> T | `op=49 (cmp/gt)`, n=0, m=1, flags=0x0300 | **MATCH** |
| `0x3012` | `0x06001000` | `CMP/HS R1, R0` | Unsigned compare: (uint32)R0 >= (uint32)R1 -> T | `op=46 (cmp/hs)`, n=0, m=1, flags=0x0300 | **MATCH** |
| `0x4000` | `0x06001000` | `SHLL R0` | Logical left shift: R0<<=1, MSB -> T, LSB 0 | `op=93 (shll)`, n=0, m=0 | **MATCH** |
| `0x4021` | `0x06001000` | `SHAR R0` | Arithmetic right shift: (int32)R0>>=1, LSB -> T, sign preserved | `op=92 (shar)`, n=0, m=2 | **MATCH** |
| `0x70FF` | `0x06001000` | `ADD #-1, R0` | Immediate sign extension: imm -1 (0xFFFFFFFF) added to R0 | `op=41 (add#)`, n=0, imm=-1 | **MATCH** |
| `0x4024` | `0x06001000` | `ROTCL R0` | Rotate left through T: new_T = MSB, new_R0 = (R0<<1)\|old_T | `op=89 (rotcl)`, n=0, m=2 | **MATCH** |
| `0x2017` | `0x06001000` | `DIV0S R1, R0` | 1-step div init: MSB(R0)->Q, MSB(R1)->M, M^Q->T | `op=54 (div0s)`, n=0, m=1 | **MATCH** |
| `0x3014` | `0x06001000` | `DIV1 R1, R0` | Single-step division step updating Q, M, T and R0 | `op=53 (div1)`, n=0, m=1 | **MATCH** |
| `0x401F` | `0x06001000` | `MAC.W @R1+, @R0+` | 16x16->32 accumulate to MAC, post-inc R1+=2, R0+=2 | `op=64 (mac.w)`, n=0, m=1, load=1 | **MATCH** |

**Synthetic Probe Disagreements: 0.**

---

## 3. Independent Semantic Cross-Checks

Representative edge cases evaluated against Hitachi manual, Mednafen, and SaturnRecomp's semantic test suite (`tests/sh2_semantics.c`):

1. **Signed vs Unsigned Compare**:
   - `0xFFFFFFFF` vs `0x00000001`:
   - `CMP/HS` (unsigned): `0xFFFFFFFF >= 1` is TRUE -> `T = 1`.
   - `CMP/GE` (signed): `-1 >= 1` is FALSE -> `T = 0`.
   - Result: All sources agree. Disagreements: 0.
2. **Shift Zero-Fill vs Sign-Fill**:
   - `0xFFFFFFFF >> 1`:
   - `SHLR` (logical): `0x7FFFFFFF` (MSB filled with 0).
   - `SHAR` (arithmetic): `0xFFFFFFFF` (sign-extended).
   - Result: All sources agree. Disagreements: 0.
3. **Immediate Sign Extension**:
   - `ADD #imm, Rn` with `imm = 0xFF (-1)`:
   - 8-bit sign-extended to 32 bits (`0xFFFFFFFF`), subtracting 1 from Rn.
   - Result: All sources agree. Disagreements: 0.
4. **Branch Target Formula & Delay Slot Execution**:
   - `target = PC + 4 + (sign_extend(disp) * 2)`.
   - In `BF/S`, `BT/S`, `BRA`, the delay slot instruction at `PC + 2` is guaranteed to execute before the branch target is evaluated.
   - Result: All sources agree. Disagreements: 0.
5. **ROTCL & DIV1 Operations**:
   - Bitwise state transitions match Hitachi SH-2 hardware specifications.
   - Result: All sources agree. Disagreements: 0.

**Total Unexplained Semantic Disagreements: 0.**

---

## 4. Test Verification and Negative Controls

- **SaturnRecomp Health Check**: Built and ran `tests/sh2_semantics` against pinned commit `26c9715`: `PASS: 39 checks, 0 failed`.
- **Project-Side Automated Test**: `tests/recomp/test_m07_reference.py` integrated into CMake / CTest.
- **Strict External Reproduction**: Verified with `python tests/recomp/test_m07_reference.py --require-external` across Windows MinGW and Linux WSL against clean checkouts of the external repository.
- **Fail-Closed Negative Controls**: 18 distinct corruption scenarios tested:
  1. Corrupted schema version -> Caught and rejected.
  2. Corrupted method ID -> Caught and rejected.
  3. Missing pinned commit metadata -> Caught and rejected.
  4. Missing decoder blob metadata -> Caught and rejected.
  5. Missing ISA blob metadata -> Caught and rejected.
  6. Truncated overlap vector list -> Caught and rejected.
  7. Zero branch target on conditional branch -> Caught and rejected.
  8. Missing branch flag on `BF` -> Caught and rejected.
  9. Missing delay slot flag on `BF/S` -> Caught and rejected.
  10. Corrupted immediate value on `ADD #-1` -> Caught and rejected.
  11. Invalid access size (3 bytes) on memory read -> Caught and rejected.
  12. Missing load flag on memory read (`mov.w@ld`) -> Caught and rejected.
  13. Spurious store flag on memory read (`mov.w@ld`) -> Caught and rejected.
  14. Missing conditional flag on `BF` -> Caught and rejected.
  15. Missing displacement flag on `BRA` -> Caught and rejected.
  16. Missing required opcode class (`DIV1`) -> Caught and rejected.
  17. Empty semantic vector list -> Caught and rejected.
  18. Missing expected output in semantic vector -> Caught and rejected.

All 14 CTest test suites pass 100% on MinGW Windows and Linux WSL (Debug and Release).

---

## 5. Method Disposition

1. **M-07A (SH-2 Decoder & Semantic Reference Corpus)**:
   - **Evidence Strength**: MEDIUM (Clean-room third-party implementation; authoritative reference remains Hitachi manual and Mednafen oracle)
   - **Workflow Utility**: HIGH (Rapid decoding cross-check and semantic disambiguation)
   - **Disposition**: **ADOPT_PARTIAL (DECODER_AND_SEMANTIC_REFERENCE)**
   - Used as an independent static cross-check accelerator for future instruction expansion.
2. **M-07B (AOT Translation Emitter / C Codegen)**:
   - **Evidence Strength**: N/A (absent)
   - **Workflow Utility**: N/A (absent)
   - **Disposition**: **NOT_PRESENT_AT_PIN (REJECT_AT_PIN / DEFER)**
   - Pinned commit `26c9715` contains no public AOT emitter or C translation generator.
