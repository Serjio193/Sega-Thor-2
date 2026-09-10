# Project state

## Status

- **D0 / T2-M0 — Canonical Revision Identity**: **COMPLETE**.
- **T2-P0 — Dual-Track Planning Hardening**: **COMPLETE** (decision D-008; established `DEVELOPMENT_PLAN.md` and `PIPELINE_VALIDATION_PLAN.md`).
- **T2-P0.1 — Dual-Track Proof-Contract Repair**: **COMPLETE** (formalized capability scope states, split V-01 into V-01-core and V-01-automation, removed TH2.LOW from V-01 gate, established pre-D8 guards).
- **D1 / T2-V01 / T2-V01.2 — Deterministic Dynamic Oracle**: **BOUNDED_PROOF** (decisions D-009, D-010; V-01-core verified; V-01-automation adopted as `ADOPT_PARTIAL` for `LOW_LEVEL_CONTROL_LAYER_PROVEN`).
- **D2 / T2-V02a / T2-V02b — Executable Module Provenance**: **BOUNDED_PROOF for 0TH2.BIN and TH2.LOW** (decision D-011; direct runtime byte mapping proven across both executable modules; 0TH2.BIN at `0x06004000..0x06086BFF` via BIOS copy loop; TH2.LOW at `0x002DA000..0x002FE7FF` via Master SH-2 copy loop; entry executions confirmed).
- **D3 / T2-D3.2 / T2-D9.1 — Exact SH-2 Decode / L0 Semantics**: **BOUNDED_PROOF expanded to JSR @Rn** (7 opcodes decoded: `MOV.W @Rm,Rn`, `MOV Rm,Rn`, `MOV.L @(disp,PC),Rn`, `MOV.L @Rm,Rn`, `BRA`, `NOP`, and `JSR @Rn`; `delayed_pc` zero-sentinel repaired to `std::optional<uint32_t>` in `Sh2CpuState` allowing target `0x00000000`; full synthetic matrix [all 16 registers, delay-slot Rn modification, alternate target, illegal slot exception, zero memory access] and negative controls verified; V-06 cross-check extended to `JSR @Rn` with 0 disagreements).
- **D4 / T2-D4.1 / T2-D9.1 — Code/Data Ownership**: **BOUNDED_PROOF expanded to bb_06004280** (`0x06004000..0x0600400B` [12 bytes] and `0x06004280..0x06004289` [10 bytes] promoted to `CONFIRMED_CODE / EXECUTED`; unexecuted remainder retains `PROBABLE_CODE / HIGH`).
- **D5 / T2-D5.1 / T2-D9.1 — Basic-Block CFG Recovery**: **BOUNDED_PROOF expanded to bb_06004280** (recovered `bb_06004280`: range `0x06004280..0x06004288`, 5 instructions, terminator `JSR @R3`, delay slot `NOP`, empty direct exits, fallthrough nullopt, dynamic target resolved at runtime to `0x0600A0F8`).
- **PRE_D8_EXECUTABLE_IDENTITY_GUARD**: **PASS for bb_06004000 and bb_06004280** (reusable fail-closed eligibility guard binding execution to revision, module, provenance, CPU, range, content bytes, and validity state; descriptors `make_bb_06004000_descriptor()` and `make_bb_06004280_descriptor()`; 10-byte negative corruption controls verified; zero memory log contamination).
- **PRE_D8_MINIMUM_EVENT_SAFETY**: **PASS for bb_06004000 bounded execution only** (two independent cold boots in Mednafen oracle proved atomic 27-cycle block duration [305462360..305462387, observation window through next instruction boundary 305462388 delta 28; earlier '18-cycle' was an arithmetic/typographical error for 28] with 0 MMIO, 0 IRQ, 0 SCU DMA, and inactive Slave SH-2).
- **D6 / T2-D6.1 / T2-D9.3 / V-07A — Mechanical Explicit-State C++**: **BOUNDED_PROOF for bb_06004000 and bb_06004280 / V-07A: PASS** (mechanical C++20 compiler generated standalone blocks `bb_06004000` and `bb_06004280` with 0 runtime interpreter dependencies verified via link-isolation targets `thor_generated_bb_06004000` and `thor_generated_bb_06004280`; V-07A transition proof verified against interpreter and Mednafen oracle; negative controls verified).
- **D7 / T2-D7.1 / T2-D9.3 / V-07B — Shadow Recompilation Framework**: **BOUNDED_PROOF for bb_06004000 and bb_06004280 / V-07B: PASS** (decision D-013; reusable `ShadowChecker` framework extended with `DELAYED_CONTROL_STATE` comparison; positive vectors passed with 0 divergences vs Mednafen oracle for both `bb_06004000` and `bb_06004280` [including synthetic target controls `0x0600A0F8`, `0x0600BEEF`, and `0x00000000`]; negative controls detected [100%]; pre-state storage isolation and anti-aliasing proven).
- **D8 / T2-D8.1 / V-07C — Authoritative Native Promotion Proof**: **BOUNDED_PROOF for bb_06004000 / V-07C: PASS** (decision D-014; reusable `NativeDispatcher` with mandatory pre-execution shadow qualification, runtime exit resolution, and memory contract write safety implemented; live authoritative override executed in pinned Mednafen debug oracle on cold boot [Run A]; bit-identical reproduction confirmed [Run B]; live interpreter retired 0 instructions in replaced block [retirements_in_interval = 0]; continuation cleanly verified to `0x06004280` matching interpreter baseline across all 23 registers with 0 divergences and 0 cycle drift [exact delta = 0 cycles at cycle 307090585]; 100% fail-closed fallback proven under memory corruption; live D8 production regression re-verified under D9.3 with 0 divergences).

- **M-02 / M-02.1 — SaturnAutoRE Mutation Fault-Injection**: **ADOPT_PARTIAL (NEGATIVE_CONTROL_HARNESS)** (reusable C++ mutation harness and live Mednafen IPC matrix proven; 12/12 bytes and 6/6 NOPs rejected fail-closed; fail-closed range/spec checks and restore precondition verified; zero-divergence non-contaminated baseline verified; evaluated on Evidence Strength [LOW] and Workflow Utility [HIGH]).
- **M-07 — SaturnRecomp SH-2 Reference Corpus**:
  - **M-07A (Decoder & Semantic Reference Corpus)**: **ADOPT_PARTIAL (DECODER_AND_SEMANTIC_REFERENCE)** (pinned commit `26c9715e5493054b8a205aa31d73d8f125fdd8f5`, blobs `6a5f7e06` and `709f9243`; 20 decode vectors and 8 live semantic cases cross-checked with 0 unexplained disagreements; 18 fail-closed negative controls verified; verified with `--require-external`; Evidence Strength [MEDIUM], Workflow Utility [HIGH]).
  - **M-07B (AOT Translation Emitter / C Codegen)**: **NOT_PRESENT_AT_PIN** (pinned commit contains no public AOT emitter or C code generator; upstream README explicitly notes absence; Evidence Strength [N/A], Workflow Utility [N/A]).
- **POST-D8 SECOND-PASS CLOSURE (ADR D-012)**: **COMPLETE / SATISFIED / CLOSED** (canonical record in `docs/POST_D8_SECOND_PASS_CLOSURE.md`; exhaustive audit across M-01..M-10; D9 unblocked for planning).
- **D9 / T2-D9.1 / T2-D9.2 / T2-D9.3 / T2-D9.4 / T2-D9.4.1 — Indirect Control-Flow Handling**: **BOUNDED_PROOF for bb_06004280 (D9.1: PASS, D9.2: PASS, D9.3: PASS, D9.4: PASS, D9.4.1: PASS)** (canonical architecture plan in `docs/D9_INDIRECT_CONTROL_FLOW_PLAN.md`; `JSR @Rn` exact decode and execution semantics implemented; candidate block `bb_06004280` [`0x06004280..0x06004288`, 10 bytes, SHA-256 `8879cbe1...`] qualified in D3/D4/D5; generic `BlockExitDescriptor` and `ResolvedBlockExit` implemented; declarative `BlockMemoryContract` hardened with `RUNTIME_CLASSIFICATION_REQUIRED` for dynamic register reads and width-aware memory intervals; `ShadowChecker` extended to verify delayed-transfer state; mechanical JSR block generation implemented; build-time target `thor_generated_bb_06004280` link-isolated; isolated shadow qualification proven for `bb_06004280` and synthetic target controls; `NativeDispatcher` generic pre-state materializer, block mask filtering, and per-block telemetry implemented; authoritative live execution in pinned Mednafen debug oracle proven with 100% register parity across all 23 registers at dynamically computed target `0x0600A0F8`; 0 interpreter retirements in replaced block; cold-boot bit-identical parity proven across independent runs; zero downstream corruption at `0x060042E0`; automated validator `test_d9_plan.py` passing with 22 negative controls; retained as a bounded technology specimen).
- **T2-ARCH / ADR D-015 — Freeze Broad C++ Translation & Establish ASM-First Recovery Strategy**: **ACCEPTED / COMPLETE** (mandatory ASM-first recovery strategy; broad C++ translation frozen until `FULL_ASM_GAME_GATE`; bounded C++ blocks `bb_06004000` and `bb_06004280` retained strictly as technology specimens; M-03 technical capability = `READY_FOR_BOUNDED_TEST`, execution = `DEFERRED_BY_ASM_FIRST_ARCHITECTURE` until `FULL_ASM_GAME_GATE` passes).

Active next technical task: **T2-ASM-01 — First Bounded ASM Round-Trip Experiment**.

Note: Basic blocks `bb_06004000` (`0x06004000..0x0600400A`) and `bb_06004280` (`0x06004280..0x06004288`) have complete decode, L0 semantic, code ownership, CFG, identity guard, minimum event safety, mechanical C++ transition proof, shadow checker validation, and authoritative native promotion proof. They are retained strictly as bounded technology/proof specimens. Broad C++ translation is frozen until the entire game passes `FULL_ASM_GAME_GATE`. D8/D9 are NOT whole-system recompiler completion.

No decompiler/recompiler architecture is considered final. External methods enter the pipeline only after bounded Thor 2 validation.

## Confirmed substrate revision

Revision ID: `thor2_ntsc_patched_fe11d2fb`

- image SHA-256: `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8`
- image size: `122830848`
- CUE SHA-256: `afc0b101bbb493adbd43fd44ffd76959484d67cf0b566137dd145f1c68d411e0`
- format: `MODE1/2352`, 52,224 raw sectors
- ISO9660 volume: `THE STORY OF THOR 2`
- ISO9660 files: 33
- manifest SHA-256: `19b56fd0fefa42c23edac055cd5e817a7a4834b7d7b423cef15a27de4bc80f49`

Two independent census runs produced identical manifest and summary output.

## Confirmed Saturn header metadata

- hardware ID: `SEGA SEGASATURN`
- maker: `SEGA ENTERPRISES`
- product: `MK-81302`
- version: `V1.000`
- date: `19960618`
- disc: `CD-1/1`
- regions field: `JTU`
- title field: `THE STORY OF      THOR 2 (patched for NTSC)`
- IP size: `0x1000`
- master stack: `0x06001000`
- slave stack: `0x06002000`
- first-read address: `0x06004000`

## Executable candidates

### `0TH2.BIN`

- SHA-256: `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64`
- size: `0x82C00`
- module status: `EXECUTABLE_MODULE / RUNTIME_MAPPING_EXACT / FULL_EXACT_MATCH` (`DIRECT_PROVENANCE_PROVEN`)
- byte classification: `CONFIRMED_CODE / EXECUTED` for dynamically observed instructions at `0x06004000..0x0600400B` (Basic Block 0, 12 bytes); unexecuted remainder `0x0600400C..0x06086BFF` remains `PROBABLE_CODE / HIGH`
- dynamic evidence: V-02a proven direct byte-exact mapping (`FULL_EXACT_MATCH`), BIOS Master SH-2 CPU transfer loop (`PC=0x00002368`) from CD Block buffer (FAD `0x0000AE..0x0001B3`), and entry execution.
- next gate: pre-D8 identity/event safety gate + D6/V-07A native block translation.

### `TH2.LOW`

- SHA-256: `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224`
- size: `0x24800`
- module status: `EXECUTABLE_MODULE / RUNTIME_MAPPING_EXACT / FULL_EXACT_MATCH` (`DIRECT_PROVENANCE_PROVEN`)
- byte classification: `CONFIRMED_CODE / EXECUTED` for dynamically observed instructions at `0x002E9910..0x002E9914`; unexecuted remainder `0x002DA000..0x002FE7FF` remains `PROBABLE_CODE / HIGH` (mapped byte-exact to disc; complete code/data/unknown ownership queued for D4)
- dynamic evidence: V-02b proven direct byte-exact mapping (`FULL_EXACT_MATCH`), Master SH-2 CPU transfer loop (`PC=0x0607DF08`) from CD Block buffer (FAD `0x00CC31..0x00CC79`), and execution at `0x002E9910` (offset `0xF910`, cycle `387459915`).
- next gate: D3 exact SH-2 decode / L0 semantics.

All other disc files remain `UNKNOWN` unless there is evidence to classify them. File extension alone is not code/data proof.

## Storage split

GitHub contains legal-safe source, tooling, hashes/manifests, evidence summaries, tests, configs, and documentation. Original image, BIOS, save states, raw traces, and other private binary artifacts remain outside GitHub in the project owner's private workspace.
