# Current task

TASK: T2-D9.4 — Authoritative Native Indirect Override & Dynamic Continuation
WHY: Integrate candidate bb_06004280 into authoritative NativeDispatcher with generic memory contract materialization; extend native bridge with block mask control and per-block stats telemetry; execute live authoritative native indirect override in pinned Mednafen debug oracle across 4 bounded modes; prove target-entry parity (0x0600A0F8), downstream continuation (0x060042E0), 0 interpreter retirements in replaced block, cold-boot determinism, and timing parity; prove fail-closed negative controls; document live evidence and update project records.
CURRENT MILESTONE: D9 — Indirect Control-Flow Handling (docs/D9_INDIRECT_CONTROL_FLOW_PLAN.md)
TASK STATUS: PASS (D9.4: PASS; D9: BOUNDED_PROOF for bb_06004280; M-03: READY_FOR_BOUNDED_TEST)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Live Mednafen debug oracle runs across all 4 modes (PURE_INTERPRETER, D8_ONLY, D9_ONLY Run 1, D9_ONLY Run 2, D8_PLUS_D9) proved 100% register parity across all 23 SH-2 registers at dynamically resolved target 0x0600A0F8; interpreter retired exactly 0 instructions during replaced block; cold boot determinism verified bit-identical; downstream continuation verified to 0x060042E0 without corruption; fixed redundant PC increment in SH7095::NativeBranch restoring branch completion parity; block mask filtering verified fail-closed; test_native_indirect unit tests verified with 6 negative controls; 19/19 CTest suites pass across MinGW and Linux WSL.
ACCEPTANCE CRITERIA:
- [x] D9.3 integrity/safety items repaired (external pins, illegal delay-slot control transfer rejection, width-aware memory intervals);
- [x] bb_06004280 registered in authoritative NativeDispatcher with generic memory contract materialization (no hardcoded literal addresses);
- [x] native bridge extended with THOR_BLOCK_MASK_* constants, mask controls, and per-block stats telemetry;
- [x] test_native_indirect unit tests pass covering positive override, dynamic anti-hardcoding, mask modes A/B/C/D, per-block stats, and 6 negative controls;
- [x] Mednafen automation and SH-2 core updated; redundant PC increment bug fixed in SH7095::NativeBranch;
- [x] live authoritative native JSR override executed in pinned Mednafen debug oracle across all 4 modes;
- [x] 100% register parity (23/23 SH-2 registers) verified at target entry 0x0600A0F8;
- [x] exactly 0 instructions retired by interpreter during replaced block interval;
- [x] cold-boot determinism verified bit-identical between independent runs;
- [x] downstream continuation to 0x060042E0 verified with zero CPU/memory corruption;
- [x] evidence documented in workstreams/T2-D9-indirect/d9_4_native_indirect_evidence.md and .json;
- [x] 19/19 CTest suites pass across MinGW and Linux WSL (Debug and Release);
- [x] test_d9_plan.py passing with 22 negative controls;
- [x] test_m07_reference.py passing with --require-external;
- [x] all human-maintained code files <= 500 lines;
- [x] git diff --check green;
- [x] terminal response only in Russian, max 7 bullets.
EVIDENCE AVAILABLE:
- Canonical D9 plan docs/D9_INDIRECT_CONTROL_FLOW_PLAN.md;
- Candidate qualification records workstreams/T2-D9-indirect/candidate_06004280.md and candidate_06004280.json;
- Live D8 regression record workstreams/T2-D9-indirect/d9_2_d8_live_regression.md;
- Live D9.4 native indirect evidence records workstreams/T2-D9-indirect/d9_4_native_indirect_evidence.md and d9_4_native_indirect_evidence.json;
- Workstream record workstreams/T2-D9-indirect/README.md;
- Generated isolated block build/generated/bb_06004280.cpp;
- Unit test suites tests/recomp/test_native_indirect.cpp, tests/recomp/test_native_dispatcher.cpp, tests/recomp/test_block_memory.cpp, tests/recomp/test_sh2_block_compiler.cpp;
- Automated plan validator test tests/recomp/test_d9_plan.py;
- Decisions record docs/DECISIONS.md.
KNOWN UNKNOWNS:
- Candidate harvester heuristics across full 0TH2.BIN and TH2.LOW binary images (deferred to M-03).
ALLOWED SCOPE:
- Authoritative native indirect override for bb_06004280, block mask filtering, per-block stats, live Mednafen execution, evidence documentation.
OUT OF SCOPE:
- Translating or promoting target 0x0600A0F8, D9.5 multi-target expansion, marking M-03 complete.

## Last verified result

`T2-D9.4_AUTHORITATIVE_NATIVE_INDIRECT_OVERRIDE_PASS`: Authoritative native JSR @R3 override proven inside pinned Mednafen debug oracle; 100% register parity (23/23 SH-2 registers) at dynamically computed target 0x0600A0F8; 0 interpreter retirements in replaced block; cold-boot bit-identical parity proven across independent runs; zero downstream corruption at 0x060042E0; block mask fail-closed gating verified; 19/19 CTest suites pass across MinGW and Linux WSL.

## Session checkpoint

CURRENT MILESTONE: D9 — Indirect Control-Flow Handling (docs/D9_INDIRECT_CONTROL_FLOW_PLAN.md)
CURRENT TASK: T2-D9.4 — Authoritative Native Indirect Override & Dynamic Continuation
TASK STATUS: PASS (D9.4: PASS; D9: BOUNDED_PROOF for bb_06004280; M-03: READY_FOR_BOUNDED_TEST)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: Authoritative native JSR override, target entry parity, 0 interpreter retirements, cold-boot determinism, downstream continuation, and block mask gating verified; 19/19 CTest suites pass on MinGW and Linux WSL.
FILES CHANGED: CMakeLists.txt, include/thor/recomp/block_memory.hpp, include/thor/recomp/native_bridge.h, include/thor/recomp/native_dispatcher.hpp, src/recomp/block_compiler.cpp, src/recomp/block_memory.cpp, src/recomp/native_dispatcher.cpp, tests/recomp/test_block_memory.cpp, tests/recomp/test_d9_plan.py, tests/recomp/test_sh2_block_compiler.cpp, tests/recomp/test_native_indirect.cpp, workstreams/T2-D9-indirect/d9_2_d8_live_regression.md, workstreams/T2-D9-indirect/d9_4_native_indirect_evidence.md, workstreams/T2-D9-indirect/d9_4_native_indirect_evidence.json, workstreams/T2-D9-indirect/README.md, docs/PROJECT_STATE.md, docs/WORKLOG.md, TASK.md.
TESTS RUN: test_native_indirect, test_native_dispatcher, test_block_memory, test_block_exit, test_sh2_block_compiler, test_shadow_positive, test_shadow_negative, test_executable_identity, test_generated_link_isolation, test_d9_plan.py, test_m07_reference.py (--require-external), 19/19 CTest suites pass across MinGW (Debug/Release) and Linux WSL (Debug/Release); source file line limit check; git diff --check.
NEW KNOWLEDGE: Dynamic branch target in SH-2 requires exact instruction-aligned execution in hardware oracle; Mednafen NativeBranch PC increment must match normal branch buffer refill; generic memory contract pre-state materializer successfully feeds High Work RAM literal pool reads without candidate-specific address hacks.
OPEN QUESTIONS: None for bb_06004280 authoritative native override.
EXACT NEXT ACTION: M-03 — Bounded SaturnAutoRE Candidate Harvester Re-evaluation & Indirect Flow Scaling.
