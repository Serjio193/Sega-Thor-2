# Reverse engineering record

## Confirmed substrate: `thor2_ntsc_patched_fe11d2fb`

T2-M0 reproducibility gate: **PASS**.

Two independent executions of `tools/disc/census_saturn_cd.py` produced identical `disc_manifest.tsv` and summary outputs from the same private input image.

### Disc identity

| Item | Value | Status |
|---|---|---|
| Image SHA-256 | `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8` | CONFIRMED |
| CUE SHA-256 | `afc0b101bbb493adbd43fd44ffd76959484d67cf0b566137dd145f1c68d411e0` | CONFIRMED |
| Format | `MODE1/2352` | CONFIRMED |
| Raw sectors | 52,224 | CONFIRMED |
| Volume ID | `THE STORY OF THOR 2` | CONFIRMED |
| Files | 33 | CONFIRMED |
| Product code | `MK-81302` | CONFIRMED |
| Version | `V1.000` | CONFIRMED |
| Header date | `19960618` | CONFIRMED |
| Header title | `THE STORY OF      THOR 2 (patched for NTSC)` | CONFIRMED |
| First-read address | `0x06004000` | CONFIRMED header field |

Full per-file identity is in `workstreams/T2-M0-disc-census/disc_manifest.tsv`.

## Executable candidate `0TH2.BIN`

Status: `CONFIRMED_CODE / EXECUTED` at entry `0x06004000`; remainder `PROBABLE_CODE / HIGH`.

- SHA-256: `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64`
- size: `0x82C00`
- candidate load base: `0x06004000`
- candidate end: `0x06086BFF`

Evidence:

- Saturn header first-read address is `0x06004000`;
- it is the first ISO9660 file record;
- file begins with dense SH-2-like instructions;
- **Dynamic proof (V-01-core)**: Master SH-2 entered `0x06004000` from BIOS (`ret=0x06002244`) at frame 680, cycle `305462360`; initial instructions establish SP=`0x06001000`, load BSS start address `0x060917DC` (from pointer at `0x06081C10`) and BSS end address `0x060B29CC` (from pointer at `0x06081C14`), and begin zeroing High WRAM BSS.

Next proof: full module provenance and mapping bounds (D2 / V-02a).

## Executable candidate `TH2.LOW`

Status: `PROBABLE_CODE / HIGH`.

- SHA-256: `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224`
- size: `0x24800`
- candidate load base: `0x002DA000`
- candidate end: `0x002FE7FF`

Static evidence is recorded in `workstreams/T2-M0-disc-census/static_load_evidence.md`.

Important distinction: the call-site evidence proves a strong relationship among the filename pointer, `0x002DA000`, and an indirect call. It does **not yet** prove the exact semantics/name of callee `0x0600A0F8`. Dynamic provenance is required.

## Public-research address anchors queued for revision validation

Prior public Thor 2 research has reported:

- `0x06009CC4` — debug-related routine;
- `0x002E55A4` — Low Work RAM code;
- `0x002E8A38` — Low Work RAM code.

For the confirmed current substrate:

- `0x002E55A4` is consistent with `TH2.LOW + 0xB5A4`;
- `0x002E8A38` is consistent with `TH2.LOW + 0xEA38`;
- both current-revision offsets contain SH-2-like instruction streams.

These public labels/semantics remain revision hints until independently behavior-verified.

## Record template

For each new finding record:

```text
ID:
STATUS:
REVISION/HASH:
DISC FILE:
FILE RANGE:
RUNTIME RANGE:
CPU:
MODULE/GENERATION:
STATIC EVIDENCE:
DYNAMIC EVIDENCE:
READS/WRITES:
CONTROL FLOW:
HARDWARE INTERACTION:
HYPOTHESIS:
CONFIDENCE:
VERIFICATION:
NEGATIVE EVIDENCE:
NEXT ACTION:
```
