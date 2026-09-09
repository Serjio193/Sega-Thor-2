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

### T2-P0.1 — Dual-Track Proof-Contract Repair

Status: **DONE**

Adversarial repair of proof contracts:
- introduced capability scope states (`PROPOSED`, `READY_FOR_BOUNDED_TEST`, `BOUNDED_PROOF`, `EXPANDED_PROOF`, `DONE`);
- split V-01 into `V-01-core` and `V-01-automation`;
- removed `TH2.LOW` from V-01 (queued under D2 / `V-02b`);
- established explicit L0 semantic gate and pre-D8 identity/event safety guards;
- split V-07 into `V-07A`, `V-07B`, and `V-07C`;
- relaxed D14 static round-trip prerequisite.

## Active

### D1 — Deterministic Dynamic Oracle

Capability state: `READY_FOR_BOUNDED_TEST`

Immediate verification gate: **V-01-core — Bounded Emulator Observation**.

Current execution status: **BLOCKED BEFORE BOOT**.

Preflight completed:

- canonical BIN/CUE SHA-256 reverified;
- SaturnAutoRE source pinned at `4662aad69f95222fe37c5e6b98f2285b1a7e4653`;
- debug Mednafen source pinned at `155426661b7ac3152e2c93a98da60ac33002b908`;
- no user-owned Saturn BIOS was found in the available private workspace.

The blocker is not evidence against Mednafen. V-01-core has not executed and no adoption decision is permitted.

Re-entry condition: provide a legally owned Saturn BIOS privately, hash it, pin effective region/BIOS/build configuration, then run two independently initialized cold boots under the V-01-core observation contract.

`TH2.LOW` provenance remains queued for D2 / V-02b after V-01-core succeeds.

## Queued development milestones

| ID | Capability | Key verification gate | Scope state |
|---|---|---|---|
| D2 | Executable module provenance | V-02a (0TH2.BIN), V-02b (TH2.LOW) | PROPOSED |
| D3 | Exact SH-2 decode + L0 semantics | V-06 cross-check + L0 semantic test suite | PROPOSED |
| D4 | Code/data/unknown ownership | V-03 (bounded batch), V-04 (schema) | PROPOSED |
| D5 | Basic-block CFG | V-03 (bounded block CFG) | PROPOSED |
| D6 | Mechanical explicit-state C++ | V-07A + pre-D8 identity/event guards | PROPOSED |
| D7 | Shadow comparison | V-07B (negative-control validation) | PROPOSED |
| D8 | **First native promotion proof** | **V-07C (native override proof)** | PROPOSED |
| D9 | Indirect control-flow handling | — | PROPOSED |
| D10 | Timing/IRQ/DMA boundaries | — (general scaling) | PROPOSED |
| D11 | Overlay/generation identity | V-10 (transformation/overlay discovery) | PROPOSED |
| D12 | Structural recovery | V-05, V-13 | PROPOSED |
| D13 | Guest-address/type provenance | V-09 | PROPOSED |
| D14 | Resource decode/reencode | V-11 (exact round-trip), V-12 (diff locator) | PROPOSED |
| D15 | HW-subsystem contracts | V-08 (SaturnRecomp component tests a–h) | PROPOSED |
| D16 | Native subsystem replacement | V-08 (components passing differential test) | PROPOSED |
| D17 | Progressive standalone runtime | V-14 (isolated, integrated, measured) | PROPOSED |
| D18 | Guest dependency removal | — (L5 equivalence) | PROPOSED |

## References

- `docs/DEVELOPMENT_PLAN.md` — full development track with milestones, dependencies, risk map.
- `docs/PIPELINE_VALIDATION_PLAN.md` — verification/adoption experiments.
- `docs/PROJECT_STATE.md` — current verified state.
- `workstreams/T2-V01-dynamic-oracle/` — V-01-core preflight, environment pin, and blocker evidence.
