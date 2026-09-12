# Current task

TASK: T2-ASM-10 — Whole-Module Source Reassembly, SH-2 Gap Decarving, Residual RTS Discharge, and FULL_ASM_GAME_GATE Finalization
WHY: Produce reproducible whole-module assembly-source roundtrip for canonical modules without committing commercial binary bytes; decarve and classify SH-2 UNKNOWN regions by affirmative evidence; perform PR-path and shared-exit refinement on the 81 UNRESOLVED_PR_PATH sites; re-evaluate residual RTS caller domains; evaluate closed-world theorems V2; implement negative controls P9 (NC-AY..NC-BF, total 66); and honestly evaluate FULL_ASM_GAME_GATE.
CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Whole-module assembly source reassembled with 0 differing bytes across all 4 canonical game modules (0TH2.BIN, TH2.LOW, SET07.BIN, BGM.BIN); multi-build determinism 100% bit-for-bit identical; full disc SHA-256 (fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8) byte-exact; 6 dynamically discovered Mednafen gameplay scenarios passed with 0 divergence and 0 cycle drift; 13,060 bytes literal pools promoted to DATA in Partition V3; 96 residual RTS sites discharged (552/638 resolved, 86 residual); 66/66 negative controls pass (100%); 53/53 pytest pass; 26/26 Linux CTests pass; FULL_ASM_GAME_GATE honestly evaluated as NOT_YET_REPROVEN due to 86 residual RTS sites and 498,392 SH-2 UNKNOWN bytes.
ACCEPTANCE CRITERIA:
- [x] Phase 0: Baseline / Push / Integrity Gate (10/10 verified);
- [x] Phase 1 & 2: Source Reassembly Architecture & Commercial Byte Hygiene (workstreams/T2-ASM-10/reassembly_model.json);
- [x] Phase 3: Canonical Byte Ownership Map V3 (workstreams/T2-ASM-10/module_byte_ownership_v3.json);
- [x] Phase 4, 5, 6, 7, 8: Source Emitter, Toolchain & Integrity Audits (tools/asm/source_reassembly_emitter.py, assembler_environment.json, instruction_roundtrip.json);
- [x] Phase 9, 10, 11, 12, 13, 14: UNKNOWN Region Census & Gap Decarving (tools/asm/sh2_gap_decarver.py, sh2_unknown_inventory.json, promotion certificates);
- [x] Phase 15: Shared Exit / PR-Path Refinement (workstreams/T2-ASM-10/pr_path_refinements.json);
- [x] Phase 16: Residual RTS Threat Correlation (workstreams/T2-ASM-10/rts_gap_correlation.json);
- [x] Phase 17: RTS Certificates V3 (workstreams/T2-ASM-10/rts_completeness_v3.json);
- [x] Phase 18, 19, 20, 21, 22: Module Build, Binary Diff, Determinism, Full Disc & Mednafen Suite (0 diff bytes, SHA match, 0 divergence);
- [x] Phase 23 & 24: Gap Decarving Scorecard & Closed-World Theorem V2 (closed_world_control_flow_v2.json);
- [x] Phase 25 & 26: Negative Controls P9 (NC-AY..NC-BF, total 66) & Unit Tests (test_whole_module_reassembly.py, test_gap_decarving.py);
- [x] Phase 27 & 28: Scorecard, Documentation & FULL_ASM_GAME_GATE Finalization;
- [x] All human-maintained source/tool/test files strictly <= 500 lines; git diff --check clean; no commercial assets committed.

EVIDENCE AVAILABLE:
- Canonical RUS binary bytes in .private/rus/
- 16 machine-readable T2-ASM-10 artifacts in workstreams/T2-ASM-10/
- Scorecard synchronized with partition V3 in workstreams/ASM_RECOVERY_SCORECARD.json
- Comprehensive technical report in docs/reports/WHOLE_MODULE_REASSEMBLY_T2_ASM_10.md

KNOWN UNKNOWNS:
- Exact semantic role of the 498,392 remaining SH-2 UNKNOWN bytes (unreferenced subroutines, unused data, or asset streams);
- Exact entry mechanisms for the 22 residual external-threat RTS sites;
- CFG structure of the 44 residual shared-epilogue RTS sites.

ALLOWED SCOPE:
- Whole-module source reassembly, SH-2 gap decarving, PR path refinement, RTS caller domain re-evaluation, closed-world theorems V2, tests, documentation.

OUT OF SCOPE:
- Broad ASM→C++ gameplay translation, M68K/BGM semantic reverse engineering, modifying canonical manifests.

## Last verified result

T2_ASM_10_AUDITED_PASS: Achieved reproducible whole-module assembly source reassembly across all 4 binaries (0TH2.BIN, TH2.LOW, SET07.BIN, BGM.BIN) with 0 differing bytes and bit-for-bit multi-build determinism. Full reconstructed disc matches canonical SHA-256 (fe11d2fb...) bit-exact. Passed all 6 dynamically discovered Mednafen gameplay scenarios with zero cycle drift and zero register divergence. Promoted 13,060 bytes literal pools to DATA_LITERAL_POOL in Partition V3, reducing SH-2 UNKNOWN to 498,392 bytes. Resolved 43 PR path sites via symbolic tracing and discharged 59 external threats via Partition V3 audit, certifying 552 / 638 RTS sites (86.52%) and reducing residual RTS to 86. Overall indirect resolution reached 2,140 / 2,226 (96.14%). Closed-world theorem over confirmed code PROVEN. All 66 negative controls PASS (including 8 new P9 controls NC-AY..NC-BF). All 53 pytest unit tests PASS. All 26 Linux CTests PASS. FULL_ASM_GAME_GATE honestly maintained as NOT_YET_REPROVEN pending resolution of the 86 residual RTS sites and 498,392 SH-2 UNKNOWN bytes.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
CURRENT TASK: T2-ASM-10 Whole-Module Source Reassembly, SH-2 Gap Decarving, Residual RTS Discharge, and FULL_ASM_GAME_GATE Finalization
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: T2-ASM-10 complete with all 28 phases verified, 66/66 negative controls pass, 53/53 pytest pass, 26/26 Linux CTests pass, and full documentation recorded.
FILES CHANGED: tools/asm/source_reassembly_emitter.py, tools/asm/sh2_gap_decarver.py, tools/asm/pr_path_refiner.py, tools/asm/rts_v3_certifier.py, tests/asm/negative_controls_p9.py, tests/asm/test_whole_module_reassembly.py, tests/asm/test_gap_decarving.py, tests/asm/test_recovery_gates.py, workstreams/ASM_RECOVERY_SCORECARD.json, workstreams/T2-ASM-10/*, docs/reports/WHOLE_MODULE_REASSEMBLY_T2_ASM_10.md, docs/WORKLOG.md, docs/REVERSE_ENGINEERING.md, docs/PROJECT_STATE.md, docs/FILE_MAP.md, TASK.md.
TESTS RUN: pytest tests/asm (53/53 PASS), python tests/asm/test_recovery_gates.py (66/66 PASS), wsl ctest --test-dir build-linux (26/26 PASS), Mednafen gameplay scenarios (6/6 PASS).
NEW KNOWLEDGE: 103 apparent threats in T2-ASM-09 were in confirmed code/data; under Rule #5 data cannot be caller edge sources; 19 RTS sites were pure leaf routines; 24 sites were severed by boundary heuristics; 38 sites are proven shared epilogues.
OPEN QUESTIONS: None for T2-ASM-10.
EXACT NEXT ACTION: Review T2-ASM-10 deliverables, commit, and prepare the next milestone plan according to project roadmap.
