# Current task

TASK: T2-ASM-09 — Residual RTS Caller-Domain Closure, Address-Taken Function Recovery, and Final Control-Flow Proof
WHY: Resolve the residual 421 RTS return-flow sites from T2-ASM-08, recover closed-world caller domains for address-taken functions, audit potential executable UNKNOWN threats, enforce Rule #5 (data tables are not caller edge sources), certify RTS completeness V2, and update CFG reclosure and partition V2.
CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Re-audited the entire 2,226 canonical indirect site inventory (100% in confirmed code, 0 data/padding overlap); scanned all 1,206 references to residual functions, tracing 838 to resolved JSR call sites and 264 to static non-call data; enforced Rule #5 that data tables in DATA cannot be caller edge sources; audited UNKNOWN-region caller threats proving 252/309 functions clean; certified 456 / 638 RTS sites resolved (71.47%), reducing residual unresolved RTS from 421 down to 182 (-239 sites); overall canonical indirect resolution reached 2,044 / 2,226 (91.82%); computed CFG reclosure V2 expanding CONFIRMED_CODE to 156,694 bytes (+456 bytes) and reducing UNKNOWN to 1,185,214 bytes (-446 bytes); 58/58 negative controls pass (including 8 new P8 controls NC-AQ..NC-AX in negative_controls_p8.py); 5/5 unit tests pass in test_rts_domain_closure.py; 26/26 Linux CTests pass; FULL_ASM_GAME_GATE honestly maintained as NOT_YET_REPROVEN pending whole-module source reassembly pass and resolution of the 182 residual RTS sites and SH-2 UNKNOWN regions.
ACCEPTANCE CRITERIA:
- [x] Phase 0: Re-audit legitimacy of entire 2,226 canonical indirect inventory (100% confirmed code, 0 data/padding overlap);
- [x] Phase 1: Categorize all 421 residual RTS sites (340 ADDRESS_TAKEN_UNBOUNDED, 81 FUNCTION_BOUNDARY_AMBIGUOUS);
- [x] Phase 2: Construct complete control transfer universe (5,298 transfers, 0 canonical BSRF);
- [x] Phase 3: Rebuild canonical call/entry graph with 14,656 edges and 121 recursive SCCs;
- [x] Phase 4: Scan and classify all 1,206 references to residual functions;
- [x] Phase 5: Trace references to operational call sinks (838 calls, 264 noncall data, 104 open);
- [x] Phase 6: Recover residual callback tables and associated call sinks (271 tables);
- [x] Phase 7: Audit residual struct callback dispatch domains;
- [x] Phase 8: Refine function entry boundaries and shared entries (81 refinements);
- [x] Phase 9: Audit tailcall domains and PR inheritance (961 tailcalls);
- [x] Phase 10: Account for UNKNOWN-region caller threats (252/309 clean, 57 fail-closed);
- [x] Phase 11: Issue FunctionCallerCertificates for all 309 functions (227 caller-complete);
- [x] Phase 12: Issue RTSCompletenessV2 certificates (456 resolved, 182 honest unresolved);
- [x] Phase 13: Evaluate closed-world theorem (confirmed code closed-world holds; potential executable closed-world held open);
- [x] Phase 14: Recompute CFG closure V2 (CONFIRMED_CODE: 156,694 bytes, UNKNOWN: 1,185,214 bytes);
- [x] Phase 15: Re-evaluate FULL_ASM_GAME_GATE honestly maintained as NOT_YET_REPROVEN;
- [x] Phase 16: Implement adversarial negative controls NC-AQ..NC-AX (58/58 negative controls pass 100%);
- [x] Phase 17: Comprehensive report docs/reports/RTS_CALLER_DOMAIN_T2_ASM_09.md, WORKLOG.md, REVERSE_ENGINEERING.md, FILE_MAP.md, and PROJECT_STATE.md updated;
- [x] All human-maintained source/tool/test files strictly <= 500 lines; git diff --check clean; no commercial assets committed.

EVIDENCE AVAILABLE:
- Canonical RUS binary bytes in .private/rus/
- Audited indirect site inventory and false decode pointer tables in workstreams/T2-ASM-08/
- 17 machine-readable T2-ASM-09 artifacts in workstreams/T2-ASM-09/
- Scorecard synchronized with partition V2 in workstreams/ASM_RECOVERY_SCORECARD.json

KNOWN UNKNOWNS:
- Full whole-module assembly source reassembly compiler pass across the confirmed code bytes.
- Residual 182 RTS return domains (81 external entry threats in UNKNOWN, 81 boundary ambiguities, 20 open caller domains).
- 511,452 SH-2 UNKNOWN bytes in 0TH2.BIN and TH2.LOW.

ALLOWED SCOPE:
- ASM-first residual RTS domain closure, address-taken recovery, UNKNOWN threat accounting, CFG reclosure V2, testing, documentation.

OUT OF SCOPE:
- Broad ASM→C++ gameplay translation, emulator integration into production, modifying canonical executable manifests.

## Last verified result

T2_ASM_09_AUDITED_PASS: Audited and closed residual RTS caller domains under strict ASM-first evidence rules. Re-audited the entire 2,226 canonical indirect site inventory (1,465 JSR, 121 JMP, 2 BRAF, 638 RTS), confirming 100% in CONFIRMED_CODE with 0 DATA/PADDING overlap. Analyzed all 421 residual RTS sites, indexing 1,206 references across the binary and proving that 838 were literal pool loads consumed by already-resolved JSRs and 264 were static non-call data. Enforced Rule #5 that data tables in DATA cannot be caller edge sources. Audited potential executable UNKNOWN caller threats across 511,452 SH-2 UNKNOWN bytes, proving 252/309 functions clean while fail-closing 57 functions. Certified 456 / 638 RTS sites as resolved (71.47%), reducing residual unresolved RTS from 421 down to 182 (net reduction of 239 sites). Overall indirect resolution reached 2,044 / 2,226 (91.82%) with 100.0% call/jump resolution (1,588 / 1,588). Computed CFG reclosure V2: CONFIRMED_CODE expanded to 156,694 bytes (+456 bytes), UNKNOWN reduced to 1,185,214 bytes (-446 bytes). All 58 negative controls pass 100% (including 8 new P8 controls NC-AQ..NC-AX in negative_controls_p8.py). All 5 unit tests in test_rts_domain_closure.py pass 100%. All 26 native tests in WSL Linux pass 100%. FULL_ASM_GAME_GATE honestly maintained as NOT_YET_REPROVEN pending full whole-module source reassembly pass. All files satisfy <= 500 lines policy. git diff --check clean. Zero commercial assets tracked.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
CURRENT TASK: T2-ASM-09 Residual RTS Caller-Domain Closure, Address-Taken Function Recovery, and Final Control-Flow Proof
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: T2_ASM_09_AUDITED_PASS. Canonical indirect sites = 2,226. Resolved indirect sites = 2,044 / 2,226 (91.82%). Call/Jump resolution = 1,588 / 1,588 (100.00%). RTS resolution = 456 / 638 certified (71.47%), 182 honest unresolved (reduced from 421). Partition V2: CODE = 156,694, DATA = 55,900, PADDING = 59,344, UNKNOWN = 1,185,214 (Total: 1,457,152 bytes). 58/58 negative controls pass. 5/5 unit tests pass. 26/26 Linux tests pass.
FILES CHANGED: tools/asm/canonical_indirect_auditor.py, tools/asm/residual_rts_analyzer.py, tools/asm/canonical_entry_graph.py, tools/asm/call_sink_and_pointer_tracer.py, tools/asm/rts_caller_certifier.py, tools/asm/cfg_reclosure_v2.py, tests/asm/negative_controls_p8.py, tests/asm/test_rts_domain_closure.py, tests/asm/test_recovery_gates.py, workstreams/T2-ASM-09/*, workstreams/ASM_RECOVERY_SCORECARD.json, docs/reports/RTS_CALLER_DOMAIN_T2_ASM_09.md, docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/WORKLOG.md, docs/REVERSE_ENGINEERING.md, TASK.md
TESTS RUN: python tools/asm/canonical_indirect_auditor.py (PASS), python tools/asm/residual_rts_analyzer.py (PASS), python tools/asm/canonical_entry_graph.py (PASS), python tools/asm/call_sink_and_pointer_tracer.py (PASS), python tools/asm/rts_caller_certifier.py (PASS), python tools/asm/cfg_reclosure_v2.py (PASS), python tests/asm/negative_controls_p8.py (8/8 PASS), python -m unittest tests/asm/test_rts_domain_closure.py (5/5 PASS), python tests/asm/test_recovery_gates.py (58/58 PASS), wsl ctest --test-dir build-linux (26/26 PASS).
NEW KNOWLEDGE: 340 of the 421 residual RTS sites from T2-ASM-08 had balanced stack frames and valid PR paths, blocked solely by overly broad address-taken heuristic; 838 function references were literal pool entries consumed by already-resolved JSRs; 264 were static non-call data; data tables in DATA cannot be caller edge sources because PR is set by call instructions; 252/309 functions are clean of UNKNOWN-region caller threats; 456 RTS sites certified resolved; 182 residual RTS sites honestly retained as unresolved; CFG reclosure V2 adds +456 confirmed code bytes and eliminates 446 UNKNOWN bytes.
OPEN QUESTIONS: Full whole-module assembly source reassembly compiler pass across the confirmed code bytes; resolution of remaining 182 RTS sites and 511,452 SH-2 UNKNOWN bytes under T2-ASM-10.
EXACT NEXT ACTION: Proceed to T2-ASM-10: Whole-Module Source Reassembly & Gap Decarving.
