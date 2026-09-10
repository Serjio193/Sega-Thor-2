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

### D3 — Exact SH-2 Decode / L0 Semantics (Startup Basic Block)

Status: **BOUNDED_PROOF expanded to first complete startup block**

Capability: correct fail-closed decoding and instruction/memory L0 semantics for SH-2 opcodes in Thor 2.
Verified gate: **V-06 — Independent SH-2 Decoder Cross-Check** + L0 semantic test suite.
Target claims proven:
- 6 block opcodes (`0x6611`, `0x6F03`, `0xD417`, `0x6442`, `0xA003`, `0x0009`) decoded into structured representation;
- V-06 cross-check against Hitachi hardware manual, pinned Mednafen `sh7095_ops.inc`, and `hazzaclark/catherine` confirmed 0 decode disagreements (machine-readable manifest `reference_decode_manifest.json`);
- Synthetic L0 semantic suite validated 16-bit sign-extension, big-endian bus access, aligned PC-relative EA computation `((PC & ~3) + 4) + (disp * 4)`, same-register writeback order (`Rm == Rn`), NOP preservation, BRA delayed branch target calculation `PC + 4 + (disp * 2)`, delay slot execution, illegal slot exception, and register isolation;
- Real Thor 2 block oracle replay matched pinned Mednafen debug oracle with 0 divergences across all 6 steps.

### D4 — Code/Data/Unknown Ownership (Block 0)

Status: **BOUNDED_PROOF for basic block 0 only**

Capability: byte-level classification of executable modules into confirmed code, probable code, data, and unknown.
Verified gate: **V-03 / V-04 — Bounded Code Ownership Validation**.
Target claims proven:
- Exactly 12 dynamically retired instruction bytes at `0x06004000..0x0600400B` promoted to `CONFIRMED_CODE / EXECUTED`;
- Unexecuted remainder of `0TH2.BIN` (`0x0600400C..0x06086BFF`) retains conservative `PROBABLE_CODE / HIGH` (no unexecuted bytes classified as data merely due to lack of observation).

### D5 — Basic-Block CFG Recovery (Block 0)

Status: **BOUNDED_PROOF for basic block 0 only**

Capability: discovery and evidence-backed representation of basic blocks, terminators, delay slots, and control-flow exits.
Verified gate: **V-03 — Bounded Block CFG Validation**.
Target claims proven:
- Basic block record `bb_06004000` created in `workstreams/T2-D4-D5-block0/block_06004000.md`;
- Bounded interval `0x06004000..0x0600400A` (6 instructions, 12 bytes);
- Terminator identified as `0xA003` (`BRA 0x06004012`) with delay slot `0x0009` (`NOP`);
- Direct taken exit identified as `0x06004012`;
- Fallthrough exit identified as null (`std::nullopt`, unconditional branch);
- No function boundaries or speculative semantic names asserted.

### D6 — Mechanical Explicit-State C++ (bb_06004000)

Status: **BOUNDED_PROOF for bb_06004000**

Capability: mechanically generated standalone C++20 translation from validated basic blocks with zero runtime interpreter dependencies.
Verified gate: **Pre-D8 identity/event safety gate (PASSED) + V-07A transition proof (PASSED)**.
Target claims proven:
- `bb_06004000` recompiled to explicit-state C++20 without interpreter wrappers;
- Link-time symbol isolation proven (test `test_generated_link_isolation` links exclusively to generated library);
- Differential transition proof against interpreter and Mednafen oracle confirmed 0 state divergences and 0 memory log divergences across 3 synthetic vectors and real Thor 2 startup;
- Negative controls verified (injected register/PC/memory corruptions detected).

### D7 — Shadow Recompilation Framework (bb_06004000)

Status: **BOUNDED_PROOF for bb_06004000** (decision D-013)

Capability: reusable shadow execution comparison framework with fail-closed eligibility checking, anti-aliasing enforcement, and negative fault controls.
Verified gate: **V-07B — Shadow Comparison Validation (PASSED)**.
Target claims proven:
- Reusable framework `ShadowChecker` implemented (`include/thor/recomp/shadow_checker.hpp`, `src/recomp/shadow_checker.cpp`);
- Outcome comparator validates R0..R15, PC, SR, PR/GBR/VBR/MACH/MACL, ordered memory log (kind, address, value, width, sequence), and event safety metadata;
- 4 positive test vectors verified with 0 divergences vs Mednafen oracle (`test_shadow_positive`);
- 100% detection rate across 24 negative fault controls with 0 false passes (`test_shadow_negative`);
- Complete pre-state storage isolation and anti-aliasing proven (`test_shadow_isolation`);
- D7 status advanced to `BOUNDED_PROOF (bb_06004000)`.

### D8 — First Native Promotion Proof (V-07C)

Status: `BOUNDED_PROOF (bb_06004000) / V-07C: PASS` (ADR D-014)

Target claims proven:
- Reusable `NativeDispatcher` with pre-execution eligibility guard, shadow qualification, and C ABI bridge implemented (`include/thor/recomp/native_dispatcher.hpp`, `src/recomp/native_dispatcher.cpp`, `include/thor/recomp/native_bridge.h`);
- Integrated with pinned Mednafen debug oracle via dynamic plugin (`libthor_native.so`);
- Live cold-boot authoritative native override executed (`Run A`) and bit-identical cold-boot reproduction verified (`Run B`);
- Live interpreter retired 0 instructions in replaced block (`retirements_in_interval = 0`);
- Continuation to `0x06004280` verified through BSS clearing and data copy with zero register divergences across all 23 CPU registers against baseline interpreter (`Run C`);
- 100% fail-closed fallback proven under memory byte corruption without partial native commit (`Run E`);
- Mandatory post-D8 second-pass plan established (`docs/POST_D8_SECOND_PASS_PLAN.md`, ADR D-012).

### D9 — Indirect Control-Flow Handling (bb_06004280)

Status: `BOUNDED_PROOF (bb_06004280) / D9.4.1: PASS` (ADR D-015)

Target claims proven:
- Exact decode and L0 execution semantics implemented for `JSR @Rn` (opcode `0x430B`);
- First indirect candidate block `bb_06004280` (`0x06004280..0x06004288`, 10 bytes, 5 instructions) qualified and verified;
- Generic `BlockExitDescriptor` and `BlockMemoryContract` implemented with `RUNTIME_CLASSIFICATION_REQUIRED` dynamic validation;
- Link-isolated build target `thor_generated_bb_06004280` compiled without interpreter dependencies;
- Isolated shadow qualification proven with 100% negative fault detection;
- Live authoritative native indirect override executed in pinned Mednafen debug oracle across 5 cold-boot runs;
- 100% register parity (23/23 SH-2 registers) verified at dynamically computed target `0x0600A0F8` (cycle `316309189`, delta = 0 cycles);
- Return site `0x0600428A` (cycle `337109623`, delta = 0 cycles) and downstream continuation `0x060042E0` (cycle `387459912`, delta = 0 cycles) verified with zero drift;
- Retained as a **bounded technology/proof specimen** per ADR D-015; broad C++ translation frozen.

### POST-D8 — External Method Second Pass (ADR D-012)

Status: `COMPLETE / SATISFIED / CLOSED` (canonical record in `docs/POST_D8_SECOND_PASS_CLOSURE.md`)

Audited all external methods M-01..M-10; verified reference corpus pins; evaluated Evidence Strength and Workflow Utility.

## Next

### T2-ARCH / ADR D-015 — Freeze Broad C++ Translation & Establish ASM-First Recovery Strategy

Status: `ACCEPTED` (ADR D-015 in `docs/DECISIONS.md`)

The project enforces an **ASM-FIRST recovery strategy**:
1. All executable binaries and overlays must be completely mapped and classified (`CODE / DATA / UNKNOWN`).
2. Exact SH-2 assembly must be mechanically reconstructed into an assemblable project tree (`asm/`).
3. Reconstructed modules must assemble deterministically and boot in clean Mednafen, reaching title screen and gameplay with runtime parity (`FULL_ASM_GAME_GATE`).
4. Only after passing `FULL_ASM_GAME_GATE` will broad systematic translation from ASM to native C++ begin.
5. Existing C++ blocks `bb_06004000` (D8) and `bb_06004280` (D9) are retained strictly as bounded technology specimens.
6. M-03 technical capability is `READY_FOR_BOUNDED_TEST`, with execution `DEFERRED_BY_ASM_FIRST_ARCHITECTURE` until `FULL_ASM_GAME_GATE` passes.

### T2-ASM-01 — First Bounded SH-2 ASM Round-Trip & Runtime Proof

Status: **BOUNDED_PROOF (bb_06004000 byte-exact & runtime verified)**

Capability: mechanical SH-2 assembly emission, open toolchain assembly/linking at original Saturn VMA, byte-exact extraction, and live runtime substitution in Mednafen oracle.
Verified gate:
- Open GNU Binutils SH toolchain (`binutils-sh-elf 2.40+2`) pinned by binary hashes;
- Real SH-2 mnemonics emitted mechanically (`mov.w`, `mov`, `mov.l`, `bra`, `nop`);
- Linker script establishes VMA `0x06004000` with zero unresolved relocations;
- 12-byte raw extraction byte-exact to canonical slice SHA-256 `83795110...`;
- Private `0TH2.BIN` splice verified bit-identical to SHA-256 `c1cc4117...`;
- Mednafen cold-boot runtime substitution matches ORIGINAL in pure interpreter mode (entry cycle `305462360`, target `305462387`, duration 27, 23/23 registers match);
- 12/12 negative controls fail closed.

### Active Next Technical Task: T2-ASM-02 — Module Assembly Skeleton & Lossless CODE/DATA/UNKNOWN Emission for 0TH2.BIN

Purpose: Scale the mechanical assembly pipeline to the complete primary disc binary `0TH2.BIN` (535,552 bytes):
- generate an assembly module skeleton representing the full 535,552 bytes losslessly using proven SH-2 mnemonics for confirmed code and raw data directives (`.byte`/`.long`) for unclassified/data ranges;
- link at `0x06004000` with linker script matching 0TH2.BIN extents;
- prove byte-exact whole-module reassembly (`c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64`);
- verify boot in clean Mednafen oracle with the rebuilt module.

## Queued development milestones

| ID | Capability | Key verification gate | Scope state |
|---|---|---|---|
| D2 | Executable module provenance | V-02a (0TH2.BIN), V-02b (TH2.LOW) | BOUNDED_PROOF (0TH2.BIN + TH2.LOW) |
| D3 | Exact SH-2 decode + L0 semantics | V-06 cross-check + L0 semantic test suite | BOUNDED_PROOF (block 0 + JSR @Rn) |
| D4 | Code/data/unknown ownership | V-03 (bounded batch), V-04 (schema) | BOUNDED_PROOF (block 0 + bb_06004280) |
| D5 | Basic-block CFG | V-03 (bounded block CFG) | BOUNDED_PROOF (block 0 + bb_06004280) |
| D6 | Mechanical explicit-state C++ | V-07A + pre-D8 identity/event guards | BOUNDED_PROOF (specimens bb_06004000, bb_06004280) |
| D7 | Shadow comparison | V-07B (negative-control validation) | BOUNDED_PROOF (specimens bb_06004000, bb_06004280) |
| D8 | First native promotion proof | V-07C (native override proof) | BOUNDED_PROOF (specimen bb_06004000) |
| D9 | Indirect control-flow handling | Bounded native JSR override | BOUNDED_PROOF (specimen bb_06004280) |
| **M-03** | **Candidate harvester re-evaluation** | **Post-D9.4 re-entry gate** | **READY_FOR_BOUNDED_TEST (DEFERRED_BY_ASM_FIRST_ARCHITECTURE)** |
| **T2-ASM-01** | **First bounded ASM round-trip** | **Candidate toolchain assembly & substitution** | **BOUNDED_PROOF (bb_06004000)** |
| **T2-ASM-02** | **Module assembly skeleton for 0TH2.BIN** | **Lossless full-module round-trip** | **ACTIVE NEXT TASK** |
| **GATE** | **FULL_ASM_GAME_GATE** | **Rebuilt Saturn game boots & plays in Mednafen** | **MANDATORY PREREQUISITE FOR BROAD C++ TRANSLATION** |
| D10 | Timing/IRQ/DMA boundaries | — (general scaling) | PROPOSED (Post-ASM-Gate) |
| D11 | Overlay/generation identity | V-10 (transformation/overlay discovery) | PROPOSED (Active for ASM reconstruction) |
| D12 | Structural recovery | V-05, V-13 | PROPOSED (Post-ASM-Gate) |
| D13 | Guest-address/type provenance | V-09 | PROPOSED (Post-ASM-Gate) |
| D14 | Resource decode/reencode | V-11 (exact round-trip), V-12 (diff locator) | PROPOSED |
| D15 | HW-subsystem contracts | V-08 (SaturnRecomp component tests a–h) | PROPOSED |
| D16 | Native subsystem replacement | V-08 (components passing differential test) | PROPOSED |
| D17 | Progressive standalone runtime | V-14 (isolated, integrated, measured) | PROPOSED |
| D18 | Guest dependency removal | — (L5 equivalence) | PROPOSED |

## References

- `docs/DEVELOPMENT_PLAN.md` — full development track with milestones, dependencies, risk map.
- `docs/PIPELINE_VALIDATION_PLAN.md` — verification/adoption experiments.
- `docs/PROJECT_STATE.md` — current verified state.
- `docs/DECISIONS.md` — architectural decisions (ADR D-001..D-015).
