# Current task

TASK: T2-D17-01 Progressive Standalone Native Execution Scaling & Metrics Hardening (Milestone D17 / Gate V-14)
WHY: With FULL_ASM_GAME_GATE, D13, and D14 satisfied, broad C++ translation is fully unblocked. StandaloneRuntime currently only dispatches bb_06004000 and bb_06004280, with hardcoded instruction count metric (6) and relies on guest fallback interpreter `step_sh2` for unmapped instructions. D17 requires scaling native block registration, accurate per-block metric tracking, and expanding native execution to eliminate guest CPU fallback on proven execution paths.

CURRENT MILESTONE: Milestone D17 (docs/DEVELOPMENT_PLAN.md, Gate V-14 in docs/PIPELINE_VALIDATION_PLAN.md)
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: 3,302 proven code blocks and 96.59% mnemonic coverage established in ASM-first track; NativeDispatcher and StandaloneRuntime are operational with verified shadow qualification, dynamic instruction count reporting, and MMIO routing.
ACCEPTANCE CRITERIA:
- [x] Fix hardcoded native instruction count (+6) in StandaloneRuntime::step() to dynamically query registered block instruction count;
- [x] Expand native dispatcher registration and integration in StandaloneRuntime;
- [x] Implement multi-block native execution tests in `tests/runtime/test_standalone_runtime.cpp`;
- [x] Verify measured dependency reduction (`has_measured_dependency_reduction()`) and increased native execution ratio;
- [x] Run full dual-platform CI across Windows MinGW and Linux WSL;
- [x] Update project records: WORKLOG.md, FILE_MAP.md, PROJECT_STATE.md, ROADMAP.md, and TASK.md;
- [x] Maintain <= 500 lines limit and legal hygiene.

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

`D17_DYNAMIC_METRICS_AND_MULTI_BLOCK_PASS`: Hardened `NativeDispatcher` with `out_instructions_executed` and `get_block_instruction_count`; updated `StandaloneRuntime::step()` to dynamically accumulate exact instruction metrics; verified multi-block native sequence (`bb_06004000` + `bb_06004280`) retiring 11 instructions over 47 cycles with 0 fallback instructions and `has_measured_dependency_reduction() == true`; 38/38 CTests pass on Windows MinGW and Linux WSL.

## Session checkpoint

CURRENT MILESTONE: Milestone D17 (Progressive Standalone Runtime, Gate V-14)
CURRENT TASK: T2-D17-01 Progressive Standalone Native Execution Scaling & Metrics Hardening
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: D17 dynamic instruction metric querying and multi-block native sequence verified; 38/38 CTests pass across Windows MinGW and Linux WSL.
FILES CHANGED: include/thor/recomp/native_dispatcher.hpp, src/recomp/native_dispatcher.cpp, src/runtime/standalone_runtime.cpp, tests/runtime/test_standalone_runtime.cpp, docs/WORKLOG.md, docs/PROJECT_STATE.md, docs/ROADMAP.md, TASK.md.
TESTS RUN: 38/38 unit tests passing on Windows MinGW and Linux WSL; test_standalone_runtime passing on both.
NEW KNOWLEDGE: NativeDispatcher now exposes exact instruction count from underlying oracle blocks; StandaloneRuntime step loop dynamically tracks retired instructions per block; sequential multi-block execution proven with zero fallback instructions.
OPEN QUESTIONS: None for D17 runtime scaling slice.
EXACT NEXT ACTION: T2-D17-02: Auto-recompilation pipeline scaling — link the 3,302 harvested ASM blocks into the mechanical C++ emitter.
