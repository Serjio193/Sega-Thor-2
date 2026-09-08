# Development Rules

This document adapts the general development discipline from `Serjio193/Sega-Thor` to the Sega Saturn / Thor 2 project.

## Source limits

- Hard limit: **500 lines per human-maintained executable/source-code file**, including C/C++ source and headers, tests, developer tooling, Python tools, and build scripts such as CMake.
- Documentation, project instructions, worklogs, ADRs, task/state files, and other prose/reference Markdown are exempt from the numeric line limit.
- At about 400 lines in a source-code file, evaluate a split before adding another major responsibility.
- Generated source may exceed 500 lines only when clearly marked generated and produced from a reproducible generator/input contract.
- Generated local artifacts, binary dumps, raw traces, extracted retail data, temporary disassembly, and build outputs are not source and must not be committed unless an explicit project rule says otherwise.

## C++ rules

- Standard: **C++20**.
- Prefer explicit ownership and value semantics.
- Prefer fixed-width integer types for guest/hardware-visible values.
- Prefer RAII and standard containers/views such as `std::array`, `std::vector`, and `std::span` where appropriate.
- Avoid global mutable state unless it mirrors a documented guest/hardware state and is wrapped behind a deliberate interface.
- Avoid macros for program logic.
- Avoid inheritance-heavy designs unless a concrete game-system need is proven.
- Avoid premature framework abstractions.
- Keep host platform APIs outside recovered game logic.
- Preserve Saturn address, width, alignment, sign-extension, endian, and wraparound semantics explicitly at guest/native boundaries.
- Do not replace a guest-visible pointer/address with a host pointer until ownership, lifetime, address semantics, and verification contract are understood.
- Preserve original provenance in transitional representations where useful (`GuestAddress`, module identity, original offsets, etc.).

## Naming

- Names describe evidenced meaning, not guessed meaning.
- Unknown routines/blocks keep address-based names such as `sub_06009CC4` or `bb_06009CC4` until evidence supports a semantic rename.
- Every important semantic rename should be reflected in the RE record with supporting evidence.
- Hardware constants retain documented Saturn addresses/bit meanings where useful.
- Toolchain/library matches do not automatically justify gameplay-semantic names.

## Reverse-engineering discipline

For translated/recovered objects, record as applicable:

- revision/hash;
- module/disc origin;
- original address/range;
- CPU;
- known callers/callees;
- inputs/outputs;
- register/memory/MMIO side effects;
- DMA/interrupt/timing interaction;
- evidence source;
- confidence/trust level;
- translation/override status;
- test status;
- unresolved questions.

Confidence and trust are distinct when needed. A range may be byte-exact yet behaviorally unverified.

## Evidence integrity

- Exact decoding, exact assembly, exact file split, or byte-identical rebuild proves representation/layout correspondence, not full behavior.
- `not observed` does not mean `not code` or `unreachable`.
- Do not promote confidence through circular caller/callee reasoning.
- When an evidence source is invalidated, downgrade dependent conclusions and record the change.
- Candidate scores/rankings are prioritization aids, not proof.
- Prefer explicit evidence counts/reasons over opaque confidence percentages unless a scoring model is defined and validated.

## Testing

- Build/tests must remain green after every completed implementation task.
- Deterministic translated routines require unit/differential tests when practical.
- Bugs discovered in translated behavior should receive regression tests.
- Tests committed to public CI must not require copyrighted retail game content unless a future explicit private mechanism is approved.
- Synthetic byte sequences, synthetic machine states, and minimal generated fixtures are preferred for public deterministic tests.
- Differential tests should compare the smallest useful contract: exact registers/flags/PC/memory effects first, broader frame/output state only when needed.
- Never weaken a test solely because production code fails it.

## Build and pre-push validation

For implementation changes, use the strongest locally available CI-equivalent validation. Once corresponding build targets exist, normally run:

1. relevant Debug build/tests;
2. relevant Release build/tests;
3. `git diff --check`;
4. source-code 500-line policy check;
5. GNU/Linux-equivalent build/link check for CMake/link-order/portability/toolchain-sensitive changes.

If an exact toolchain/platform is unavailable, record the limitation. Do not claim CI readiness that was not tested. GitHub Actions should confirm locally tested work, not be the first compile/link attempt.

## Documentation

Every meaningful task updates at least one project record, and all applicable records must remain synchronized:

- `docs/WORKLOG.md` — what was done and how it was verified;
- `docs/REVERSE_ENGINEERING.md` — what was learned about the original game;
- `docs/DECISIONS.md` — why architecture/direction changed;
- `docs/FILE_MAP.md` — where responsibilities live;
- `docs/ROADMAP.md` / `docs/PROJECT_STATE.md` — milestone/status changes;
- `TASK.md` — active bounded task/checkpoint.

Code comments are not a replacement for project documentation.

## Commits and PRs

Use a simple prefix where useful:

- `core:`
- `saturn:`
- `game:`
- `tools:`
- `tests:`
- `docs:`
- `build:`
- `re:`

Keep commits single-purpose when practical.

A PR description should include:

1. goal;
2. exact scope;
3. evidence used;
4. tests/verification run;
5. documentation updated;
6. known unknowns/limitations;
7. exact next step.

## Scope control

Do not add these to the production architecture before their validated roadmap point or an explicit ADR:

- generalized Sega Saturn emulator runtime;
- runtime JIT as a shortcut around bounded static/mechanical proof;
- modern renderer replacement before renderer contracts are understood;
- modern audio replacement before sound contracts are understood;
- ECS framework;
- scripting-language replacement;
- HD assets/remaster pipeline;
- widescreen gameplay changes;
- online/network features;
- large engine/framework rewrites unrelated to the current proof;
- removal of interpreter/oracle fallback before the relevant coverage/contract is proven.

## No silent assumptions

If a value or behavior is uncertain, use explicit markers such as:

`UNKNOWN`, `HYPOTHESIS`, `UNVERIFIED`, `PROBABLE_CODE`, or another project-defined confidence state.

Never turn a hypothesis into a semantic API/type/name without recording the evidence.

## Stop conditions

Stop the current implementation path and document/research when:

- a boundary/identity needed for the implementation is uncertain;
- two revisions appear to disagree materially and provenance is unresolved;
- the proposed implementation requires guessing behavior;
- an indirect target set cannot be bounded safely;
- an IRQ/DMA/device/other-CPU interaction makes the assumed atomic contract uncertain;
- a dependency would materially change architecture;
- current verification cannot distinguish success from failure;
- the next step would require proprietary/leaked SDK/tool material;
- the active task would need to expand scope to proceed.

The response to uncertainty is bounded investigation and documentation, not feature drift.
