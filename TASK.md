# Current task

TASK: T2-ASM-08 — Return Address Provenance, Final Indirect Dispatch Closure, and FULL_ASM_GAME_GATE Push (Audited)
WHY: Audit and harden T2-ASM-08 control-flow closure: remove 7 false-positive BSRF table decodes, re-verify 36 JSR sites from raw binary bytes, replace PRProvenanceEngine with path-sensitive symbolic stack-slot tracking without synthetic placeholders, derive honest resolution metrics, retract overpromoted code, and re-evaluate FULL_ASM_GAME_GATE.
CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Reclassified 3 literal pointer tables in 0TH2.BIN as FUNCTION_POINTER_TABLE_DATA, eliminating 7 false BSRF sites and correcting canonical indirect denominator to 2,226 (canonical BSRF count = 0); verified all 36 residual JSR sites from raw binary bytes via forward reaching-definitions dataflow with delay slots (36/36 proven exact single, zero reaching clobbers); modeled path-sensitive symbolic stack-slot tracking (exact R15 delta, slot S-4 spill/reload pairing, leaf zero PR-write checks); issued machine-readable RTS completeness certificates with zero synthetic placeholders (CALLERS_OF_*), certifying 217 RTS sites as RESOLVED_FINITE_SET and retaining 421 honest unresolved RTS sites; derived total canonical resolution at 1,805 / 2,226 (81.09%) with 100% CALL/JUMP resolution (1,588 / 1,588); whole-module byte carver protected pointer tables, retracted 1,292 invalid code bytes back to UNKNOWN/DATA, and reduced executable UNKNOWN bytes by -66,203 bytes down to 1,185,660; 50/50 negative controls pass (including NC-AO and NC-AP in negative_controls_p7.py); 6/6 unit tests in test_return_provenance.py pass; FULL_ASM_GAME_GATE honestly maintained as NOT_YET_REPROVEN pending full whole-module source reassembly compiler pass.
ACCEPTANCE CRITERIA:
- [x] Phase 0: Reclassify 7 pointer-table halfwords as DATA (canonical denominator: 2,226; canonical BSRF = 0);
- [x] Phase 1: Re-verify all 36 JSR sites from raw binary bytes using forward dataflow with delay slots (36/36 proven);
- [x] Phase 2: Audited call graph with SCC decomposition, separating internal recursion from external callers;
- [x] Phase 3: Path-sensitive symbolic stack and PR tracking with rts_completeness_certificates.json (zero synthetic placeholders; 217 certified, 421 honest unresolved);
- [x] Phase 4: Master indirect resolver with derived resolution metrics (1,805 resolved / 2,226 canonical; 1,588/1,588 call/jump, 217/638 RTS);
- [x] Phase 5: Executable byte carver protecting pointer tables, retracting 1,292 invalid code bytes, and reducing UNKNOWN by -66,203 bytes;
- [x] Phase 6: Adversarial negative controls NC-AO and NC-AP implemented (50/50 total negative controls pass 100%);
- [x] Phase 7: Unit tests in tests/asm/test_return_provenance.py updated with invariant assertions (6/6 PASS);
- [x] Phase 8: FULL_ASM_GAME_GATE honestly maintained as NOT_YET_REPROVEN;
- [x] Phase 9: Comprehensive report docs/reports/RETURN_PROVENANCE_T2_ASM_08.md, WORKLOG.md, REVERSE_ENGINEERING.md, FILE_MAP.md, and PROJECT_STATE.md updated;
- [x] All human-maintained source/tool/test files strictly <= 500 lines; git diff --check clean; no commercial assets committed.

EVIDENCE AVAILABLE:
- Canonical RUS binary bytes in .private/rus/
- Master indirect site inventory, call graph, and function boundaries in workstreams/T2-ASM-06/
- Struct site inventory, field layouts, proven writers, and callback tables in workstreams/T2-ASM-07/
- Audited pointer tables, raw JSR proofs, audited call graph, RTS certificates, master scorecard, CFG closure, and module partitions in workstreams/T2-ASM-08/

KNOWN UNKNOWNS:
- Full whole-module assembly source reassembly compiler pass across the confirmed code bytes.
- Residual 421 RTS return domains with open or unmodeled caller contexts.

ALLOWED SCOPE:
- ASM-first indirect dispatch and return address resolution, PR provenance, byte carving, testing, documentation.

OUT OF SCOPE:
- Broad ASM→C++ gameplay translation, emulator integration into production, modifying canonical executable manifests.

## Last verified result

T2_ASM_08_AUDITED_PASS: Audited and hardened T2-ASM-08 indirect control-flow closure. Reclassified 3 literal pointer tables in 0TH2.BIN as FUNCTION_POINTER_TABLE_DATA, eliminating 7 false BSRF sites and establishing the canonical indirect denominator at 2,226 (canonical BSRF count = 0). Verified all 36 residual JSR sites directly from raw binary bytes via forward reaching-definitions dataflow with delay slots (36/36 proven exact single, zero clobbers). Built audited call graph with SCC decomposition (11,648 validated edges). Implemented path-sensitive symbolic stack-slot and PR tracking, generating machine-readable rts_completeness_certificates.json with zero synthetic placeholders (CALLERS_OF_*); certified 217 RTS sites as RESOLVED_FINITE_SET while honestly retaining 421 RTS sites with open/unmodeled caller domains as UNRESOLVED. Reconciled master indirect scorecard: 1,805 / 2,226 resolved (81.09%; 1,588 / 1,588 CALL/JUMP [100%], 217 / 638 RTS [34.01%]). Recomputed whole-module CFG worklist closure: protected pointer tables as data, retracted 1,292 invalid code bytes back to UNKNOWN/DATA, and reduced executable UNKNOWN bytes by -66,203 bytes (from 1,251,863 down to 1,185,660). All 50 negative controls pass 100% (including NC-AO and NC-AP in negative_controls_p7.py). All 6 unit tests in test_return_provenance.py pass 100%. FULL_ASM_GAME_GATE honestly maintained as NOT_YET_REPROVEN pending whole-binary source reassembly compiler pass. All files satisfy <= 500 lines policy. git diff --check clean. Zero commercial assets tracked.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
CURRENT TASK: T2-ASM-08 Return Address Provenance, Final Indirect Dispatch Closure, and FULL_ASM_GAME_GATE Push (Audited)
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: T2_ASM_08_AUDITED_PASS. Canonical indirect sites = 2,226 (7 false BSRF decodes removed, canonical BSRF = 0). Resolved indirect sites = 1,805 / 2,226 (81.09%). Call/Jump resolution = 1,588 / 1,588 (100.00%). RTS resolution = 217 / 638 certified (34.01%), 421 honest unresolved. Executable UNKNOWN byte reduction = -66,203 bytes (down to 1,185,660, with 1,292 code bytes retracted). 50/50 negative controls pass. 6/6 unit tests pass.
FILES CHANGED: tools/asm/pointer_table_classifier.py, tools/asm/raw_byte_jsr_tracer.py, tools/asm/audited_call_graph_builder.py, tools/asm/pr_provenance_engine.py, tools/asm/final_indirect_resolver.py, tools/asm/executable_byte_carver.py, tests/asm/negative_controls_p7.py, tests/asm/test_return_provenance.py, tests/asm/test_recovery_gates.py, workstreams/T2-ASM-08/*, workstreams/ASM_RECOVERY_SCORECARD.json, docs/reports/RETURN_PROVENANCE_T2_ASM_08.md, docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/WORKLOG.md, docs/REVERSE_ENGINEERING.md, TASK.md
TESTS RUN: python tests/asm/pointer_table_classifier.py (PASS), python tools/asm/raw_byte_jsr_tracer.py (36/36 PASS), python tools/asm/audited_call_graph_builder.py (PASS), python tools/asm/pr_provenance_engine.py (638/638 PASS), python tools/asm/final_indirect_resolver.py (PASS), python tools/asm/executable_byte_carver.py (PASS), python tests/asm/negative_controls_p7.py (10/10 PASS), python tests/asm/test_recovery_gates.py (50/50 PASS), python -m unittest tests/asm/test_return_provenance.py (6/6 PASS).
NEW KNOWLEDGE: 7 historical BSRF sites were false decodes of function pointer high words in 3 literal pointer tables; 36 JSR sites verified directly from raw bytes via reaching definitions dataflow; 217 RTS sites certified under strict path-sensitive PR stack slot and caller domain contracts with zero synthetic placeholders; 421 RTS sites honestly retained as unresolved; 1,292 invalid code bytes retracted back to UNKNOWN/DATA.
OPEN QUESTIONS: Full whole-module assembly source reassembly compiler pass across the confirmed code bytes; M68K sound driver / BGM.BIN semantic recovery under T2-SND-01.
EXACT NEXT ACTION: Proceed to next scheduled roadmap milestone: whole-module assembly source reassembly pass or M68K sound driver / BGM.BIN semantic recovery under T2-SND-01.
