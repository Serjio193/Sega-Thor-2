# Current task

TASK: D1 — Deterministic Dynamic Oracle (V-01-core Bounded Emulator Observation)
WHY: establish reproducible dynamic execution observation of Thor 2 from a fixed canonical start recipe before attempting executable provenance, decode, or code translation.
CURRENT MILESTONE: D1 / V-01-core
TASK STATUS: READY_FOR_BOUNDED_TEST
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 90%
SLICE CONFIDENCE EVIDENCE: T2-M0 established canonical disc bytes and boot metadata; T2-P0.1 tightened V-01-core to a 19-parameter pinned boot observation contract; TH2.LOW removed from D1 gate.
ACCEPTANCE CRITERIA:
- pin exact Mednafen version/commit, build hash/flags, and complete 19-parameter configuration recipe;
- execute canonical boot recipe for Thor 2 image `fe11d2fb...`;
- observe at least one bounded CPU-labelled execution transition in `0TH2.BIN` boot code with explicit event semantics;
- observe at least one selected memory effect (address, width, value);
- reproduce the exact observation identically across at least two independent cold-boot runs;
- record emulator version, CPU identity (Master SH-2), and observation semantics without committing copyrighted bytes;
- decide `ADOPT`, `ADOPT_PARTIAL`, `REJECT`, or `DEFER` for Mednafen oracle capability.
EVIDENCE AVAILABLE:
- canonical revision `thor2_ntsc_patched_fe11d2fb` and manifest `disc_manifest.tsv`;
- `0TH2.BIN` candidate mapped range `0x06004000..0x06086BFF`;
- Saturn header first-read `0x06004000`, master stack `0x06001000`;
- tightened V-01-core experiment definition in `docs/PIPELINE_VALIDATION_PLAN.md`.
KNOWN UNKNOWNS:
- exact Mednafen build / execution flags that produce deterministic execution on this host;
- exact Master SH-2 PC sequence during initial boot transition before main loop.
ALLOWED SCOPE:
- bounded Mednafen execution under pinned configuration;
- observing boot transition in `0TH2.BIN` candidate range;
- recording legal-safe configuration and observation logs outside git;
- committing only legal-safe evidence summaries and configs.
OUT OF SCOPE:
- executing SaturnAutoRE automation scripts (V-01-automation is a later sub-gate);
- observing or verifying `TH2.LOW` provenance (belongs to D2 / V-02b);
- implementing SH-2 decoder or translator;
- native runtime or subsystem implementation;
- committing ROMs, BIOS, save states, or raw execution traces.

## Last verified result

T2-P0.1 dual-track proof-contract repair completed.

## Session checkpoint

CURRENT MILESTONE: T2-P0.1 completed; D1 / V-01-core ready
CURRENT TASK: D1 — Deterministic Dynamic Oracle (V-01-core Bounded Emulator Observation)
TASK STATUS: READY_FOR_BOUNDED_TEST
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 90%
LAST VERIFIED RESULT: T2-P0.1 proof-contract repair complete; capability states formalized; pre-D8 guards established
FILES CHANGED: docs/DEVELOPMENT_PLAN.md, docs/PIPELINE_VALIDATION_PLAN.md, docs/ROADMAP.md, docs/PROJECT_STATE.md, docs/DECISIONS.md, docs/WORKLOG.md, TASK.md
TESTS RUN: git diff --check; source line limit check; documentation consistency checks
NEW KNOWLEDGE: decoupled V-01-core from automation; removed TH2.LOW from V-01; introduced L0 execution/memory semantics gate; added pre-D8 identity guard and PRE_D8_MINIMUM_EVENT_SAFETY; split V-07 into V-07A/B/C; relaxed D14 static round-trip
OPEN QUESTIONS: which exact Mednafen binary build will be used as the pinned baseline for V-01-core?
BLOCKERS: none
EXACT NEXT ACTION: Execute V-01-core bounded emulator observation.
