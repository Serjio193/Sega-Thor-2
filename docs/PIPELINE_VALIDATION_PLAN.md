# Pipeline validation plan

## Objective

Build the Thor 2 decompiler/recompiler as a gradually proven chain, not as a preselected stack. Every external project or technique is a hypothesis. Test it independently on a bounded Thor 2 slice, preserve evidence, and retain it only if it passes.

## Experiment states

`PROPOSED -> TESTING -> PROVEN -> ADOPT | ADOPT_PARTIAL`

Alternative terminal states: `REJECT`, `DEFER`.

Only one new methodological experiment may be active at once.

## Common gate

For each method:

1. state one falsifiable hypothesis;
2. pin Thor 2 revision/module/hash and inputs;
3. bound the slice;
4. run the experiment without changing other pipeline components;
5. save raw evidence and reproducible procedure;
6. use an independent check when practical;
7. record divergence and negative results;
8. decide `ADOPT`, `ADOPT_PARTIAL`, `REJECT`, or `DEFER`;
9. only then begin the next method.

## Phase 0 — Canonical Thor 2 substrate

**Source:** project owner's disc image.

Hypothesis: revision identity, disc files, hashes, boot metadata, and initial load provenance can be reproduced deterministically.

Minimum experiment: produce ISO9660 manifest, hashes, boot metadata, `IP.BIN`/boot area metadata, `0TH2.BIN` metadata, and executable candidates.

PASS: repeated extraction yields the same manifest and hashes.

Decision target: `ADOPT` canonical-input layer.

## Phase 1 — SaturnAutoRE

**Source:** `AJBats/SaturnAutoRE`.

Hypothesis: instrumented Mednafen can provide a reproducible dynamic oracle for Thor 2.

Minimum experiment: one boot/save-state scenario; observe one known address/routine and one deterministic memory effect twice from the same state.

PASS: trace includes CPU/PC/effect and can become a testable claim.

## Phase 2 — Daytona module/provenance model

**Source:** `AJBats/saturn-daytona-cce-re`.

Hypothesis: immutable disc files + load addresses + resident/hot-swapped module generations are a useful Thor 2 identity model.

Minimum experiment: prove one `disc file -> load/transformation -> executed PC range` path and test whether its code identity changes over time.

PASS: runtime code range has reproducible origin/generation, or generation is proven unnecessary for that bounded range.

## Phase 3 — Daytona function/boundary finder

Hypothesis: function/code-data boundaries can be discovered by AI/static hypotheses + oracle scoring + monotonically growing bedrock.

Minimum experiment: one small module range; candidates from direct calls/branches/prologue/dynamic entries; independent manual/oracle review.

PASS: real entries and code/data/unknown are separated without forced semantic naming; false positives remain rejected/unknown.

## Phase 4 — SOTN Saturn segmentation

**Source:** `Xeeynamo/sotn-decomp`.

Hypothesis: Splat-style YAML or a compatible schema is a useful persistent byte-ownership database.

Minimum experiment: describe one module as ordered `CODE/DATA/UNKNOWN/PADDING` regions and split it without changing bytes.

PASS: every byte has exactly one owner and `UNKNOWN` is preserved.

## Phase 5 — Ghidra Saturn Loader + library signatures

Hypothesis: state import and Sega/SBL/SGL/GFS/runtime signatures can provide independently verifiable labels and correct RAM mapping.

Minimum experiment: import one known state/mapping; run signatures; verify each candidate via bytes/xrefs/runtime evidence.

Rule: a Ghidra label alone is never `CONFIRMED`.

## Phase 6 — Catherine as independent SH-2 decoder oracle

**Source:** `hazzaclark/catherine`.

Hypothesis: Catherine can independently cross-check the project's exact SH-2 decoder.

Minimum experiment: compare a corpus of actually executed Thor 2 opcodes across our decoder, Catherine, and another reference.

PASS: no unexplained decode/flow/delay-slot disagreement; disagreements become regression vectors.

## Phase 7 — Sega-Thor mechanical block promotion on SH-2

**Source:** `Serjio193/Sega-Thor` methodology.

Hypothesis: an executed Thor 2 SH-2 basic block can be mechanically translated to explicit-state C++ and shadow-compared before native override.

Minimum experiment: one RAM-only block without MMIO/DMA/known scheduling boundary.

Compare at least registers, PC, SR, PR, MACH/MACL, ordered memory effects, and declared timing/event contract.

PASS: zero divergence and real native override preserves the checkpoint.

This is the central proof for `mechanical before semantic`.

## Phase 8 — SaturnRecomp components

**Source:** `sonsegajp/SaturnRecomp`.

Never wholesale-import the runtime. Test components one at a time:

1. SH-2 state/semantics;
2. memory map/helpers;
3. scheduler/event model;
4. SCU DMA/interrupt behavior;
5. VDP1;
6. VDP2;
7. M68K/SCSP;
8. CD/SMPC.

Each component requires a bounded Thor 2 differential test. Decisions are component-level `ADOPT_PARTIAL` or rejection.

## Phase 9 — Azel address provenance to native types

**Source:** `yaz0r/Azel`.

Hypothesis: guest-address provenance can be preserved while gradually introducing typed native structures.

Minimum experiment: one confirmed table/structure through `GuestAddress/GuestPtr` to typed view.

PASS: code is clearer, offsets remain evidence-backed, provenance is retained, behavior unchanged.

## Phase 10 — Baroque transformed executable/data lesson

Hypothesis: a CD file may be transformed/decompressed/relocated before execution; disc bytes are not automatically runtime bytes.

Minimum experiment: trace `CD read -> RAM write -> possible transformation -> instruction fetch` for one path.

PASS: either a transformed executable path is found, or direct loading is proven for the bounded path only.

## Phase 11 — Princess Crown / Shining Force III resource round-trip

Hypothesis: resource semantics should be promoted only after byte-accurate decode/reencode proof.

Minimum experiment: one small Thor 2 non-code resource -> neutral JSON/YAML-like representation -> rebuild.

PASS: reencoded bytes match, or every intentional difference is explained.

## Phase 12 — Thor 2 translation-patch differential mining

Hypothesis: independent translation patches can serve as locators for text/font/script/resource regions, not as truth.

Minimum experiment: compatible original vs one patch -> changed-sector/file/range map -> verify one range through original consumer code.

Rule: patch diff is a hint/evidence locator only.

## Phase 13 — Semantic AI recovery

Hypothesis: AI is useful after mechanical proof when every structural/semantic rewrite can be falsified by the oracle.

Minimum experiment: one proven mechanical block/function -> structured C++ -> same differential contract.

Semantic rename requires separate evidence.

## Phase 14 — Progressive standalone extraction

Hypothesis: proven blocks/subsystems can gradually move from emulator-owned execution into a deterministic standalone Thor 2 runtime.

Minimum experiment: one subsystem with a small explicit hardware contract.

PASS: standalone path matches agreed observable state on a regression corpus.

Only here does production removal of emulator dependency begin.

## Target chain — hypothesis until individually proven

`Canonical Disc`
`-> Provenance / Module DB`
`-> Dynamic Oracle`
`-> Exact SH-2 Decode`
`-> Code/Data/Unknown Boundary DB`
`-> Mechanical Basic-Block Translation`
`-> Shadow Verification`
`-> Native Promotion`
`-> Structural Recovery`
`-> Semantic Recovery`
`-> Native Subsystem Replacement`
`-> Progressive Standalone Runtime`
`-> remove guest CPU/hardware components only where proven safe`

## Forbidden shortcuts

- Do not combine two unproven methods in one experiment.
- Do not treat pretty decompiler output as proof.
- Do not treat executed coverage as a complete code map.
- Do not treat Ghidra labels as truth.
- Do not treat byte-identical rebuild as sufficient behavioral proof when a stronger contract is required.
- Do not repair divergence with candidate-specific hacks without root-cause evidence.
- Do not assign semantic names because they merely sound plausible.
- Do not remove fallback before coverage/contract evidence supports it.
- Do not build a complete Saturn runtime before Thor 2 demonstrates that a subsystem is required.

## Current experiment

`T2-M0 — Canonical Disc + Executable/Module Census`

All later phases are queued only.
