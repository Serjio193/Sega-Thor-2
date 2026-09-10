# Current task

TASK: T2-D9.4.1 — Native Indirect Proof Integrity Repair
WHY: Audit clean oracle provenance (Mednafen commit 155426661b7ac3152e2c93a98da60ac33002b908, src/ss/sh7095.h and src/ss/sh7095.inc 100% untouched); repair native-branch hardware pipeline delay-slot refill convention without modifying core oracle; correct candidate SHA-256 and oracle baseline hashes; reproduce 0-cycle timing parity at target entry (0x0600A0F8), return site (0x0600428A), and downstream continuation (0x060042E0); rerun all 5 live experiment modes; verify cold-boot determinism and 6 negative controls; update project records.
CURRENT MILESTONE: D9 — Indirect Control-Flow Handling (docs/D9_INDIRECT_CONTROL_FLOW_PLAN.md)
TASK STATUS: PASS (D9.4: PASS; D9: BOUNDED_PROOF for bb_06004280; M-03: READY_FOR_BOUNDED_TEST)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Live Mednafen debug oracle runs across all 5 modes (PURE_INTERPRETER, D8_ONLY, D9_ONLY Run 1, D9_ONLY Run 2, D8_PLUS_D9) proved 100% register parity (23/23 SH-2 registers) at target 0x0600A0F8 (cycle 316309189, delta 0), return site 0x0600428A (cycle 337109623, delta 0, R15=06002ED8), and downstream continuation 0x060042E0 (cycle 387459912, delta 0); core SH-2 interpreter 100% clean and untouched; DUT patch cleanly applied; cold boot determinism verified bit-identical; test_native_indirect unit tests verified with 6 negative controls; 19/19 CTest suites pass across MinGW and Linux WSL.
ACCEPTANCE CRITERIA:
- [x] clean oracle provenance audited (Mednafen 15542666..., sh7095.h and sh7095.inc 100% untouched);
- [x] DUT integration patch isolated and committed under workstreams/T2-D9-indirect/patches/;
- [x] hardware pipeline delayed-branch refill convention implemented in native bridge adapter without touching oracle core;
- [x] target-entry timing parity reproduced at 0x0600A0F8 (pure = 316309189, native = 316309189, delta = 0);
- [x] return site parity established at 0x0600428A (pure = 337109623, native = 337109623, delta = 0, R15 match);
- [x] downstream continuation established at 0x060042E0 (pure = 387459912, native = 387459912, delta = 0);
- [x] all 5 live modes executed and telemetry recorded;
- [x] cold-boot determinism verified bit-identical between independent runs;
- [x] 6 negative controls verified in test_native_indirect;
- [x] evidence documented in workstreams/T2-D9-indirect/d9_4_native_indirect_evidence.md and .json;
- [x] 19/19 CTest suites pass across MinGW and Linux WSL;
- [x] all human-maintained code files <= 500 lines;
- [x] git diff --check green;
- [x] terminal response only in Russian, max 7 bullets.
EVIDENCE AVAILABLE:
- Canonical D9 plan docs/D9_INDIRECT_CONTROL_FLOW_PLAN.md;
- Candidate qualification records workstreams/T2-D9-indirect/candidate_06004280.md and candidate_06004280.json;
- Live D8 regression record workstreams/T2-D9-indirect/d9_2_d8_live_regression.md;
- Live D9.4.1 native indirect evidence records workstreams/T2-D9-indirect/d9_4_native_indirect_evidence.md and d9_4_native_indirect_evidence.json;
- DUT integration patch workstreams/T2-D9-indirect/patches/mednafen_dut_integration.patch;
- Workstream record workstreams/T2-D9-indirect/README.md;
- Unit test suite tests/recomp/test_native_indirect.cpp;
- Automated plan validator test tests/recomp/test_d9_plan.py;
- Decisions record docs/DECISIONS.md.
KNOWN UNKNOWNS:
- Candidate harvester heuristics across full 0TH2.BIN and TH2.LOW binary images (deferred to M-03).
ALLOWED SCOPE:
- Authoritative native indirect override proof integrity repair, clean oracle provenance audit, DUT adapter patch, timing parity reproduction, documentation repair.
OUT OF SCOPE:
- Translating or promoting target 0x0600A0F8, D9.5 multi-target expansion, starting M-03 execution.

## Last verified result

T2-D9.4.1_NATIVE_INDIRECT_PROOF_INTEGRITY_REPAIR_PASS: Clean oracle provenance audited (Mednafen 15542666..., sh7095.h/inc untouched); hardware pipeline delay-slot refill convention verified; 0-cycle delta proven at target entry 0x0600A0F8 (316309189), return site 0x0600428A (337109623), and downstream continuation 0x060042E0 (387459912); 23/23 register parity verified across all checkpoints; cold-boot bit-identical determinism proven; DUT patch recorded; 19/19 CTest suites pass across MinGW and Linux WSL.

## Session checkpoint

CURRENT MILESTONE: D9 — Indirect Control-Flow Handling (docs/D9_INDIRECT_CONTROL_FLOW_PLAN.md)
CURRENT TASK: T2-D9.4.1 — Native Indirect Proof Integrity Repair
TASK STATUS: PASS (D9.4: PASS; D9: BOUNDED_PROOF for bb_06004280; M-03: READY_FOR_BOUNDED_TEST)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: Clean oracle provenance, pipeline delay-slot contract, 0-cycle deltas across target/return/downstream, 23/23 register parity, cold-boot determinism verified; 19/19 CTest suites pass on MinGW and Linux WSL.
FILES CHANGED: src/recomp/native_dispatcher.cpp, tests/recomp/test_native_indirect.cpp, workstreams/T2-D9-indirect/patches/mednafen_dut_integration.patch, workstreams/T2-D9-indirect/d9_4_native_indirect_evidence.md, workstreams/T2-D9-indirect/d9_4_native_indirect_evidence.json, docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/WORKLOG.md, TASK.md.
TESTS RUN: test_native_indirect, test_native_dispatcher, test_block_memory, test_block_exit, test_sh2_block_compiler, test_shadow_positive, test_shadow_negative, test_executable_identity, test_generated_link_isolation, test_d9_plan.py, test_m07_reference.py (--require-external), 19/19 CTest suites pass across MinGW (Debug/Release) and Linux WSL (Debug/Release); 5-mode live Mednafen experiment suite; source file line limit check; git diff --check.
NEW KNOWLEDGE: In SH-2 delayed branching within Mednafen, entering a branch target requires setting Pipe_ID to the delay-slot opcode, Pipe_IF to the first target opcode, and PC to target + 2. Emulating this exact pipeline state during native override transfer guarantees zero cycle drift and eliminates stack displacement on target entry.
OPEN QUESTIONS: None for bb_06004280 proof integrity repair.
EXACT NEXT ACTION: M-03 — Bounded SaturnAutoRE Candidate Harvester Re-evaluation & Indirect Flow Scaling.
