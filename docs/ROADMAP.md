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

### D1 — Deterministic Dynamic Oracle (V-01-core / V-01-automation)

Status: **BOUNDED_PROOF** (decisions D-009, D-010)

Capability: reproducible dynamic observation of Thor 2 execution under a pinned configuration and scripted IPC harness.
Verified gates:
- **V-01-core**: bounded emulator observation under pinned Mednafen debug fork; Run A/B identical match (ADR D-009 `ADOPT`).
- **V-01-automation**: low-level scripted IPC control via `MednafenBot`; Run A/B identical match, negative control verified (ADR D-010 `ADOPT_PARTIAL` for `LOW_LEVEL_CONTROL_LAYER_PROVEN`).

Target claims proven: Master SH-2 candidate boot entry at `0x06004000` (hook pc `0x06004002` via pc-2 fallback), step transitions/retirements (`0x06004000` `MOV.W @R1, R6`; `0x06004002` `MOV R0, R15`; `0x06004004` `MOV.L @(0x5C, PC), R4`), deterministic cycle counter, dynamic memory read watchpoint (`0x06081C10` = `0x060917DC` via `MOV.L @R4, R4` at `0x06004006`), and automated programmatic reproducibility via `MednafenBot`.

### D2 — Executable Module Provenance (0TH2.BIN and TH2.LOW paths)

Status: **BOUNDED_PROOF for 0TH2.BIN and TH2.LOW** (decision D-011)

Capability: exact runtime mapping, disc provenance, and execution confirmation for executable modules.
Verified gates:
- **V-02a — 0TH2.BIN Executable Provenance** (ADR D-011; Daytona provenance methodology adopted as `ADOPT_PARTIAL`).
- **V-02b — TH2.LOW Executable Provenance** (`PASS / V02B_DIRECT_PROVENANCE_PROVEN`).

Target claims proven:
- `0TH2.BIN` (LBA 24..285, 535,552 bytes, SHA-256 `c1cc4117...`): read via CD Block FAD `0x0000AE..0x0001B3`, transferred directly into High Work RAM at `0x06004000..0x06086BFF` via BIOS Master SH-2 CPU copy loop (`PC=0x00002368`), confirmed byte-exact (`FULL_EXACT_MATCH`), and executed by Master SH-2.
- `TH2.LOW` (LBA 52123..52195, 149,504 bytes, SHA-256 `78139689...`): read via CD Block FAD `0x00CC31..0x00CC79`, transferred directly into Low Work RAM at `0x002DA000..0x002FE7FF` via Master SH-2 CPU copy loop (`PC=0x0607DF08`, zero SCU DMA), confirmed byte-exact (`FULL_EXACT_MATCH`), and executed by Master SH-2 at `0x002E9910..0x002E9914` (offset `0xF910`, cycle `387459915`).

### D3 — Exact SH-2 Decode / L0 Semantics (Target Startup Subset)

Status: **BOUNDED_PROOF for target startup subset**

Capability: correct fail-closed decoding and instruction/memory L0 semantics for SH-2 opcodes in Thor 2.
Verified gate: **V-06 — Independent SH-2 Decoder Cross-Check** + L0 semantic test suite.
Target claims proven:
- 4 target opcodes (`0x6611`, `0x6F03`, `0xD417`, `0x6442`) decoded into structured representation;
- V-06 cross-check against Hitachi hardware manual, pinned Mednafen `sh7095_ops.inc`, and `hazzaclark/catherine` confirmed 0 decode disagreements;
- Synthetic L0 semantic suite validated 16-bit sign-extension, big-endian bus access, aligned PC-relative EA computation `((PC & ~3) + 4) + (disp * 4)`, same-register writeback order (`Rm == Rn`), and architectural register isolation;
- Real Thor 2 startup oracle vector matched pinned Mednafen debug oracle with 0 divergences across all 4 steps.

## Next

### Development: D3 — Exact SH-2 Decode / L0 Semantics (corpus expansion) / D4 — Code/Data/Unknown Ownership

Status: `PROPOSED`

- Review T2-D3.1 evidence before expanding D3 opcode corpus or authorizing D4 batch classification.
- Next capability slice: expand SH-2 decoder/executor coverage or perform code/data ownership boundary analysis on executed blocks (D4 / V-03).

## Queued development milestones

| ID | Capability | Key verification gate | Scope state |
|---|---|---|---|
| D2 | Executable module provenance | V-02a (0TH2.BIN), V-02b (TH2.LOW) | BOUNDED_PROOF (0TH2.BIN + TH2.LOW) |
| D3 | Exact SH-2 decode + L0 semantics | V-06 cross-check + L0 semantic test suite | BOUNDED_PROOF (startup subset) |
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
