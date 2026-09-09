# Roadmap

## Completed

### D0 / T2-M0 — Canonical Revision Identity

Status: **DONE**

Evidence:

- revision `thor2_ntsc_patched_fe11d2fb` confirmed by hashes;
- 33-file ISO9660 manifest reproduced identically twice;
- executable candidates and static load evidence recorded;
- census tool and synthetic tests committed.

### T2-P0 — Dual-Track Planning Checkpoint

Status: **DONE**

Separated the project planning model into two explicit synchronized tracks:

- **Development Track** (`docs/DEVELOPMENT_PLAN.md`): capability-oriented milestones D0–D18.
- **Verification Track** (`docs/PIPELINE_VALIDATION_PLAN.md`): method/component experiments V-01–V-14.

A failed external method does not invalidate the development capability it was meant to enable.

## Next

### D1 — Deterministic Dynamic Oracle

Status: `PROPOSED`

Capability: reproducible dynamic observation of Thor 2 execution.

Verification gate: **V-01** (SaturnAutoRE / instrumented Mednafen).

If V-01 fails, the capability persists — test another emulator/tool.

First target claim: observe execution in the `0TH2.BIN` candidate range and attempt `TH2.LOW` provenance confirmation.

## Queued development milestones

| ID | Capability | Key verification gate |
|---|---|---|
| D2 | Executable module provenance | V-02 |
| D3 | Exact SH-2 decode | V-06 |
| D4 | Code/data/unknown ownership | V-03, V-04 |
| D5 | Basic-block CFG | V-03 |
| D6 | Mechanical explicit-state C++ | V-07 |
| D7 | Shadow comparison | V-07 |
| D8 | **First native promotion proof** | **V-07** |
| D9 | Indirect control-flow handling | — |
| D10 | Timing/IRQ/DMA boundaries | — |
| D11 | Overlay/generation identity | V-10 |
| D12 | Structural recovery | V-05, V-13 |
| D13 | Guest-address/type provenance | V-09 |
| D14 | Resource decode/reencode | V-11, V-12 |
| D15 | HW-subsystem contracts | V-08 |
| D16 | Native subsystem replacement | V-08 |
| D17 | Progressive standalone runtime | V-14 |
| D18 | Guest dependency removal | — |

## References

- `docs/DEVELOPMENT_PLAN.md` — full development track with milestones, dependencies, risk map.
- `docs/PIPELINE_VALIDATION_PLAN.md` — verification/adoption experiments.
- `docs/PROJECT_STATE.md` — current verified state.
