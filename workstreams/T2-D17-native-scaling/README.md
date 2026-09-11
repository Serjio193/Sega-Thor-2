# T2-D17-02: Scalable Native Candidate Pipeline Evidence

## 1. Timing Integrity Repair Summary

Canonical D9 evidence:
-  ARCHITECTURAL_BLOCK_ENTRY_CYCLE: 316309168
-  DELAY_SLOT_ENTRY_CYCLE: 316309187 (delta 19)
-  TARGET_ENTRY_CYCLE: 316309189 (delta 21)
-  ARCHITECTURAL_BLOCK_DURATION: 21 cycles

Mednafen Integration Hook Distinction:
- In Mednafen emulator integration, NativeBranchTo performs 1 cycle pipeline refill via CPU[0].timestamp++, advancing 20 cycles to reach target arrival at 316309189.
- In StandaloneRuntime, architectural duration is exactly 21 cycles.
- Combined sequential native execution (bb_06004000 [27] + bb_06004280 [21]) retires 11 native instructions over 48 cycles with zero fallback instructions.
- Corrected MACL transcription typo in workstreams/T2-D9-indirect/d9_4_native_indirect_evidence.md (repaired to 0x00000000).

## 2. 3,302-Block Census Results

- Total Harvested Blocks: 3,302 (100.0%)
  * 0TH2.BIN: 3,126
  * TH2.LOW: 176
- Summary by Lifecycle State:
  * HARVESTED: 3,302
  * MNEMONIC_PROVEN: 3,032
  * CODEGEN_ELIGIBLE: 270 (243 in 0TH2.BIN, 27 in TH2.LOW)
  * GENERATED: 270 (100.0% of eligible)
  * COMPILES: 270 (100.0% of eligible)
  * SHADOW_ELIGIBLE: 1 (bb_06004000 / bb_06004280)
  * NATIVE_PROMOTION_ELIGIBLE: 1
  * PROMOTED: 1 (bb_06004000 and bb_06004280)
- Fail-Closed Rejection Reasons:
  * UNSUPPORTED_EMITTER_OPCODE: 3,015 blocks
  * INVALID_BLOCK_BOUNDARY: 14 blocks
  * UNSUPPORTED_CONTROL_FLOW: 3 blocks

## 3. Batch Compilation & Link Isolation

- Generated 270 standalone C++20 functions in build/generated/native_blocks/.
- Sharded into 6 translation units (native_blocks_shard_00.cpp .. native_blocks_shard_05.cpp).
- Master catalog generated: native_block_catalog.hpp and native_block_catalog.cpp.
- Master forward declaration header: native_blocks_all.hpp.
- Compiled into link-isolated library target thor_generated_batch_candidates.
- Verified 0 interpreter dependencies via test_generated_link_isolation.
- Verified differential state transition equivalence against thor_sh2 interpreter via test_v07a_transition.
