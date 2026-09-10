# Current task

TASK: D15 Hardware Subsystem Contracts (VDP1, VDP2, SCSP) Passed
WHY: Progress the progressive native C++20 recovery architecture following FULL_ASM_GAME_GATE certification, D10/D11 pass, and D12 pass per ADR D-015:
1. Implement D15 (Hardware Subsystem Contracts: VDP1, VDP2, SCSP):
   - VDP1: 32-byte command decoder, jump modes (NEXT, ASSIGN, CALL, RETURN, SKIP), user/system clipping, local coordinate transformation, and display list tracer.
   - VDP2: plane configurations (NBG0..NBG3, RBG0, Sprite, Back), CRAM 15-bit/24-bit decoding, 16.16 fixed-point rotation matrix transform, multi-plane priority arbitration, and color calculation blending.
   - SCSP: sound command packet structure, ring buffer FIFO mailbox, BGM state transitions (Play, Stop, Pause, Resume), SFX slot dynamic allocation, master volume clamping, and driver reset.
2. Establish unit test suites (`tests/hw/test_vdp1.cpp`, `tests/hw/test_vdp2.cpp`, `tests/hw/test_scsp.cpp`) registered as CTest #21, #22, #23 in `CMakeLists.txt`.
3. Verify dual-platform green CTests across Windows MinGW and Linux WSL (32/32 passing).
CURRENT MILESTONE: Progressive Native Recovery Track (D10..D18 post-FULL_ASM_GAME_GATE)
TASK STATUS: PASS (D15 = PASS; 32/32 CTests pass across Windows MinGW and Linux WSL)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: VDP1 engine implemented in include/thor/hw/vdp1_types.hpp (81 lines), include/thor/hw/vdp1.hpp (70 lines), and src/hw/vdp1.cpp (234 lines); VDP2 engine implemented in include/thor/hw/vdp2_types.hpp (69 lines), include/thor/hw/vdp2.hpp (50 lines), and src/hw/vdp2.cpp (175 lines); SCSP engine implemented in include/thor/hw/scsp_types.hpp (56 lines), include/thor/hw/scsp.hpp (46 lines), and src/hw/scsp.cpp (144 lines); unit tests tests/hw/test_vdp1.cpp (91 lines), tests/hw/test_vdp2.cpp (85 lines), and tests/hw/test_scsp.cpp (111 lines) passing 100%; 32/32 CTests pass on Windows MinGW and Linux WSL; 93/93 human-maintained source files <= 500 lines.
ACCEPTANCE CRITERIA:
- [x] implement VDP1 display list decoder and coordinate transformation;
- [x] implement VDP2 background plane priority arbitration and color blending;
- [x] implement SCSP audio command ring buffer and sound driver state machine;
- [x] implement unit test suites test_vdp1, test_vdp2, test_scsp;
- [x] isolate disc verification scratch directory per platform (full_game_proof_win, full_game_proof_linux);
- [x] verify <= 500 lines policy across all human-maintained source/test/tool files (93/93 clean);
- [x] pass 32/32 CTests across Windows MinGW and Linux WSL;
- [x] document results in docs/WORKLOG.md, docs/PROJECT_STATE.md, docs/ROADMAP.md, and docs/FILE_MAP.md.
EVIDENCE AVAILABLE:
- Hardware models: include/thor/hw/, src/hw/;
- Tests: tests/hw/test_vdp1.cpp, tests/hw/test_vdp2.cpp, tests/hw/test_scsp.cpp;
- Test suite: 32/32 CTests pass on Windows MinGW and Linux WSL.
KNOWN UNKNOWNS:
- Direct hardware hooking interfaces for live differential testing against Mednafen runtime buffers.
ALLOWED SCOPE:
- Hardware subsystem modeling, command protocols, state machines, unit tests, documentation.
OUT OF SCOPE:
- Replacing Saturn emulator subsystem without differential verification.

## Last verified result

`D15_PASSED`: D15 VDP1, VDP2, and SCSP hardware subsystem contracts implemented and verified; 32/32 CTests pass on Windows MinGW and Linux WSL; 93/93 human-maintained source files clean under <= 500 lines limit.

## Session checkpoint

CURRENT MILESTONE: Progressive Native Recovery Track (D10..D18 post-FULL_ASM_GAME_GATE)
CURRENT TASK: D16 / T2-NAT-04 — Native Subsystem Replacement (VDP1/VDP2/SCSP Native Backends)
TASK STATUS: READY
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: D15 verified and passed; 32/32 CTests pass across Windows MinGW and Linux WSL.
FILES CHANGED: CMakeLists.txt, docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/WORKLOG.md, include/thor/hw/vdp1.hpp, include/thor/hw/vdp1_types.hpp, include/thor/hw/vdp2.hpp, include/thor/hw/vdp2_types.hpp, include/thor/hw/scsp.hpp, include/thor/hw/scsp_types.hpp, src/hw/vdp1.cpp, src/hw/vdp2.cpp, src/hw/scsp.cpp, TASK.md, tests/hw/test_vdp1.cpp, tests/hw/test_vdp2.cpp, tests/hw/test_scsp.cpp, tools/asm/verify_full_game_disc.py.
TESTS RUN: 32/32 CTests on Windows MinGW and Linux WSL; line limit audit (93/93 clean); git diff --check.
NEW KNOWLEDGE: VDP1 display lists operate as a stack-based instruction stream with conditional subroutine calls and jump links. VDP2 arbitrates up to 7 plane layers with color calculation and affine rotation transforms. SCSP processes async sound command packets through a ring buffer mailbox from SH-2 to M68K.
OPEN QUESTIONS: Integrating native hardware backend renderers and differential state verification in D16.
EXACT NEXT ACTION: D16 / T2-NAT-04 — Native Subsystem Replacement (VDP1/VDP2/SCSP Native Backends).
