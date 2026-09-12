# Current task

TASK: T2-ASM-12 — Targeted UNKNOWN Caller-Threat Elimination, Region Ownership Proof, and External-Entry Closure
WHY: Advance the ASM-first proof track from the sound T2-ASM-11 baseline (453 resolved, 185 honest unresolved) by systematically decomposing and proving the caller-threat frontier for the 81 UNRESOLVED_EXTERNAL_ENTRY RTS sites and affected UNRESOLVED_CALLER_DOMAIN sites across both executable-source and data-target channels; establishing affirmative consumer-chain proof for literal pool function pointers; applying reachability-exclusion certificates (UNKNOWN_BUT_PROVEN_NO_EXECUTABLE_INGRESS) without erasing data-target relevance; rebuilding canonical entry graph v2 and caller domains v5; resolving the 8 independent tailcall domains; certifying RTS V5; adding 9 new adversarial negative controls P12 (NC-BW..NC-CE, total 91); and updating ownership v4 and closed-world theorems v3 under a strict fail-closed contract.
CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Baseline commit f7b9eabd5d0614fb8f4ef1f452e6709ba8c3c7a7 verified; reporting split reconciled; threat universe rebased (100% of 99 references in DATA literal pools with 0 open consumers); 2,801 false decodes excised; 35,435 UNKNOWN intervals reachability-excluded; 8 tailcall functions bounded (retained fail-closed); RTS V5 certified (510 resolved, 128 unresolved, INVALID_RESOLVED == 0); 91 negative controls pass 100%; 4/4 byte-exact modules, full disc bit-identical SHA-256, Mednafen 6 scenarios zero divergence.
ACCEPTANCE CRITERIA:
- [x] Phase 0: Baseline and reporting integrity (commit f7b9eab..., 4/4 hashes, disc SHA, 82 negative controls, 58 pytest, 26 CTests, reporting reconciliation);
- [x] Phase 1: Threat rebase audit & external-entry threat universe (workstreams/T2-ASM-12/threat_rebase_audit.json, external_threat_universe.json);
- [x] Phase 2: UNKNOWN region clustering & ranking (workstreams/T2-ASM-12/unknown_threat_regions.json);
- [x] Phase 3: Threat source raw-byte validation (alignment, delay slots, surrounding decode);
- [x] Phase 4: Positive data-structure proof & literal consumer chains (workstreams/T2-ASM-12/targeted_data_certificates.json);
- [x] Phase 5: Executability proof for candidate code (workstreams/T2-ASM-12/targeted_code_certificates.json);
- [x] Phase 6: Dual-channel reachability-exclusion certificates (workstreams/T2-ASM-12/reachability_exclusion_certificates.json);
- [x] Phase 7: Synthesized target provenance to real call sinks (workstreams/T2-ASM-12/threat_to_call_sink_provenance.json);
- [x] Phase 8: Generalized false decode audit (workstreams/T2-ASM-12/unknown_false_decode_audit.json);
- [x] Phase 9: Tailcall external domains completion (workstreams/T2-ASM-12/tailcall_external_domains.json);
- [x] Phase 10: Canonical entry graph V2 & threat frontier graph (workstreams/T2-ASM-12/canonical_entry_graph_v2.json, external_threat_frontier.json);
- [x] Phase 11: Targeted dynamic oracle in Mednafen (workstreams/T2-ASM-12/external_threat_dynamic_oracle.json);
- [x] Phase 12: Caller-domain rebuild V5 (workstreams/T2-ASM-12/function_caller_domains_v5.json);
- [x] Phase 13: RTS V5 certifier (tools/asm/rts_v5_certifier.py <= 500 lines, workstreams/T2-ASM-12/rts_completeness_v5.json);
- [x] Phase 14: Independent RTS V5 soundness auditor (tools/asm/rts_v5_soundness_auditor.py <= 500 lines, workstreams/T2-ASM-12/rts_v5_soundness_audit.json, INVALID_RESOLVED == 0);
- [x] Phase 15: PR & caller blocker side effects evaluated;
- [x] Phase 16: Byte ownership V4 (workstreams/T2-ASM-12/executable_byte_partition_v4.json, SH2 UNKNOWN on caller frontier tracked);
- [x] Phase 17: Closed-world theorem V3 (workstreams/T2-ASM-12/closed_world_control_flow_v3.json);
- [x] Phase 18: Negative controls P12 (tests/asm/negative_controls_p12.py, NC-BW..NC-CE, total 91 controls);
- [x] Phase 19: Test suite update & regression gates (tests/asm/test_external_entry_closure.py, test_recovery_gates.py updated);
- [x] Phase 20: Documentation & reporting (docs/reports/EXTERNAL_ENTRY_THREAT_CLOSURE_T2_ASM_12.md, WORKLOG, REVERSE_ENGINEERING, PROJECT_STATE, FILE_MAP, TASK.md);
- [x] Phase 21: Gate evaluation (ASM_90_GATE = 100.00% mnemonic coverage, FULL_ASM_GAME_GATE fail-closed evaluation);
- [x] All human-maintained source/tool/test files strictly <= 500 lines; git diff --check clean; zero commercial assets committed.

EVIDENCE AVAILABLE:
- Canonical RUS binary bytes in .private/rus/
- Baseline commit f7b9eabd5d0614fb8f4ef1f452e6709ba8c3c7a7
- Sound RTS V4 audit in workstreams/T2-ASM-11/rts_completeness_v4.json
- Scorecard in workstreams/ASM_RECOVERY_SCORECARD.json
- Ownership V3 in workstreams/T2-ASM-10/module_byte_ownership_v3.json
- Ownership V4 in workstreams/T2-ASM-12/executable_byte_partition_v4.json

KNOWN UNKNOWNS:
- Resolution of the single upstream tailcall blocker at 0x0602F5C8 in sub_0602F312 (currently 0 callers), which blocks 8 tailcall functions (24 RTS sites);
- Executable classification of the 202 UNKNOWN bytes across 5 intervals on the active caller threat frontier (6 candidate branches);
- 59 residual PR-path sites and 39 open caller-domain sites.

ALLOWED SCOPE:
- Threat rebase, dual-channel reachability exclusion, literal pool consumer chain tracing, tailcall domain auditing, canonical entry graph v2, caller domains v5, RTS V5 certification, negative controls P12.

OUT OF SCOPE:
- Broad 498,392-byte UNKNOWN sweep, sound recovery (T2-SND-01), ASM→C++ translation, metric forcing.

## Last verified result

T2_ASM_12_PASS: Baseline commit f7b9eabd5d0614fb8f4ef1f452e6709ba8c3c7a7. Certified RTS completeness V5: 510/638 resolved (265 exact, 245 finite; 79.94%), 128 honest unresolved (30 external threats across 8 tailcall and 4 branch functions, 59 PR path, 39 caller domain). Calls/jumps 1,588/1,588 (100.0%). Overall indirect 2,098/2,226 (94.25%). Independent soundness audit: INVALID_RESOLVED_CERTIFICATES == 0. 91/91 negative controls pass; 63/63 pytest pass; 41/41 Linux CTests pass; 4/4 modules byte-exact (0 diff bytes); full disc SHA-256 exact; Mednafen 6-scenario suite 0 divergence.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
CURRENT TASK: T2-ASM-12 Targeted UNKNOWN Caller-Threat Elimination, Region Ownership Proof, and External-Entry Closure
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: T2_ASM_12_PASS
FILES CHANGED: tools/asm/threat_rebase_and_universe.py, tools/asm/dual_channel_threat_prover.py, tools/asm/rts_v5_certifier.py, tools/asm/rts_v5_soundness_auditor.py, tests/asm/negative_controls_p12.py, tests/asm/test_external_entry_closure.py, tests/asm/test_recovery_gates.py, tests/asm/negative_controls_p11.py, workstreams/ASM_RECOVERY_SCORECARD.json, docs/reports/EXTERNAL_ENTRY_THREAT_CLOSURE_T2_ASM_12.md, docs/WORKLOG.md, docs/PROJECT_STATE.md, docs/REVERSE_ENGINEERING.md, docs/FILE_MAP.md, TASK.md.
TESTS RUN: 91/91 negative controls pass, 63/63 pytest pass, 41/41 Linux CTests pass, 4/4 module reassembly byte-exactness verified, full disc SHA verified.
NEW KNOWLEDGE: 100% of 99 historical reference sources verified in DATA literal pools with 0 open consumers; 2,801 UNKNOWN edges proved false decodes; active caller threat frontier decarved to 202 bytes across 5 intervals; upstream tailcall blocker isolated to 0x0602F5C8 (sub_0602F312); RTS V5 certified at 510/638 (79.94%).
OPEN QUESTIONS: None.
EXACT NEXT ACTION: Await user review and instructions for next ASM recovery milestone.
