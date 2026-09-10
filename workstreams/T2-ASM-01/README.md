# T2-ASM-01 — First Bounded SH-2 ASM Round-Trip & Runtime Proof

## Overview

- **Task**: `T2-ASM-01`
- **Architectural Authority**: ADR `D-015` (`ASM_FIRST_RECOVERY`)
- **Status**: **PASS**
- **Target Block**: `bb_06004000` (Master SH-2, `0TH2.BIN`, `0x06004000..0x0600400A`)
- **Byte Extent**: 12 bytes (`66 11 6F 03 D4 17 64 42 A0 03 00 09`)
- **Target Revision**: `thor2_ntsc_patched_fe11d2fb`
- **Dynamic Oracle**: Pinned Mednafen debug fork (`AJBats/mednafen-saturn-debug` commit `155426661b7ac3152e2c93a98da60ac33002b908`)

---

## Mission Accomplished

1. **Toolchain Selected & Pinned**:
   - Single open toolchain: GNU Binutils SH cross-toolchain (`binutils-sh-elf 2.40+2`).
   - Pinned exact SHA-256 hashes of `sh-elf-as`, `sh-elf-ld`, `sh-elf-objcopy`, `sh-elf-objdump`.
   - Explicit target: `sh-elf`, explicit ISA: `-isa=sh2`, explicit big-endian: `-big` / `-EB`.
   - Strictly zero proprietary Sega SDK, zero leaked tools.
2. **Mechanical Assembly Emission**:
   - Implemented bounded SH-2 ASM emitter (`tools/asm/generate_asm_slice.py`).
   - Emits real SH-2 mnemonics (`MOV.W @Rm, Rn`, `MOV Rm, Rn`, `MOV.L @(disp,PC), Rn`, `MOV.L @Rm, Rn`, `BRA disp`, `NOP`).
   - Real mnemonics only; raw opcode words (`.word`) strictly forbidden for proven instructions.
   - Fails closed on unknown opcodes.
3. **Linker & VMA Proof**:
   - Linker script `asm/linker/bb_06004000.ld` establishes original VMA `0x06004000`.
   - Symbolic resolution resolves `lit_06004064` and `loc_06004012` naturally into `D417` and `A003`.
   - Output `.text` size verified: exactly 12 bytes, zero unresolved relocations.
4. **Byte-Exact Gate**:
   - Length: 12 == 12 bytes.
   - Differing bytes: 0.
   - SHA-256: `837951102416988d0fc9cbc55c581662463a28dca74dceeb6bd0fca3fdaec10e`.
   - Classification: `ASM_BYTE_EXACT`.
5. **Private Module Splice Test**:
   - Spliced the 12 rebuilt bytes into private canonical `0TH2.BIN` at offset 0.
   - Canonical module SHA-256 `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64` preserved byte-for-byte.
6. **Bounded Runtime Substitution Proof in Mednafen**:
   - Executed clean Mednafen oracle in pure interpreter mode (`native_mode 0`).
   - Compared cold boot ORIGINAL vs cold boot ASM_REBUILT.
   - Entry `0x06004000`: cycle `305462360`, 23 architectural registers match 100%.
   - Target `0x06004012`: cycle `305462387`, duration exactly 27 cycles, 23 registers match 100%.
   - Checkpoint `0x06004280`: cycle `307090585`, continuation matches 100%.
   - Classification: `ASM_RUNTIME_VERIFIED`.
7. **Negative Controls**:
   - 12/12 negative controls passed and verified to fail closed.

---

## State & Gate Accounting

- `bb_06004000`:
  - `ASM_BYTE_EXACT`: **PASS**
  - `ASM_RUNTIME_VERIFIED`: **PASS**
- `FULL_ASM_GAME_GATE`: **NOT_SATISFIED** (1/N slices proven).
- Broad C++ Translation: **FROZEN**.
- M-03 Status: **READY_FOR_BOUNDED_TEST / DEFERRED_BY_ASM_FIRST_ARCHITECTURE**.
- Next Task: `T2-ASM-02 — Module Assembly Skeleton & Lossless CODE/DATA/UNKNOWN Emission for 0TH2.BIN`.
