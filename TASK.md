# Current task

TASK: T2-ASM-06 — Indirect Control Flow Resolution, Jump Table Recovery, and Code Denominator Closure
WHY: Resolve indirect control-flow sites across 0TH2.BIN, TH2.LOW, SET07.BIN, and BGM.BIN, drive down unresolved indirect sites from baseline 2,231, recover jump tables, bound RTS caller domains, and reduce residual undecoded gaps towards FULL_ASM_GAME_GATE.
CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Baseline HEAD at ad0e2f5ef1a407bbe592a7bdab197835a6eac4c3; 32/32 negative controls pass (8 base + 8 P3 NC-A..H + 8 P4 NC-I..P + 8 P5 NC-Q..X); 8/8 unit tests in test_indirect_resolution.py pass; 26/26 Linux CTests pass; unresolved indirect sites reduced from 2,231 down to 855 (-61.68% reduction); residual undecoded gaps reduced from 2,206 down to 1,561 (-645 gaps eliminated, -29.24%); 46 jump tables recovered with proven bounds; 134 leaf RTS caller domains bounded.
ACCEPTANCE CRITERIA:
- [x] Phase 0: Baseline gate verified (HEAD at ad0e2f5ef1a407bbe592a7bdab197835a6eac4c3, 24 negative controls green);
- [x] Phase 1: Canonical indirect site inventory in workstreams/T2-ASM-06/indirect_sites.json (2,233 sites, 2 baseline resolved, 2,231 unresolved);
- [x] Phase 2: Structural classification in workstreams/T2-ASM-06/indirect_site_classes.json;
- [x] Phase 3: Constant propagator in tools/asm/constant_propagator.py with call-clobber and memory safety;
- [x] Phase 4: Register provenance engine in tools/asm/register_provenance.py (1,242 PC literal targets resolved);
- [x] Phase 5: Jump table recovery engine in tools/asm/jump_table_recovery.py (46 jump tables with proven bounds and 0 data overlaps);
- [x] Phase 6 & 7: Dynamic target oracle documentation in workstreams/T2-ASM-06/indirect_dynamic_targets.json;
- [x] Phase 8: RTS caller domain resolution in tools/asm/indirect_resolver.py (134 leaf RTS sites bounded, 504 retained as RTS_UNRESOLVED);
- [x] Phase 9 & 10: Call graph and function boundaries in workstreams/T2-ASM-06/call_graph.json (3,019 functions, 5,271 call edges);
- [x] Phase 14: Indirect resolution scorecard in workstreams/T2-ASM-06/indirect_resolution_scorecard.json (1,378 resolved, 855 unresolved);
- [x] Phase 15..17: CFG closure recomputed in workstreams/T2-ASM-06/cfg_closure.json (residual gaps 2,206 -> 1,561, delta = -645);
- [x] Phase 18: Re-evaluate FULL_ASM_GAME_GATE (honestly maintained as NOT_YET_REPROVEN);
- [x] Phase 19: Adversarial negative controls NC-Q .. NC-X in tests/asm/negative_controls_p5.py (32/32 total negative controls pass);
- [x] Phase 21: Unit test suite in tests/asm/test_indirect_resolution.py (8/8 PASS);
- [x] Phase 22: Final report in docs/reports/INDIRECT_CONTROL_FLOW_T2_ASM_06.md and documentation updated;
- [x] Source file line limits <= 500 lines; git diff --check clean; no commercial assets committed.

EVIDENCE AVAILABLE:
- Canonical RUS binary bytes in .private/rus/
- P3 control flow resolution inventory (2,233 indirect sites)
- CDL execution traces, D9 dynamic checkpoints, ASM-01..04 test logs

KNOWN UNKNOWNS:
- 855 residual indirect sites (551 dynamically executed sites in 0TH2.BIN / TH2.LOW using struct function pointers, 304 unexecuted / cold edges);
- 1,561 residual undecoded gaps in 0TH2.BIN and TH2.LOW.

ALLOWED SCOPE:
- ASM-first indirect control-flow resolution, jump tables, constant propagation, call graph recovery, testing, documentation.

OUT OF SCOPE:
- Broad ASM→C++ gameplay translation, emulator integration into production, modifying canonical executable manifests.

## Last verified result

T2_ASM_06_PASS: Resolved 1,378 of 2,233 indirect control flow sites (+1,376 net resolved), reducing unresolved indirect sites from 2,231 down to 855 (-61.68% reduction). Resolved 1,244 of 1,595 INDIRECT_CALL_JUMP sites (77.99%) and 134 of 638 RETURN_FLOW (RTS) sites (21.00%) strictly respecting Rule 1 and Rule 7. Recovered 46 indexed jump tables with proven bounds checks and zero guarded data collisions. Recovered 3,019 function boundaries and 5,271 call edges. Injected 402 proven indirect targets into SH-2 CFG worklist, reducing residual undecoded gaps from 2,206 down to 1,561 (-645 gaps eliminated, -29.24%) and discovering 361 newly confirmed code segments. All 32 negative controls pass (8 base + 8 P3 NC-A..H + 8 P4 NC-I..P + 8 P5 NC-Q..X). All 8 unit tests in test_indirect_resolution.py pass. FULL_ASM_GAME_GATE honestly maintained as NOT_YET_REPROVEN. All files satisfy <= 500 lines policy. git diff --check clean. Zero commercial assets tracked.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
CURRENT TASK: T2-ASM-06 Indirect Control Flow Resolution, Jump Table Recovery, and Code Denominator Closure
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: T2_ASM_06_PASS. Unresolved indirect sites = 855 (down from 2,231). Residual gaps = 1,561 (down from 2,206). 32/32 negative controls pass. 8/8 unit tests pass. 26/26 Linux CTests pass.
FILES CHANGED: tools/asm/constant_propagator.py, tools/asm/register_provenance.py, tools/asm/jump_table_recovery.py, tools/asm/call_graph_builder.py, tools/asm/indirect_resolver.py, tests/asm/negative_controls_p5.py, tests/asm/test_indirect_resolution.py, tests/asm/test_recovery_gates.py, workstreams/T2-ASM-06/*, workstreams/ASM_RECOVERY_SCORECARD.json, docs/reports/INDIRECT_CONTROL_FLOW_T2_ASM_06.md, docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/WORKLOG.md, TASK.md
TESTS RUN: python tests/asm/negative_controls_p5.py (8/8 PASS), python tests/asm/test_indirect_resolution.py (8/8 PASS), python tests/asm/test_recovery_gates.py (32/32 PASS), wsl ctest --test-dir build-linux (26/26 PASS).
NEW KNOWLEDGE: 1,200 JSR calls resolve to static PC literal targets; 46 jump tables use AND_MASK and MOV_LIMIT; 134 RTS sites belong to bounded leaf functions; 645 undecoded gaps resolved to confirmed code and data.
OPEN QUESTIONS: Resolution of remaining 855 indirect sites (struct-field function pointers at 551 dynamically active sites) and closing the remaining 1,561 undecoded gaps.
EXACT NEXT ACTION: Target remaining 855 indirect sites (focusing on 551 dynamically executed sites) or proceed to M68K sound driver / BGM.BIN semantic recovery under T2-SND-01.
