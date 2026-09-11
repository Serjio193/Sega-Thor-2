# Current task

TASK: T2-D17-02 Scalable Native Candidate Pipeline (Timing Integrity Repair + 3,302-Block Census + Manifest-Driven Batch C++ Generation)
WHY: Broad native recompilation scaling requires moving from bespoke per-block C++ emission to an automated, manifest-driven batch generation pipeline over the 3,302 harvested ASM blocks while maintaining strict qualification gating, timing integrity (reconciling bb_06004280 21 architectural cycles vs 20 integration hook cycles), and fail-closed isolation between linkable candidates and promoted blocks.

CURRENT MILESTONE: Milestone D17 (docs/DEVELOPMENT_PLAN.md, Gate V-14 in docs/PIPELINE_VALIDATION_PLAN.md) — ADVANCED_PROTOTYPE / IN_PROGRESS (Gate V-14: NOT_YET_PASSED)
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: 3,302 harvested blocks parsed across 0TH2.BIN (3,126) and TH2.LOW (176); 270 CODEGEN_ELIGIBLE blocks batch-generated and compiled into link-isolated library `thor_generated_batch_candidates`; differential transition proven against thor_sh2; timing integrity reconciled to 21 cycles (48 cycles multi-block sequence).
ACCEPTANCE CRITERIA:
- [x] Timing repair: reconcile bb_06004280 cycle accounting (21 architectural cycles, 20 hook cycles), update StandaloneRuntime multi-block test to 48 cycles, fix MACL typo in d9_4_native_indirect_evidence.md;
- [x] Status normalization: ensure docs/ROADMAP.md and docs/PROJECT_STATE.md do NOT claim D17, V-14, or D18 complete;
- [x] Fail-closed census: evaluate all 3,302 harvested ASM blocks into 8 mutually exclusive states with explicit rejection reasons;
- [x] Generic block generator CLI: add flags (--block-name, --module, --start-pc, --length, --offset, --out-header, --out-source) with fallback to legacy positional syntax;
- [x] Batch C++ generation: emit all 270 eligible candidate blocks, 6 compilation shards, master catalog, and master header;
- [x] Link-isolated target: configure `thor_generated_batch_candidates` in CMakeLists.txt with zero interpreter dependencies;
- [x] Scalable enable/disable gating: implement enable_pc/disable_pc/is_pc_enabled/enable_all_proven/disable_all in NativeDispatcher and C ABI;
- [x] Strict promotion isolation: exactly 2 blocks (bb_06004000, bb_06004280) promoted; remaining 268 link-isolated;
- [x] Differential transition proof: verify candidate differential equivalence against thor_sh2 interpreter in test_v07a_transition.cpp;
- [x] Maintain <= 500 lines limit across all human-maintained files.

EVIDENCE AVAILABLE:
- D17 workstream evidence: `workstreams/T2-D17-native-scaling/batch_codegen_evidence.md`, `batch_codegen_evidence.json`, `block_census_summary.json`;
- Canonical D9 indirect evidence: `workstreams/T2-D9-indirect/candidate_06004280.json`, `d9_4_native_indirect_evidence.json`;
- Automated pipeline test suite: `tests/recomp/test_native_pipeline.py`.
KNOWN UNKNOWNS:
- Extended SH-2 opcode emission in mechanical block compiler (e.g., TST, CMP, ADD, SUB) to admit remaining 3,015 candidate blocks.
ALLOWED SCOPE:
- Recompilation tools, runtime dispatch gating, batch block generation, differential transition tests, workstream records, documentation.
OUT OF SCOPE:
- Wholesale emulator replacement; unverified promotion of batch candidates.

## Last verified result

`D17_02_BATCH_CODEGEN_AND_CENSUS_PASS`: Reconciled timing integrity (21 architectural cycles for `bb_06004280`, 48 cycles multi-block sequence); completed fail-closed census over 3,302 harvested blocks identifying 270 `CODEGEN_ELIGIBLE` candidates; batch-generated all 270 blocks across 6 compilation shards and verified zero-warning compilation in link-isolated target `thor_generated_batch_candidates`; differential transition proven against `thor_sh2`; 41/41 CTests passing.

## Session checkpoint

CURRENT MILESTONE: Milestone D17 (Progressive Standalone Runtime, Gate V-14: NOT_YET_PASSED)
CURRENT TASK: T2-D17-02 Scalable Native Candidate Pipeline
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: 3,302-block census, 270-block batch codegen, 6-shard link-isolated library, per-PC enable/disable gating, and timing integrity verified at 48 cycles. 41/41 CTests pass.
FILES CHANGED: CMakeLists.txt, include/thor/recomp/native_bridge.h, include/thor/recomp/native_dispatcher.hpp, include/thor/sh2/sh2_block.hpp, src/recomp/block_compiler.cpp, src/recomp/native_dispatcher.cpp, src/sh2/sh2_block.cpp, tests/recomp/test_generated_link_isolation.cpp, tests/recomp/test_native_indirect.cpp, tests/recomp/test_native_pipeline.py, tests/recomp/test_v07a_transition.cpp, tests/runtime/test_standalone_runtime.cpp, tools/recomp/build_native_block_census.py, tools/recomp/generate_batch_native_blocks.py, tools/recomp/generate_sh2_block.cpp, docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/FILE_MAP.md, docs/WORKLOG.md, TASK.md, workstreams/T2-D9-indirect/d9_4_native_indirect_evidence.md, workstreams/T2-D17-native-scaling/*
TESTS RUN: 41/41 unit tests passing on Windows MinGW (`ctest --test-dir build -E test_gameplay_scenarios`).
NEW KNOWLEDGE: Census establishes 270/3302 blocks currently codegen-eligible under 7 opcodes (91.3% rejected on opcodes alone); bounded block discovery prevents fallthrough overruns; Mednafen hook advances 20 cycles while standalone architecture requires 21 cycles.
OPEN QUESTIONS: None for T2-D17-02 scaling slice.
EXACT NEXT ACTION: T2-D17-03: Expand mechanical compiler opcodes (CMP, TST, ADD, SUB, etc.) to scale candidate block eligibility from 270 to >1000 blocks and establish shadow qualification harness for batch candidates.
