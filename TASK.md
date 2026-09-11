# Current task

TASK: T2-ASM-INTEGRITY-04 — Purify Dynamic Execution Evidence, Perform Instruction-Level P3 CFG Closure, Reconcile P3 Code into Canonical Manifests, and Re-verify FULL_ASM_GAME_GATE
WHY: Fulfill all findings of independent integrity review: cleanly bifurcate byte vs instruction-PC execution evidence, resolve all P3 gaps with instruction-level delay-slot and literal-pool aware CFG worklist, reconcile all confirmed code into canonical manifests with proven mnemonics, verify bit-exact reassembly and disc parity, enforce 16 negative controls (including 8 new P3 NCs), and re-verify FULL_ASM_GAME_GATE = PASS. Broad C++ translation remains strictly frozen.

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015, ADR D-019)
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Baseline origin/main 4a03b83bd3d8dfee02cd59c051b5bdd1ab832b3d verified. Executed PC union purified (63,216 byte addresses, 16 even-aligned instruction PCs, 0 manifest-derived, 0 missing artifacts, 0x0600428A confirmed from D9). Instruction-level P3 CFG worklist closed 3,927 gaps (CONFIRMED_CODE: 2,685, PROVEN_DATA: 643, PROVEN_PADDING: 178, PROVEN_UNREACHABLE: 421; 0 unresolved unknowns). Manifest reconciliation complete: confirmed code denominator expanded from 56,166 to 95,422 bytes (87,344 in 0TH2.BIN, 8,036 in TH2.LOW, 12 in SET07.BIN, 30 in BGM.BIN) with 100.00% mnemonic coverage (0 bytes pending). Rebuilt modules byte-exact with 0 relocations; full disc SHA-256 fe11d2fb... verified; Mednafen cold boot (6 checkpoints) and 6 gameplay scenarios verified with zero divergence; 16/16 negative controls pass; 41/41 CTest Windows and 40/40 CTest Linux pass.

ACCEPTANCE CRITERIA:
- [x] Baseline verified at 4a03b83; FULL_ASM_GAME_GATE reset to NOT_YET_REPROVEN during execution; CPLUSPLUS_TRANSLATION = FROZEN;
- [x] Purify dynamic execution evidence union: separate executed byte addresses (63,216) from instruction PCs (16), zero manifest-derived entries, zero unaligned PCs, direct D9 parse with SHA-256 verification;
- [x] Instruction-level P3 CFG worklist closure using Thor SH-2 decoder: delay slots modeled, literal pool accesses marked proven data, 3,927 gaps partitioned with 0 unresolved unknowns;
- [x] Reconcile P3 confirmed code into manifests: 0TH2.BIN (87,344 bytes code/mnemonic), TH2.LOW (8,036 bytes code/mnemonic); total denominator 95,422 bytes (100.00% coverage, RAW_CODE_PENDING == 0);
- [x] Rebuild all 4 module containers byte-exact with zero relocations;
- [x] Verify full rebuilt disc SHA-256 bit-identical (fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8);
- [x] Mednafen cold-boot 6 checkpoints and 6 gameplay scenarios verified with zero divergence;
- [x] Implement and pass all 8 new negative controls (NC-A through NC-H), total 16/16 negative controls pass;
- [x] Hardened gate validator confirms FULL_ASM_GAME_GATE = PASS;
- [x] 41/41 CTest Windows and 40/40 CTest Linux pass;
- [x] Human-maintained source files <= 500 lines; git diff --check clean.

EVIDENCE AVAILABLE:
- Carver integrity diff: workstreams/T2-ASM-CARVER/carver_integrity_diff.json;
- Purified execution union: workstreams/T2-ASM-CARVER/executed_pc_union.json;
- Instruction-level P3 CFG resolution: workstreams/T2-ASM-CARVER/p3_control_flow_resolution.json;
- Canonical manifests: asm/manifests/0TH2.BIN.json, asm/manifests/TH2.LOW.json;
- Audited scorecard: workstreams/ASM_RECOVERY_SCORECARD.json;
- Gate validator & test suite: tools/asm/validate_recovery_gates.py, tests/asm/test_recovery_gates.py, tests/asm/negative_controls_p3.py;
- Rebuilt full disc verification: tools/asm/verify_full_game_disc.py;
- Multi-scenario gameplay regression suite: tools/asm/verify_gameplay_scenarios.py.

KNOWN UNKNOWNS:
- None for full assembly recovery track. Broad C++ translation remains frozen awaiting user authorization.

ALLOWED SCOPE:
- Forensic carver, dynamic evidence union, instruction-level CFG worklist, manifest reconciliation, gate validation, assembly containers, disc verification, tests, documentation.

OUT OF SCOPE:
- Broad C++ translation before explicit user authorization after FULL_ASM_GAME_GATE.

## Last verified result

T2_ASM_INTEGRITY_04_PASS: FULL_ASM_GAME_GATE verified. All 95,422 confirmed code bytes decoded into real mnemonics (87,344 in 0TH2.BIN, 8,036 in TH2.LOW, 12 in SET07.BIN, 30 in BGM.BIN). RAW_CODE_PENDING == 0 across SH-2 and M68K. Purified dynamic evidence union separates 63,216 byte entries from 16 instruction-start PCs (0 manifest taint, 0 unaligned PCs, all dynamic entries backed by real artifacts). Instruction-level P3 CFG worklist closed all 3,927 gaps (CONFIRMED_CODE: 2,685, PROVEN_DATA: 643, PROVEN_PADDING: 178, PROVEN_UNREACHABLE: 421; 0 unresolved unknowns). All 4 module containers reassembled byte-exact with zero relocations. Reconstructed full disc matches canonical SHA-256 fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8. Mednafen cold boot (6 checkpoints) and multi-scenario gameplay (6 scenarios) pass with 0 divergence and 0 cycle drift. All 16 negative controls (8 base + 8 P3 NC-A..NC-H) pass 100%. 41/41 CTest Windows and 40/40 CTest Linux pass.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015, ADR D-019)
CURRENT TASK: T2-ASM-INTEGRITY-04 Purify Dynamic Execution Evidence, Perform Instruction-Level P3 CFG Closure, Reconcile P3 Code into Canonical Manifests, and Re-verify FULL_ASM_GAME_GATE
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: FULL_ASM_GAME_GATE = PASS. 100.00% mnemonic coverage across confirmed code (95,422 / 95,422 bytes). RAW_CODE_PENDING == 0. UNRESOLVED_CONTROL_FLOW_UNKNOWN == 0. UNKNOWN_EXECUTION_HITS == 0. All 4 modules byte-exact. Canonical disc SHA-256 verified. Mednafen zero divergence across full 6-scenario gameplay suite. 16/16 negative controls pass. 41/41 CTest Windows, 40/40 CTest Linux pass. All human-maintained files <= 500 lines. git diff --check clean.
FILES CHANGED: asm/manifests/0TH2.BIN.json, asm/manifests/TH2.LOW.json, tests/asm/negative_controls_p3.py, tests/asm/test_recovery_gates.py, tools/asm/export_sh2_asm_ir.cpp, tools/asm/validate_recovery_gates.py, tools/carver/executed_pc_union.py, tools/carver/p3_control_flow_resolver.py, tools/carver/thor_decoder.py, workstreams/ASM_RECOVERY_SCORECARD.json, workstreams/T2-ASM-CARVER/executed_pc_union.json, workstreams/T2-ASM-CARVER/p3_control_flow_resolution.json, docs/WORKLOG.md, TASK.md
TESTS RUN: ctest --test-dir build --output-on-failure (41/41 PASS), wsl ctest --test-dir build_linux -E test_gameplay_scenarios (40/40 PASS), python tests/asm/test_recovery_gates.py (16/16 NC PASS), python tools/asm/verify_full_module.py (PASS), python tools/asm/verify_full_game_disc.py (PASS), python tools/asm/verify_gameplay_scenarios.py (PASS), python tools/asm/validate_recovery_gates.py (PASS).
NEW KNOWLEDGE: Dynamic execution evidence purified into separate byte-trace vs instruction-start representations; instruction-level delay-slot and literal-pool aware CFG worklist resolves all P3 gaps without bulk overpromotion; confirmed code denominator reconciled at 95,422 bytes with 100% proven mnemonics; Mednafen bit-for-bit parity preserved.
OPEN QUESTIONS: None for ASM recovery track.
EXACT NEXT ACTION: Report completed FULL_ASM_GAME_GATE to the user and await explicit user authorization for the next phase (ASM→C++ transition).
