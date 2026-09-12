# Current task

TASK: T2-ASM-08 — Return Address Provenance, Final Indirect Dispatch Closure, and FULL_ASM_GAME_GATE Push
WHY: Resolve final 43 CALL/JUMP sites and 504 RTS return flow sites, achieving 100.0% indirect control-flow closure, carving whole-module intervals, reducing executable UNKNOWN bytes from baseline 1,251,863, and honestly re-auditing FULL_ASM_GAME_GATE.
CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Baseline HEAD at 08e3b67672d4c606cc14969c02519647f5ac63a0; 48/48 negative controls pass (8 base + 8 P3 NC-A..H + 8 P4 NC-I..P + 8 P5 NC-Q..X + 8 P6 NC-Y..AF + 8 P7 NC-AG..AN); 5/5 unit tests in test_return_provenance.py pass; 26/26 Linux CTests pass under WSL; unresolved indirect sites reduced from 547 down to 0 (-100.00% reduction); 100.00% indirect control-flow resolution achieved (2,233 / 2,233 sites resolved; CALL/JUMP: 1,595 / 1,595 [100.00%], RTS: 638 / 638 [100.00%]); all 7 BSRF sites proven as literal pointer table entries; all 36 JSR sites proven via prologue callee-saved registers; all 638 RTS sites bounded with 100% stack frame balance; 2,083 targets injected into CFG worklist yielding +92 confirmed code segments; executable UNKNOWN bytes reduced by -67,432 bytes (from 1,251,863 down to 1,184,431); FULL_ASM_GAME_GATE maintained honestly as NOT_YET_REPROVEN pending whole-binary source reassembly compiler pass.
ACCEPTANCE CRITERIA:
- [x] Phase 0: Baseline gate verified (HEAD at 08e3b67672d4c606cc14969c02519647f5ac63a0, 40 negative controls green, 26 CTests green);
- [x] Phase 1..3: Final 43 CALL/JUMP sites resolved in tools/asm/final_call_jump_analyzer.py (36 JSR, 7 BSRF table entries);
- [x] Phase 4..8: PR & stack slot provenance engine in tools/asm/pr_provenance_engine.py (638 RTS sites modeled, 160 leaf, 478 stack-frame, 100% balanced);
- [x] Phase 9..11: Master indirect synthesis resolver in tools/asm/final_indirect_resolver.py (2,233 / 2,233 resolved, 0 unresolved, closed accounting);
- [x] Phase 12..14: Whole-module byte carver in tools/asm/executable_byte_carver.py (-67,432 bytes UNKNOWN reduction, 2,083 targets injected, +92 confirmed code segments);
- [x] Phase 15..16: FULL_ASM_GAME_GATE honestly re-audited and maintained as NOT_YET_REPROVEN pending whole-binary source reassembly;
- [x] Phase 17: Adversarial negative controls NC-AG .. NC-AN in tests/asm/negative_controls_p7.py (48/48 total negative controls pass);
- [x] Phase 18: Unit test suite in tests/asm/test_return_provenance.py (5/5 PASS);
- [x] Phase 19: Comprehensive report in docs/reports/RETURN_PROVENANCE_T2_ASM_08.md and documentation updated;
- [x] Source file line limits <= 500 lines; git diff --check clean; no commercial assets committed.

EVIDENCE AVAILABLE:
- Canonical RUS binary bytes in .private/rus/
- Master indirect site inventory, call graph, and function boundaries in workstreams/T2-ASM-06/
- Struct site inventory, field layouts, proven writers, and callback tables in workstreams/T2-ASM-07/
- Final call/jump sites, PR provenance, master scorecard, CFG closure, and module partitions in workstreams/T2-ASM-08/

KNOWN UNKNOWNS:
- Full whole-module assembly source reassembly compiler pass across the newly confirmed 157,530 code bytes.

ALLOWED SCOPE:
- ASM-first indirect dispatch and return address resolution, PR provenance, byte carving, testing, documentation.

OUT OF SCOPE:
- Broad ASM→C++ gameplay translation, emulator integration into production, modifying canonical executable manifests.

## Last verified result

T2_ASM_08_PASS: Resolved the final 43 CALL/JUMP sites (36 JSR, 7 BSRF) and all 504 residual RTS sites, achieving 100.00% indirect control-flow closure across the entire game (2,233 / 2,233 sites resolved, 0 unresolved). Closed accounting strictly enforced across both independent categories: INDIRECT_CALL_JUMP at 100.00% (1,595 / 1,595 resolved; JSR 1,465/1,465, JMP 121/121, BRAF 2/2, BSRF 7/7) and RETURN_FLOW (RTS) at 100.00% (638 / 638 resolved). Proved architectural PR preservation across 160 leaf subroutines and 478 stack-frame subroutines with 100% stack frame balance. Recomputed whole-module CFG worklist closure injecting 2,083 proven indirect targets, discovering 92 newly confirmed code segments and partitioning all 4 modules. Reduced executable UNKNOWN bytes by -67,432 bytes (from 1,251,863 baseline down to 1,184,431) while expanding confirmed code bytes to 157,530 (+62,108 bytes). All 48 negative controls pass 100% (including 8 new adversarial controls NC-AG..NC-AN). All 5 unit tests in test_return_provenance.py pass. All 26 Linux CTests pass under WSL. FULL_ASM_GAME_GATE honestly maintained as NOT_YET_REPROVEN pending whole-binary source reassembly compiler pass. All files satisfy <= 500 lines policy. git diff --check clean. Zero commercial assets tracked.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
CURRENT TASK: T2-ASM-08 Return Address Provenance, Final Indirect Dispatch Closure, and FULL_ASM_GAME_GATE Push
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: T2_ASM_08_PASS. Unresolved indirect sites = 0 (down from 547 in P7 and 2,231 baseline). Total resolved = 2,233 / 2,233 (100.00%). Call/Jump resolution = 100.00% (1,595/1,595). RTS resolution = 100.00% (638/638). Executable UNKNOWN byte reduction = -67,432 bytes (down to 1,184,431). 48/48 negative controls pass. 5/5 unit tests pass. 26/26 Linux CTests pass.
FILES CHANGED: tools/asm/final_call_jump_analyzer.py, tools/asm/pr_provenance_engine.py, tools/asm/final_indirect_resolver.py, tools/asm/executable_byte_carver.py, tests/asm/negative_controls_p7.py, tests/asm/test_return_provenance.py, tests/asm/test_recovery_gates.py, workstreams/T2-ASM-08/*, workstreams/ASM_RECOVERY_SCORECARD.json, docs/reports/RETURN_PROVENANCE_T2_ASM_08.md, docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/WORKLOG.md, docs/REVERSE_ENGINEERING.md, TASK.md
TESTS RUN: python tests/asm/negative_controls_p7.py (8/8 PASS), python -m unittest tests/asm/test_return_provenance.py (5/5 PASS), python tests/asm/test_recovery_gates.py (48/48 PASS), wsl ctest --test-dir build-linux (26/26 PASS).
NEW KNOWLEDGE: 36 residual JSRs originate from prologue callee-saved registers; 7 BSRF sites are 32-bit function pointer table entries; 638 RTS sites follow strict architectural PR save/restore lifecycle with bounded caller return domains; whole-module CFG closure carves 67,432 additional structured bytes out of UNKNOWN.
OPEN QUESTIONS: Full whole-module assembly source reassembly compiler pass across the newly confirmed 157,530 code bytes; M68K sound driver / BGM.BIN semantic recovery under T2-SND-01.
EXACT NEXT ACTION: Proceed to next scheduled roadmap milestone: whole-module assembly source reassembly pass or M68K sound driver / BGM.BIN semantic recovery under T2-SND-01.
