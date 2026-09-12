# Current task

TASK: T2-ASM-11 — Context-Sensitive Shared-Epilogue Decomposition, Multi-Entry CFG Normalization, and Residual RTS Return-Domain Closure
WHY: Advance the ASM-first proof track from the sound T2-ASM-10.1 baseline (420 resolved, 218 honest unresolved) by decomposing shared epilogues across the 81 UNRESOLVED_PR_PATH sites using context-sensitive PR dataflow; auditing and resolving the 56 UNRESOLVED_CALLER_DOMAIN sites (including formalizing the 43 revoked return edges from data literal pools as FALSE_CALL_EDGE); targeting high-leverage UNKNOWN caller threats blocking the 81 UNRESOLVED_EXTERNAL_ENTRY sites; certifying RTS V4 without metric-forcing; adding 8 new negative controls P11 (NC-BO..NC-BV, total 82); and updating the control-flow scorecard and gate status under a strict fail-closed contract.
CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Baseline commit 2575529a047690eaa3f07702b5f19b86f08c9a1c verified; exact classification of the 218 residual RTS sites documented; root cause of the 43 revoked return edges proven to be FALSE_CALL_EDGE from literal pool lower halfwords (e.g. 0xBA88 matching BSR); context-sensitive PR dataflow model established.
ACCEPTANCE CRITERIA:
- [x] Phase 0: Baseline reproduction (commit 2575529a..., 4/4 hashes, disc SHA, Mednafen 6-scenario, 74 negative controls, 53 pytest, 26 CTests);
- [x] Phase 1: Residual 218 site inventory V4 (workstreams/T2-ASM-11/residual_rts_v4_inventory.json);
- [x] Phase 2: Context-sensitive CFG (workstreams/T2-ASM-11/context_sensitive_cfg.json);
- [x] Phase 3: Shared epilogue census & clustering (workstreams/T2-ASM-11/shared_epilogue_clusters.json);
- [x] Phase 4: Context-sensitive PR engine (tools/asm/context_sensitive_pr_engine.py <= 500 lines);
- [x] Phase 5: Epilogue return partitioning & tailcall PR contexts (workstreams/T2-ASM-11/shared_epilogue_return_domains.json, tailcall_pr_contexts_v2.json);
- [x] Phase 6: Function boundary normalization (workstreams/T2-ASM-11/function_boundary_v4.json);
- [x] Phase 7: Caller-domain audit & false call edge formalization (workstreams/T2-ASM-11/caller_return_domain_audit.json);
- [x] Phase 8: Revalidation of the 43 revoked return edges (proven FALSE_CALL_EDGE);
- [x] Phase 9: Return domain reconstruction for caller-complete functions;
- [x] Phase 10: Tail-merge epilogue isolation & stack frame generation tracking;
- [x] Phase 11: Dynamic validation in Mednafen (if needed to confirm candidate contexts);
- [x] Phase 12: Targeted external threats analysis (workstreams/T2-ASM-11/targeted_external_threats.json);
- [x] Phase 13: RTS V4 certifier (tools/asm/rts_v4_certifier.py <= 500 lines, workstreams/T2-ASM-11/rts_completeness_v4.json);
- [x] Phase 14: Independent RTS V4 soundness auditor (tools/asm/rts_v4_soundness_auditor.py <= 500 lines, workstreams/T2-ASM-11/rts_v4_soundness_audit.json);
- [x] Phase 15: Invariant verification (INVALID_RESOLVED_CERTIFICATES == 0, zero-element domains == 0, return PCs in DATA == 0);
- [x] Phase 16: Zero-forcing check (certifier derived dynamically from proof artifacts);
- [x] Phase 17: Adversarial negative controls P11 (tests/asm/negative_controls_p11.py, NC-BO..NC-BV, total 82);
- [x] Phase 18: Test suite update (tests/asm/test_shared_epilogue_closure.py, test_recovery_gates.py updated);
- [x] Phase 19: Full-disc & Mednafen invariants verified;
- [x] Phase 20: Control-flow scorecard & gate status update (workstreams/ASM_RECOVERY_SCORECARD.json);
- [x] Phase 21: Documentation & reporting (docs/reports/SHARED_EPILOGUE_CLOSURE_T2_ASM_11.md, WORKLOG, REVERSE_ENGINEERING, PROJECT_STATE, FILE_MAP, TASK.md);
- [x] All human-maintained source/tool/test files strictly <= 500 lines; git diff --check clean; zero commercial assets committed.

EVIDENCE AVAILABLE:
- Canonical RUS binary bytes in .private/rus/
- Baseline commit 2575529a047690eaa3f07702b5f19b86f08c9a1c
- Sound RTS V3.1 audit in workstreams/T2-ASM-10-1/rts_completeness_v3_1.json
- Scorecard in workstreams/ASM_RECOVERY_SCORECARD.json
- T2-ASM-11 artifacts in workstreams/T2-ASM-11/

KNOWN UNKNOWNS:
- 185 residual unresolved RTS sites: 81 UNRESOLVED_EXTERNAL_ENTRY, 59 UNRESOLVED_PR_PATH, 45 UNRESOLVED_CALLER_DOMAIN;
- 498,392 SH-2 UNKNOWN bytes awaiting future targeted decarving.

ALLOWED SCOPE:
- Context-sensitive PR dataflow, shared epilogue decomposition, caller-domain audit, false call edge excision, boundary normalization, RTS V4 certification, negative controls P11, scorecard updates.

OUT OF SCOPE:
- Broad 498,392-byte UNKNOWN sweep, sound recovery (T2-SND-01), ASM→C++ translation, metric forcing.

## Last verified result

T2_ASM_11_PASS: Context-sensitive shared-epilogue decomposition and residual RTS return-domain closure complete. 630/638 PR paths proven (62 stack slots, 17 leaf, 2 ambiguous). Function boundaries normalized resolving artificial splits. 14,656 entry edges audited; 2,288 false call edges from literal pools excised (formalizing the 43 revoked return edges as FALSE_CALL_EDGE). RTS V4 certified: 453 / 638 (71.00%) resolved, 185 / 638 (29.00%) honest unresolved (+33 net resolved sites: 22 PR + 11 caller domain). Independent soundness audit: 0 violations across all 638 certificates (INVALID_RESOLVED_CERTIFICATES == 0, 0 zero-element domains, 0 data returns). Overall canonical indirect resolution: 2,041 / 2,226 (91.69%), ASM_90_GATE = PASS. 82/82 adversarial negative controls pass (8 new P11 NC-BO..NC-BV); 58/58 pytest pass; 26/26 Linux CTests pass; 4/4 modules byte-exact (0 differing bytes); full-disc SHA-256 bit-identical; Mednafen 6-scenario suite 0 divergence.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
CURRENT TASK: T2-ASM-11 Context-Sensitive Shared-Epilogue Decomposition, Multi-Entry CFG Normalization, and Residual RTS Return-Domain Closure
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: T2_ASM_11_PASS
FILES CHANGED: TASK.md, docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/REVERSE_ENGINEERING.md, docs/WORKLOG.md, docs/reports/SHARED_EPILOGUE_CLOSURE_T2_ASM_11.md, tests/asm/negative_controls_p11.py, tests/asm/test_recovery_gates.py, tests/asm/test_shared_epilogue_closure.py, tools/asm/caller_return_domain_auditor.py, tools/asm/context_sensitive_pr_engine.py, tools/asm/rts_v4_certifier.py, tools/asm/rts_v4_soundness_auditor.py, workstreams/ASM_RECOVERY_SCORECARD.json, workstreams/T2-ASM-11/
TESTS RUN: 82/82 negative controls, 58/58 pytest, 26/26 Linux CTests, 4/4 reassembly, full-disc SHA, 6 Mednafen scenarios.
NEW KNOWLEDGE: 43 revoked return edges proven to be literal pool false call decodes (2,288 excised); shared epilogues successfully decomposed; 453/638 RTS sites soundly certified (0 invalid).
OPEN QUESTIONS: None for T2-ASM-11.
EXACT NEXT ACTION: Propose T2-ASM-12 as next milestone. STOP.
