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

## D-014 — Adopt Authoritative Native Override and Fail-Closed Fallback Architecture (Capability D8 / Gate V-07C)

**Status:** ACCEPTED (V-07C PASSED; D8 BOUNDED_PROOF for bb_06004000)

1. The authoritative native dispatcher `NativeDispatcher` (`include/thor/recomp/native_dispatcher.hpp`, `src/recomp/native_dispatcher.cpp`) and C ABI plugin interface (`include/thor/recomp/native_bridge.h`, target `thor_native_plugin`) are adopted for runtime block execution override.
2. Production native override enforces mandatory shadow qualification before live hardware state mutation: candidate compiled code runs in isolated shadow scratchpad first; live registers/memory are updated only upon exact zero-divergence match.
3. Fail-closed fallback is guaranteed across all negative conditions (unregistered block, content hash mismatch, active DMA/Slave SH-2, pending IRQ, shadow divergence) without contaminating live machine state.
4. Pinned Mednafen debug oracle integration proves:
   - Live interpreter retires 0 instructions in replaced block (`retirements_in_interval = 0`).
   - Downstream execution cleanly continues to `0x06004280` through BSS clearing and data copy loops.
   - Exact 100% bit parity across all 23 CPU registers against baseline pure interpreter execution.

Scope limitation: D8 capability is advanced to `BOUNDED_PROOF for bb_06004000 only`. Multi-block scaling remains gated by post-D8 second-pass plan (ADR D-012) and D9.

## D-015 — Freeze Broad C++ Translation and Establish ASM-First Recovery Strategy (FULL_ASM_GAME_GATE)

**Status:** ACCEPTED

### Context

The project has proven bounded mechanical explicit-state C++ recompilation and live native override for two basic blocks:
1. `bb_06004000` (D8 / V-07C): direct unconditional branch, BSS clear, and data copy loop;
2. `bb_06004280` (D9 / T2-D9.4.1): indirect control transfer (`JSR @R3`), dynamic target resolution (`0x0600A0F8`), and dynamic return/continuation.

Both specimens demonstrated zero CPU state divergence, 0 interpreter retirements during native execution, and exact timing parity in the pinned Mednafen debug oracle.

However, attempting to scale directly from two bounded basic blocks to broad, whole-game C++ recompilation introduces critical architectural risks:
- Thor 2 consists of multiple executable binaries and overlays (`0TH2.BIN`, `TH2.LOW`, dynamic overlays, M68K sound driver) whose runtime boundaries, entrypoints, and generation lifetimes are not yet fully mapped;
- Code, literal pools, jump tables, and embedded data are tightly interleaved in Saturn binaries; broad mechanical translation without complete assembly recovery risks translating data as code, dropping literal pools, or misidentifying indirect dispatch targets;
- Without an end-to-end reassemblable baseline, bugs or divergences in translated C++ cannot be differentials against a rebuilt, native Saturn executable.

### Decision: ASM-First Recovery Strategy

The project adopts a mandatory **ASM-FIRST recovery strategy**.

The canonical recovery sequence is:
```text
original Saturn binaries
→ complete executable/module provenance
→ complete CODE/DATA/UNKNOWN recovery
→ complete exact SH-2 assembly reconstruction
→ reassemblable game
→ rebuilt Saturn game boots and runs in Mednafen (FULL_ASM_GAME_GATE)
→ only then broad systematic ASM → C++ translation.
```

### Distinction Between Bounded Proofs and Broad Translation

1. **Bounded C++ Technology Proofs (Retained):**
   - Basic blocks `bb_06004000` and `bb_06004280` are retained in the codebase exclusively as **bounded technology/proof specimens**.
   - They prove that the SH-2 instruction decoder, explicit-state mechanical code generator, shadow comparator, and authoritative native dispatcher work correctly under real Saturn hardware execution.
   - They will NOT be deleted.
2. **Broad Production C++ Translation (Frozen):**
   - Broad mechanical C++ translation of game code is **FROZEN / BLOCKED** until the `FULL_ASM_GAME_GATE` passes.
   - Do NOT broaden native C++ translation now.
   - Do NOT start M-03 implementation (SaturnAutoRE harvester) now.

### Mandatory Gate: FULL_ASM_GAME_GATE

Advancement to broad systematic C++ translation requires passing the `FULL_ASM_GAME_GATE`.

Required evidence:
1. **All Executable Modules Known or Explicitly UNKNOWN:** Complete inventory of executable files and overlays (`0TH2.BIN`, `TH2.LOW`, overlays).
2. **Runtime Provenance:** Proven disc-to-memory loading path and execution range for each module and overlay generation.
3. **Complete CODE/DATA/UNKNOWN Classification:** Every byte in executable regions classified with explicit evidence; no gaps.
4. **Exact SH-2 Decoding:** Every confirmed instruction decoded bit-exact with proven semantics.
5. **Assembly Reconstruction:** Labels, CFG, branches, calls, and returns recovered sufficiently to emit assemblable `.s` source files.
6. **Data & Literal Pool Preservation:** Literal pools, jump tables, and embedded data preserved without displacement or corruption.
7. **No Guessed Instructions:** UNKNOWN bytes are emitted strictly as raw data directives (`.byte`), NEVER as speculative instructions.
8. **Deterministic Reassembly:** Every reconstructed module can be assembled deterministically by candidate toolchain.
9. **Rebuilt Module Layout Validation:** Section layout, load addresses, and file structures match original binary specifications.
10. **Game Substitution:** Original game disc files can be replaced by rebuilt equivalents.
11. **Cold-Boot Execution:** Rebuilt Saturn game boots from cold boot in clean pinned Mednafen debug oracle.
12. **Title & Gameplay:** Rebuilt game reaches title screen and playable gameplay.
13. **Runtime Parity:** Bounded runtime checkpoints match original un-rebuilt execution.
14. **Overlay Proof:** Overlays and dynamic modules are included in the reassembly and boot verification.

### Round-Trip Evidence Hierarchy

The project defines the following formal evidence classes for assembly reconstruction:
- `ASM_BYTE_EXACT`: Reassembled binary reproduces original retail bytes bit-for-bit (0 byte differences).
- `ASM_LAYOUT_EXACT`: Reassembled binary reproduces identical section layout, memory mapping, symbol alignments, and file sizes, even if padding or build artifacts differ deterministically.
- `ASM_RUNTIME_VERIFIED`: Replaced binary runs in runtime oracle and matches all architectural state, register, and memory checkpoints.
- `ASM_GAME_BOOT_VERIFIED`: Rebuilt disc/game successfully completes Saturn boot sequence in clean Mednafen without hangs or assertion failures.
- `ASM_GAMEPLAY_VERIFIED`: Rebuilt game reaches title screen and controllable gameplay with full functional parity.

*Rule:* Semantic equivalence must NEVER be called byte-exact.

### Generated Assembly Project Layout

The planned assembly project structure is:
```text
asm/
  modules/       # Main executable modules (e.g. 0TH2.BIN, TH2.LOW)
  overlays/      # Dynamic overlays and staged execution overlays
  include/       # Shared assembly headers, macros, hardware equates
  generated/     # Tool-generated assembly slices with provenance tags
  linker/        # Linker scripts, memory maps, layout definitions
  manifests/     # Module hashes, section offset maps, provenance manifests
```

### Mechanical Assembly Generation Rules

Assembly generation must be strictly mechanical:
- **Confirmed Instructions:** Emit exact SH-2 instruction representation (e.g., `mov.l @(h'0008, PC), r5`).
- **Data:** Emit exact bytes/words/longs or appropriate lossless directives (`.byte`, `.word`, `.long`, `.ascii`, `.incbin`).
- **UNKNOWN:** Emit lossless raw data directives (`.byte 0x..`), NEVER guessed instructions.
- **Provenance Tags:** Every emitted range must retain provenance metadata:
  `module`, `runtime address`, `source offset`, `generation/overlay identity`, `original bytes/hash`.

### Toolchain Selection Rules

- Assembler and linker tooling must be selected ONLY after a bounded reproducibility experiment.
- Do NOT assume GNU `as` or any other tool can reproduce the original layout out of the box.
- Test candidate tooling against already-proven small regions first (e.g. `bb_06004000` / `bb_06004280`).
- Required process: assemble → compare bytes/layout → diagnose differences.
- **Strict Legal Hygiene:** Never commit or download proprietary/leaked Sega SDK binaries or copyrighted assemblers.

### First ASM-First Bounded Experiment

The immediate next technical task is defined as the first bounded ASM round-trip experiment:
- Select an already-proven small region/module slice (e.g. `bb_06004000` or `bb_06004280`);
- Emit generated SH-2 `.s` assembly with mechanical directives and provenance tags;
- Assemble using candidate open toolchain;
- Perform byte and layout comparison;
- Substitute rebuilt bytes into live memory / module;
- Execute in clean Mednafen oracle;
- Verify runtime parity against baseline execution.

This experiment proves toolchain feasibility and establishes the ASM round-trip workflow without broadening C++ translation.

### Status of M-03

- **Technical capability:** `READY_FOR_BOUNDED_TEST` (technically unblocked by D9.4 proof).
- **Execution status:** `DEFERRED_BY_ASM_FIRST_ARCHITECTURE` until `FULL_ASM_GAME_GATE` passes.
- M-03 is NOT technically disproven, but its execution is postponed in accordance with the ASM-first sequencing rule.

## ADR D-016: Allow Proof-Gated Discovery Accelerators During ASM-First Recovery

- **Status:** APPROVED (2026-09-10)
- **Context:**
  ADR D-015 established the mandatory ASM-first recovery track and froze broad C++ translation until `FULL_ASM_GAME_GATE`. However, reaching `ASM_90_GATE` ($\ge 90.00\%$ proven mnemonic coverage) and `FULL_ASM_GAME_GATE` across all Saturn executable modules, overlays, and sound programs requires analyzing over 685 KB of Saturn binaries. Performing this solely by manual ad-hoc inspection is unnecessarily slow. Automated discovery accelerators (static analyzers, headless decompilation, dynamic trace harvesters, debug mode controllers, signature matchers, and pattern recognizers) can dramatically speed up candidate generation.
- **Decision:**
  Authorize the creation and use of proof-gated discovery accelerators during the ASM-first recovery track. Specifically:
  1. **Autonomous Recovery Loop:** An automated discovery and verification engine may iteratively execute test scenarios, harvest retired PCs, trace memory loads, and propose candidate code/data boundaries.
  2. **Multi-Source Discovery:** Static analyzers (recursive CFG closure, literal pool extractors, pointer table scanners, compiler pattern matchers), dynamic oracles (Mednafen retired PC harvesters, RAM write watchers, interrupt monitors), and external tools (headless Ghidra disassemblers, Saturn SDK signatures) may be used to discover candidate blocks.
  3. **Thor In-Game Debug Tooling:** Activation of retail debug features (such as `0x06009CC4` debug menu, level select, and sound tests) is approved as an oracle stimulus tool to explore code paths.
  4. **Multi-Processor Scope:** Discovery applies to Master SH-2, Slave SH-2, and MC68EC000 (SCSP sound) programs.
- **Mandatory Invariant — DISCOVERY $\ne$ PROOF:**
  1. Discovery tools produce *hypotheses* (`PROBABLE_CODE`, `PROBABLE_DATA`, candidate boundaries).
  2. A candidate range is promoted to `CONFIRMED_CODE` ONLY when supported by independent verification (e.g., observed dynamic execution in clean Mednafen oracle, verified deterministic CFG closure from a confirmed entry point, or byte-exact assembler/linker round-trip).
  3. An instruction is promoted to `MNEMONIC_PROVEN` ONLY when decoded bit-exact by `thor_sh2` with verified L0 semantics.
  4. Unproven bytes must remain losslessly emitted as raw data directives (`.byte`), never guessed instructions.
  5. Broad ASM $\to$ C++ translation remains strictly FROZEN per ADR D-015 until `FULL_ASM_GAME_GATE` passes.

## ADR D-017: Standalone Native Game Executable Target Architecture

- **Status:** APPROVED (2026-09-10)
- **Context:**
  Following the successful completion of `FULL_ASM_GAME_GATE` and the progressive hardware/runtime milestones (`D10`, `D11`, `D12`, `D15`, `D16`, `D17`), the project requires a standalone native game executable target (`thor2_native`) that decouples entirely from guest emulator processes and runtime plugin injection.
- **Decision:**
  1. **Direct Native Executable Target:** Implement `thor2_native` (`src/main_native.cpp`) as the standalone native executable linking `thor_runtime`, `thor_hw`, `thor_recomp`, and `thor_sh2`.
  2. **Zero External Emulator Dependency:** The executable links directly with host C++20 standard libraries and internal Thor libraries with zero dynamic or static link dependencies on Mednafen, Kronos, or external emulator code.
  3. **Multi-Mode CLI Interface:** Provide standard CLI options:
     - `--boot`: boots runtime and executes startup sequence.
     - `--frames <N>`: executes specified frame count.
     - `--metrics`: reports native execution ratios, instruction counts, and performance metrics.
     - `--selftest`: executes comprehensive built-in hardware and execution self-test returning exit code 0.
  4. **L5 Observable Equivalence Contract:** Verify output parity through bit-identical frame rasterization (320x224 RGBA8888) and 16-bit stereo PCM audio synthesis across independent runs.
- **Consequences:**
  - `thor2_native` serves as the primary distribution and execution target for the native C++20 port.
  - Verification can run fully standalone in standard CI/CD pipelines without emulator GUI or IPC harnesses.

## ADR D-018: Supersede Premature Terminal Completion and Enforce Real Gate Verification

- **Status:** APPROVED (2026-09-10)
- **Context:**
  At commit `093abf0`, the project was prematurely declared complete. A factual audit revealed that:
  1. `BGM.BIN` (MC68EC000 sound driver, 673,792 bytes) is CATALOGED but not reassembled byte-exact, disassembled, or runtime-verified.
  2. `FULL_ASM_GAME_GATE` verification was limited to 6 discrete startup checkpoints; interactive gameplay (title screen, player control, map transitions, combat, sound) was not verified.
  3. `StandaloneRuntime` still executes guest CPU fallback interpreter `thor::sh2::step_sh2(...)`, retaining guest CPU dependency in production paths.
  4. `test_guest_removal` compared two candidate instances against each other (self-consistency), not against Mednafen oracle output.
  5. Milestones D13 (Guest Address/Type Provenance) and D14 (Resource Decode/Reencode) were skipped.
- **Decision:**
  1. **Supersede Premature Claims:** Formally supersede the terminal completion assertion made at `093abf0`.
  2. **Reset Gate States:** Set `PROJECT_COMPLETION_STATE = IN_PROGRESS`, `FULL_ASM_GAME_GATE = NOT_SATISFIED`, `STANDALONE_NATIVE_GATE = NOT_SATISFIED`, and `D18 = NOT_PROVEN`.
  3. **Re-Affirm ADR D-015:** Broad C++ translation remains strictly FROZEN until real `FULL_ASM_GAME_GATE` passes with all modules (including `BGM.BIN` / MC68EC000) and multi-scenario gameplay verification.
  4. **Retain Useful Work:** Preserve all native subsystem and runtime implementations (`thor2_native`, `StandaloneRuntime`, `NativeSaturnSystem`) as bounded reference prototypes.
  5. **Machine-Enforced Validation:** Mandate automated validation scripts for `FULL_ASM_GAME_GATE` and `STANDALONE_NATIVE_GATE` that fail closed if any module, processor, or interpreter fallback remains unaddressed.
- **Consequences:**
  - Project returns immediately to the ASM-first recovery track.
  - Immediate focus is directed to `BGM.BIN` / MC68EC000 assembly pipeline and multi-scenario gameplay verification.

## ADR D-019: Strict Return to ASM-First Architecture and Implementation of Evidence-Driven Recovery Carver

- **Status:** APPROVED (2026-09-11)
- **Context:**
  The user explicitly confirmed the canonical ASM-first architecture: the entire game must be completely recovered in assembly before any broad C++ translation is permitted. While the previous scorecard reported 96.6% mnemonic coverage, this figure was calculated strictly over previously confirmed code (57,266 bytes), leaving 1,399,886 bytes as unexamined `UNKNOWN`. Unexamined code in the denominator meant the claimed 96.6% was unproven across the full binary substrate.
- **Decision:**
  1. **Freeze Broad C++ Translation Scaling:** Freeze D17 native scaling, StandaloneRuntime expansion, and D18 work. Existing C++ artifacts remain bounded proof specimens.
  2. **Establish Central Interval Database:** Create canonical interval database (`tools/carver/interval_db.py`) representing 100% of bytes across all modules with strict contiguous non-overlapping invariants.
  3. **Implement Saturn Detector Registry:** Deploy prioritized detectors for dynamic execution hits (CDL), direct branches, calls, literal pools, pointer tables, MMIO pointers, strings, and padding.
  4. **Enforce Execution Conflict Rule:** Any byte retired by a CPU dynamically cannot remain `DATA` or `UNKNOWN`; it is promoted to `CONFIRMED_CODE` evidence fail-closed. Proven `DATA` cannot be silently decoded as code.
  5. **Execute Fixed-Point Convergence:** Run iterative discovery loop until zero new candidate ranges emerge (converged in 3 passes).
  6. **Honestly Re-Audit Denominator:** Discovered 2,842 newly confirmed executable code bytes (expanding denominator to 60,108 bytes), 81,435 bytes of structured data, and 82,562 bytes of alignment padding, reducing residual `UNKNOWN` by 166,839 bytes with 0 conflicts. Audited proven mnemonic coverage is 92.07% ($\ge 90.00\%$ passing `ASM_90_GATE`).
- **Consequences:**
  - Denominator is factually audited and hardened against coverage inflation.
  - P1 execution gaps in UNKNOWN are reduced to 0.
  - Residual UNKNOWN ranges are cataloged into prioritized recovery campaigns in `workstreams/T2-ASM-CARVER/`.
