# Worklog

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
