# Current task

TASK: POST-D8 / M-02.1 / M-07 — SaturnRecomp SH-2 Reference Corpus Experiment
WHY: Repair M-02 fail-closed range/spec and restore precondition safety; audit pinned SaturnRecomp source (commit 26c9715e5493054b8a205aa31d73d8f125fdd8f5); evaluate available SH-2 reference assets; build external decoder probe adapter; cross-check 6 startup overlap opcodes and 14 future-expansion synthetic probe opcodes; cross-check execution semantics against Hitachi manual and Mednafen oracle; build machine-readable reference manifest and project-side automated test with fail-closed negative controls; assign dispositions under ADR D-012.
CURRENT MILESTONE: POST-D8 Second-Pass Method Experiments (docs/POST_D8_SECOND_PASS_PLAN.md / ADR D-012)
TASK STATUS: PASS (M-02.1: RANGE_AND_RESTORE_SAFETY_VERIFIED; M-07A: ADOPT_PARTIAL; M-07B: NOT_PRESENT_AT_PIN; POST_D8: ACTIVE)
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Pinned SaturnRecomp commit 26c9715e5493054b8a205aa31d73d8f125fdd8f5 audited; M-07A (decoder & execution-semantic reference corpus) verified present; M-07B (public AOT emitter) verified absent at pin; zero foreign code vendored into Sega-Thor-2; M-02.1 fail-closed range/spec checks and restore precondition verified across 7 new regressions; 6 startup overlap opcodes verified with 0 decode disagreements; 14 future-expansion synthetic probe opcodes verified with 0 decode or semantic disagreements; external health check (tests/sh2_semantics) passed (39/39); derived legal-safe manifest and automated test with 9 fail-closed negative controls implemented; 14/14 CTest suites passing on Windows MinGW and Linux WSL (Debug and Release).
ACCEPTANCE CRITERIA:
- [x] repair M-02 fail-closed range/spec and restore precondition safety;
- [x] pin external SaturnRecomp commit 26c9715e5493054b8a205aa31d73d8f125fdd8f5;
- [x] audit actual assets: M-07A (decoder/semantics present) vs M-07B (AOT emitter absent);
- [x] maintain zero vendoring / zero copying of foreign source into Sega-Thor-2;
- [x] implement reproducible external decoder probe adapter (tools/recomp/saturnrecomp_adapter.py);
- [x] cross-check 6 startup block (bb_06004000) opcodes (0 disagreements across 4 sources);
- [x] cross-check 14 future-expansion synthetic probe opcodes (0 disagreements across sources);
- [x] run SaturnRecomp semantic self-test health check (39/39 passing);
- [x] cross-check representative semantic edge cases against Hitachi manual and Mednafen (0 disagreements);
- [x] create derived legal-safe reference manifest (workstreams/POST-D8-M07-saturnrecomp/reference_vectors.json);
- [x] implement project-side automated test (tests/recomp/test_m07_reference.py);
- [x] verify 9 fail-closed negative controls (100% detection rate);
- [x] assign dispositions: M-07A (ADOPT_PARTIAL), M-07B (NOT_PRESENT_AT_PIN);
- [x] update POST_D8_SECOND_PASS_PLAN.md with closure audit gate;
- [x] 14/14 unit test suites passed across Windows MinGW and Linux WSL (Debug and Release);
- [x] all human-maintained source/test/tool files <= 500 lines;
- [x] terminal response only in Russian, max 7 bullets.
EVIDENCE AVAILABLE:
- Workstream record workstreams/POST-D8-M07-saturnrecomp/README.md;
- Workstream record workstreams/POST-D8-M07-saturnrecomp/experiment_evidence.md;
- Reference manifest workstreams/POST-D8-M07-saturnrecomp/reference_vectors.json;
- Probe adapter tools/recomp/saturnrecomp_adapter.py;
- Automated test tests/recomp/test_m07_reference.py;
- Second-pass plan docs/POST_D8_SECOND_PASS_PLAN.md.
KNOWN UNKNOWNS:
- Multi-block recompilation scaling for D9.
ALLOWED SCOPE:
- Bounded evaluation of SaturnRecomp SH-2 reference corpus;
- M-02.1 fail-closed range and restore safety repair.
OUT OF SCOPE:
- Starting D9 multi-block scaling before POST-D8 closure audit;
- Copying/vendoring foreign source into Sega-Thor-2.

## Last verified result

`T2-POST-D8.2_M07_ADOPT_PARTIAL`: Evaluated SaturnRecomp commit 26c9715e5493054b8a205aa31d73d8f125fdd8f5 under ADR D-012; M-02.1 range/spec and restore safety repair completed with 7 regressions; M-07A adopted partially as DECODER_AND_SEMANTIC_REFERENCE (20 opcodes evaluated, 0 decode disagreements, 0 semantic disagreements, 9 negative controls verified); M-07B determined NOT_PRESENT_AT_PIN (no public AOT emitter); 14/14 CTest suites passing on Windows MinGW and Linux WSL.

## Session checkpoint

CURRENT MILESTONE: POST-D8 Second-Pass Method Experiments (docs/POST_D8_SECOND_PASS_PLAN.md / ADR D-012)
CURRENT TASK: POST-D8 / M-02.1 / M-07 — SaturnRecomp SH-2 Reference Corpus Experiment
TASK STATUS: PASS (M-02.1: RANGE_AND_RESTORE_SAFETY_VERIFIED; M-07A: ADOPT_PARTIAL; M-07B: NOT_PRESENT_AT_PIN; POST_D8: ACTIVE)
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: M-07 reference corpus validated; 6 overlap and 14 synthetic probe vectors confirmed with 0 disagreements; 9 negative controls verified; 14/14 C++ tests pass on MinGW and Linux WSL (Debug and Release).
FILES CHANGED: include/thor/recomp/mutation_harness.hpp, src/recomp/mutation_harness.cpp, tests/recomp/test_mutation_harness.cpp, tools/recomp/mutation_harness.py, tools/recomp/saturnrecomp_adapter.py, tests/recomp/test_m07_reference.py, workstreams/POST-D8-M07-saturnrecomp/README.md, workstreams/POST-D8-M07-saturnrecomp/experiment_evidence.md, workstreams/POST-D8-M07-saturnrecomp/reference_vectors.json, docs/POST_D8_SECOND_PASS_PLAN.md, docs/PROJECT_STATE.md, docs/WORKLOG.md, docs/FILE_MAP.md, CMakeLists.txt, TASK.md
TESTS RUN: test_mutation_harness (all 12 cases pass including 7 new regressions), test_m07_reference.py (all positive checks, 9 negative controls, live cross-checks pass), 14/14 CTest suites pass across MinGW Debug/Release and Linux WSL Debug/Release; source line limits check (all human-maintained files <= 293 lines); git diff --check.
NEW KNOWLEDGE: SaturnRecomp commit 26c9715 contains an excellent 0-wrong SH-2 decoder and semantic test corpus (M-07A), but does NOT contain a public ahead-of-time C translation generator (M-07B).
OPEN QUESTIONS: None for M-07.
EXACT NEXT ACTION: POST-D8 SECOND-PASS CLOSURE AUDIT.
