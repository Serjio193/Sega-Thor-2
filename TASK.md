# Current task

TASK: T2-D9.1 — JSR @Rn L0 Semantics & bb_06004280 Block Qualification
WHY: Repair D9.P0 integrity issues (timing discrepancy 19 vs 21 cycles, eliminate invalid V-09A label, repair delayed_pc zero-sentinel in Sh2CpuState); implement exact JSR @Rn opcode decode (0x4n0B, OpcodeId::JSR, ControlFlowType::CALL) and execution semantics; prove synthetic semantics across 8 test dimensions; independently cross-check semantics against Hitachi SH-2 hardware manual, pinned Mednafen, and Catherine; qualify candidate basic block bb_06004280 (0x06004280..0x06004288, 10 bytes, SHA-256 8879cbe1...) in D3/D4/D5; reproduce candidate execution, reads, PR, and timing across two independent cold boots in Mednafen oracle; run all regressions across Windows MinGW and Linux WSL (Debug + Release).
CURRENT MILESTONE: D9 — Indirect Control-Flow Handling (docs/D9_INDIRECT_CONTROL_FLOW_PLAN.md)
TASK STATUS: PASS (D9.1: PASS; D9: READY_FOR_BOUNDED_TEST; bb_06004280: QUALIFIED / CONFIRMED_CODE / EXECUTED)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Exact JSR @Rn decode (0x4n0B) and execution semantics implemented; Sh2CpuState.delayed_pc upgraded to std::optional<uint32_t>; 8-dimension synthetic L0 test matrix passing (normal target, alternate target, delay-slot Rn mutation, zero target 0x00000000, PR overwrite, illegal slot exception, all 16 registers, zero memory accesses); 4-way independent cross-check confirms 0 decode/semantic disagreements; bb_06004280 block discovery and execution replay match Mednafen oracle post-state and stepping trace identically; candidate timing reconciled to 21 cycles (entry 316309168, delay slot entry 316309187, target entry 316309189); invalid V-09A label eliminated across all docs with negative control in test_d9_plan.py; 16/16 CTest test suites pass across MinGW and Linux WSL (Debug and Release).
ACCEPTANCE CRITERIA:
- [x] candidate timing discrepancy reconciled (19 cycles delay-slot entry, 21 cycles block completion / target entry);
- [x] non-canonical V-09A label eliminated across all documents, plans, and READMEs;
- [x] delayed_pc zero-sentinel repaired to std::optional<uint32_t> in Sh2CpuState;
- [x] exact JSR @Rn decode (0x4n0B, OpcodeId::JSR, ControlFlowType::CALL, has_delay_slot = true) implemented;
- [x] exact JSR @Rn execution semantics (pre-delay Rn capture, PR = PC + 4, delayed_pc, delay-slot evaluation order, illegal slot exception) implemented;
- [x] 8-dimension synthetic L0 test matrix passing with 0 divergences;
- [x] independent cross-check across Hitachi manual, Mednafen, and Catherine confirms 0 disagreements;
- [x] reference decode vector added to reference_decode_manifest.hpp and reference_decode_manifest.json;
- [x] basic block bb_06004280 qualified in D3/D4/D5 with discovery and execution replay tests;
- [x] two independent cold-boot reproductions in Mednafen oracle confirmed bit-identical execution;
- [x] test_d9_plan.py passing with 11 negative controls (including timing arithmetic and V-09A checks);
- [x] 16/16 CTest suites pass across MinGW and Linux WSL (Debug and Release);
- [x] all human-maintained source/test/tool files <= 500 lines;
- [x] git diff --check green;
- [x] terminal response only in Russian, max 7 bullets.
EVIDENCE AVAILABLE:
- Canonical D9 plan docs/D9_INDIRECT_CONTROL_FLOW_PLAN.md;
- Candidate qualification record workstreams/T2-D9-indirect/candidate_06004280.md;
- Workstream record workstreams/T2-D9-indirect/README.md;
- Reference decode manifests tests/sh2/reference_decode_manifest.hpp and workstreams/T2-D3-sh2-decode/reference_decode_manifest.json;
- Unit test suites tests/sh2/test_sh2_decoder.cpp, tests/sh2/test_sh2_l0_semantics.cpp, tests/sh2/test_sh2_block.cpp;
- Automated plan validator test tests/recomp/test_d9_plan.py;
- Closure record docs/POST_D8_SECOND_PASS_CLOSURE.md;
- Decisions record docs/DECISIONS.md (ADR D-006, D-009, D-010, D-011, D-012, D-014).
KNOWN UNKNOWNS:
- None for JSR @Rn L0 semantics or candidate bb_06004280 qualification.
ALLOWED SCOPE:
- JSR @Rn decoding, execution semantics, delayed branch state fix, bb_06004280 block qualification, unit tests, timing reconciliation, and documentation.
OUT OF SCOPE:
- D9.2 generic BlockExitDescriptor, native override for bb_06004280, D9.3/D9.4/M-03, marking D9 BOUNDED_PROOF.

## Last verified result

`T2-D9.1_JSR_L0_AND_BLOCK_QUALIFIED_PASS`: SH-2 JSR @Rn opcode decode and L0 execution semantics fully implemented and proven; delayed_pc zero-sentinel repaired to std::optional; candidate timing reconciled to 21 cycles (entry 316309168, delay slot entry 316309187, target entry 316309189); V-09A label eliminated; bb_06004280 qualified under D3/D4/D5 with discovery and execution replay matching Mednafen oracle; 2 independent cold boot runs confirmed bit-identical reproduction; 16/16 CTest suites pass across MinGW and Linux WSL (Debug and Release); test_d9_plan.py passes with 11 negative controls.

## Session checkpoint

CURRENT MILESTONE: D9 — Indirect Control-Flow Handling (docs/D9_INDIRECT_CONTROL_FLOW_PLAN.md)
CURRENT TASK: T2-D9.1 — JSR @Rn L0 Semantics & bb_06004280 Block Qualification
TASK STATUS: PASS (D9.1: PASS; D9: READY_FOR_BOUNDED_TEST)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: JSR @Rn L0 semantics proven, candidate bb_06004280 qualified, timing reconciled, 16/16 CTest suites pass on MinGW and Linux WSL.
FILES CHANGED: include/thor/sh2/sh2_state.hpp, include/thor/sh2/sh2_types.hpp, src/sh2/sh2_decoder.cpp, src/sh2/sh2_executor.cpp, src/sh2/sh2_block.cpp, tests/sh2/reference_decode_manifest.hpp, workstreams/T2-D3-sh2-decode/reference_decode_manifest.json, tests/sh2/test_sh2_decoder.cpp, tests/sh2/test_sh2_l0_semantics.cpp, tests/sh2/test_sh2_block.cpp, tests/recomp/test_d9_plan.py, docs/D9_INDIRECT_CONTROL_FLOW_PLAN.md, workstreams/T2-D9-indirect/candidate_06004280.md, workstreams/T2-D9-indirect/README.md, docs/PROJECT_STATE.md, docs/DEVELOPMENT_PLAN.md, docs/WORKLOG.md, TASK.md
TESTS RUN: test_sh2_decoder, test_sh2_l0_semantics, test_sh2_block, test_d9_plan.py (11 negative controls), test_post_d8_closure.py, test_m07_reference.py (--require-external), 16/16 CTest suites pass across MinGW (Debug/Release) and Linux WSL (Debug/Release); source file line limit check; git diff --check.
NEW KNOWLEDGE: 19 cycles was delay-slot entry (316309187), whereas 21 cycles is block completion / target entry (316309189); JSR @Rn delay-slot evaluation order verified (Rn mutated in delay slot does not alter target); target 0x00000000 valid and cleanly supported via std::optional delayed_pc.
OPEN QUESTIONS: Generic BlockExitDescriptor representation in D9.2.
EXACT NEXT ACTION: D9.2 Generic Dynamic-Exit Representation & Declarative Memory Descriptors.
