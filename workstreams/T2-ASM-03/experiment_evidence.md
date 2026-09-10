# T2-ASM-03 — Evidence Record

## Context

- **Task**: `T2-ASM-03` — TH2.LOW Lossless ASM Container & Shared ASM Recovery Infrastructure
- **ADR Authority**: ADR `D-015` (`ASM_FIRST_RECOVERY`)
- **Module**: `TH2.LOW`
- **Module Size**: 149,504 bytes (`0x24800` bytes)
- **Saturn VMA Base**: `0x002DA000`
- **Saturn VMA End**: `0x002FE7FF` (inclusive) / `0x002FE800` (exclusive)
- **CD-ROM LBA Extent**: Sector 52123 .. Sector 52195 (73 sectors * 2048 = 149,504 bytes)
- **Canonical Module SHA-256**: `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224`
- **Canonical Retail Disc SHA-256**: `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8`

---

## 1. Provenance and Partitioning

`TH2.LOW` is partitioned exhaustively into three non-overlapping ranges covering all 149,504 bytes:

| Range | Start Offset | End Offset (excl) | Runtime Range | Byte Count | Classification | Representation | Description |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 63,760 (`0xF910`) | `0x002DA000..0x002E9910` | 63,760 | `UNKNOWN` | `RAW_UNKNOWN` | Pre-entry data and routines |
| 1 | 63,760 (`0xF910`) | 63,762 (`0xF912`) | `0x002E9910..0x002E9912` | 2 | `CONFIRMED_CODE` | `RAW_CODE_PENDING_DECODE` | Opcode `0x2FE6` (`MOV.L R14, @-R15`) |
| 2 | 63,762 (`0xF912`) | 149,504 (`0x24800`) | `0x002E9912..0x002FE800` | 85,742 | `UNKNOWN` | `RAW_UNKNOWN` | Post-entry data and routines |

**Partition Sum**: $63,760 + 2 + 85,742 = 149,504$ bytes.
**Confirmed Code**: 2 bytes.
**Raw Unknown**: 149,502 bytes.
**Zero gaps, zero overlaps.**

---

## 2. Reassembly & Link Verification

- **Toolchain**:
  - `sh-elf-as` (GNU binutils-sh-elf 2.40+2) SHA-256: `fd3ddc347d0f83521b98e039e30acf93380930dd521d5031682767e822c074e5`
  - `sh-elf-ld` (GNU binutils-sh-elf 2.40+2) SHA-256: `e369cd410424715b549f2e61fc12f1f93f525f656ff3f60f2fdc22f689c8472d`
  - `sh-elf-objcopy` (GNU binutils-sh-elf 2.40+2) SHA-256: `1da83e2a6bbabe453a0fe12a37dd57a262135fc9cb769413655cdfc5e54aaea2`
  - `sh-elf-objdump` (GNU binutils-sh-elf 2.40+2) SHA-256: `ee13a67c88f386a388cf10eb4710d13f05691ac008af103b84329276bc41eb35`
- **Assembled ELF**:
  - Relocations remaining: **0** (`NONE (Clean)`)
  - Linker Assertions Passed:
    - `ADDR(.text) == 0x002DA000`
    - `SIZEOF(.text) == 149504`
    - `entry_002E9910 == 0x002E9910`
- **Extracted Binary**:
  - Length: 149,504 bytes
  - SHA-256: `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224`
  - Byte-Exact Match: **149,504 / 149,504 bytes (100%)**
  - Determinism: 0 differing bytes between independent builds

---

## 3. Disc Splicing Verification

- **Target Sectors**: LBA 52123 .. 52195 (73 sectors)
- **Sector Format**: Mode 1 / 2352 (2048 payload bytes per sector, header 16 bytes)
- **Resulting Disc SHA-256**: `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8`
- Bit-identical to original canonical disc image.

---

## 4. Occurrence-Aware Runtime Evidence (Clean Mednafen Oracle)

The dynamic execution path was traced in clean Mednafen (interpreter-only mode, `native_mode 0`):

1. `0x06004000` (occ 0): Cycle `305462360`, entry point from BIOS.
2. `0x06004012` (occ 0): Cycle `305462387`, branch target of `bb_06004000` (duration 27 cycles).
3. `0x06004280` (occ 0): Cycle `307090585`, candidate entry pass.
4. `0x06004280` (occ 1): Cycle `316309168`, candidate entry pass before TH2.LOW load.
5. `0x0600A0F8` (occ 2): Cycle `316309189`, called from `0x06004286` with `PR=0x0600428A`, `R4="TH2.LOW"` (`0x06081C20`), `R5=0x002DA000`, `R3=0x0600A0F8`. This is the verified load routine for `TH2.LOW`.
6. `0x002E9910` (occ 0): Cycle `387459915`, executed within `TH2.LOW` with `PR=0x060042E4`, called from `0x060042E0`.
   - Opcode: `0x2FE6` (`MOV.L R14, @-R15`)
   - Registers at hit:
     - `PC=0x002E9912`
     - `PR=0x060042E4`
     - `R0=0x06096521`
     - `R1=0x06082DB4`
     - `R2=0x002E9910`
     - `R3=0x060F7D18`
     - `R15=0x06002EDC`
     - `VBR=0x06000000`

### Differential Verification (ORIGINAL vs ASM_REBUILT)

- Checkpoints evaluated: 6
- Divergent cycles: **0**
- Divergent registers: **0 / 23 across all checkpoints**
- Status: **ZERO DIVERGENCE (PASS)**
