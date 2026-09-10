# T2-ASM-02 — Full 0TH2.BIN Lossless Assembly Container & Byte-Exact Module Round-Trip

## Overview

- **Task**: `T2-ASM-02`
- **Architectural Authority**: ADR `D-015` (`ASM_FIRST_RECOVERY`)
- **Status**: **PASS**
- **Target Module**: `0TH2.BIN` (Primary Saturn Game Binary, Master SH-2)
- **Module Extent**: 535,552 bytes (`0x82C00` bytes, VMA `0x06004000..0x06086BFF`)
- **Confirmed Code Extent**: 22 bytes (`bb_06004000` [12 bytes] + `bb_06004280` [10 bytes])
- **Lossless RAW_UNKNOWN Extent**: 535,530 bytes (`.byte` directives, zero `.incbin`, zero raw `.word` escapes)
- **Target Revision**: `thor2_ntsc_patched_fe11d2fb`
- **Canonical Module SHA-256**: `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64`
- **Canonical Disc SHA-256**: `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8`
- **Dynamic Oracle**: Pinned Mednafen debug fork (`AJBats/mednafen-saturn-debug` commit `155426661b7ac3152e2c93a98da60ac33002b908`)

---

## Mission Accomplished

1. **Tooling Provenance Debt Repaired**:
   - Replaced temporary Python decoders with generic C++ tool `tools/asm/export_sh2_asm_ir.cpp` linked directly against authoritative `thor_sh2` (`thor::sh2::decode_sh2`).
   - Integrated into root CMake build (`export_sh2_asm_ir`).
   - Exports complete machine-readable Assembly IR JSON (`assembly_ir.json`) containing opcode IDs, operands, flow classifications, and label metadata.
2. **Private Lossless Full-Module Assembly Container**:
   - Implemented generator `tools/asm/generate_full_module_asm.py`.
   - Emits real SH-2 mnemonics for all 11 confirmed code instructions (22 bytes across `bb_06004000` and `bb_06004280`).
   - Emits remaining 535,530 bytes losslessly via `.byte` directives (16 bytes per line).
   - Generated private assembly stored under gitignored `.private/asm/0TH2/0TH2.s` (33,521 lines).
   - Strictly zero commercial binary payload tracked in Git.
3. **Real Module Label Resolution (Zero `.equ` Workarounds)**:
   - Resolved all literal pool loads and branch targets to real in-module byte offsets:
     - `loc_06004012` at offset `+0x12` (`0x06004012`)
     - `lit_06004064` at offset `+0x64` (`0x06004064`)
     - `lit_0600435C` at offset `+0x35C` (`0x0600435C`)
     - `lit_06004360` at offset `+0x360` (`0x06004360`)
     - `lit_06004364` at offset `+0x364` (`0x06004364`)
   - GNU `sh-elf-as` computes exact displacements natively in the same `.text` section without `.equ` hacks.
4. **Linker Script Assertions & VMA Proof**:
   - Linker script `asm/linker/0TH2.ld` links at Saturn VMA `0x06004000`.
   - Hard linker assertions enforce: `ADDR(.text) == 0x06004000`, `SIZEOF(.text) == 535552`, and exact addresses for all 5 labels.
   - Clean ELF link verified: zero unresolved relocations.
5. **Byte-Exact Parity & Dual-Build Determinism**:
   - Build pipeline `tools/asm/build_full_module.py` extracts exactly 535,552 bytes.
   - Differing bytes: 0. SHA-256: `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64`.
   - Dual-build determinism verified: 0 differing bytes between independent builds.
6. **Sector-by-Sector Private Disc Splice Verification**:
   - Reassembled 535,552 bytes spliced across sectors 24..285 of retail disc image.
   - Spliced disc image SHA-256 matches canonical retail disc `fe11d2fb...` bit-for-bit.
7. **Interpreter-Only Mednafen Runtime Parity Across 5 Checkpoints**:
   - Executed clean Mednafen oracle in pure interpreter mode (`native_mode 0`).
   - Compared cold-boot ORIGINAL vs cold-boot ASM_REBUILT:
     - `0x06004000` (entry): cycle `305462360`, 23/23 registers match.
     - `0x06004012` (branch target): cycle `305462387`, duration 27 cycles, 23/23 registers match.
     - `0x06004280` (checkpoint): cycle `307090585`, 23/23 registers match.
     - `0x0600A0F8` (checkpoint): cycle `316309144`, 23/23 registers match.
     - `0x002E9910` (checkpoint): cycle `387459915`, 23/23 registers match.
   - Zero register divergence, zero timing divergence.
8. **Negative Controls Suite & Publication Hygiene**:
   - 28/28 negative controls pass and fail closed (`tools/asm/verify_full_module.py`).
   - Git publication hygiene verified: zero private files or commercial payloads tracked.

---

## State & Gate Accounting

- `0TH2.BIN`:
  - `MODULE_CONTAINER_ESTABLISHED`: **PASS**
  - `ASM_BYTE_EXACT`: **PASS** (535,552 / 535,552 bytes)
  - `ASM_RUNTIME_VERIFIED`: **PASS** (5 checkpoints, 0 divergence)
- `FULL_ASM_GAME_GATE`: **IN_PROGRESS** (primary module skeleton established; other disc modules remain).
- Broad C++ Translation: **FROZEN** (ADR D-015).
