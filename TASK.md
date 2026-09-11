# Current task

TASK: T2-D17-01 Progressive Standalone Native Execution Scaling & Metrics Hardening (Milestone D17 / Gate V-14)
WHY: With FULL_ASM_GAME_GATE, D13, and D14 satisfied, broad C++ translation is fully unblocked. StandaloneRuntime currently only dispatches bb_06004000 and bb_06004280, with hardcoded instruction count metric (6) and relies on guest fallback interpreter `step_sh2` for unmapped instructions. D17 requires scaling native block registration, accurate per-block metric tracking, and expanding native execution to eliminate guest CPU fallback on proven execution paths.

CURRENT MILESTONE: Milestone D17 (docs/DEVELOPMENT_PLAN.md, Gate V-14 in docs/PIPELINE_VALIDATION_PLAN.md)
TASK STATUS: IN_PROGRESS
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: 3,302 proven code blocks and 96.59% mnemonic coverage established in ASM-first track; NativeDispatcher and StandaloneRuntime are operational with verified shadow qualification and MMIO routing.
ACCEPTANCE CRITERIA:
- [ ] Fix hardcoded native instruction count (+6) in StandaloneRuntime::step() to dynamically query registered block instruction count;
- [ ] Expand native dispatcher registration and integration in StandaloneRuntime;
- [ ] Implement multi-block native execution tests in `tests/runtime/test_standalone_runtime.cpp`;
- [ ] Verify measured dependency reduction (`has_measured_dependency_reduction()`) and increased native execution ratio;
- [ ] Run full dual-platform CI across Windows MinGW and Linux WSL;
- [ ] Update project records: WORKLOG.md, FILE_MAP.md, PROJECT_STATE.md, ROADMAP.md, and TASK.md;
- [ ] Maintain <= 500 lines limit and legal hygiene.

EVIDENCE AVAILABLE:
- D13 GuestAddress/GuestView and D14 SpriteArchive;
- Proven native blocks bb_06004000 and bb_06004280;
- StandaloneRuntime and NativeSaturnSystem unified hardware bridge.
KNOWN UNKNOWNS:
- Standalone CD-ROM block emulation for runtime file streaming.
ALLOWED SCOPE:
- Runtime libraries (`include/thor/runtime/`, `src/runtime/`), unit tests (`tests/runtime/`), documentation.
OUT OF SCOPE:
- Wholesale emulator replacement without block-level proof.

## Last verified result

`D14_RESOURCE_ROUNDTRIP_PASS`: Recovered Ancient Sprite Package format (`SpriteArchive`); verified 100% bit-exact re-encoding (`BYTE_ROUNDTRIP_EXACT`, 0 byte differences) across 6 retail disc assets (`BAW.BIN`, `DIT.BIN`, `SHADE.BIN`, `ARELE.BIN`, `EFREET.BIN`, `BRAS.BIN`, 503,504 bytes); 6/6 negative controls pass; 38/38 unit tests passing on Windows MinGW and Linux WSL.

## Session checkpoint

CURRENT MILESTONE: Milestone D17 (Progressive Standalone Runtime, Gate V-14)
CURRENT TASK: T2-D17-01 Progressive Standalone Native Execution Scaling & Metrics Hardening
TASK STATUS: IN_PROGRESS
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: Milestones D13 (Gate V-09) and D14 (Gate V-11) satisfied with zero divergence; 38/38 unit tests passing across Windows and Linux WSL.
FILES CHANGED: CMakeLists.txt, docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/WORKLOG.md, include/thor/resource/sprite_archive.hpp, src/resource/sprite_archive.cpp, tests/resource/test_resource_roundtrip.cpp.
TESTS RUN: 38/38 unit tests passing on Windows MinGW and Linux WSL; test_resource_roundtrip passing on both.
NEW KNOWLEDGE: Ancient Sprite Package archive format fully decoded and proven byte-roundtrip exact; 12-byte header with 16-bit animation offset table, animation scripts, and 4bpp sprite pixel data.
OPEN QUESTIONS: None for D17 runtime scaling slice.
EXACT NEXT ACTION: Update StandaloneRuntime::step() metrics and expand native block integration.
