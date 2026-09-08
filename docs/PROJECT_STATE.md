# Project state

## Status

Active milestone: **T2-M0 — Canonical Disc + Executable/Module Census**

Pipeline maturity: **research bootstrap**.

No external method is adopted by default. Every technique remains `PROPOSED` until it passes its bounded Thor 2 validation experiment.

## Current private input revision

Current laboratory image is a patched NTSC build supplied by the project owner. Preliminary disc reconnaissance observed:

- Saturn product code: `MK-81302`
- version string: `V1.000`
- date field: `19960618`
- title/header text indicates `THE STORY OF THOR 2 (patched for NTSC)`
- disc format: MODE1/2352
- ISO9660 file count observed: 33
- `0TH2.BIN` exists and is a main executable candidate
- `0TH2.BIN` observed size: `0x82C00` bytes
- boot first-read/load address observed: `0x06004000`

These are **preliminary observations** until T2-M0 produces reproducible manifests/hashes and records their extraction procedure.

## Storage split

GitHub:

- source code
- tools
- tests
- legal-safe configs
- hashes/manifests
- evidence summaries
- documentation

Private Google Drive laboratory (`Thor2/RE_Work`):

- original disc image
- extracted retail binaries
- save states
- RAM dumps
- large/raw traces
- Ghidra databases containing retail bytes
- temporary patch diffs and other private binary artifacts

## Current next action

Complete T2-M0:

1. canonical disc identity;
2. reproducible ISO9660 manifest;
3. per-file hashes;
4. executable-candidate census;
5. initial disc-file -> expected load/runtime provenance table;
6. store raw/private outputs outside GitHub and commit only legal-safe metadata.
