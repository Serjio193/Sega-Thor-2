# T2-M0 — Canonical Disc + Executable/Module Census

Status: **DONE**

## Hypothesis

We can deterministically derive a legal-safe identity/manifest layer from the private disc image and use it as bedrock for later reverse engineering.

## Result

**PASS.**

Two independent census executions produced identical manifest and summary outputs.

Confirmed revision: `thor2_ntsc_patched_fe11d2fb`.

## Method

Rather than persist extracted retail files, the final M0 method hashes logical ISO9660 extents directly from the private raw `MODE1/2352` image. This provides the same stable per-file identity while reducing duplicated commercial data.

Tool: `tools/disc/census_saturn_cd.py`.

Tests: `tests/test_census_saturn_cd.py`.

## Public/legal-safe outputs

- `config/revisions/thor2_ntsc_patched_fe11d2fb.yaml`
- `disc_manifest.tsv`
- `executable_candidates.tsv`
- `static_load_evidence.md`
- updates to `docs/PROJECT_STATE.md` and `docs/REVERSE_ENGINEERING.md`

## Key findings

### Disc

- image SHA-256: `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8`
- CUE SHA-256: `afc0b101bbb493adbd43fd44ffd76959484d67cf0b566137dd145f1c68d411e0`
- 52,224 raw sectors
- 33 ISO9660 files
- manifest SHA-256: `19b56fd0fefa42c23edac055cd5e817a7a4834b7d7b423cef15a27de4bc80f49`

### Main executable candidate

`0TH2.BIN`:

- size `0x82C00`
- SHA-256 `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64`
- candidate base `0x06004000`
- status `PROBABLE_CODE / HIGH`

### Low Work RAM candidate

`TH2.LOW`:

- size `0x24800`
- SHA-256 `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224`
- candidate base `0x002DA000`
- candidate end `0x002FE7FF`
- status `PROBABLE_CODE / HIGH`

Static call-site evidence is documented separately. Runtime load/execution remains deliberately unconfirmed.

## Acceptance criteria

- [x] reproducible disc identity
- [x] reproducible boot metadata
- [x] complete legal-safe file manifest
- [x] SHA-256 for every ISO9660 file
- [x] second independent census produced identical output
- [x] executable candidates are confidence-scored rather than inferred from extension
- [x] load addresses recorded only where evidence exists
- [x] legal-safe revision config produced
- [x] no retail file content committed
- [x] exact next experiment stated

## Next experiment

`T2-M1 — SaturnAutoRE dynamic-oracle validation`.

The first dynamic target should verify one deterministic runtime claim, preferably the `TH2.LOW` write/load provenance or another bounded known Thor 2 anchor.
