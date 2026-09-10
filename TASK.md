# Current task

TASK: T2-D9.2 — Generic Dynamic Exit & Declarative Memory Contract
WHY: Implement reusable static and runtime block-exit representation (BlockExitDescriptor and ResolvedBlockExit); generalize NativeDispatcher target handling to eliminate single-block hardcoded target_pc constant while preserving D8 behavior; implement declarative memory dependency contract (BlockMemoryContract, MemoryDependencyDescriptor) distinguishing STATIC_ADDRESS and REGISTER_AT_EXECUTION; prove descriptors on bb_06004000 and bb_06004280; establish canonical candidate_06004280.json metadata record; harden test_d9_plan.py with 19 negative controls; verify regressions green across MinGW and Linux WSL (Debug + Release).
CURRENT MILESTONE: D9 — Indirect Control-Flow Handling (docs/D9_INDIRECT_CONTROL_FLOW_PLAN.md)
TASK STATUS: PASS (D9.2: PASS; D9: READY_FOR_BOUNDED_TEST)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Reusable BlockExitDescriptor and ResolvedBlockExit implemented and tested across synthetic controls (normal target 0x0600A0F8, alternate 0x0600BEEF, zero target 0x00000000, hardcoded detector, direct post-PC mismatch fail-closed); NativeDispatcher generalized with hardcoded target_pc removed and authoritative live_cpu.pc resolution verified; BlockMemoryContract implemented with exact 3 dependencies proven for bb_06004000 and bb_06004280; candidate_06004280.json machine-readable metadata established; frame numbering reconciled to debugger reported frame 701 with presentation frame note; test_d9_plan.py passing with 19 negative controls; 18/18 CTest test suites pass across MinGW and Linux WSL (Debug and Release).
ACCEPTANCE CRITERIA:
- [x] D9.1 evidence drift repaired (timing equations, schema fields, frame counting notes);
- [x] frame counting reconciled to debugger reported frame 701 with presentation counting note, frame equality removed from proof claims;
- [x] D3 reference decode manifest scope updated to span bb_06004000 and bb_06004280, authority roles separated;
- [x] candidate_06004280.json established as canonical machine-readable metadata record;
- [x] reusable BlockExitDescriptor and ResolvedBlockExit implemented with strict static/runtime separation;
- [x] static exit derivation proven for bb_06004000 (DIRECT) and bb_06004280 (INDIRECT_CALL, static target absent);
- [x] runtime exit resolution implemented from verified post-state PC and PR;
- [x] NativeDispatcher single-block target_pc hardcode removed, target resolved from live_cpu.pc;
- [x] D8 native override behavior preserved exactly (bb_06004000 reaches 0x06004012, 27 cycles);
- [x] declarative BlockMemoryContract and MemoryDependencyDescriptor implemented distinguishing STATIC_ADDRESS and REGISTER_AT_EXECUTION;
- [x] memory dependencies proven on bb_06004280 (exact 3 U32 static reads) and bb_06004000 (R1 dynamic S16 read, static U32 literal read, R4 dynamic U32 read);
- [x] fail-closed behavior verified for unrepresentable memory access and MMIO addresses;
- [x] test_d9_plan.py hardened with 19 negative controls;
- [x] 18/18 CTest suites pass across MinGW and Linux WSL (Debug and Release);
- [x] all human-maintained source/test/tool files <= 500 lines;
- [x] git diff --check green;
- [x] terminal response only in Russian, max 7 bullets.
EVIDENCE AVAILABLE:
- Canonical D9 plan docs/D9_INDIRECT_CONTROL_FLOW_PLAN.md;
- Candidate qualification records workstreams/T2-D9-indirect/candidate_06004280.md and candidate_06004280.json;
- Workstream record workstreams/T2-D9-indirect/README.md;
- Reference decode manifests tests/sh2/reference_decode_manifest.hpp and workstreams/T2-D3-sh2-decode/reference_decode_manifest.json;
- Unit test suites tests/recomp/test_block_exit.cpp, tests/recomp/test_block_memory.cpp, tests/recomp/test_native_dispatcher.cpp;
- Automated plan validator test tests/recomp/test_d9_plan.py;
- Closure record docs/POST_D8_SECOND_PASS_CLOSURE.md;
- Decisions record docs/DECISIONS.md (ADR D-006, D-009, D-010, D-011, D-012, D-014).
KNOWN UNKNOWNS:
- None for generic exit and declarative memory representation.
ALLOWED SCOPE:
- BlockExitDescriptor, ResolvedBlockExit, derive_block_exit_descriptor, resolve_block_exit, BlockMemoryContract, MemoryDependencyDescriptor, derive_block_memory_contract, NativeDispatcher generalization, candidate JSON metadata, unit tests, and documentation.
OUT OF SCOPE:
- D9.3 shadow qualification of bb_06004280, native promotion of bb_06004280, D9.4, M-03, marking D9 BOUNDED_PROOF.

## Last verified result

`T2-D9.2_GENERIC_EXIT_AND_MEMORY_CONTRACT_PASS`: Reusable BlockExitDescriptor and ResolvedBlockExit implemented with strict static/runtime separation; NativeDispatcher target handling generalized to eliminate hardcoded target constant while preserving D8 behavior; declarative BlockMemoryContract implemented with exact 3 dependencies proven for bb_06004000 and bb_06004280; candidate_06004280.json metadata established; test_d9_plan.py hardened to 19 negative controls; 18/18 CTest suites pass across MinGW and Linux WSL (Debug and Release).

## Session checkpoint

CURRENT MILESTONE: D9 — Indirect Control-Flow Handling (docs/D9_INDIRECT_CONTROL_FLOW_PLAN.md)
CURRENT TASK: T2-D9.2 — Generic Dynamic Exit & Declarative Memory Contract
TASK STATUS: PASS (D9.2: PASS; D9: READY_FOR_BOUNDED_TEST)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: Generic exit and declarative memory models implemented and tested; D8 native override preserved; candidate JSON metadata created; 18/18 CTest suites pass on MinGW and Linux WSL.
FILES CHANGED: include/thor/recomp/block_exit.hpp, src/recomp/block_exit.cpp, include/thor/recomp/block_memory.hpp, src/recomp/block_memory.cpp, include/thor/recomp/native_dispatcher.hpp, src/recomp/native_dispatcher.cpp, CMakeLists.txt, tests/recomp/test_block_exit.cpp, tests/recomp/test_block_memory.cpp, tests/recomp/test_native_dispatcher.cpp, tests/recomp/test_d9_plan.py, workstreams/T2-D9-indirect/candidate_06004280.json, workstreams/T2-D9-indirect/candidate_06004280.md, workstreams/T2-D9-indirect/README.md, workstreams/T2-D3-sh2-decode/reference_decode_manifest.json, docs/D9_INDIRECT_CONTROL_FLOW_PLAN.md, docs/PROJECT_STATE.md, docs/DEVELOPMENT_PLAN.md, docs/WORKLOG.md, docs/FILE_MAP.md, TASK.md
TESTS RUN: test_block_exit, test_block_memory, test_native_dispatcher, test_mutation_harness, test_d9_plan.py (19 negative controls), test_post_d8_closure.py, test_m07_reference.py (--require-external), 18/18 CTest suites pass across MinGW (Debug/Release) and Linux WSL (Debug/Release); source file line limit check; git diff --check.
NEW KNOWLEDGE: Clean decoupling of static CFG descriptor (BlockExitDescriptor) from dynamic execution output (ResolvedBlockExit) enables generic dynamic target resolution without hardcoding; memory dependencies represent execution contracts distinct from executable identity; bb_06004280 requires exactly 3 static literal reads; bb_06004000 requires 1 dynamic register read, 1 static literal read, and 1 dynamic register read.
OPEN QUESTIONS: Mechanical JSR code generation in block_compiler for D9.3.
EXACT NEXT ACTION: D9.3 — Mechanical JSR Block Generation + Isolated Shadow Qualification for bb_06004280.
