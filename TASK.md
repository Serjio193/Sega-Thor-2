# Current task

TASK: T2-ARCH — Freeze Broad C++ Translation and Establish ASM-First Recovery Gate
WHY: Establish mandatory ASM-first recovery strategy per user architectural decision and ADR D-015; freeze broad C++ mechanical recompilation of game code; retain existing C++ blocks bb_06004000 and bb_06004280 strictly as bounded technology/proof specimens; define the mandatory FULL_ASM_GAME_GATE; define round-trip evidence classes (ASM_BYTE_EXACT, ASM_LAYOUT_EXACT, ASM_RUNTIME_VERIFIED, ASM_GAME_BOOT_VERIFIED, ASM_GAMEPLAY_VERIFIED); define planned asm/ directory layout and mechanical assembly rules; define candidate toolchain evaluation rules without proprietary Sega SDK code; define the first bounded ASM round-trip experiment (T2-ASM-01); record M-03 as READY_FOR_BOUNDED_TEST (DEFERRED_BY_ASM_FIRST_ARCHITECTURE); update canonical project documents.
CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
TASK STATUS: PASS (ADR D-015 accepted; broad C++ translation frozen; FULL_ASM_GAME_GATE established; T2-ASM-01 defined)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Architectural decision recorded in docs/DECISIONS.md (ADR D-015); clear boundary established between bounded C++ specimens (retained) and broad C++ translation (frozen); FULL_ASM_GAME_GATE specified with 14 concrete evidence criteria; 5-tier round-trip evidence hierarchy defined; planned asm/ layout defined in docs/FILE_MAP.md; M-03 status decoupled and recorded as READY_FOR_BOUNDED_TEST / DEFERRED_BY_ASM_FIRST_ARCHITECTURE; first bounded ASM round-trip experiment defined; all project documents synchronized; all tests passing (19/19 CTest suites).
ACCEPTANCE CRITERIA:
- [x] audit current DEVELOPMENT_PLAN, TASK, PROJECT_STATE, DECISIONS, and post-D8/D9 records;
- [x] create ADR D-015 establishing ASM_FIRST_RECOVERY as a mandatory architectural constraint;
- [x] explicitly distinguish bounded C++ technology specimens (bb_06004000, bb_06004280 retained) vs broad C++ translation (frozen);
- [x] define mandatory FULL_ASM_GAME_GATE with 14 concrete evidence criteria;
- [x] define round-trip evidence hierarchy (ASM_BYTE_EXACT, ASM_LAYOUT_EXACT, ASM_RUNTIME_VERIFIED, ASM_GAME_BOOT_VERIFIED, ASM_GAMEPLAY_VERIFIED);
- [x] define generated assembly project layout (asm/modules, asm/overlays, asm/include, asm/generated, asm/linker, asm/manifests);
- [x] define mechanical assembly generation rules (exact SH-2 representation, lossless raw data directives for UNKNOWN, provenance tags);
- [x] define toolchain selection rules (bounded reproducibility experiment first, no proprietary/leaked Sega SDK material);
- [x] define first bounded ASM round-trip experiment (T2-ASM-01 on small proven region/module slice);
- [x] update M-03 status to READY_FOR_BOUNDED_TEST / DEFERRED_BY_ASM_FIRST_ARCHITECTURE;
- [x] update all canonical project documents consistently (DEVELOPMENT_PLAN, ROADMAP, ARCHITECTURE, PROJECT_STATE, FILE_MAP, WORKLOG, TASK);
- [x] exactly one next technical task determined: T2-ASM-01 (defined, not executed);
- [x] all documentation and plan validators pass;
- [x] git diff --check green and <= 500 line limits satisfied;
- [x] terminal response in Russian, max 7 bullets.
EVIDENCE AVAILABLE:
- Architectural decision docs/DECISIONS.md (ADR D-015);
- Development plan docs/DEVELOPMENT_PLAN.md (ASM-First Recovery Strategy & FULL_ASM_GAME_GATE);
- Project architecture docs/ARCHITECTURE.md;
- Project roadmap docs/ROADMAP.md;
- Project state docs/PROJECT_STATE.md;
- Workstream record workstreams/T2-D9-indirect/README.md;
- Plan validator tests/recomp/test_d9_plan.py;
- Closure audit validator tests/recomp/test_post_d8_closure.py.
KNOWN UNKNOWNS:
- Candidate assembler and linker toolchain compatibility for exact SH-2 binary layout matching (to be diagnosed in T2-ASM-01).
ALLOWED SCOPE:
- Architectural freeze of broad C++ translation, ADR D-015 authoring, FULL_ASM_GAME_GATE definition, documentation updates, definition of T2-ASM-01.
OUT OF SCOPE:
- Executing T2-ASM-01, deleting C++ proof specimens, broadening C++ translation, executing M-03.

## Last verified result

`T2-ARCH_ASM_FIRST_RECOVERY_GATE_ESTABLISHED`: ADR D-015 accepted; broad C++ mechanical translation frozen until FULL_ASM_GAME_GATE; bounded C++ blocks bb_06004000 and bb_06004280 retained as technology specimens; FULL_ASM_GAME_GATE defined with 14 criteria; 5-tier round-trip hierarchy defined; asm/ layout specified; M-03 recorded as READY_FOR_BOUNDED_TEST / DEFERRED_BY_ASM_FIRST_ARCHITECTURE; exactly one next technical task defined (T2-ASM-01).

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
CURRENT TASK: T2-ARCH — Freeze Broad C++ Translation and Establish ASM-First Recovery Gate
TASK STATUS: PASS (ADR D-015 accepted; broad C++ translation frozen; FULL_ASM_GAME_GATE established; T2-ASM-01 defined)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: ADR D-015 accepted; ASM-first strategy and FULL_ASM_GAME_GATE defined; all canonical documentation synchronized; 19/19 CTest suites pass.
FILES CHANGED: docs/DECISIONS.md, docs/DEVELOPMENT_PLAN.md, docs/ARCHITECTURE.md, docs/ROADMAP.md, docs/PROJECT_STATE.md, docs/FILE_MAP.md, docs/WORKLOG.md, workstreams/T2-D9-indirect/README.md, TASK.md.
TESTS RUN: test_d9_plan.py, test_post_d8_closure.py, test_native_indirect, test_native_dispatcher, 19/19 CTest suites across MinGW and Linux WSL; source file line limit check; git diff --check.
NEW KNOWLEDGE: Broad C++ mechanical translation before complete binary assembly reconstruction introduces high risks of unclassified data and lost literal pools. Rebuilding the entire Sega Saturn game as a reassemblable SH-2 assembly project first ensures complete coverage and bit-exact/layout parity before C++ translation.
OPEN QUESTIONS: Which open toolchain (e.g. GNU as with specific options) provides the closest layout reproduction on SH-2 Saturn binaries without proprietary Sega SDK binaries.
EXACT NEXT ACTION: T2-ASM-01 — First Bounded ASM Round-Trip Experiment (define test slice, assemble with candidate toolchain, compare bytes, verify runtime parity).
