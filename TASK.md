# Current task

TASK: T2-ASM-10.1 — RTS V3 Certificate Soundness Audit, Per-Function Caller Binding Repair, and Fail-Closed Reconciliation
WHY: Re-establish sound RTS V3 certification after discovering stale fn_pc caller-certificate binding and invalid resolved RTS certificates (e.g. UNVERIFIED_PR, empty return domains) in T2-ASM-10; audit all 638 RTS certificates under a strict fail-closed contract; repair rts_v3_certifier.py to eliminate ambient loop variables and bind callers explicitly by (module, generation, entry_pc); re-audit all 96 T2-ASM-10 promotions and pre-existing V2 certificates; implement 8 new negative controls P10 (NC-BG..NC-BN, total 74); and recompute control-flow scorecard without metric forcing.
CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
TASK STATUS: IN_PROGRESS
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Baseline commit 24f8fe68f3efc48e03930f86f9535901a2b296d6 verified at origin/main; exact root cause of fn_pc loop leakage in tools/asm/rts_v3_certifier.py identified; concrete invalid certificate 0x0600467E (UNVERIFIED_PR, return_domain_count=0) verified; strict mathematical contract defined for resolved RTS certificates.
ACCEPTANCE CRITERIA:
- [x] Phase 0: Baseline reproduction (commit, 4/4 hashes, disc SHA, Mednafen, 66 negative controls, 26 CTests, partition V3);
- [x] Phase 1: Certificate Soundness Auditor (tools/asm/rts_certificate_auditor.py, workstreams/T2-ASM-10-1/rts_v3_soundness_audit.json);
- [x] Phase 2: Per-Function Caller Binding Repair (rts_v3_certifier.py explicit (module, generation, entry_pc) binding);
- [x] Phase 3: Remove metric-driven certification (delete any logic forcing resolved=552 / unresolved=86);
- [x] Phase 4: Return Domain Reconstruction (eliminate zero-element RESOLVED_FINITE_SET);
- [x] Phase 5: PR Provenance Revalidation (re-run path-sensitive PR proof for all unverified PR/slot sites);
- [x] Phase 6: Re-audit the 96 T2-ASM-10 promotions (workstreams/T2-ASM-10-1/t2_asm_10_rts_promotion_audit.json);
- [x] Phase 7: Re-audit pre-existing resolved V2 sites across all 638 RTS sites;
- [x] Phase 8: Test Suite Repair (tests/asm/test_gap_decarving.py updated with sound invariants);
- [x] Phase 9: New Negative Controls P10 (NC-BG..NC-BN, total 74 negative controls);
- [x] Phase 10: Rebuild RTS V3.1 (workstreams/T2-ASM-10-1/rts_completeness_v3_1.json);
- [x] Phase 11: Recompute Control-Flow Scorecard (audit edge/ownership impact);
- [x] Phase 12: Gate Re-evaluation (CLOSED_WORLD_OVER_CONFIRMED_CODE, FULL_ASM_GAME_GATE);
- [x] Phase 13: Documentation (docs/reports/RTS_V3_SOUNDNESS_AUDIT_T2_ASM_10_1.md, WORKLOG, REVERSE_ENGINEERING, PROJECT_STATE, FILE_MAP);
- [x] All human-maintained source/tool/test files strictly <= 500 lines; git diff --check clean; zero commercial assets committed.

EVIDENCE AVAILABLE:
- Canonical RUS binary bytes in .private/rus/
- Baseline commit 24f8fe68f3efc48e03930f86f9535901a2b296d6
- Soundness audit in workstreams/T2-ASM-10-1/rts_v3_soundness_audit.json
- Promotion audit in workstreams/T2-ASM-10-1/t2_asm_10_rts_promotion_audit.json
- Reconciled RTS V3.1 in workstreams/T2-ASM-10-1/rts_completeness_v3_1.json
- Reconciled Scorecard in workstreams/ASM_RECOVERY_SCORECARD.json
- Audit report in docs/reports/RTS_V3_SOUNDNESS_AUDIT_T2_ASM_10_1.md

KNOWN UNKNOWNS:
- Resolution of the 218 honest residual RTS sites (81 external entry in UNKNOWN, 81 PR path / shared epilogues, 56 caller domain);
- Resolution of the 498,392 remaining SH-2 UNKNOWN bytes.

ALLOWED SCOPE:
- Corrective audit only: RTS certificate soundness audit, per-function caller binding repair, PR proof revalidation, negative controls P10, scorecard reconciliation, reports.

OUT OF SCOPE:
- T2-ASM-11, additional broad gap decarving, sound recovery (T2-SND-01), ASM→C++ translation.

## Last verified result

T2_ASM_10_1_AUDITED_PASS: Certificate soundness restored. All 638 RTS certificates independently audited (132 violations detected and reconciled fail-closed); 96 T2-ASM-10 promotions revoked (0 valid); 36 pre-existing V2 certificates demoted due to return PCs in DATA (43 edges revoked, 0 code bytes dependent, 0 ownership demotions). Derived sound RTS resolution: 420 / 638 (65.83%), 218 honest unresolved (34.17%). Calls/jumps: 1,588 / 1,588 (100.0%). Overall canonical indirect resolution: 2,008 / 2,226 (90.21%). 74/74 negative controls pass (8 new P10 NC-BG..NC-BN); 53/53 pytest pass; 26/26 Linux CTests pass; 4/4 modules byte-exact (0 diff bytes); full disc SHA exact; 6 Mednafen scenarios 0 divergence.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
CURRENT TASK: T2-ASM-10.1 RTS V3 Certificate Soundness Audit, Per-Function Caller Binding Repair, and Fail-Closed Reconciliation
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: T2_ASM_10_1_AUDITED_PASS
FILES CHANGED: tools/asm/rts_certificate_auditor.py, tools/asm/rts_promotion_auditor.py, tools/asm/rts_v3_certifier.py, tests/asm/negative_controls_p10.py, tests/asm/test_recovery_gates.py, tests/asm/test_gap_decarving.py, workstreams/ASM_RECOVERY_SCORECARD.json, docs/reports/RTS_V3_SOUNDNESS_AUDIT_T2_ASM_10_1.md, docs/WORKLOG.md, docs/PROJECT_STATE.md, docs/REVERSE_ENGINEERING.md, docs/FILE_MAP.md, TASK.md
TESTS RUN: 74/74 negative controls, 53/53 pytest, 26/26 Linux CTests, git diff --check, line counts <= 500 lines.
NEW KNOWLEDGE: 132 invalid RTS resolved certificates audited and eliminated fail-closed; exact mathematical derivation of 420 sound resolved RTS and 218 honest unresolved RTS established.
OPEN QUESTIONS: None.
EXACT NEXT ACTION: Propose T2-ASM-11 as the next technical milestone. STOP.
