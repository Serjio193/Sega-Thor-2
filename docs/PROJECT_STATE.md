# Project state

## Status

`T2-M0 — Canonical Disc + Executable/Module Census`: **COMPLETE**.

Next queued experiment: **T2-M1 — SaturnAutoRE dynamic-oracle validation** (`PROPOSED`, not yet adopted).

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
- classification: `PROBABLE_CODE / HIGH`
- candidate mapped range: `0x06004000..0x06086BFF`
- next gate: dynamic execution provenance.

### `TH2.LOW`

- SHA-256: `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224`
- size: `0x24800`
- classification: `PROBABLE_CODE / HIGH`
- candidate mapped range: `0x002DA000..0x002FE7FF`
- static evidence: `0TH2.BIN` prepares a call with a pointer to `TH2.LOW` and `R5 = 0x002DA000`.
- next gate: dynamic write/load provenance plus instruction fetch.

All other disc files remain `UNKNOWN` unless there is evidence to classify them. File extension alone is not code/data proof.

## Storage split

GitHub contains legal-safe source, tooling, hashes/manifests, evidence summaries, tests, configs, and documentation. Original image and raw/private binary artifacts remain outside GitHub in the project owner's private Drive workspace.
