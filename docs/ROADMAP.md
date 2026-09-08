# Roadmap

## M0 — Canonical substrate

Status: **COMPLETE**

Evidence:

- revision `thor2_ntsc_patched_fe11d2fb` confirmed by hashes;
- 33-file ISO9660 manifest reproduced identically twice;
- executable candidates and static load evidence recorded;
- census tool and synthetic tests committed.

## M1 — Dynamic oracle experiment

Status: `PROPOSED — NEXT`

Evaluate `AJBats/SaturnAutoRE`/instrumented Mednafen on exactly one deterministic Thor 2 runtime claim.

First preferred claim: observe `TH2.LOW` provenance into the `0x002DA000..0x002FE7FF` candidate range and later instruction fetch from that range.

No SaturnAutoRE component is adopted until this bounded experiment passes.

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
