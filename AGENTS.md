# AGENTS.md — Thor 2 project rules

## Mission

Recover **The Story of Thor 2 / The Legend of Oasis** as a portable native implementation through evidence-driven reverse engineering, mechanical recompilation, differential verification, and progressive semantic recovery.

The final goal is a native game implementation, not a universal Sega Saturn emulator.

## Priority order

1. Legal repository hygiene.
2. Behavioral fidelity.
3. Reproducible evidence.
4. Verification/oracle correctness.
5. Clear architecture.
6. Portability.
7. Performance.
8. Enhancements.

## Repository hygiene

- Never commit commercial disc images, BIOS files, extracted retail binaries, original assets, save states, RAM dumps, raw traces containing substantial copyrighted data, Ghidra databases containing imported retail bytes, or translation-patch payloads.
- Treat the original disc image as immutable input.
- Identify every researched revision by hashes and metadata.
- Never merge conclusions from PAL/US/JP/patched/translated revisions without explicit provenance.
- Google Drive `Thor2/RE_Work` is the private laboratory store. GitHub contains only legal-safe source, tools, configs, tests, derived metadata, and documentation.

## Evidence model

Use explicit states:

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

Do not write semantic production C++ for a concrete slice while `CURRENT SLICE UNDERSTANDING CONFIDENCE < 90%`.

Exception: mechanically generated machine-equivalent code may exist before semantic understanding if its instruction semantics and differential contract are independently verified.

## Required lifecycle

Every substantive task follows:

`UNKNOWN -> EVIDENCE -> UNDERSTOOD -> IMPLEMENTED -> VERIFIED -> DOCUMENTED`

Never skip `VERIFIED`.

## One experiment at a time

Only one new methodological experiment may be active at once.

External techniques start as `PROPOSED`. They may enter the main pipeline only after a bounded Thor 2 experiment ends as:

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
- confidence;
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

## Function boundaries

- Function boundaries are hypotheses over CFG/evidence, not ground truth from Ghidra.
- Initial recompilation unit is a basic block, not a guessed function.
- Multiple entries/shared tails are allowed until evidence resolves them.
- Semantic names require evidence; otherwise keep address-based names such as `sub_06009CC4` or `bb_06009CC4`.

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

## Testing rules

- Deterministic transformations require deterministic tests.
- Never change a test merely to make an incorrect implementation pass.
- Preserve negative results and divergence artifacts.
- No candidate-specific hacks without evidence for the root cause.
- Do not optimize before measurement.

## Source discipline

- Human-maintained C/C++/Python/build/test files should stay under 500 lines; around 400 lines, evaluate splitting.
- One module, one clear responsibility.
- Generated sources may exceed this when clearly marked generated.

## Documentation set

Maintain:

- `docs/PROJECT_STATE.md`
- `docs/PROJECT_VISION.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/WORKLOG.md`
- `docs/DECISIONS.md`
- `docs/REVERSE_ENGINEERING.md`
- `docs/FILE_MAP.md`
- `docs/PIPELINE_VALIDATION_PLAN.md`

## Commit prefixes

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
- verification ran, or the result is explicitly `UNVERIFIED`;
- evidence location is recorded;
- documentation is updated;
- remaining unknowns are listed;
- no commercial material entered GitHub;
- the exact next action is stated.

## Governing question

Before every change ask:

**What exactly does this change prove, reproduce, or make testable relative to original Thor 2 behavior?**

If there is no answer, the change is not yet needed.
