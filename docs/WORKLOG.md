# Worklog

## 2026-09-09 — T2-V01 SaturnAutoRE / Mednafen Setup + V-01-core Execution

### Task

Establish the local pinned SaturnAutoRE / Mednafen debug environment and execute the first `V-01-core` bounded emulator observation on canonical Thor 2 media (`fe11d2fb...`).

### Method

1. Cloned `AJBats/SaturnAutoRE` (commit `4662aad69f95222fe37c5e6b98f2285b1a7e4653`) and verified `mednafen` submodule (commit `155426661b7ac3152e2c93a98da60ac33002b908`) into external sibling directory `e:\Github\SaturnAutoRE`.
2. Inspected build instructions: native Linux build per `BUILD_WINDOWS.md` line 84 executed without source code modification using system GCC 13.3.0 in WSL Ubuntu 24.04.
3. Verified retail firmware candidates in local environment: `mpr-17933.bin` (SHA-256: `96e106f740ab448cf89f0dd49dfbac7fe5391cb6bd6e14ad5e3061c13330266f`, NA/EU v1.00) and `sega_101.bin` (SHA-256: `dcfef4b99605f872b6c3b6d05c045385cdea3d1b702906a0ed930df7bcb7deac`, JP v1.01). Verified untracked status.
4. Inspected Mednafen region logic: canonical disc header contains `JTU` and security strings for JP, Asia, and NA; Mednafen autodetects region `0x4` (`SMPC_AREA_NA`) by preference order and selects `mpr-17933.bin`.
5. Pinned 19-parameter configuration recipe in `workstreams/T2-V01-dynamic-oracle/environment_pin.yaml`.
6. Executed two independent cold-boot runs (`RUN_A` and `RUN_B`) in isolated environments (`/tmp/t2_v01_run_a`, `/tmp/t2_v01_run_b`) with zero reused state.

### Results

- **PASS (`V01_CORE_BOUNDED_PROOF`)**: 100% identical match across all declared comparison fields between Run A and Run B.
- **Entry Point**: Master SH-2 entered `0TH2.BIN` boot entry `0x06004000` at frame 680, cycle `305462360` (breakpoint hit: `break pc=0x06004002 addr=0x06004000`).
- **Architectural State**: All 23 CPU registers matched identically across runs (SP: `0x06001000`, SR: `0x00000001`, VBR: `0x06000000`).
- **Instruction Transition**: `step 1` advanced PC to `0x06004004` and cycle count to `305462361` (+1 cycle) identically across runs.
- **Memory Effect**: Instruction at `0x06004006` (`mov.l @r4, r4`) performed a 32-bit `MEMORY_READ` from `0x06081C10`, reading value `0x060917DC` identically across runs.
- **Cheap Census**: Master SH-2 active; Slave SH-2 inactive (`active=0`, PC=0); sound disabled via `--sound 0`.
- **Classification Promotion**: `0TH2.BIN` entry at `0x06004000` promoted to `CONFIRMED_CODE / EXECUTED`.
- **Decision D-009**: `ADOPT` bounded Mednafen oracle capability for Thor 2.
- Autonomous RE pipeline (`V-01-automation`) remains deferred.

### Exact next action

Review V-01-core evidence before authorizing V-01-automation.

## 2026-09-09 — V-01-core preflight and blocker proof

### Task

Begin the bounded D1 / V-01-core emulator observation without starting SaturnAutoRE automation or `TH2.LOW` provenance work.

### Preflight performed

- Rehashed the mounted canonical Thor 2 BIN/CUE and confirmed exact T2-M0 identities:
  - image SHA-256 `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8`;
  - CUE SHA-256 `afc0b101bbb493adbd43fd44ffd76959484d67cf0b566137dd145f1c68d411e0`.
- Pinned `AJBats/SaturnAutoRE` at `4662aad69f95222fe37c5e6b98f2285b1a7e4653`.
- Pinned its Mednafen debug submodule `AJBats/mednafen-saturn-debug` at `155426661b7ac3152e2c93a98da60ac33002b908`.
- Confirmed that the pinned debug fork documents Master/Slave register dumps, stepping/breakpoints, cache-aware memory reads, write watchpoints, and cycle/event metadata suitable for the planned bounded observation.
- Checked the mounted private paths and connected Drive for the common Mednafen Saturn BIOS filenames and Saturn-BIOS/Mednafen candidates.

### Blocker

Mednafen's Saturn core requires a Saturn BIOS. No user-owned Saturn BIOS is available in the private workspace checked, and no Mednafen executable is installed in the current execution environment. The source candidate is pinned, but a runnable binary hash/build configuration cannot be completed before the runtime environment is prepared.

The project will not source proprietary Saturn BIOS bytes from public download sites.

This is an objective input blocker, not a Mednafen failure. V-01-core has not executed and no `ADOPT`, `ADOPT_PARTIAL`, or `REJECT` decision is justified.

### Result

`V01_CORE_PRE_EXECUTION_BLOCKED_BIOS`

D1 remains `READY_FOR_BOUNDED_TEST`; current task stop state is `BLOCKED`.

Evidence/config is recorded in `workstreams/T2-V01-dynamic-oracle/`.

### Exact next action

Provide a legally owned Saturn BIOS privately; hash it and pin effective region/BIOS/build configuration, then resume V-01-core with two independently initialized cold-boot observations.

## 2026-09-09 — T2-P0.1 Dual-Track Proof-Contract Repair

### Task

Apply adversarial review corrections to proof contracts and gates in `docs/DEVELOPMENT_PLAN.md`, `docs/PIPELINE_VALIDATION_PLAN.md`, `docs/ROADMAP.md`, `docs/PROJECT_STATE.md`, `docs/DECISIONS.md`, and `TASK.md`.

### Finding

The T2-P0 dual-track model correctly separated capabilities from candidate methods, but had remaining proof-contract ambiguities:
- conflated running a bounded experiment with whole-capability completion (`V-xx PASS` vs `Dxx DONE`);
- bundled Mednafen observation with SaturnAutoRE automation and `TH2.LOW` provenance in V-01;
- lacked explicit separation between SH-2 decode correctness, instruction execution semantics, and memory access semantics (L0);
- lacked pre-D8 executable identity invalidation guards and machine event safety (`PRE_D8_MINIMUM_EVENT_SAFETY`);
- lacked negative-control validation for the shadow comparison checker (V-07B);
- placed an unnecessary unconditional D1 dependency on static resource round-trips.

### Changes

- **Capability scope states:** Formalized `PROPOSED`, `READY_FOR_BOUNDED_TEST`, `BOUNDED_PROOF`, `EXPANDED_PROOF`, and `DONE` in `DEVELOPMENT_PLAN.md`, `PIPELINE_VALIDATION_PLAN.md`, and ADR `D-008`.
- **V-01 split:** Separated into `V-01-core` (19-parameter pinned boot observation) and `V-01-automation` (SaturnAutoRE scripting). Explicitly removed `TH2.LOW` provenance from V-01 PASS criteria (queued under D2 / `V-02b`).
- **D2 / V-02 scoping:** Split into `V-02a` (`0TH2.BIN`) and `V-02b` (`TH2.LOW`); one path pass = one path proven (`D2 BOUNDED_PROOF`), not whole capability DONE.
- **L0 Semantic Gate:** Mandated independent synthetic edge-case tests separating decode correctness from instruction and memory execution semantics.
- **Pre-D8 Guards:** Added executable identity invalidation guard (backing RAM changes invalidate translation; no silent cache patching) and `PRE_D8_MINIMUM_EVENT_SAFETY` (verified absence of observable machine event boundaries).
- **V-07 split:** Split into `V-07A` (transition proof), `V-07B` (shadow checker validation with 5 negative controls and pre-state isolation), and `V-07C` (real native override proof with metrics).
- **D14 / V-11 relaxed:** Pure structural resource round-trip permitted from D0 static evidence; `BYTE_ROUNDTRIP_EXACT` requires zero byte differences.
- **Publication gate:** Clarified that repository hygiene is an ongoing publication gate, not permanently solved by `.gitignore`.
- **TASK.md:** Completed T2-P0.1 and queued `D1` / `V-01-core` as exact next task.

### Result

`DUAL_TRACK_MODEL_REPAIRED`.
`V01_CORE_READY`.

### Exact next action

Execute V-01-core bounded emulator observation.

## 2026-09-09 — T2-P0 Dual-Track Development / Verification Plan Hardening

### Task

Harden the project planning model into two explicit, synchronized tracks:
1. Development Track: capability-oriented milestones D0–D18 in dependency order.
2. Verification / Adoption Track: method/component experiments V-01–V-14 with smallest falsifiable gates.

### Finding

The prior planning model:
- conflated required project capabilities with specific external tools (e.g. M1 named after SaturnAutoRE);
- bundled 8 independent Saturn hardware subsystems into a single phase (SaturnRecomp);
- lacked fallback routes for when an external tool is rejected;
- lacked an explicit risk/proof map showing when Saturn uncertainties become blocking.

### Changes

- added `docs/DEVELOPMENT_PLAN.md` with capability milestones D0–D18, critical-path dependency graph, risk/proof map for 13 Saturn risks, coupling matrix, and failure scenario analysis;
- rewrote `docs/PIPELINE_VALIDATION_PLAN.md` with structured experiment specifications V-01–V-14 (falsifiable hypotheses, minimum experiments, pass/fail criteria, divergence classifications);
- rewrote `docs/ROADMAP.md` as a concise indexed roadmap connecting D0–D18 with V-01–V-14;
- updated `docs/PROJECT_STATE.md` with the dual-track status;
- accepted ADR `D-008` in `docs/DECISIONS.md`;
- updated `docs/FILE_MAP.md`;
- updated `TASK.md` checkpoint.

### Evaluation of M1 / V-01

Evaluated SaturnAutoRE dynamic-oracle validation:
- conclusion: `M1_READY_WITH_SMALLER_SCOPE`.
- SaturnAutoRE automation is decoupled from Mednafen oracle viability: if SaturnAutoRE Python scripts fail on this image, Mednafen itself can still be evaluated as the dynamic oracle (`ADOPT_PARTIAL`).
- First target claim remains observing boot execution in `0TH2.BIN` and attempting `TH2.LOW` provenance confirmation.

### Result

`DUAL_TRACK_PLAN_ESTABLISHED`.
`M1_READY_WITH_SMALLER_SCOPE`.

### Exact next action

Prepare the bounded V-01 experiment: pin Mednafen version, define minimal boot observation, and test reproducibility.

## 2026-09-09 — Sega-Thor rules-transfer audit

### Task

Re-audit the first project's governance and ensure every transferable development/RE rule is present in Sega-Thor-2.

### Sources audited

- `Serjio193/Sega-Thor/AGENTS.md`
- `Serjio193/Sega-Thor/AI_DEVELOPMENT_CONTRACT.md`
- `Serjio193/Sega-Thor/docs/DEVELOPMENT_RULES.md`
- `Serjio193/Sega-Thor/docs/RE_TOOLCHAIN_GUIDE.md`
- `Serjio193/Sega-Thor/docs/EVIDENCE_INTEGRITY_AUDIT.md`
- `Serjio193/Sega-Thor/CONTRIBUTING.md`
- first-project `TASK.md` task/checkpoint discipline

### Finding

The initial Thor 2 bootstrap transferred the core RE philosophy well but was incomplete as an operational development contract.

Missing/weaker items included:

- hard 500-line source/build/test/tool limit;
- mandatory task header;
- blocker proof and explicit stop states;
- session checkpoint;
- before/during/after task workflow;
- local CI-equivalent pre-push gate;
- detailed C++20/ownership/portability rules;
- regression-test rule for discovered behavioral bugs;
- PR description contract;
- Saturn-adapted historical SDK/toolchain evidence boundary;
- explicit separation of exact round-trip/static/executed/behavior-verified trust;
- prohibition on weak caller chains bootstrapping confidence;
- explicit correction record when a prior claim/implementation is wrong;
- contributor/task governance files.

### Changes

- strengthened `AGENTS.md`;
- added `AI_DEVELOPMENT_CONTRACT.md`;
- added `docs/DEVELOPMENT_RULES.md`;
- added `docs/RE_TOOLCHAIN_GUIDE.md`;
- added `docs/RULES_TRANSFER_AUDIT.md`;
- added `TASK.md`;
- added `CONTRIBUTING.md`;
- updated `docs/FILE_MAP.md`.

Mega Drive-specific active direction, addresses, milestone IDs, and the old prohibition on Thor 2 work were intentionally not copied. Their governing concepts were adapted to Saturn where applicable.

### Verification

Manual rule-by-rule cross-audit against the first-project governance sources. No production code/build target changed in this task, so Debug/Release build validation is not applicable. Repository contents remain legal-safe documentation/metadata/source only.

### Result

`COMPLETE FOR TRANSFERABLE GOVERNANCE RULES`.

### Exact next action

Start only the queued `T2-M1 — SaturnAutoRE Dynamic-Oracle Validation` bounded experiment. Do not combine recompilation, SaturnRecomp adoption, or another unproven method into T2-M1.

---

## 2026-09-08/09 — Project bootstrap and T2-M0

### Repository foundation

- Created legal-safe GitHub foundation.
- Adapted evidence/verification rules from `Serjio193/Sega-Thor` for Saturn.
- Established one-method-at-a-time validation and explicit `ADOPT/ADOPT_PARTIAL/REJECT/DEFER` outcomes.
- Set T2-M0 as the first and only active workstream.

### T2-M0 results

Implemented `tools/disc/census_saturn_cd.py` using only Python standard library.

The tool:

- validates the supported single-track CUE shape;
- reads raw `MODE1/2352` sectors;
- parses Saturn boot header fields;
- parses ISO9660 directory records;
- hashes logical file extents without extracting retail files;
- emits legal-safe manifest/summary metadata.

Validation performed:

- independent census run 1;
- independent census run 2;
- `disc_manifest.tsv` identical between runs;
- summary output identical between runs;
- three synthetic unit tests pass.

Confirmed substrate:

- revision ID `thor2_ntsc_patched_fe11d2fb`;
- image SHA-256 `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8`;
- 33 ISO9660 files;
- manifest SHA-256 `19b56fd0fefa42c23edac055cd5e817a7a4834b7d7b423cef15a27de4bc80f49`.

Static executable-candidate work found:

- `0TH2.BIN` -> candidate High Work RAM base `0x06004000`;
- `TH2.LOW` -> strong static candidate Low Work RAM base `0x002DA000`;
- `TH2.LOW` relationship documented without declaring callee semantics confirmed.

### Decision

T2-M0 acceptance gate is satisfied using direct extent hashing instead of persisting extracted retail files. This reduces private-data duplication while retaining reproducibility.

### Next queued experiment

`T2-M1 — SaturnAutoRE dynamic-oracle validation`.

It must first prove one deterministic Thor 2 observation before any SaturnAutoRE component is adopted.
