# Current task

TASK: T2-ASM-CARVER-02 / T2-ASM-06 — Proof-Integrity Repair + Complete Executable ASM Closure
WHY: Complete proof-integrity repair of recovery carver, eliminate all Python opcode masks in favor of C++ thor_sh2, resolve all P3 control-flow gaps under formal typed evidence contracts, complete SH-2 CPU ISA decode support, eliminate all RAW_CODE_PENDING bytes across SH-2 and M68K, harden the recovery gate validator with independent machine verification and negative controls, and verify full disc byte-exact reassembly and Mednafen gameplay parity. Broad C++ translation remains strictly frozen.

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015, ADR D-019)
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Hardened FULL_ASM_GAME_GATE validator independently recomputed: SH2_RAW_CODE_PENDING == 0, M68K_RAW_CODE_PENDING == 0, UNKNOWN_EXECUTION_HITS == 0, UNRESOLVED_CONTROL_FLOW_UNKNOWN == 0, Carver conflicts == 0, 100.00% mnemonic coverage across 56,164 confirmed code bytes. All 4 module containers byte-exact. Rebuilt disc matches canonical SHA-256 fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8. Mednafen zero divergence. 41/41 CTest passing on Windows and 40/40 passing on WSL Linux.

ACCEPTANCE CRITERIA:
- [x] Correct gate status: FULL_ASM_GAME_GATE = NOT_SATISFIED, CPLUSPLUS_TRANSLATION = FROZEN;
- [x] Implement formal typed evidence contracts (CONFIRMED_CODE_DYNAMIC, CONFIRMED_CODE_DIRECT_CFG, DATA_LITERAL_POOL, DATA_POINTER_TABLE, DATA_STRING, PADDING);
- [x] Remove all Python SH-2 opcode masks; delegate all SH-2 decoding to C++ `thor::sh2::decode_sh2`;
- [x] Re-audit all carver promotions and generate `carver_integrity_diff.json`;
- [x] Reconcile campaign accounting between JSON and narrative (add consistency test);
- [x] Harvest M68K execution coverage in sound RAM;
- [x] Recompute true ASM denominator and promote confirmed code through real mnemonics;
- [x] Complete SH2 and M68K assembly: SH2_RAW_CODE_PENDING == 0, M68K_RAW_CODE_PENDING == 0;
- [x] Harden FULL_ASM_GAME_GATE validator with independent recomputation and negative controls;
- [x] Full disc byte-exact reassembly (canonical disc SHA) and clean Mednafen proof;
- [x] Human-maintained source files <= 500 lines.

EVIDENCE AVAILABLE:
- Carver integrity diff: `workstreams/T2-ASM-CARVER/carver_integrity_diff.json`;
- P3 control flow resolution: `workstreams/T2-ASM-CARVER/p3_control_flow_resolution.json`;
- Audited scorecard: `workstreams/ASM_RECOVERY_SCORECARD.json`;
- Gate validator & test suite: `tools/asm/validate_recovery_gates.py`, `tests/asm/test_recovery_gates.py`;
- Rebuilt full disc verification: `tools/asm/verify_full_game_disc.py`.

KNOWN UNKNOWNS:
- None for full assembly recovery track. Broad C++ translation remains frozen awaiting user authorization.

ALLOWED SCOPE:
- Forensic carver, evidence contracts, thor_sh2 ISA completion, manifest updates, gate validation, assembly containers, disc verification, tests, documentation.

OUT OF SCOPE:
- Broad C++ translation before explicit user authorization after FULL_ASM_GAME_GATE.

## Last verified result

`T2_ASM_06_PASS`: Proof-integrity repair and complete executable ASM closure verified. All 56,164 confirmed code bytes decoded into real mnemonics (52,856 in 0TH2.BIN, 3,266 in TH2.LOW, 12 in SET07.BIN, 30 in BGM.BIN). RAW_CODE_PENDING == 0 across SH-2 and M68K. P3 control-flow gaps audited and resolved (UNRESOLVED_CONTROL_FLOW_UNKNOWN == 0). Carver conflicts == 0. All 4 module containers reassembled byte-exact with zero relocations. Reconstructed full disc matches canonical SHA-256 fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8. Mednafen cold boot and multi-scenario gameplay pass with 0 divergence. Hardened gate validator passes all positive and negative controls. 41/41 CTest on Windows and 40/40 on Linux pass.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015, ADR D-019)
CURRENT TASK: T2-ASM-CARVER-02 / T2-ASM-06 Proof-Integrity Repair + Complete Executable ASM Closure
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: FULL_ASM_GAME_GATE = PASS. 100.00% mnemonic coverage across confirmed code (56,164 / 56,164 bytes). RAW_CODE_PENDING == 0. UNRESOLVED_CONTROL_FLOW_UNKNOWN == 0. UNKNOWN_EXECUTION_HITS == 0. All 4 modules byte-exact. Canonical disc SHA-256 verified. Mednafen zero divergence. 41/41 CTest Windows, 40/40 CTest Linux pass. All human-maintained files <= 500 lines. git diff --check clean.
FILES CHANGED: include/thor/sh2/*, src/sh2/*, tools/asm/*, tools/carver/*, asm/manifests/*, tests/*, workstreams/*, docs/*, TASK.md
TESTS RUN: `ctest --test-dir build --output-on-failure` (41/41 PASS), `wsl ctest --test-dir build_linux -E test_gameplay_scenarios` (40/40 PASS), `python tests/asm/test_recovery_gates.py` (PASS), `python -m unittest tests/carver/test_carver_pipeline.py` (PASS), `python tests/asm/test_manifest_schema.py` (PASS), `python -m unittest tests/recomp/test_native_pipeline.py` (PASS), `python tools/asm/verify_full_game_disc.py` (PASS).
NEW KNOWLEDGE: Implemented 100% complete Hitachi SH-2 ISA in C++ (all 17 remaining opcodes including MAC.L, MAC.W, MUL.L, TAS, XTRCT, BRAF, BSRF, GBR transfers and bitwise ops); zero hand-written opcode masks remain in Carver; formal typed evidence contracts audit all candidate promotions; P3 control flow gaps resolved to 0 unresolved; all confirmed code closed with real mnemonics.
OPEN QUESTIONS: None for ASM recovery track.
EXACT NEXT ACTION: Report completed FULL_ASM_GAME_GATE to the user and await explicit user authorization for the next phase (ASM→C++ transition).
