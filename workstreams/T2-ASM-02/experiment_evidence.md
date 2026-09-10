# Experiment Evidence: T2-ASM-02 — Full 0TH2.BIN Lossless Assembly Container

## Experiment Metadata

- **Experiment ID**: `T2-ASM-02`
- **Architectural Directive**: ADR `D-015` (`ASM_FIRST_RECOVERY`)
- **Module**: `0TH2.BIN` (Primary Sega Saturn Retail Executable)
- **Base VMA**: `0x06004000`
- **Total Byte Size**: 535,552 bytes (`0x82C00`)
- **Canonical Module SHA-256**: `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64`
- **Canonical Disc SHA-256**: `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8`
- **Toolchain**: GNU Binutils SH Cross-Toolchain (`binutils-sh-elf 2.40+2`)
  - `sh-elf-as`: `fd3ddc347d0f83521b98e039e30acf93380930dd521d5031682767e822c074e5`
  - `sh-elf-ld`: `e369cd410424715b549f2e61fc12f1f93f525f656ff3f60f2fdc22f689c8472d`
  - `sh-elf-objcopy`: `1da83e2a6bbabe453a0fe12a37dd57a262135fc9cb769413655cdfc5e54aaea2`
  - `sh-elf-objdump`: `ee13a67c88f386a388cf10eb4710d13f05691ac008af103b84329276bc41eb35`
- **Dynamic Oracle**: Pinned Mednafen debug fork (`AJBats/mednafen-saturn-debug` commit `155426661b7ac3152e2c93a98da60ac33002b908`)

---

## Technical Results

### 1. Tooling Provenance Repair & Generic Assembly IR

`tools/asm/export_sh2_asm_ir.cpp` was implemented and linked directly against `thor_sh2` (`thor::sh2::decode_sh2`).
The tool decodes input binary slices into a generic Assembly IR JSON (`scratch/assembly_ir.json`):
- All 11 instructions across `bb_06004000` and `bb_06004280` decode with `is_valid() == true`.
- Zero unmodeled opcodes.
- Displacements and branch targets are computed mechanically via `Sh2Instruction::compute_effective_address()` and `compute_branch_target()`.

### 2. Lossless Module Assembly Generation

`tools/asm/generate_full_module_asm.py` produces:
- Private assembly container `.private/asm/0TH2/0TH2.s` (33,521 lines):
  - Proven code instructions emitted as real SH-2 mnemonics with comments.
  - RAW_UNKNOWN bytes emitted as `.byte` directives chunked up to 16 bytes per line.
  - Labels emitted at real byte offsets:
    - `loc_06004012:` at offset `+0x12`
    - `lit_06004064:` at offset `+0x64`
    - `lit_0600435C:` at offset `+0x35C`
    - `lit_06004360:` at offset `+0x360`
    - `lit_06004364:` at offset `+0x364`
  - Zero `.equ` workarounds used.
  - Zero `.incbin` directives used.
- Linker script `asm/linker/0TH2.ld`:
  - `ASSERT(ADDR(.text) == 0x06004000, "VMA of .text must be 0x06004000")`
  - `ASSERT(SIZEOF(.text) == 535552, "Size of .text must be exactly 535552 bytes")`
  - `ASSERT` checks on all 5 in-module label addresses.
- Public manifest `asm/manifests/0TH2.BIN.json` (zero commercial bytes).

### 3. Byte-Exact Extraction & Determinism

- Assembled with: `sh-elf-as -isa=sh2 -big .private/asm/0TH2/0TH2.s -o block.o`
- Linked with: `sh-elf-ld -EB -T asm/linker/0TH2.ld block.o -o block.elf`
- Extracted with: `sh-elf-objcopy -O binary -j .text block.elf block.bin`
- Relocation table: 0 unresolved relocations in ELF.
- Extracted byte length: `535552`. Differing bytes: `0`.
- Extracted SHA-256: `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64` (MATCH).
- Dual-build determinism: independent build directories `out/asm_module_build_1` and `out/asm_module_build_2` produced bit-identical binaries (0 differing bytes).

### 4. Sector-by-Sector Disc Splice Parity

Rebuilt binary was spliced into sectors 24..285 (Mode 1 / 2352 bytes per sector, user data offset +16).
The resulting disc image matched canonical retail disc SHA-256 `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8` exactly.

### 5. Mednafen Interpreter Runtime Parity (5 Checkpoints)

Automated cold-boot parity was evaluated in clean Mednafen (`native_mode 0`):

| Checkpoint | Target Address | Original Cycle | Rebuilt Cycle | Register Match |
| :--- | :--- | :--- | :--- | :--- |
| `entry_06004000` | `0x06004000` | 305462360 | 305462360 | 23 / 23 (100%) |
| `branch_target_06004012` | `0x06004012` | 305462387 | 305462387 | 23 / 23 (100%) |
| `checkpoint_06004280` | `0x06004280` | 307090585 | 307090585 | 23 / 23 (100%) |
| `checkpoint_0600A0F8` | `0x0600A0F8` | 316309144 | 316309144 | 23 / 23 (100%) |
| `checkpoint_002E9910` | `0x002E9910` | 387459915 | 387459915 | 23 / 23 (100%) |

Block duration `0x06004000` -> `0x06004012`: exactly 27 cycles in both runs.
Cycle divergence: **0 cycles**.
Register divergence: **0 registers**.

### 6. Negative Controls (28 / 28 PASS)

All 28 negative control mutations failed closed:
- NC01: Range 1 opcode mutation (`mov.w @r1, r7`) -> FAIL CLOSED
- NC02: Range 2 opcode mutation (`jsr @r4`) -> FAIL CLOSED
- NC03: Range 2 literal target mutation (`mov.l lit, r6`) -> FAIL CLOSED
- NC04: Range 1 branch target mutation (`bra loc_06004014`) -> FAIL CLOSED
- NC05: Missing delay slot Range 1 -> FAIL CLOSED
- NC06: Missing delay slot Range 2 -> FAIL CLOSED
- NC07: Assembler wrong endian (`-little`) -> FAIL CLOSED
- NC08: Linker wrong endian (`-EL`) -> FAIL CLOSED
- NC09: Linker wrong base VMA (`0x06005000`) -> FAIL CLOSED
- NC10: Linker wrong size assertion (`535550`) -> FAIL CLOSED
- NC11: Linker wrong label assertion `loc_06004012` -> FAIL CLOSED
- NC12: Linker wrong label assertion `lit_06004064` -> FAIL CLOSED
- NC13: Linker wrong label assertion `lit_0600435C` -> FAIL CLOSED
- NC14: Linker wrong label assertion `lit_06004360` -> FAIL CLOSED
- NC15: Linker wrong label assertion `lit_06004364` -> FAIL CLOSED
- NC16: Unresolved relocation (undefined label) -> FAIL CLOSED
- NC17: Unexpected alignment padding -> FAIL CLOSED
- NC18: Output length truncated (< 535552 bytes) -> FAIL CLOSED
- NC19: Output length expanded (> 535552 bytes) -> FAIL CLOSED
- NC20: Corrupted raw byte at offset 0x1000 -> FAIL CLOSED
- NC21: Corrupted expected SHA in manifest -> FAIL CLOSED
- NC22: Toolchain `sh-elf-as` hash corruption -> FAIL CLOSED
- NC23: Toolchain `sh-elf-ld` hash corruption -> FAIL CLOSED
- NC24: Toolchain `sh-elf-objcopy` hash corruption -> FAIL CLOSED
- NC25: Toolchain `sh-elf-objdump` hash corruption -> FAIL CLOSED
- NC26: Manifest wrong module name -> FAIL CLOSED
- NC27: Manifest wrong revision identity -> FAIL CLOSED
- NC28: Git leak detection guard -> FAIL CLOSED
