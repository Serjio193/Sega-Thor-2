# Project state

## Status

- **D0 / T2-M0 — Canonical Revision Identity**: **COMPLETE**.
- **T2-P0 — Dual-Track Planning Hardening**: **COMPLETE** (decision D-008; established `DEVELOPMENT_PLAN.md` and `PIPELINE_VALIDATION_PLAN.md`).
- **T2-P0.1 — Dual-Track Proof-Contract Repair**: **COMPLETE** (formalized capability scope states, split V-01 into V-01-core and V-01-automation, removed TH2.LOW from V-01 gate, established pre-D8 guards).
- **D1 / T2-V01 / T2-V01.2 — Deterministic Dynamic Oracle**: **BOUNDED_PROOF** (decisions D-009, D-010; V-01-core verified; V-01-automation adopted as `ADOPT_PARTIAL` for `LOW_LEVEL_CONTROL_LAYER_PROVEN`).
- **D2 / T2-V02a — Executable Module Provenance**: **BOUNDED_PROOF for 0TH2.BIN only** (decision D-011; direct runtime byte mapping proven across all 535,552 bytes to `0x06004000..0x06086BFF`; transfer mechanism `DIRECT_CPU_COPY_OBSERVED`; entry execution confirmed).

Active next verification step: **Review V-02a evidence before authorizing V-02b TH2.LOW provenance**.
Active next development capability: **D2 — Executable Module Provenance (TH2.LOW path)**.

Note: `TH2.LOW` provenance is queued under D2 / V-02b.

No decompiler/recompiler architecture is considered final. External methods enter the pipeline only after bounded Thor 2 validation.

## Confirmed substrate revision

Revision ID: `thor2_ntsc_patched_fe11d2fb`

- image SHA-256: `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8`
- image size: `122830848`
- CUE SHA-256: `afc0b101bbb493adbd43fd44ffd76959484d67cf0b566137dd145f1c68d411e0`
- format: `MODE1/2352`, 52,224 raw sectors
- ISO9660 volume: `THE STORY OF THOR 2`
- ISO9660 files: 33
- manifest SHA-256: `19b56fd0fefa42c23edac055cd5e817a7a4834b7d7b423cef15a27de4bc80f49`

Two independent census runs produced identical manifest and summary output.

## Confirmed Saturn header metadata

- hardware ID: `SEGA SEGASATURN`
- maker: `SEGA ENTERPRISES`
- product: `MK-81302`
- version: `V1.000`
- date: `19960618`
- disc: `CD-1/1`
- regions field: `JTU`
- title field: `THE STORY OF      THOR 2 (patched for NTSC)`
- IP size: `0x1000`
- master stack: `0x06001000`
- slave stack: `0x06002000`
- first-read address: `0x06004000`

## Executable candidates

### `0TH2.BIN`

- SHA-256: `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64`
- size: `0x82C00`
- module status: `EXECUTABLE_MODULE / RUNTIME_MAPPING_EXACT / FULL_EXACT_MATCH` (`DIRECT_PROVENANCE_PROVEN`)
- byte classification: `CONFIRMED_CODE / EXECUTED` for dynamically observed instructions at `0x06004000..0x06004008`; unexecuted remainder `0x06004008..0x06086BFF` remains `PROBABLE_CODE / HIGH` (ownership queued for D4)
- dynamic evidence: V-02a proven direct byte-exact mapping (`FULL_EXACT_MATCH`), BIOS Master SH-2 CPU transfer loop (`PC=0x00002368`) from CD Block buffer (FAD `0x0000AE..0x0001B3`), and entry execution.
- next gate: complete D2 via TH2.LOW provenance (V-02b).

### `TH2.LOW`

- SHA-256: `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224`
- size: `0x24800`
- classification: `PROBABLE_CODE / HIGH`
- candidate mapped range: `0x002DA000..0x002FE7FF`
- static evidence: `0TH2.BIN` prepares a call with a pointer to `TH2.LOW` and `R5 = 0x002DA000`.
- next gate: D2 / V-02b dynamic provenance after V-01-core.

All other disc files remain `UNKNOWN` unless there is evidence to classify them. File extension alone is not code/data proof.

## Storage split

GitHub contains legal-safe source, tooling, hashes/manifests, evidence summaries, tests, configs, and documentation. Original image, BIOS, save states, raw traces, and other private binary artifacts remain outside GitHub in the project owner's private workspace.
