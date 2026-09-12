# Current task

TASK: T2-ASM-07 — Struct Function Pointer Recovery, Entity/Actor Dispatch Domains, and Residual CFG Closure
WHY: Resolve struct function pointers, actor callback dispatch domains, and callee-saved literal registers across the remaining 855 unresolved indirect sites (prioritizing 551 dynamically active sites), pushing indirect resolution and CFG closure forward.
CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Baseline HEAD at b2bcf8e06757ad6415c5c26dfb3142e310927a8a; 40/40 negative controls pass (8 base + 8 P3 NC-A..H + 8 P4 NC-I..P + 8 P5 NC-Q..X + 8 P6 NC-Y..AF); 7/7 unit tests in test_struct_callback_resolution.py pass; 26/26 Linux CTests pass; unresolved indirect sites reduced from 855 down to 547 (-36.02% reduction); Call/Jump resolution reached 97.30% (1,552 / 1,595 resolved; JMP 100%, BRAF 100%, JSR 97.54%); 427 proven static field writers; 808 static function pointer tables; 10 finite callback domains bounded; 546 unique targets injected into CFG worklist yielding +114 confirmed code segments.
ACCEPTANCE CRITERIA:
- [x] Phase 0: Baseline gate verified (HEAD at b2bcf8e06757ad6415c5c26dfb3142e310927a8a, 32 negative controls green);
- [x] Phase 1: Struct site isolator in tools/asm/struct_site_isolator.py (855 unresolved sites parsed, 551 dynamic / 304 cold reconciled, 209 callee-saved literals, 98 struct sites isolated);
- [x] Phase 2 & 3: Object base provenance & struct field inventory in tools/asm/object_provenance_analyzer.py (6 object archetypes, 15 struct callback fields mapped);
- [x] Phase 4..7: Callback field writers & table recovery in tools/asm/callback_field_analyzer.py (427 proven field writers, 808 static callback tables, 10 bounded entity callback domains);
- [x] Phase 8, 11, 12: Struct callback resolver in tools/asm/struct_callback_resolver.py (308 additional sites resolved, 1,686 total resolved, 547 unresolved; Call/Jump 97.30%);
- [x] Phase 13 & 14: Full CFG closure engine in tools/asm/complete_cfg_closure.py (546 targets injected, +114 confirmed code segments, +80 proven data segments);
- [x] Phase 16: Adversarial negative controls NC-Y .. NC-AF in tests/asm/negative_controls_p6.py (40/40 total negative controls pass);
- [x] Phase 18: Re-evaluate FULL_ASM_GAME_GATE (honestly maintained as NOT_YET_REPROVEN due to 547 unresolved sites);
- [x] Phase 19: Unit test suite in tests/asm/test_struct_callback_resolution.py (7/7 PASS);
- [x] Phase 20: Comprehensive report in docs/reports/STRUCT_CALLBACK_RECOVERY_T2_ASM_07.md and documentation updated;
- [x] Source file line limits <= 500 lines; git diff --check clean; no commercial assets committed.

EVIDENCE AVAILABLE:
- Canonical RUS binary bytes in .private/rus/
- Master indirect site inventory and dynamic oracle execution traces
- Struct site inventory, field layouts, proven writers, and callback tables in workstreams/T2-ASM-07/

KNOWN UNKNOWNS:
- 547 residual indirect sites (504 RTS return flow sites, 36 JSR sites, 7 BSRF table entries);
- 1,595 residual undecoded gap fragments in 0TH2.BIN and TH2.LOW.

ALLOWED SCOPE:
- ASM-first struct function pointer resolution, object provenance, callback table recovery, testing, documentation.

OUT OF SCOPE:
- Broad ASM→C++ gameplay translation, emulator integration into production, modifying canonical executable manifests.

## Last verified result

T2_ASM_07_PASS: Resolved 308 additional indirect sites across 0TH2.BIN and TH2.LOW, reaching 1,686 total resolved sites (75.50%) and reducing unresolved indirect sites from 855 down to 547 (-36.02% reduction). Pushed INDIRECT_CALL_JUMP resolution to 97.30% (1,552 / 1,595 resolved; JMP 100% [121/121], BRAF 100% [2/2], JSR 97.54% [1,429/1,465]). Strictly maintained Rule 1 category separation with RETURN_FLOW (RTS) at 21.00% (134 / 638 resolved, 504 quarantined). Recovered 6 concrete object archetypes across High RAM, Low RAM, and system vectors. Proved 427 static field store writers and recovered 808 static function pointer tables. Bounded target domains across all 10 active entity callback field offsets (+0x00..+0x28). Injected 546 unique proven indirect targets into the SH-2 CFG worklist, discovering 114 newly confirmed code segments (3,160 total) and 80 proven data segments (2,240 total). All 40 negative controls pass 100% (including 8 new adversarial controls NC-Y..NC-AF). All 7 unit tests in test_struct_callback_resolution.py pass. All 26 Linux CTests pass under WSL. FULL_ASM_GAME_GATE honestly maintained as NOT_YET_REPROVEN. All files satisfy <= 500 lines policy. git diff --check clean. Zero commercial assets tracked.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
CURRENT TASK: T2-ASM-07 Struct Function Pointer Recovery, Entity/Actor Dispatch Domains, and Residual CFG Closure
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: T2_ASM_07_PASS. Unresolved indirect sites = 547 (down from 855 in P5/P6 and 2,231 baseline). Call/Jump resolution = 97.30% (1,552/1,595). 40/40 negative controls pass. 7/7 unit tests pass. 26/26 Linux CTests pass.
FILES CHANGED: tools/asm/struct_site_isolator.py, tools/asm/object_provenance_analyzer.py, tools/asm/callback_field_analyzer.py, tools/asm/struct_callback_resolver.py, tools/asm/complete_cfg_closure.py, tests/asm/negative_controls_p6.py, tests/asm/test_struct_callback_resolution.py, tests/asm/test_recovery_gates.py, workstreams/T2-ASM-07/*, workstreams/ASM_RECOVERY_SCORECARD.json, docs/reports/STRUCT_CALLBACK_RECOVERY_T2_ASM_07.md, docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/WORKLOG.md, TASK.md
TESTS RUN: python tests/asm/negative_controls_p6.py (8/8 PASS), python tests/asm/test_struct_callback_resolution.py (7/7 PASS), python tests/asm/test_recovery_gates.py (40/40 PASS), wsl ctest --test-dir build-linux (26/26 PASS).
NEW KNOWLEDGE: 209 call/jump sites are callee-saved literal registers preserved across calls; 427 static field writers bound 10 entity callback offsets; 808 callback tables exist in binary; 114 new code segments confirmed via CFG closure.
OPEN QUESTIONS: Resolution of remaining 547 indirect sites (504 RTS return flow sites, 36 JSR sites, 7 BSRF table entries).
EXACT NEXT ACTION: Proceed to next scheduled roadmap milestone or address remaining 547 indirect sites or begin M68K sound driver / BGM.BIN semantic recovery under T2-SND-01.
