# Roadmap

## M0 — Canonical substrate

Status: **ACTIVE**

Deliverables:

- reproducible disc identity;
- file manifest and hashes;
- boot metadata;
- executable-candidate census;
- first load/provenance hypotheses;
- legal-safe metadata committed to GitHub.

Exit gate: repeated extraction produces identical manifest/hashes and all claims are revision-scoped.

## M1 — Dynamic oracle experiment

Status: `PROPOSED`

Evaluate SaturnAutoRE/Mednafen on one deterministic Thor 2 observation.

## M2 — Module/provenance experiment

Status: `PROPOSED`

Evaluate Daytona-style module identity and generation tracking on one executable path.

## M3 — Boundary discovery experiment

Status: `PROPOSED`

Evaluate AI/static/oracle boundary discovery on one bounded module range.

## M4 — Persistent segmentation experiment

Status: `PROPOSED`

Evaluate SOTN/Splat-style byte ownership for one module.

## M5 — Decoder cross-check experiment

Status: `PROPOSED`

Cross-check executed SH-2 opcode corpus with multiple independent decoders.

## M6 — First SH-2 mechanical translation proof

Status: `PROPOSED`

Mechanically translate one safe executed block, shadow it, then perform real native override with zero divergence.

## Later milestones

Only schedule after prior gates:

- expand automated native promotion;
- recover overlays/transforms;
- recover resource formats;
- structural/semantic recovery;
- proof-gated Saturn subsystem replacement;
- progressive standalone runtime.

See `docs/PIPELINE_VALIDATION_PLAN.md` for the authoritative method queue.
