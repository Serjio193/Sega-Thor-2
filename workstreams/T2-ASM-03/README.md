# T2-ASM-03 — TH2.LOW Lossless ASM Container & Shared ASM Recovery Infrastructure

## Overview

- **Task**: `T2-ASM-03`
- **Architectural Authority**: ADR `D-015` (`ASM_FIRST_RECOVERY`)
- **Status**: **PASS**
- **Target Module**: `TH2.LOW` (Secondary Saturn Binary / Low-Memory Subsystem, Master SH-2)
- **Module Extent**: 149,504 bytes (`0x24800` bytes, VMA `0x002DA000..0x002FE7FF`)
- **Confirmed Code Extent**: 2 bytes (`0x002E9910..0x002E9912`, 1 instruction `0x2FE6` MOV.L R14, @-R15)
- **Assembly Representation**: `RAW_CODE_PENDING_DECODE` (losslessly emitted as `.byte 0x2F, 0xE6` without speculative mnemonic emission)
- **Lossless RAW_UNKNOWN Extent**: 149,502 bytes (`.byte` directives across 2 contiguous partitions)
- **Partition Integrity**: 3 ranges covering exactly `0..149504` (zero gaps, zero overlaps)
- **Target Revision**: `thor2_ntsc_patched_fe11d2fb`
- **Canonical Module SHA-256**: `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224`
- **Canonical Disc SHA-256**: `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8`
- **Dynamic Oracle**: Pinned Mednafen debug build (`AJBats/mednafen-saturn-debug` commit `155426661b7ac3152e2c93a98da60ac33002b908`)

---

## Technical Accomplishments

1. **Shared ASM Recovery Infrastructure Hardened**:
   - Formalized canonical manifest schema (`asm/schema/module_manifest.schema.json`) with mandatory non-overlapping range partitioning (`CONFIRMED_CODE`, `PROBABLE_CODE`, `DATA`, `UNKNOWN`) and assembly representations (`MNEMONIC_PROVEN`, `RAW_CODE_PENDING_DECODE`, `RAW_DATA`, `RAW_UNKNOWN`).
   - Upgraded both `0TH2.BIN.json` and `TH2.LOW.json` to the formal partition model.
   - Eliminated ad-hoc Python SH-2 decoders in verification scripts in favor of authoritative C++ tool `tools/asm/verify_sh2_rebuilt.cpp` linked against `thor_sh2` (`thor::sh2::decode_sh2`).
   - Added environment variable support (`THOR_SATURNAUTORE_DIR`, `THOR_MEDNAFEN_DIR`, `THOR_DISC_IMAGE`, `THOR_BIOS_IMAGE`) with pre-run integrity validation of all assets and git commits.
2. **Private Lossless Assembly Container for TH2.LOW**:
   - Implemented manifest-driven assembly generation in `tools/asm/generate_full_module_asm.py`.
   - Emits private assembly container `.private/asm/TH2_LOW/TH2_LOW.s` (9,365 lines).
   - Generates linker script `asm/linker/TH2_LOW.ld` linking at Saturn VMA `0x002DA000` with hard assertions for `ADDR(.text) == 0x002DA000`, `SIZEOF(.text) == 149504`, and `entry_002E9910 == 0x002E9910`.
   - Strictly zero commercial binary payload tracked in Git.
3. **Byte-Exact Parity & Determinism**:
   - Reassembled with pinned GNU `binutils-sh-elf 2.40+2`.
   - Extracted 149,504 raw bytes: bit-identical to original `TH2.LOW` (SHA-256 `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224`).
   - Dual-build determinism verified (0 differing bytes between independent runs).
   - Zero unresolved relocations in linked ELF.
4. **Private Disc Splicing**:
   - Spliced reassembled 149,504 bytes across 73 sectors starting at CD-ROM LBA 52123.
   - Spliced disc image SHA-256 matches canonical retail disc `fe11d2fb...` bit-for-bit.
5. **Occurrence-Aware Runtime Verification**:
   - Replaced fragile sequential breakpoint loops with explicit occurrence-aware specifications.
   - Discovered and proved that `0x06004280` has 2 occurrences (occ 0 at cycle 307090585, occ 1 at cycle 316309168).
   - Proved that `0x0600A0F8` occurrence 2 (cycle 316309189, `PR=0x0600428A`) is the true loader call for `TH2.LOW` issued from `0x06004286`.
   - Proved that `0x002E9910` in `TH2.LOW` is executed at cycle 387459915 (`PR=0x060042E4`), advancing through subsequent instruction steps.
   - Verified zero cycle divergence and 23/23 matching registers between original cold boot and substituted `TH2.LOW` cold boot.
6. **Comprehensive Negative Controls & Automated Tests**:
   - 10/10 module negative controls pass fail-closed for `TH2.LOW`.
   - 20/20 negative controls pass fail-closed for `0TH2.BIN`.
   - 9/9 schema/partition negative controls pass fail-closed (`tests/asm/test_manifest_schema.py`).
   - 23/23 CTest test suites pass across Windows MinGW and Linux WSL.

---

## State & Gate Accounting

- `TH2.LOW`:
  - `MODULE_CONTAINER_ESTABLISHED`: **PASS**
  - `ASM_BYTE_EXACT`: **PASS** (149,504 / 149,504 bytes)
  - `ASM_RUNTIME_VERIFIED`: **PASS** (occurrence 0 executed at cycle 387459915, 0 divergence)
- `0TH2.BIN`:
  - `ASM_BYTE_EXACT`: **PASS**
  - `ASM_RUNTIME_VERIFIED`: **PASS** (occurrence-aware)
- Broad C++ Translation: **FROZEN** (ADR D-015).
