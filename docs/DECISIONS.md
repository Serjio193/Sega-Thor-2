# Decisions

## D-001 — Split public source from private commercial inputs

**Status:** ACCEPTED

GitHub contains only legal-safe source, tools, configs, tests, hashes/manifests, evidence summaries, and documentation. Commercial/raw binary inputs remain external/private.

## D-002 — One methodological experiment at a time

**Status:** ACCEPTED

Do not integrate several new external techniques simultaneously. Each method must be independently tested on Thor 2 and end in `ADOPT`, `ADOPT_PARTIAL`, `REJECT`, or `DEFER`.

## D-003 — Mechanical translation may precede semantic understanding

**Status:** WORKING HYPOTHESIS

The project will attempt machine-equivalent explicit-state translation before semantic naming. This becomes accepted only after Thor 2 SH-2 shadow/native proof.

## D-004 — Basic block is the initial translation unit

**Status:** WORKING HYPOTHESIS

Function boundaries are not required for correctness. They remain evidence-backed annotations until proven useful.

## D-005 — Unknown is a first-class classification

**Status:** ACCEPTED

`not executed` does not imply data. The project preserves unknown regions explicitly.

## D-006 — No wholesale Saturn runtime import

**Status:** ACCEPTED

External Saturn runtime components, including SaturnRecomp, are evaluated component-by-component against Thor 2 requirements and oracle evidence.

## D-007 — Transfer Sega-Thor governance, adapt platform-specific scope

**Status:** ACCEPTED

The transferable development/RE discipline proven in `Serjio193/Sega-Thor` is mandatory for Sega-Thor-2: confidence gating, evidence-first lifecycle, task/stop/checkpoint discipline, hard source-size limits, local validation, evidence-integrity rules, historical-toolchain boundaries, focused scope/commits, and synchronized project documentation.

Mega Drive/Beyond Oasis-specific roadmap instructions, addresses, milestone IDs, and platform-specific implementation facts are not copied. Their general governing principle is adapted to Saturn only when applicable.

The canonical transfer record is `docs/RULES_TRANSFER_AUDIT.md`. Future material governance changes in Sega-Thor require a new explicit audit rather than assumed automatic inheritance.

## D-008 — Dual-track planning and decoupled method validation

**Status:** ACCEPTED

The project planning model is rebuilt into two synchronized tracks:
1. **Development Track** (`docs/DEVELOPMENT_PLAN.md`): defines capabilities D0–D18 in dependency order, specifying what the project builds regardless of candidate tool choice.
2. **Verification Track** (`docs/PIPELINE_VALIDATION_PLAN.md`): defines bounded experiments V-01–V-14, specifying what evidence an external method must produce before adoption into the build path.

A candidate external method's failure (e.g. SaturnAutoRE in V-01) does not invalidate the development capability (D1 deterministic dynamic oracle); the project retains the requirement and tests alternative candidate tools. Planning documents distinguish `PROPOSED`, `VALIDATED`, `ADOPTED`, `SUPERSEDED`, `REJECTED`, and `DEFERRED`.

Under T2-P0.1, capability evidence scope is further formalized:
- Verification decisions: `PROPOSED`, `TESTING`, `VALIDATED`, `ADOPT`, `ADOPT_PARTIAL`, `SUPERSEDED`, `REJECT`, `DEFER`.
- Capability scope states: `PROPOSED`, `READY_FOR_BOUNDED_TEST`, `BOUNDED_PROOF`, `EXPANDED_PROOF`, `DONE`.
- Non-conflation invariant: `V-xx PASS` proves a declared bounded observation/experiment contract only and does not imply whole-capability completion (`Dxx DONE`).

## D-009 — Adopt bounded Mednafen debug fork as initial dynamic oracle

**Status:** ACCEPTED (ADOPT for V-01-core)

The pinned Mednafen debug fork (`AJBats/mednafen-saturn-debug` commit `155426661b7ac3152e2c93a98da60ac33002b908`) built natively under WSL (GCC 13.3.0) is adopted as the deterministic dynamic oracle for bounded Thor 2 boot observation (`V-01-core`).

Evidence: Two independent cold-boot runs (`RUN_A` and `RUN_B`) with debugger `deterministic` mode enabled produced 100% identical results across CPU identity (`MASTER_SH2`), frame (680), cycle (305462360), entry candidate PC (`0x06004000` with hook PC `0x06004002` via pc-2 fallback), all 23 register states, step transitions (Steps 1–6 with confirmed opcode retirements), and dynamic memory read watchpoint hit (`0x06081C10` = `0x060917DC` via `MOV.L @R4, R4` at `0x06004006`, cycle `305462372`).

Scope limitation: This decision adopts Mednafen for bounded execution observation only. It does not adopt autonomous RE pipeline scripting (`V-01-automation`), whole-game determinism, or hardware-perfect timing across unobserved systems. D1 capability remains at `BOUNDED_PROOF`.

## D-010 — Adopt SaturnAutoRE MednafenBot Control Layer as ADOPT_PARTIAL

**Status:** ACCEPTED (ADOPT_PARTIAL for V-01-automation)

The low-level IPC control harness `MednafenBot` from `AJBats/SaturnAutoRE` (commit `4662aad69f95222fe37c5e6b98f2285b1a7e4653`) is adopted as `ADOPT_PARTIAL` for scripted execution control and observation capture.

Evidence: Two independent automation runs (`RUN_A` and `RUN_B`) drove the pinned Mednafen debug oracle and reproduced the accepted `V-01-core` bounded observation with 100% parity across all 23 CPU registers, deterministic cycles (entry cycle 305462360, watchpoint cycle 305462372), step transitions (Steps 1–6), and dynamic read watchpoint hit (`0x06081C10` = `0x060917DC`). A negative control test with 5 deliberate corruptions was correctly flagged as `FAIL`.

Configuration delta: `MednafenBot.start()` unconditionally injects `-cd.image_memcache 1`. Controlled comparison proved this delta neutral for the bounded observation window.

Scope limitation: Adoption is strictly limited to `LOW_LEVEL_CONTROL_LAYER_PROVEN` (scripted IPC driver). Higher-level SaturnAutoRE autonomous workflows (`auto_re.py`, function discovery heuristics, NOP experiments, claim generation, and graduation logic) remain unverified and unadopted. D1 capability remains at `BOUNDED_PROOF`.

## D-011 — Adopt Daytona Module Provenance Methodology as ADOPT_PARTIAL and Confirm 0TH2.BIN Direct Runtime Mapping

**Status:** ACCEPTED (ADOPT_PARTIAL for Daytona provenance methodology; V-02a PASSED)

1. The Daytona module provenance methodology (`AJBats/saturn-daytona-cce-re` inspected at commit `bf2ea285e0dc699b659c4d2cdd0a59d07f92d276`) is adopted as `ADOPT_PARTIAL` for the concept of explicit module mapping verification via pre-execution live RAM snapshotting and full-file SHA-256 byte comparison.
2. The runtime executable provenance of Thor 2's primary boot binary `0TH2.BIN` is confirmed as `V02A_DIRECT_PROVENANCE_PROVEN`.

Evidence:
- Disc extent: ISO9660 LBA 24..285 (262 sectors, 535,552 bytes, SHA-256 `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64`).
- CD Block transfer: `cdb.log` confirms sector read sequence via `Get and Delete Sector Data` from FAD `0x0000AE` (LBA 24) through FAD `0x0001B3` (LBA 285).
- Transfer mechanism: `mem.log` confirms Master SH-2 BIOS ROM copy loop at PC `0x00002368` transferring bytes from CD Block data register directly into High Work RAM `0x06004000..0x06086BFF` (`DIRECT_CPU_COPY_OBSERVED`).
- Byte identity: Two independent pre-execution live RAM dumps at base `0x06004000` (535,552 bytes) yielded SHA-256 `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64` (`FULL_EXACT_MATCH`, 0 differing bytes).
- Execution: Master SH-2 hit breakpoint at `0x06004000` and executed instructions inside the mapped range.

Scope limitation: D2 capability is advanced to `BOUNDED_PROOF for 0TH2.BIN only`. `TH2.LOW` provenance remains unproven and is queued under `V-02b`. Daytona-specific build/link pipelines remain unadopted.

## D-012 — Mandatory post-D8 second pass over external methods

**Status:** ACCEPTED

Reaching `D8 — First Native Promotion Proof` is a mandatory planning checkpoint, not permission to permanently discard external ideas that were skipped, deferred, considered weak, or not yet testable during the first pass.

After D8 reaches its bounded native-promotion proof, the project MUST create a new synchronized second-pass plan for the external projects and methods inventoried by the project. The second pass must re-enumerate methods that are untested, partially tested, deferred, rejected only on preliminary judgment, or retained only as references/heuristics.

A method MUST NOT be skipped merely because ChatGPT, Opus, Astra, another AI reviewer, or a human reviewer considers the idea weak, inelegant, heuristic, low-confidence, or unlikely to become a proof mechanism. If the method is technically testable on Thor 2, it receives a bounded experiment before the project moves past the post-D8 checkpoint.

Second-pass evaluation uses two independent axes:
1. **Evidence strength** — whether the method can support a proof claim.
2. **Workflow utility** — whether it materially accelerates discovery, candidate generation, classification, automation, implementation, or review when followed by independent verification.

Therefore a method may be retained as a `DISCOVERY_METHOD`, `HEURISTIC`, `ACCELERATOR`, or `REFERENCE` even when it is insufficient for proof. Failing a proof threshold alone is not grounds for rejection.

Post-D8 advancement rule:
- before ordinary D9+ scaling/recovery work begins, create the second-pass experiment plan and execute every remaining method that is meaningfully testable with capabilities available at D8;
- methods blocked by a genuinely missing later prerequisite are recorded explicitly as `PREREQUISITE_BLOCKED`, with the exact downstream gate where they MUST be tested; they may not be silently dropped or rejected without experiment;
- every second-pass method ends with an evidence record and explicit disposition (`ADOPT`, `ADOPT_PARTIAL`, `REJECT`, `DEFER`, or retained heuristic/reference role);
- only after this checkpoint is satisfied may the project resume normal post-D8 progression.

The purpose is to avoid losing practically useful techniques merely because they appear weaker than the project's proof layer. The proof layer remains authoritative; the second pass determines which additional techniques can safely accelerate the work beneath that layer.

## D-013 — Adopt Reusable Shadow Execution Framework (Capability D7 / Gate V-07B)

**Status:** ACCEPTED (V-07B PASSED; D7 BOUNDED_PROOF for bb_06004000)

1. The shadow execution comparison framework `ShadowChecker` (`include/thor/recomp/shadow_checker.hpp`, `src/recomp/shadow_checker.cpp`) is adopted as the reusable differential verification harness for mechanical recompilation.
2. The framework enforces strict pre-state storage isolation, pointer anti-aliasing between candidate and oracle mutable contexts, and fail-closed block eligibility checking before candidate invocation.
3. The framework includes an exhaustive outcome comparator checking:
   - registers R0..R15;
   - program counter PC;
   - status register SR;
   - control registers PR, GBR, VBR, MACH, MACL;
   - ordered memory access log (kind, address, value, width, access sequence);
   - bounded event safety metadata (MMIO, IRQ, DMA, Slave SH-2, delay slot atomicity).

Evidence:
- Zero positive divergences across 4 independent test vectors (`test_shadow_positive`), including real Thor 2 startup capture matching accepted Mednafen oracle constants.
- 100% negative fault detection rate across 24 injection controls (`test_shadow_negative`) with zero false passes.
- Pre-state storage isolation and non-aliasing proven (`test_shadow_isolation`).

Scope limitation: D7 is advanced to `BOUNDED_PROOF for bb_06004000`. D8 / V-07C (authoritative native promotion) remains strictly `PROPOSED` until explicit zero-divergence fallback architecture is proven.
