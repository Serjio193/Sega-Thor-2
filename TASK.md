# Current task

TASK: D12 Structural Recovery & Subsystem Function Demarcation Passed
WHY: Progress the progressive native C++20 recovery architecture following FULL_ASM_GAME_GATE certification and D10/D11 pass per ADR D-015:
1. Implement D12 (Structural Recovery & Subsystem Function Demarcation): formalize function entry kinds (`MODULE_ENTRY`, `DIRECT_CALL_TARGET`, `INDIRECT_CALL_TARGET`, `EXCEPTION_VECTOR`) and exit kinds (`SUBROUTINE_RETURN`, `EXCEPTION_RETURN`, `TAIL_CALL`, `NON_RETURNING`).
2. Catalog and demarcate canonical Thor 2 subroutines: `sub_06004000_boot`, `sub_0600A0F8_load_file`, `sub_002E9910_engine_start`, `sub_060D8000_stage_overlay`.
3. Recover caller/callee adjacency and verify call graph queries (`get_callers`, `get_callees`, `find_by_pc`).
4. Verify dual-platform green CTests across Windows MinGW and Linux WSL (29/29 passing).
CURRENT MILESTONE: Progressive Native Recovery Track (D10..D18 post-FULL_ASM_GAME_GATE)
TASK STATUS: PASS (D12 = PASS; 29/29 CTests pass across Windows MinGW and Linux WSL)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: D12 function boundary modeling implemented in include/thor/recomp/function_boundary.hpp (68 lines) and src/recomp/function_boundary.cpp (143 lines); unit test suite tests/recomp/test_function_boundary.cpp (133 lines) passing 100%; 29/29 CTests pass on Windows MinGW and Linux WSL; 81/81 human-maintained source files <= 500 lines.
ACCEPTANCE CRITERIA:
- [x] implement D12 function entry kinds and exit kinds;
- [x] implement FunctionDescriptor and FunctionBoundaryCatalog;
- [x] catalog canonical Thor 2 routines (boot, load_file, engine_start, stage_overlay);
- [x] implement caller/callee adjacency indexing and queries;
- [x] implement D12 unit test suite test_function_boundary;
- [x] verify <= 500 lines policy across all human-maintained source/test/tool files (81/81 clean);
- [x] pass 29/29 CTests across Windows MinGW and Linux WSL;
- [x] document results in docs/WORKLOG.md, docs/PROJECT_STATE.md, docs/ROADMAP.md, and docs/FILE_MAP.md.
EVIDENCE AVAILABLE:
- Function catalog: include/thor/recomp/function_boundary.hpp, src/recomp/function_boundary.cpp;
- Tests: tests/recomp/test_function_boundary.cpp;
- Test suite: 29/29 CTests pass on Windows MinGW and Linux WSL.
KNOWN UNKNOWNS:
- Exact VDP1, VDP2, and SCSP command protocols and MMIO registers for D15 hardware subsystem contracts.
ALLOWED SCOPE:
- Function boundary modeling, call-graph adjacency, cataloging canonical subroutines, tests, documentation.
OUT OF SCOPE:
- Full decompilation or speculative function recovery without evidence.

## Last verified result

`D12_PASSED`: D12 function boundary kinds, descriptors, canonical Thor 2 routines, and caller/callee adjacency graphs implemented and verified; 29/29 CTests pass on Windows MinGW and Linux WSL; 81/81 human-maintained source files clean under <= 500 lines limit.

## Session checkpoint

CURRENT MILESTONE: Progressive Native Recovery Track (D10..D18 post-FULL_ASM_GAME_GATE)
CURRENT TASK: D15 / T2-NAT-03 — Hardware Subsystem Contracts (VDP1, VDP2, SCSP)
TASK STATUS: READY
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: D12 verified and passed; 29/29 CTests pass across Windows MinGW and Linux WSL.
FILES CHANGED: CMakeLists.txt, docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/WORKLOG.md, include/thor/recomp/function_boundary.hpp, src/recomp/function_boundary.cpp, tests/recomp/test_function_boundary.cpp, TASK.md.
TESTS RUN: 29/29 CTests on Windows MinGW and Linux WSL; line limit audit (81/81 clean); git diff --check.
NEW KNOWLEDGE: Function boundaries in Thor 2 form a hierarchical call graph with distinct entry/exit classifications. Boot code (`0x06004000`) performs initial setup and calls `load_file` (`0x0600A0F8`), which transitions control to `TH2.LOW` (`0x002E9910`), which dynamically dispatches stage overlays like `SET07.BIN` (`0x060D8000`).
OPEN QUESTIONS: Defining formal native C++ hardware contracts for VDP1 (sprites/polygons), VDP2 (background planes/scroll), and SCSP (sound commands) under D15.
EXACT NEXT ACTION: D15 / T2-NAT-03 — Hardware Subsystem Contracts (VDP1, VDP2, SCSP).
