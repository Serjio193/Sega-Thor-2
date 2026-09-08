# AGENTS.md — mandatory Thor 2 project instructions

This is the first document any AI agent or contributor must read before changing the repository.

## Mission

Recover **The Story of Thor 2 / The Legend of Oasis** as a portable C++20 native implementation through evidence-driven reverse engineering, mechanical recompilation, differential verification, and progressive semantic recovery.

The long-term target is a native game implementation, not a universal Sega Saturn emulator.

## Priority order

When priorities conflict, use this order:

1. Legal repository hygiene.
2. Behavioral fidelity to the original game.
3. Reproducible evidence and tests.
4. Verification/oracle correctness.
5. Clear architecture and maintainability.
6. Portability.
7. Performance.
8. Enhancements.

## Non-negotiable project rules

1. Do not change the project goal without an explicit architecture decision recorded in `docs/DECISIONS.md`.
2. Never commit commercial disc images, BIOS files, extracted retail binaries, original assets, save states, RAM dumps, raw traces containing substantial copyrighted data, Ghidra databases containing imported retail bytes, translation-patch payloads, proprietary SDK binaries, leaked/private source trees, or other commercial game data.
3. Treat the original disc image as immutable input.
4. Identify every researched revision by hashes and metadata. Never merge conclusions from PAL/US/JP/patched/translated revisions without explicit provenance.
5. GitHub contains legal-safe source, tooling, configs, tests, hashes/manifests, derived metadata, and documentation. Private/raw laboratory material stays outside GitHub, currently under Google Drive `Thor2/RE_Work` where applicable.
6. Keep human-maintained executable/source/build-code files at **500 lines or fewer**. This includes C/C++ source and headers, tests, developer tooling, Python tools, and build scripts such as CMake. At about 400 lines, evaluate a split before adding another major responsibility. Documentation, worklogs, ADRs, task/state files, and other prose/reference Markdown are exempt. Generated sources may exceed 500 lines only when clearly marked generated; generated local artifacts are not committed unless an explicit project rule requires them.
7. Prefer small modules with one clear responsibility.
8. Work on one active technical result at a time. Only one new methodological experiment may be active at once. Future ideas go to roadmap/backlog; do not casually switch milestones or broaden scope.
9. Do not implement unrelated features while the active task/milestone is unfinished.
10. Every meaningful task must update the project record: `docs/WORKLOG.md`; `docs/REVERSE_ENGINEERING.md` when RE knowledge changes; `docs/DECISIONS.md` when architecture/direction changes; `docs/FILE_MAP.md` when topology/responsibility changes; and `docs/ROADMAP.md` / `docs/PROJECT_STATE.md` when status changes.
11. Every reverse-engineered module/routine/block must retain revision/address/provenance, evidence, assumptions/confidence, and test/verification status.
12. Deterministic translated behavior requires deterministic tests whenever practical. Bugs found in translated behavior should receive regression tests.
13. Preserve original behavior first. Widescreen, HD assets, QoL, remaster features, online features, and other enhancements belong after verified parity unless a documented milestone explicitly says otherwise.
14. Never silently invent unknown game behavior. Mark unknowns and gather evidence.
15. Never replace reverse engineering with a full Saturn CPU/system emulator as the production architecture unless explicitly approved in an ADR. Emulator/interpreter components are allowed as bounded oracle/fallback infrastructure when documented.
16. Keep commits focused: one conceptual task per commit whenever practical.
17. Do not push implementation changes until the locally available CI-equivalent validation is green. When corresponding targets exist, this includes relevant Debug and Release builds/tests, `git diff --check`, the source-file-limit check, and a GNU/Linux-equivalent build/link check for toolchain-sensitive code. If an exact CI toolchain is unavailable, record the limitation and do not claim CI readiness. GitHub Actions must not be the first compile/link test for work-in-progress implementation.
18. Historical SDK/toolchain material is evidence, not authority. Any task using historical assemblers, linkers, compilers, Sega libraries/SDKs, preserved source trees, or fingerprints must follow `docs/RE_TOOLCHAIN_GUIDE.md`. Never claim Ancient used a candidate toolchain/library without project-specific evidence.
19. If a previous implementation, test, classification, or claim is wrong, say so directly, preserve the negative evidence when useful, and record the reason/fix.
20. Do not optimize without measurement.

## Evidence and confidence model

Use explicit states as appropriate:

- `CONFIRMED`
- `HIGH`
- `MEDIUM`
- `LOW`
- `HYPOTHESIS`
- `UNKNOWN`
- `UNVERIFIED`

When useful, track separately:

- `MILESTONE UNDERSTANDING CONFIDENCE`
- `CURRENT SLICE UNDERSTANDING CONFIDENCE`

Do not start or extend semantic production C++ for a concrete slice while `CURRENT SLICE UNDERSTANDING CONFIDENCE < 90%`.

Exception: mechanically generated machine-equivalent code may exist before semantic understanding when its exact instruction semantics and differential contract are independently verified. This exception does not authorize semantic naming or speculative native subsystem design.

Confidence is not optimism. Briefly record what concrete evidence justifies >=90% when semantic production implementation begins.

## Evidence trust must not bootstrap itself

Exact decode/disassembly/reassembly/round-trip is not behavioral proof.

When useful, distinguish trust levels such as:

- `BYTE_OR_ASM_ROUNDTRIP_EXACT` — representation reproduces the source bytes;
- `STATIC_SUPPORTED` — independent static evidence supports code/boundary/role;
- `EXECUTED` — dynamic evidence proves the path/range executed;
- `BEHAVIOR_VERIFIED` — required behavior/state contract was independently checked.

A higher level requires explicit evidence. Weak caller chains cannot recursively promote each other: an incoming edge supports a target only when the edge is exact and the caller already has an independently justified trust level.

## Required lifecycle

Every substantive task follows:

`UNKNOWN -> EVIDENCE -> UNDERSTOOD -> IMPLEMENTED -> VERIFIED -> DOCUMENTED`

Never skip `VERIFIED`. A step is not complete before `DOCUMENTED`.

The detailed task header, stop states, and session checkpoint are mandatory and defined in `AI_DEVELOPMENT_CONTRACT.md`.

## Method validation

External techniques start as `PROPOSED`. They may enter the main Thor 2 pipeline only after a bounded experiment ends as:

- `ADOPT`
- `ADOPT_PARTIAL`

Other valid outcomes:

- `REJECT`
- `DEFER`

Do not combine multiple unproven methods in one experiment; otherwise causality cannot be established.

## Reverse-engineering record

For each important module/routine/basic block record as applicable:

- binary revision/hash;
- disc file and file offset;
- runtime load address;
- module/overlay identity and generation;
- original address/range;
- CPU: Master SH-2 / Slave SH-2 / M68K / SCU DSP;
- callers/callees;
- direct flow;
- unresolved indirect flow;
- inputs/outputs;
- register effects;
- RAM reads/writes;
- MMIO reads/writes;
- DMA/interrupt/timing observations;
- static evidence;
- dynamic evidence;
- confidence/trust level;
- translation status;
- shadow status;
- native override status;
- test status;
- remaining unknowns.

## Saturn executable identity

Guest PC alone may be insufficient.

If runtime evidence shows that RAM can be repopulated with different code, executable identity must include at least:

`revision + CPU + module/overlay generation + guest address`

Do not assume a stable address implies a stable executable body.

## Code/data classification

Use at least:

- `CONFIRMED_CODE`
- `PROBABLE_CODE`
- `UNKNOWN`
- `PROBABLE_DATA`
- `CONFIRMED_DATA`
- `CODE_AND_DATA`
- `PADDING`

Never infer `not executed == data`.

## Function boundaries and naming

- Function boundaries are hypotheses over CFG/evidence, not ground truth from Ghidra or a prologue detector.
- Initial recompilation unit is a basic block, not a guessed function.
- Multiple entries/shared tails are allowed until evidence resolves them.
- Semantic names require evidence; otherwise keep address-based names such as `sub_06009CC4` or `bb_06009CC4`.
- A toolchain/library fingerprint may support a boundary/library hypothesis but does not by itself establish gameplay semantics.

## Mechanical recompilation

1. Keep exact decoded instruction representation separate from higher semantic IR.
2. Unsupported exact IR fails closed.
3. Unknown indirect targets remain runtime-dispatched/fallback.
4. Hardware-visible access is a higher-risk class.
5. A block that can cross an IRQ/DMA/scheduler/device boundary is not automatically atomic.
6. Shadow mode precedes native promotion.
7. In shadow mode the original interpreter/runtime remains authoritative.
8. Promotion requires a declared zero-divergence contract.
9. Rejected candidates stay fallback; do not patch their results to force a pass.
10. Candidate-specific hacks are prohibited unless independent evidence identifies the root cause.

## Verification hierarchy

- `L0` instruction semantic equivalence
- `L1` basic-block CPU-state equivalence
- `L2` memory-effect equivalence
- `L3` scheduler/interrupt/DMA/MMIO equivalence
- `L4` frame/game-state equivalence
- `L5` externally observable equivalence

Every promotion/replacement states its required verification level.

## Oracle rules

- Exact disassembly/reassembly is not behavioral proof.
- Dynamic execution proves a path exists; lack of observation does not prove unreachable.
- Static and dynamic evidence remain distinguishable.
- Emulator output is a practical oracle, not automatically hardware truth.
- Record emulator version/commit/build with traces.
- For critical Saturn semantics prefer two independent checks when practical: documentation/independent emulator/real hardware plus local differential evidence.
- Never change the oracle or a test solely to make a candidate pass. Determine whether implementation, understanding, oracle, or test is wrong.

## AI rules

AI may:

- classify evidence;
- propose boundaries and structures;
- recover candidate types;
- propose semantic names with confidence;
- generate tests;
- mechanically translate verified IR;
- refactor verified mechanical code;
- investigate divergence.

AI may not without verification:

- turn a hypothesis into fact;
- assign confident semantic names;
- alter machine semantics;
- alter timing contracts;
- alter the oracle to make a candidate pass;
- remove fallback;
- replace a Saturn subsystem in production.

## Required workflow for every task

Before substantive implementation:

1. Read `docs/PROJECT_VISION.md`.
2. Read `docs/ROADMAP.md` and identify the active milestone/task.
3. Read `docs/ARCHITECTURE.md`.
4. Read `docs/FILE_MAP.md`.
5. Read the latest relevant `docs/WORKLOG.md` and `docs/DECISIONS.md` entries.
6. Read `AI_DEVELOPMENT_CONTRACT.md` and `docs/DEVELOPMENT_RULES.md`.
7. If historical SDK/toolchain/compiler/library evidence is involved, read `docs/RE_TOOLCHAIN_GUIDE.md` before drawing conclusions.
8. Record the concrete task, confidence, scope, unknowns, and acceptance criteria in `TASK.md` / the active workstream record before production code changes.

During work:

1. Work only on the active task.
2. Keep human-maintained source/build/test/tool files within the 500-line policy.
3. Add/update deterministic tests alongside translated logic when practical.
4. Record RE discoveries and provenance as they are established.
5. Avoid speculative refactors/frameworks unrelated to the active task.
6. Preserve failed experiments and divergences when they materially constrain future work.

After work:

1. Run the relevant Debug/Release/tests and CI-equivalent checks available for the changed surface.
2. Run `git diff --check` and the source-file-limit check before push when working from a local checkout.
3. Run a GNU/Linux-equivalent build/link check when portability/toolchain-sensitive code is affected and such a target exists.
4. Update `docs/WORKLOG.md` with results, limitations, and remaining unknowns.
5. Update `docs/FILE_MAP.md` if structure/responsibility changed.
6. Update `docs/ROADMAP.md` / `docs/PROJECT_STATE.md` if status moved.
7. Record any architectural decision.
8. Update `TASK.md` with the session checkpoint and exact next action.
9. Push only after the available pre-push validation is green; record unavailable validation honestly.

## Documentation set

Maintain:

- `TASK.md`
- `AI_DEVELOPMENT_CONTRACT.md`
- `docs/PROJECT_STATE.md`
- `docs/PROJECT_VISION.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/WORKLOG.md`
- `docs/DECISIONS.md`
- `docs/REVERSE_ENGINEERING.md`
- `docs/FILE_MAP.md`
- `docs/PIPELINE_VALIDATION_PLAN.md`
- `docs/DEVELOPMENT_RULES.md`
- `docs/RE_TOOLCHAIN_GUIDE.md`

## Commit prefixes

Use a simple prefix where useful:

- `core:`
- `saturn:`
- `game:`
- `tools:`
- `tests:`
- `docs:`
- `build:`
- `re:`

## Definition of done

A task is DONE only when:

- the claimed result exists;
- acceptance criteria are met;
- behavior is tested/verified at the required level, or explicitly `UNVERIFIED` when the task permits that state;
- evidence location is recorded;
- documentation/project record is updated;
- architecture/file map remains accurate;
- source-file policy is satisfied;
- no commercial/private prohibited material entered GitHub;
- remaining unknowns are listed;
- the exact next action is stated.

## Governing question

Before every change ask:

**What exactly does this change prove, reproduce, or make testable relative to original Thor 2 behavior?**

If there is no clear answer, the change is not yet needed.
