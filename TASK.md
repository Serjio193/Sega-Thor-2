# Current task

TASK: T2-ASM-INTEGRITY-05 — Evidence Monotonicity, True Architectural-PC Evidence, Generation-Aware CFG Closure, and Non-Circular Unreachability Proof
WHY: Enforce true architectural-PC semantics, full (revision, cpu, module, generation, address) identity, zero silent evidence demotions from parent baseline, reconcile P3 DATA and PADDING into canonical manifests, stop CFG at protected DATA/PADDING boundaries, eliminate circular unreachability heuristics and module-name shortcuts, remove hardcoded fallback, inventory indirect sites, and implement negative controls NC-I through NC-P.
CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015, ADR D-019)
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Baseline origin/main f4e0ffded0a10ba22490c3e2b865dcb61d7fe1e8 verified. FULL_ASM_GAME_GATE honestly reported as NOT_YET_REPROVEN (Claimed = NOT_YET_REPROVEN, Valid = False) due to 2,231 unresolved indirect control-flow sites preventing non-circular proof of reachability on 2,206 residual undecoded gaps. CPLUSPLUS_TRANSLATION = FROZEN_BY_ASM_FIRST_ARCHITECTURE.
ACCEPTANCE CRITERIA:
- [x] Baseline verified at f4e0ffd; FULL_ASM_GAME_GATE set to NOT_YET_REPROVEN; CPLUSPLUS_TRANSLATION = FROZEN_BY_ASM_FIRST_ARCHITECTURE;
- [x] True architectural-PC semantics in executed_pc_union.py: 7 unique entry PCs across 0TH2.BIN and TH2.LOW, 0 taint, PR candidates (37) and Mednafen PC+2 entries (70) quarantined;
- [x] Generation-aware module identity: normalized to full 5-tuple (revision, cpu, module, generation, address/range);
- [x] Zero silent evidence demotions: manifests incorporate Carver DATA/PADDING (57,722 data, 52,145 pad) with silent_evidence_demotions == 0 vs parent 4a03b83;
- [x] Canonical manifests schema update: PADDING added to module_manifest.schema.json and test_manifest_schema.py;
- [x] CFG worklist halts at protected DATA/PADDING boundaries;
- [x] Circular unreachability heuristic eliminated: 2,206 residual undecoded gaps remain UNKNOWN;
- [x] Module-name shortcuts eliminated: SET07.BIN / BGM.BIN classified strictly from evidence;
- [x] Hardcoded fallback removed: entry 0x0600428A backed by verified D9 evidence;
- [x] Indirect control flow sites inventoried: 2,233 total, 2 resolved, 2,231 unresolved;
- [x] Negative controls NC-I through NC-P implemented and pass (24/24 total NC pass);
- [x] Gate validator confirms honest FULL_ASM_GAME_GATE = NOT_YET_REPROVEN;
- [x] Reassembled module containers byte-exact (0 relocations);
- [x] Full disc bit-identical (fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8);
- [x] Mednafen cold-boot 6 checkpoints verified with zero divergence;
- [x] CTest Linux 40/40 pass;
- [x] Human-maintained source files <= 500 lines; git diff --check clean.

EVIDENCE AVAILABLE:
- Purified execution union: workstreams/T2-ASM-CARVER/executed_pc_union.json;
- Instruction-level P3 CFG resolution: workstreams/T2-ASM-CARVER/p3_control_flow_resolution.json;
- Canonical manifests: asm/manifests/0TH2.BIN.json, asm/manifests/TH2.LOW.json, asm/manifests/SET07.BIN.json, asm/manifests/BGM.BIN.json;
- Manifest schema & tests: asm/schema/module_manifest.schema.json, tests/asm/test_manifest_schema.py;
- Audited scorecard: workstreams/ASM_RECOVERY_SCORECARD.json;
- Gate validator & test suite: tools/asm/validate_recovery_gates.py, tests/asm/test_recovery_gates.py, tests/asm/negative_controls_p4.py;
- Rebuilt full disc verification: tools/asm/verify_full_game_disc.py;
- Rebuilt module verification: tools/asm/verify_full_module.py.

KNOWN UNKNOWNS:
- 2,231 unresolved indirect control flow sites (JSR, JMP, BRAF, BSRF, RTS) across the binary footprint preventing reachability proof of 2,206 residual gaps without register/data-flow analysis.

ALLOWED SCOPE:
- Forensic carver, dynamic evidence union, instruction-level CFG worklist, manifest reconciliation, gate validation, assembly containers, disc verification, tests, documentation.

OUT OF SCOPE:
- C++ translation or native subsystem scaling before explicit user authorization after re-proving FULL_ASM_GAME_GATE.

## Last verified result

T2_ASM_INTEGRITY_05_PASS: Dynamic execution evidence purified to true architectural instruction-entry PCs (7 unique entries, zero taint, debug-presented and return candidates quarantined). Module identity fully 5-tuple normalized. Evidence monotonicity verified with silent_evidence_demotions == 0 against parent baseline 4a03b83. Manifests reconciled with Carver DATA (57,722 bytes) and PADDING (52,145 bytes); module_manifest schema updated and verified with 9 negative controls. CFG worklist halts at guarded DATA/PADDING boundaries. Circular unreachability heuristic eliminated: 2,206 residual undecoded gaps remain UNKNOWN due to 2,231 unresolved indirect sites. Module-name shortcuts eliminated. Reassembled module containers match canonical SHA-256 with 0 relocations. Reconstructed full disc matches canonical SHA-256 fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8. Mednafen pure interpreter cold-boot 6 checkpoints verified with 0 divergence. All 24 negative controls (8 base + 8 P3 NC-A..NC-H + 8 P4 NC-I..NC-P) pass 100%. Gate validator passes with honest FULL_ASM_GAME_GATE = NOT_YET_REPROVEN. Linux CTest 40/40 tests pass.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015, ADR D-019)
CURRENT TASK: T2-ASM-INTEGRITY-05 Evidence Monotonicity, True Architectural-PC Evidence, Generation-Aware CFG Closure, and Non-Circular Unreachability Proof
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: FULL_ASM_GAME_GATE = NOT_YET_REPROVEN (honest blocker: 2,206 residual undecoded gaps unproven as unreachable due to 2,231 unresolved indirect control-flow sites). CPLUSPLUS_TRANSLATION = FROZEN_BY_ASM_FIRST_ARCHITECTURE. Monotonicity preserved (silent_evidence_demotions == 0). Canonical byte partition: Code 95,422 bytes (100% proven mnemonics), Data 57,722 bytes, Padding 52,145 bytes, Unknown 1,251,863 bytes (Total 1,457,152 bytes). All 4 modules byte-exact. Canonical disc SHA-256 verified. Mednafen zero divergence across 6 cold-boot checkpoints. 24/24 negative controls pass. 40/40 CTest Linux pass. All human-maintained files <= 500 lines. git diff --check clean.
FILES CHANGED: asm/manifests/0TH2.BIN.json, asm/manifests/BGM.BIN.json, asm/manifests/SET07.BIN.json, asm/manifests/TH2.LOW.json, asm/schema/module_manifest.schema.json, docs/PROJECT_STATE.md, docs/WORKLOG.md, tests/asm/negative_controls_p4.py, tests/asm/test_manifest_schema.py, tests/asm/test_recovery_gates.py, tools/asm/validate_recovery_gates.py, tools/carver/executed_pc_union.py, tools/carver/p3_control_flow_resolver.py, workstreams/ASM_RECOVERY_SCORECARD.json, workstreams/T2-ASM-CARVER/executed_pc_union.json, workstreams/T2-ASM-CARVER/p3_control_flow_resolution.json, TASK.md
TESTS RUN: wsl ctest --test-dir build_linux -E test_gameplay_scenarios (40/40 PASS), python tests/asm/test_manifest_schema.py (PASS, 9 NC PASS), python tests/asm/test_recovery_gates.py (24/24 NC PASS), python tools/asm/verify_full_module.py (PASS, 20 NC PASS), python tools/asm/verify_full_game_disc.py (PASS), python tools/asm/validate_recovery_gates.py (PASS).
NEW KNOWLEDGE: True architectural PC entries quarantined from return candidates (PR) and Mednafen presented PC+2 hook offsets; residual gaps cannot be proven unreachable without resolving 2,231 indirect branch sites (JSR/JMP/BRAF/BSRF/RTS); circular heuristics removed; evidence monotonicity formally guaranteed against parent baseline.
OPEN QUESTIONS: Strategy for static data-flow/constant-propagation analysis to resolve indirect branch jump tables in subsequent task.
EXACT NEXT ACTION: Report completed T2-ASM-INTEGRITY-05 state to the user in Russian (max 8 bullets) and await instructions for indirect control flow resolution or next ASM integrity slice.
