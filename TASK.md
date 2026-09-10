# Current task

TASK: T2-ASM-05 — Bulk PC Harvesting, Opcode Modeling & ASM_90_GATE Passed
WHY: Implement the fifth experiment of ADR D-015 (ASM_FIRST_RECOVERY): expand the `thor_sh2` opcode decoder and executor across the high-frequency instruction profile observed in gameplay CDL traces; modularize SH-2 emulation units to maintain strict file size policy (human-maintained files <= 500 lines); partition the primary executable `0TH2.BIN` and secondary executable `TH2.LOW` into exhaustive confirmed code blocks and raw unknown ranges; reassemble both binaries byte-exact with pinned GNU `binutils-sh-elf 2.40+2`; execute occurrence-aware runtime substitution proofs in clean Mednafen oracle; prove fail-closed negative controls; advance Proven Mnemonic Coverage beyond 90.00% across all confirmed code to satisfy and pass **`ASM_90_GATE`**.
CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015, ADR D-016)
TASK STATUS: PASS (ASM_90_GATE = PASS: 96.59% >= 90.00%; 0TH2.BIN: ASM_BYTE_EXACT = PASS, ASM_RUNTIME_VERIFIED = PASS, PROVEN = 96.46%; TH2.LOW: ASM_BYTE_EXACT = PASS, ASM_RUNTIME_VERIFIED = PASS, PROVEN = 99.51%; SET07.BIN: ASM_BYTE_EXACT = PASS, PROVEN = 100.00%; 26/26 CTests pass across MinGW and Linux WSL)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Pinned CDL gameplay harvesting produced 26,979 executed instructions in 0TH2.BIN and 1,633 in TH2.LOW; thor_sh2 expanded to 63 opcodes with full L0 semantics and unit tests; TH2.LOW partitioned into 176 proven code blocks (3,250 / 3,266 bytes = 99.51% proven); 0TH2.BIN partitioned into 3,126 proven code blocks (52,050 / 53,958 bytes = 96.46% proven); total proven coverage reached 96.59% (55,312 / 57,264 bytes); both modules reassembled byte-exact with pinned GNU binutils-sh-elf 2.40+2; Mednafen cold-boot runtime proof verified 0 cycle/register divergence across all 6 checkpoints; 20/20 0TH2, 10/10 TH2.LOW, 9/9 SET07 negative controls pass; 26/26 CTests pass on Windows MinGW and Linux WSL.
ACCEPTANCE CRITERIA:
- [x] expand thor_sh2 opcode model to cover >= 90% of dynamic instruction execution;
- [x] refactor decoder and executor to maintain <= 500 lines per human-maintained source file;
- [x] partition TH2.LOW into confirmed code blocks and unknown ranges (353 ranges, 176 proven blocks);
- [x] reassemble TH2.LOW byte-exact (149,504 / 149,504 bytes, SHA-256 78139689...);
- [x] partition 0TH2.BIN into confirmed code blocks and unknown ranges (6,353 ranges, 3,126 proven blocks);
- [x] reassemble 0TH2.BIN byte-exact (535,552 / 535,552 bytes, SHA-256 c1cc4117...);
- [x] prove dual-build determinism for both modules;
- [x] verify sector-by-sector private disc splice for both modules;
- [x] verify occurrence-aware Mednafen cold-boot runtime parity with 0 cycle / register divergence;
- [x] pass all fail-closed negative controls (20 for 0TH2.BIN, 10 for TH2.LOW, 9 for SET07.BIN);
- [x] achieve PROVEN_MNEMONIC_COVERAGE >= 90.00% to satisfy ASM_90_GATE (achieved 96.59%);
- [x] update scorecard workstreams/ASM_RECOVERY_SCORECARD.json with ASM_90_GATE = PASS;
- [x] line limit <= 500 lines satisfied across all human-maintained files;
- [x] 26/26 CTest suites pass on Windows MinGW and Linux WSL.
EVIDENCE AVAILABLE:
- Manifests: asm/manifests/0TH2.BIN.json, asm/manifests/TH2.LOW.json, asm/manifests/SET07.BIN.json, asm/manifests/BGM.BIN.json;
- Linker scripts: asm/linker/0TH2.ld, asm/linker/TH2_LOW.ld, asm/linker/SET07.ld, asm/linker/BGM.ld;
- Scorecard: workstreams/ASM_RECOVERY_SCORECARD.json (ASM_90_GATE = PASS, coverage = 96.59%);
- Decoder/Executor: include/thor/sh2/*, src/sh2/* (all <= 500 lines);
- Tests: tests/sh2/*, tests/asm/* (26/26 CTests pass).
KNOWN UNKNOWNS:
- Resolving the final pending raw code sequences (3.41% pending in 0TH2.BIN, 0.49% in TH2.LOW) during progressive semantic recovery.
ALLOWED SCOPE:
- SH-2 opcode expansion, modularization for file size policy, multi-block assembly, response file support, reassembly, runtime proof, negative controls, documentation.
OUT OF SCOPE:
- Broad C++ translation (frozen per ADR D-015 until FULL_ASM_GAME_GATE).

## Last verified result

`T2-ASM-05_ASM_90_GATE_PASSED`: thor_sh2 expanded to 63 opcodes with modularized decoder/executor adhering to <= 500 lines policy; TH2.LOW partitioned into 176 proven blocks (99.51% proven coverage); 0TH2.BIN partitioned into 3,126 proven blocks (96.46% proven coverage); overall proven mnemonic coverage reached 96.59% (55,312 / 57,264 bytes), passing ASM_90_GATE; both modules reassembled byte-exact with pinned GNU binutils-sh-elf 2.40+2; Mednafen cold-boot runtime substitution proof verified 0 cycle / register divergence across all 6 checkpoints; all negative controls pass; 26/26 CTests pass on Windows MinGW and Linux WSL.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015, ADR D-016)
CURRENT TASK: FULL_ASM_GAME_GATE — Full Saturn Disc Game Boot & Gameplay Verification
TASK STATUS: READY
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: ASM_90_GATE passed at 96.59% proven coverage; 0TH2.BIN and TH2.LOW byte-exact reassembly and Mednafen cold-boot runtime parity verified; 26/26 CTests pass across MinGW and Linux WSL.
FILES CHANGED: CMakeLists.txt, asm/manifests/0TH2.BIN.json, asm/manifests/BGM.BIN.json, asm/manifests/SET07.BIN.json, asm/manifests/TH2.LOW.json, asm/linker/0TH2.ld, asm/linker/BGM.ld, include/thor/sh2/sh2_decoder.hpp, include/thor/sh2/sh2_executor.hpp, include/thor/sh2/sh2_types.hpp, src/sh2/sh2_decoder.cpp, src/sh2/sh2_decoder_ext.cpp, src/sh2/sh2_disasm.cpp, src/sh2/sh2_executor.cpp, src/sh2/sh2_executor_ext.cpp, tests/sh2/test_sh2_decoder.cpp, tests/sh2/test_sh2_decoder_extended.cpp, tests/sh2/test_sh2_l0_extended.cpp, tools/asm/export_sh2_asm_ir.cpp, tools/asm/generate_full_module_asm.py, tools/asm/verify_full_module.py, workstreams/ASM_RECOVERY_SCORECARD.json, docs/PROJECT_STATE.md, docs/WORKLOG.md, TASK.md.
TESTS RUN: 26/26 CTests on Windows MinGW and Linux WSL; build_full_module.py; verify_full_module.py on 0TH2.BIN, TH2.LOW, SET07.BIN; runtime_substitution_proof.py on 0TH2.BIN and TH2.LOW in Mednafen; line limit verification; git diff --check.
NEW KNOWLEDGE: The 63-opcode SH-2 decoder/executor covers 96.46% of instructions in 0TH2.BIN and 99.51% in TH2.LOW. GNU binutils-sh-elf 2.40+2 cleanly reassembles both massive multi-block containers (69k lines for 0TH2.s, 11.5k lines for TH2.LOW.s) with bit-for-bit exactness. Cold boot in Mednafen achieves exact cycle and register reproduction at all architectural checkpoints.
OPEN QUESTIONS: Mednafen automation harness for full game playthrough validation across all stages.
EXACT NEXT ACTION: FULL_ASM_GAME_GATE — Full Saturn Disc Game Boot & Gameplay Verification.
