# T2-M0 — Canonical Disc + Executable/Module Census

Status: **ACTIVE**

## Why

Every later address, disassembly, trace, module hypothesis, and recompilation test must be tied to a reproducible binary revision. The currently supplied image is visibly patched for NTSC, so external PAL/US/JP addresses cannot be imported blindly.

## Hypothesis

We can deterministically derive a legal-safe identity/manifest layer from the private disc image and use it as bedrock for later reverse engineering.

## Inputs

Private, outside GitHub:

- Thor 2 CUE/BIN image supplied by the project owner;
- current logical laboratory location: `Thor2/RE_Work` on connected Google Drive.

## Tasks

1. Record CUE/track geometry.
2. Parse Saturn boot header.
3. Enumerate ISO9660 files with LBA/size.
4. Extract files privately.
5. Compute SHA-256 for disc image components and extracted files.
6. Classify executable candidates without assuming every `.BIN` is code.
7. Record candidate expected load addresses when evidence exists.
8. Search extracted files for direct correspondence to known runtime code only as a revision-mapping experiment.
9. Produce legal-safe manifest/config in `config/revisions/`.
10. Store commercial extracted bytes only in private workspace.

## Acceptance criteria

- A second clean extraction produces the same file list and hashes.
- Boot metadata is reproducible.
- Every committed executable candidate references a file hash, not just a filename.
- Claims distinguish observed facts from hypotheses.
- No commercial bytes are committed.
- The exact next experiment is identified after the census.

## Expected outputs

Public/legal-safe:

```text
config/revisions/<revision>.yaml
workstreams/T2-M0-disc-census/disc_manifest.tsv
workstreams/T2-M0-disc-census/executable_candidates.tsv
docs/REVERSE_ENGINEERING.md updates
```

Private:

```text
extracted disc files
IP/boot raw bytes
raw hash inventories if they contain private paths
binary comparison artifacts
```

## Current preliminary facts

See `docs/PROJECT_STATE.md`. They remain preliminary until this workstream passes.
