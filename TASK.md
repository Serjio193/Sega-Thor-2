# Current task

TASK: D8 / V-07C — T2-D8.1.1 Native Scheduler/Timing Parity Repair
WHY: Eliminate the +14 cycle drift at continuation checkpoint 0x06004280; reconcile NativeDispatcher cycle cost (27 vs 28 cycles); reconcile interval retirement accounting (6 instructions); achieve cycle-exact parity (delta = 0) at both exit 0x06004012 and continuation checkpoint 0x06004280; verify zero register divergences and 100% fail-closed negative control.
CURRENT MILESTONE: D8 / V-07C (bb_06004000 Authoritative Native Override & Timing Parity)
TASK STATUS: PASS (D8: BOUNDED_PROOF for bb_06004000; V-07C: PASS; POST_D8: ACTIVE)
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Reconciled exact 27-cycle block duration (305462360..305462387) and cycle 305462388 measurement boundary; proved root cause of +14 cycle drift was bypassing SH-2 cache line warming for literal pool 0x06004060..0x0600406F and SDRAM pointer 0x06081C10..0x06081C1F; eliminated drift completely by routing native memory access through CPU[0].MRFP/MWFP and synchronizing bus/cache timestamps; repaired interval retirement accounting in Mednafen to properly count delay slot retirement (Mode 0: 6, Mode 2: 0); proved cycle-exact parity (native_cycle == interpreter_cycle == 307090585, delta = 0 cycles) at continuation checkpoint 0x06004280 across 1.628M cycles; verified 0 register divergences across all 23 CPU registers; verified 100% fail-closed negative control under byte corruption; 12/12 unit test suites passed across Windows MinGW and Linux WSL (Debug and Release).
ACCEPTANCE CRITERIA:
- [x] audit exact Mednafen SH-2 accounting and derive cycle timestamps;
- [x] explain 27 vs 28 cycle discrepancy (27 is block duration; 28 is post-completion of 0x06004012);
- [x] repair retirement interval counter in Mednafen (Mode 0: 6, Mode 2: 0);
- [x] eliminate +14 cycle drift by routing memory through CPU[0].MRFP/MWFP to preserve cache state;
- [x] prove cycle-exact parity at exit 0x06004012 (delta = 0);
- [x] prove cycle-exact parity at continuation checkpoint 0x06004280 (delta = 0, cycle 307090585);
- [x] verify Run A and Run B are bit-identical;
- [x] verify Run E is 100% fail-closed with zero partial commits;
- [x] 12/12 unit test suites passed across 4 configurations (Windows/Linux Debug/Release);
- [x] all human-maintained source/test/build files <= 500 lines;
- [x] update project governance / worklog / roadmap / file map / RE records;
- [x] status remains BOUNDED_PROOF for bb_06004000 (never claim DONE).
EVIDENCE AVAILABLE:
- Workstream record workstreams/T2-D8-V07C-native/README.md;
- Workstream record workstreams/T2-D8-V07C-native/native_override_evidence.md;
- Post-D8 plan docs/POST_D8_SECOND_PASS_PLAN.md;
- Test target test_native_dispatcher and scratch/v07c_results.json.
KNOWN UNKNOWNS:
- Multi-block recompilation chaining and dynamic branch dispatcher scaling for D9;
- Secondary executable TH2.LOW native block promotion;
- Peripheral and SCU interrupt handling in late gameplay loops.
ALLOWED SCOPE:
- Timing parity repair and bounded native override for bb_06004000 only;
- Reusable NativeDispatcher framework;
- Oracle plugin integration and continuation proof to 0x06004280.
OUT OF SCOPE:
- D9 multi-block recompilation;
- Unbounded native execution past verified blocks;
- Claiming D8 whole-recompiler completion.

## Last verified result

`T2-D8.1.1_TIMING_PARITY_PROVEN`: Cycle-exact native scheduler timing parity proven for `bb_06004000` under pinned Mednafen debug oracle on cold boot; original interpreter retired exactly 0 instructions in replaced block; continuation to `0x06004280` verified with ZERO register divergences and ZERO cycle drift (exact delta = 0 cycles at cycle `307090585` vs baseline interpreter); bit-identical cold-boot reproduction confirmed; fail-closed fallback proven under byte corruption without partial native commit; 12/12 tests passed in Debug & Release on Windows MinGW and Linux WSL.

## Session checkpoint

CURRENT MILESTONE: D8 / V-07C (bb_06004000 Authoritative Native Override & Timing Parity)
CURRENT TASK: D8 / V-07C — T2-D8.1.1 Native Scheduler/Timing Parity Repair
TASK STATUS: PASS (D8: BOUNDED_PROOF for bb_06004000; V-07C: PASS; POST_D8: ACTIVE)
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: Cycle-exact timing parity proven for bb_06004000 under Mednafen oracle; 0 retirements in interval; 0 cycle drift and 0 register divergences vs interpreter at continuation 0x06004280 (cycle 307090585); bit-identical cold-boot reproduction; 100% fail-closed fallback; 12/12 tests passed on Windows MinGW & Linux WSL
FILES CHANGED: src/recomp/native_dispatcher.cpp, workstreams/T2-D8-V07C-native/README.md, workstreams/T2-D8-V07C-native/native_override_evidence.md, docs/PROJECT_STATE.md, docs/WORKLOG.md, docs/REVERSE_ENGINEERING.md, TASK.md
TESTS RUN: test_sh2_decoder, test_sh2_l0_semantics, test_sh2_oracle_vector, test_sh2_block, test_executable_identity, test_sh2_block_compiler, test_generated_link_isolation, test_v07a_transition, test_shadow_positive, test_shadow_negative, test_shadow_isolation, test_native_dispatcher (all 12 passed in MinGW Debug/Release and Linux WSL Debug/Release), Python unittest suite (3/3 pass), V-07C verification matrix (5/5 pass, delta=0 cycles), git diff --check, source line limits (all <= 279 lines)
NEW KNOWLEDGE: Cache line warming during basic block execution affects downstream memory latency; routing native memory callbacks through CPU[0].MRFP/MWFP ensures SH-2 cache state and BSC bus latency tracking are 100% synchronized, eliminating all timing divergence
OPEN QUESTIONS: Execution schedule for second-pass external methods (M-01..M-10) before D9 batch scaling
EXACT NEXT ACTION: Execute post-D8 second-pass method experiments (docs/POST_D8_SECOND_PASS_PLAN.md / ADR D-012).
