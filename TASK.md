# Current task

TASK: D18 Guest Dependency Removal & Standalone Game Executable Target Passed
WHY: Deliver the terminal milestone of the progressive native C++20 recovery architecture following FULL_ASM_GAME_GATE certification, D10/D11, D12, D15, D16, and D17:
1. Implement D18 (Guest Dependency Removal & Standalone Game Executable Target):
   - Standalone Game Executable Target: `thor2_native` (`src/main_native.cpp`) compiling and linking directly with `thor_runtime`, `thor_hw`, `thor_recomp`, and `thor_sh2` with zero external emulator library dependencies.
   - Portable CLI Interface: `--boot`, `--frames <N>`, `--metrics`, `--selftest`, and `--help`.
   - L5 Observable Equivalence: bit-identical 320x224 RGBA8888 video rasterization and 16-bit stereo PCM audio synthesis across independent cold-boot executions.
2. Establish unit test suite `tests/runtime/test_guest_removal.cpp` registered as CTest #26 in `CMakeLists.txt`.
3. Verify dual-platform green CTests across Windows MinGW and Linux WSL (35/35 passing).
CURRENT MILESTONE: Progressive Native Recovery Track (D10..D18 post-FULL_ASM_GAME_GATE) — TERMINAL COMPLETION
TASK STATUS: COMPLETE / PASS (35/35 CTests pass across Windows MinGW and Linux WSL)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Standalone native game executable target thor2_native implemented in src/main_native.cpp (76 lines); unit test suite tests/runtime/test_guest_removal.cpp (108 lines) passing 100%; 35/35 CTests pass on Windows MinGW and Linux WSL; 100/100 human-maintained source files <= 500 lines; zero commercial bytes committed.
ACCEPTANCE CRITERIA:
- [x] implement standalone native executable target thor2_native with portable CLI interface;
- [x] verify zero emulator library or guest dependency handles;
- [x] verify L5 observable equivalence: bit-identical multi-frame video rendering and audio generation;
- [x] establish unit test suite test_guest_removal;
- [x] verify <= 500 lines policy across all human-maintained source/test/tool files (100/100 clean);
- [x] pass 35/35 CTests across Windows MinGW and Linux WSL;
- [x] document results in docs/WORKLOG.md, docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/DECISIONS.md, and docs/FILE_MAP.md.
EVIDENCE AVAILABLE:
- Executable: thor2_native (src/main_native.cpp);
- Tests: tests/runtime/test_guest_removal.cpp;
- Test suite: 35/35 CTests pass on Windows MinGW and Linux WSL.
KNOWN UNKNOWNS:
- None for D18.
ALLOWED SCOPE:
- Standalone game executable, CLI interface, L5 observable equivalence tests, documentation.
OUT OF SCOPE:
- Full interactive window presentation requiring SDL/GLFW (keep headless and portable C++20 standard library compliant).

## Last verified result

`D18_PASSED`: D18 Guest Dependency Removal and Standalone Native Game Target verified and passed; L5 observable equivalence satisfied; 35/35 CTests pass on Windows MinGW and Linux WSL; all 100 human-maintained source files clean under <= 500 lines limit.

## Session checkpoint

CURRENT MILESTONE: Progressive Native Recovery Track (D10..D18 post-FULL_ASM_GAME_GATE) — TERMINAL COMPLETION
CURRENT TASK: Autonomous End-to-End Thor 2 Recovery
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: D18 verified and passed; 35/35 CTests pass across Windows MinGW and Linux WSL.
FILES CHANGED: CMakeLists.txt, docs/DECISIONS.md, docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/WORKLOG.md, src/main_native.cpp, tests/runtime/test_guest_removal.cpp, TASK.md.
TESTS RUN: 35/35 CTests on Windows MinGW (53.75s) and Linux WSL; line limit audit (100/100 clean); git diff --check.
NEW KNOWLEDGE: Standalone native game target thor2_native executes with zero emulator dependencies, achieving deterministic L5 video and audio rendering.
OPEN QUESTIONS: None.
EXACT NEXT ACTION: Push commits and deliver terminal summary.
