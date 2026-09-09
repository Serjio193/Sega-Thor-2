# Pipeline Validation Plan

Status: `ADOPTED`

This document defines the method/component experiments and adoption gates for The Story of Thor 2. Every external technique or component is treated as a hypothesis. It enters the project pipeline only after a bounded experiment on a Thor 2 slice ends in `ADOPT` or `ADOPT_PARTIAL`.

For the capability-oriented development sequence these experiments feed into, see `DEVELOPMENT_PLAN.md`.

## Experiment states

- `PROPOSED` — method identified; not yet tested on Thor 2.
- `TESTING` — one bounded experiment is active.
- `VALIDATED` — hypothesis demonstrated on a bounded Thor 2 slice.
- `ADOPT` — method enters the project pipeline.
- `ADOPT_PARTIAL` — only the proven part enters.
- `REJECT` — method does not pass Thor 2 validation.
- `DEFER` — potentially useful but intentionally postponed.
- `SUPERSEDED` — replaced by a different approach.

`VALIDATED` describes evidence. `ADOPT` describes a project decision. They are separate.

Only one new methodological experiment may be active at once.

## Common gate

For each method:

1. State one falsifiable hypothesis.
2. Pin Thor 2 revision/module/hash and inputs.
3. Bound the slice.
4. Run the experiment without changing other pipeline components.
5. Save raw evidence and reproducible procedure.
6. Use an independent check when practical.
7. Record divergence and negative results.
8. Decide ADOPT / ADOPT_PARTIAL / REJECT / DEFER.
9. Only then begin the next method.

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

---

## Experiments

### V-01 — Dynamic Oracle via Instrumented Emulator

```
EXPERIMENT ID:         V-01
SOURCE METHOD / PROJECT: AJBats/SaturnAutoRE + Mednafen
CAPABILITY IT MAY ENABLE: D1 — Deterministic Dynamic Oracle
FALSIFIABLE HYPOTHESIS: Instrumented Mednafen can reproducibly observe Thor 2 execution state from a fixed starting point.
WHY TEST IT:           All behavioral claims require dynamic proof; this is the critical first capability after disc identity.
PREREQUISITES:         D0 DONE; working Mednafen build that loads this image.
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; boot sequence; 0TH2.BIN candidate range.
MINIMUM EXPERIMENT:    (a) Boot the image in pinned Mednafen version. (b) Observe one PC/memory-effect pair. (c) Repeat from same start state. (d) Optionally attempt TH2.LOW provenance observation.
AUTHORITATIVE ORACLE: Mednafen execution itself (defines the oracle baseline for this experiment).
INDEPENDENT CHECK:     Same observation via manual debugger or second emulator build if practical.
RAW EVIDENCE TO RETAIN: Save states, trace logs (private).
LEGAL-SAFE EVIDENCE TO COMMIT: Evidence summary, emulator version/commit hash, observation record without copyrighted bytes.
PASS CRITERIA:         Same CPU/PC/memory observation reproduced >= 2 times from same state; emulator version recorded.
FAIL CRITERIA:         Non-deterministic results from same state, or inability to boot/observe this revision.
DIVERGENCE CLASSIFICATION: If SaturnAutoRE automation fails but Mednafen works: ADOPT_PARTIAL for Mednafen oracle, REJECT SaturnAutoRE automation. If Mednafen itself fails: REJECT this emulator version; test another.
WHAT PASS WOULD PROVE: Mednafen is a viable deterministic oracle for this revision.
WHAT PASS WOULD NOT PROVE: Hardware accuracy of Mednafen; complete execution coverage; SaturnAutoRE necessity.
WHAT FAIL WOULD MEAN:  Try another emulator or build. Oracle capability still required by D1.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
RE-ENTRY CONDITION IF DEFERRED: Re-test when emulator/tooling improves or alternative oracle candidate appears.
```

### V-02 — Module Provenance Model

```
EXPERIMENT ID:         V-02
SOURCE METHOD / PROJECT: AJBats/saturn-daytona-cce-re module/provenance methodology
CAPABILITY IT MAY ENABLE: D2 — Executable Module Provenance
FALSIFIABLE HYPOTHESIS: Thor 2 executable modules can be tracked from disc file → load address → executed PC range with generation identity if needed.
WHY TEST IT:           Must know what code is at what address before translating.
PREREQUISITES:         D0, D1 (at least one dynamic observation).
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; 0TH2.BIN and TH2.LOW.
MINIMUM EXPERIMENT:    Trace one disc file read → RAM write → instruction fetch for 0TH2.BIN or TH2.LOW. Check whether content at the target range changes over time.
AUTHORITATIVE ORACLE: D1 dynamic oracle.
INDEPENDENT CHECK:     Compare traced RAM content with disc file bytes.
RAW EVIDENCE TO RETAIN: Memory traces, content snapshots (private).
LEGAL-SAFE EVIDENCE TO COMMIT: Load address, offset mapping, generation count if applicable.
PASS CRITERIA:         At least one range has reproducible disc origin and stable or tracked identity.
FAIL CRITERIA:         Provenance cannot be established for the chosen range.
DIVERGENCE CLASSIFICATION: If Daytona model does not fit Thor 2 module layout: model is adapted, not forced.
WHAT PASS WOULD PROVE: Module provenance identity is useful for Thor 2.
WHAT PASS WOULD NOT PROVE: All files have simple provenance; no overlays exist elsewhere.
WHAT FAIL WOULD MEAN:  Provenance model needs adjustment; try different approach.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
RE-ENTRY CONDITION IF DEFERRED: Re-test when more dynamic evidence is available.
```

### V-03 — Code/Data Boundary Discovery

```
EXPERIMENT ID:         V-03
SOURCE METHOD / PROJECT: Daytona funcfinder methodology
CAPABILITY IT MAY ENABLE: D4 — Code/Data/Unknown Ownership; D5 — Basic-Block CFG
FALSIFIABLE HYPOTHESIS: Code/data boundaries can be discovered via AI/static hypotheses + oracle scoring without forced semantic naming.
WHY TEST IT:           Need to classify bytes before translating.
PREREQUISITES:         D3 (decoder), D1 (oracle for scoring).
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; one bounded range within confirmed 0TH2.BIN code.
MINIMUM EXPERIMENT:    Generate candidates from direct calls/branches/prologue evidence/dynamic entries. Independently verify a small batch.
AUTHORITATIVE ORACLE: D1 dynamic oracle.
INDEPENDENT CHECK:     Manual review of a random subset.
RAW EVIDENCE TO RETAIN: Candidate lists, scoring logs.
LEGAL-SAFE EVIDENCE TO COMMIT: Boundary map, confidence scores, method description.
PASS CRITERIA:         Real code entries and code/data/unknown separated; false positives remain rejected/unknown.
FAIL CRITERIA:         Cannot reliably distinguish code from data in the test range.
DIVERGENCE CLASSIFICATION: Method-specific issue vs fundamental Thor 2 layout issue.
WHAT PASS WOULD PROVE: Semi-automated boundary discovery works for Thor 2.
WHAT PASS WOULD NOT PROVE: Complete coverage; function semantics; boundaries outside the tested range.
WHAT FAIL WOULD MEAN:  Manual classification for small ranges; method still useful if partially adopted.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
RE-ENTRY CONDITION IF DEFERRED: When more execution evidence makes scoring more reliable.
```

### V-04 — Persistent Segmentation Schema

```
EXPERIMENT ID:         V-04
SOURCE METHOD / PROJECT: Xeeynamo/sotn-decomp (Splat-style YAML)
CAPABILITY IT MAY ENABLE: D4 — Code/Data/Unknown Ownership (persistent representation)
FALSIFIABLE HYPOTHESIS: YAML or compatible schema is a useful persistent byte-ownership database for Thor 2 modules.
WHY TEST IT:           Need a persistent, version-controlled representation of ownership that grows monotonically.
PREREQUISITES:         D4 (at least partial classification exists).
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; one module.
MINIMUM EXPERIMENT:    Describe one module as ordered CODE/DATA/UNKNOWN/PADDING regions. Verify 100% byte coverage with exactly one owner.
AUTHORITATIVE ORACLE: Existing D4 classification.
INDEPENDENT CHECK:     Regenerate from schema and verify byte-identical split.
RAW EVIDENCE TO RETAIN: Schema file, split output.
LEGAL-SAFE EVIDENCE TO COMMIT: Schema definition, region boundaries (no copyrighted bytes).
PASS CRITERIA:         Every byte has exactly one owner; UNKNOWN is preserved; schema supports future refinement.
FAIL CRITERIA:         Schema cannot represent Thor 2 module structure.
WHAT PASS WOULD PROVE: Splat-style schema works for Thor 2.
WHAT PASS WOULD NOT PROVE: Optimal schema design; complete module coverage.
WHAT FAIL WOULD MEAN:  Design alternative schema.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
RE-ENTRY CONDITION IF DEFERRED: When D4 has enough classification to warrant persistent representation.
```

### V-05 — Ghidra Saturn Loader + Library Signatures

```
EXPERIMENT ID:         V-05
SOURCE METHOD / PROJECT: VGKintsugi Ghidra Saturn Loader/Processor; Saturn SDK signature research
CAPABILITY IT MAY ENABLE: Supports D4 and D12 — ownership and structural recovery
FALSIFIABLE HYPOTHESIS: Save-state imports and Sega/SBL/SGL/GFS/runtime signatures can provide independently verifiable labels and correct RAM mapping.
WHY TEST IT:           Library identification separates boilerplate from game-specific code.
PREREQUISITES:         D0; preferably D1 (for state to import).
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; one known state/mapping.
MINIMUM EXPERIMENT:    Import one known state. Run signatures. Verify each candidate hit via bytes/xrefs/runtime evidence.
AUTHORITATIVE ORACLE: D1 for runtime verification of hits.
INDEPENDENT CHECK:     Match against public library documentation.
RAW EVIDENCE TO RETAIN: Ghidra project (private — contains imported bytes).
LEGAL-SAFE EVIDENCE TO COMMIT: Confirmed library identifications with evidence; rejected candidates.
PASS CRITERIA:         Some independently confirmed library identifications, or useful RAM-state import proven.
FAIL CRITERIA:         No confirmed identifications and no useful state import.
RULE:                  A Ghidra label alone is NEVER CONFIRMED.
WHAT PASS WOULD PROVE: Ghidra loader + signatures are useful for Thor 2.
WHAT PASS WOULD NOT PROVE: All Ghidra labels are correct.
WHAT FAIL WOULD MEAN:  Manual library identification; loader may still help with state import.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
RE-ENTRY CONDITION IF DEFERRED: When better signatures or state-import support becomes available.
```

### V-06 — Independent SH-2 Decoder Cross-Check

```
EXPERIMENT ID:         V-06
SOURCE METHOD / PROJECT: hazzaclark/catherine
CAPABILITY IT MAY ENABLE: D3 — Exact SH-2 Decode (verification)
FALSIFIABLE HYPOTHESIS: Catherine can independently validate the project's SH-2 decoder on the Thor 2 executed opcode corpus.
WHY TEST IT:           Wrong decode = wrong translation. Independent cross-check is cheap insurance.
PREREQUISITES:         D3 (our decoder exists), D1 (executed opcode corpus).
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; corpus of actually executed opcodes.
MINIMUM EXPERIMENT:    Compare decode output (opcode, mnemonic, operands, flow type, delay slot) across our decoder, Catherine, and at least one other reference.
AUTHORITATIVE ORACLE: SH7604/SH7095 hardware manual.
INDEPENDENT CHECK:     Third reference decoder (e.g., Mednafen disassembler).
RAW EVIDENCE TO RETAIN: Comparison tables.
LEGAL-SAFE EVIDENCE TO COMMIT: Disagreement/agreement summary, regression vectors.
PASS CRITERIA:         No unexplained semantic decode disagreements on the executed corpus. Disagreements become regression test vectors.
FAIL CRITERIA:         Persistent unexplained decode disagreements.
WHAT PASS WOULD PROVE: Our decoder is correct for the executed instruction set.
WHAT PASS WOULD NOT PROVE: Correctness for unexecuted rare instructions.
WHAT FAIL WOULD MEAN:  Fix decoder bugs; disagreements are valuable.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
RE-ENTRY CONDITION IF DEFERRED: When decoder is ready for cross-check.
```

### V-07 — Mechanical Basic-Block Promotion Proof

```
EXPERIMENT ID:         V-07
SOURCE METHOD / PROJECT: Serjio193/Sega-Thor mechanical promotion methodology
CAPABILITY IT MAY ENABLE: D6, D7, D8 — the central proof of mechanical translation
FALSIFIABLE HYPOTHESIS: One executed Thor 2 SH-2 basic block can be mechanically translated to explicit-state C++, shadow-compared against the oracle, and then native-overridden with zero divergence.
WHY TEST IT:           This is THE central proof for the entire project methodology.
PREREQUISITES:         D3 (decoder), D5 (block boundaries), D1 (oracle for shadow comparison).
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; one RAM-only block from 0TH2.BIN without MMIO/DMA/IRQ boundary.
MINIMUM EXPERIMENT:    Translate one block. Shadow-compare R0-R15, PC, SR, PR, GBR, VBR, MACH/MACL, ordered memory effects, and declared timing/event contract on a natural invocation.
AUTHORITATIVE ORACLE: D1 dynamic oracle.
INDEPENDENT CHECK:     Manual state comparison of the first few executions.
RAW EVIDENCE TO RETAIN: Full state comparison logs, generated C++ source (private if contains copyrighted constants).
LEGAL-SAFE EVIDENCE TO COMMIT: Block address, comparison summary, pass/fail record, generated C++ structure (without copyrighted literal data).
PASS CRITERIA:         All shadow comparisons zero-divergence. Native override execution preserves the checkpoint state identically.
FAIL CRITERIA:         Any unexplained state divergence.
DIVERGENCE CLASSIFICATION: (a) Decode error → fix decoder. (b) Generation error → fix generator. (c) Oracle error → investigate oracle. (d) Timing/interrupt → reclassify block as timing-sensitive.
WHAT PASS WOULD PROVE: Mechanical basic-block translation works for Thor 2 SH-2 code.
WHAT PASS WOULD NOT PROVE: All blocks will pass; timing-sensitive blocks are handled; semantic recovery works.
WHAT FAIL WOULD MEAN:  Investigate root cause per divergence classification. If ALL candidates fail, re-examine fundamental approach.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
RE-ENTRY CONDITION IF DEFERRED: N/A — this experiment is critical-path.
```

### V-08 — SaturnRecomp Component Testing

```
EXPERIMENT ID:         V-08
SOURCE METHOD / PROJECT: sonsegajp/SaturnRecomp
CAPABILITY IT MAY ENABLE: D15, D16 — hardware-subsystem contracts and native replacement
FALSIFIABLE HYPOTHESIS: Individual SaturnRecomp components can serve as independent references or bounded adoption candidates for Thor 2 subsystem contracts.
WHY TEST IT:           SaturnRecomp has implemented Saturn subsystems; bounded reuse or cross-reference may accelerate D15/D16.
PREREQUISITES:         D1 (oracle for differential testing); D15 in progress (contract understanding needed to evaluate components).
RULE:                  Never wholesale-import the runtime. Test components strictly one at a time.

Sub-experiments, each requiring independent bounded testing:
  V-08a: SH-2 state/semantics
  V-08b: Memory map/helpers
  V-08c: Scheduler/event model
  V-08d: SCU DMA/interrupt behavior
  V-08e: VDP1
  V-08f: VDP2
  V-08g: M68K/SCSP
  V-08h: CD/SMPC

Each sub-experiment:
  - compares API/semantics with our oracle on Thor 2 workload;
  - requires a bounded differential test;
  - ends in component-level ADOPT_PARTIAL or REJECT.

PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; subsystem-specific workload.
MINIMUM EXPERIMENT:    For each component: compare one bounded subsystem behavior against oracle.
AUTHORITATIVE ORACLE: D1 dynamic oracle.
PASS CRITERIA:         Component passes bounded differential test on Thor 2 workload.
FAIL CRITERIA:         Semantic or behavioral mismatch that cannot be cleanly isolated.
WHAT PASS WOULD PROVE: That specific component is usable for Thor 2.
WHAT PASS WOULD NOT PROVE: Other components are also correct.
WHAT FAIL WOULD MEAN:  Build that component from scratch using D15 contracts.
PIPELINE DECISION:     ADOPT_PARTIAL per component / REJECT per component / DEFER
RE-ENTRY CONDITION IF DEFERRED: When D15 contract understanding reaches the relevant subsystem.
```

### V-09 — Guest-Address/Native-Type Provenance Model

```
EXPERIMENT ID:         V-09
SOURCE METHOD / PROJECT: yaz0r/Azel
CAPABILITY IT MAY ENABLE: D13 — Guest-Address/Type Provenance
FALSIFIABLE HYPOTHESIS: Guest-address provenance can be preserved while gradually introducing typed native structures.
WHY TEST IT:           Typed structures improve maintainability but must not lose provenance or break verification.
PREREQUISITES:         D12 (structural recovery provides confirmed structures).
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; one confirmed data structure.
MINIMUM EXPERIMENT:    Create GuestAddress/GuestPtr representation for one confirmed table/structure, then typed view. Verify provenance retained and behavior unchanged.
AUTHORITATIVE ORACLE: D1 + shadow comparison.
PASS CRITERIA:         Code is clearer; all fields/offsets remain evidence-backed; provenance retained; differential behavior unchanged.
FAIL CRITERIA:         Provenance lost or differential behavior changes.
WHAT PASS WOULD PROVE: Typed-view migration pattern works for Thor 2.
WHAT PASS WOULD NOT PROVE: All structures can be typed; premature typing is safe.
WHAT FAIL WOULD MEAN:  Stay on flat guest addresses until better approach found.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
RE-ENTRY CONDITION IF DEFERRED: When D12 has more confirmed structures.
```

### V-10 — Transformed Executable/Overlay Detection

```
EXPERIMENT ID:         V-10
SOURCE METHOD / PROJECT: Baroque Saturn reverse engineering lessons
CAPABILITY IT MAY ENABLE: D11 — Overlay/Generation Identity; supports D2
FALSIFIABLE HYPOTHESIS: In Thor 2, CD file content may be transformed (decompressed, relocated, patched) before execution; disc bytes are not automatically runtime bytes.
WHY TEST IT:           If transformation occurs, the provenance model must include transformation nodes; direct disc→RAM assumption would be wrong.
PREREQUISITES:         D1 (can observe memory writes and instruction fetches).
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; boot sequence and TH2.LOW loading path.
MINIMUM EXPERIMENT:    Trace CD read → RAM write → compare written bytes with disc file bytes → observe later instruction fetch. Look for bytes that differ from disc source.
AUTHORITATIVE ORACLE: D1 dynamic oracle + disc file comparison.
PASS CRITERIA:         Either a transformed executable path is found, or direct loading is proven for the bounded path.
FAIL CRITERIA:         Cannot determine whether transformation occurred (inconclusive).
WHAT PASS WOULD PROVE: Whether THIS path involves transformation (not a global conclusion).
WHAT PASS WOULD NOT PROVE: All paths are the same; no other file is transformed.
WHAT FAIL WOULD MEAN:  Extend observation; do not assume direct loading without proof.
PIPELINE DECISION:     ADOPT (transformation model) / ADOPT (direct-load confirmation) / DEFER
RE-ENTRY CONDITION IF DEFERRED: When more loading paths are traced.
```

### V-11 — Resource Round-Trip Proof

```
EXPERIMENT ID:         V-11
SOURCE METHOD / PROJECT: Princess Crown tools, sf3tools, similar Saturn translation projects
CAPABILITY IT MAY ENABLE: D14 — Resource Decoding/Reencoding
FALSIFIABLE HYPOTHESIS: Game resources can be decoded to a neutral representation and reencoded to byte-identical output.
WHY TEST IT:           Native runtime needs to load resources; modification/localization requires decode/reencode.
PREREQUISITES:         D0 (disc files), D1 (runtime observation of resource loading for format discovery).
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; one small non-code resource.
MINIMUM EXPERIMENT:    Recover parser for one resource type. Export to neutral representation. Rebuild. Compare with original.
AUTHORITATIVE ORACLE: Byte comparison with original disc file extent.
PASS CRITERIA:         Reencoded bytes match original, or every intentional difference is explained.
FAIL CRITERIA:         Cannot achieve byte-identical round-trip and differences are unexplained.
WHAT PASS WOULD PROVE: Resource decode/reencode methodology works for this resource type.
WHAT PASS WOULD NOT PROVE: All resource types are understood.
WHAT FAIL WOULD MEAN:  Analyze format more deeply; try a different resource type.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
RE-ENTRY CONDITION IF DEFERRED: When D1 reveals resource loading patterns.
```

### V-12 — Translation-Patch Differential Mining

```
EXPERIMENT ID:         V-12
SOURCE METHOD / PROJECT: Existing Thor 2 translation patches (Russian, French, Spanish, etc.)
CAPABILITY IT MAY ENABLE: Supports D14 — Resource Decoding (locating resource areas)
FALSIFIABLE HYPOTHESIS: Independent translation patches can serve as locators for text/font/script/resource regions without accepting their semantic claims as fact.
WHY TEST IT:           Patch diffs are cheap evidence for WHERE resources live; saves manual searching.
PREREQUISITES:         D0; access to a compatible unpatched original revision for comparison.
PINNED THOR 2 REVISION / MODULE / SLICE: Canonical patched revision vs compatible original (if available).
MINIMUM EXPERIMENT:    Compare canonical revision with one patch (or with unpatched original). Build changed-sector/file/range map. Verify one range through original consumer code analysis.
AUTHORITATIVE ORACLE: Our own code/resource analysis of the identified range.
RULE:                  Patch diff is a locator/evidence HINT, not source of truth.
PASS CRITERIA:         Diff identifies a real resource/code target, confirmed by our independent analysis.
FAIL CRITERIA:         Diff ranges do not correspond to identifiable resources.
WHAT PASS WOULD PROVE: Patch-differential method is useful for locating resources.
WHAT PASS WOULD NOT PROVE: Patch semantics are correct; all resources are found.
WHAT FAIL WOULD MEAN:  Locate resources by other means (runtime tracing).
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
RE-ENTRY CONDITION IF DEFERRED: When D14 needs resource location assistance.
```

### V-13 — AI-Assisted Structural/Semantic Recovery

```
EXPERIMENT ID:         V-13
SOURCE METHOD / PROJECT: Project methodology + Azel + SaturnAutoRE patterns
CAPABILITY IT MAY ENABLE: D12, D13 — Structural Recovery, Guest-Address/Type Provenance
FALSIFIABLE HYPOTHESIS: AI is useful AFTER mechanical proof for structural and semantic hypotheses, provided every transformation can be falsified by oracle-based differential testing.
WHY TEST IT:           AI can dramatically accelerate structural recovery if properly constrained.
PREREQUISITES:         D8 (proven mechanical base — AI works on verified mechanical code only).
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; one proven mechanical block/function.
MINIMUM EXPERIMENT:    AI proposes structured C++ for one proven block without semantic names above evidence level. Run differential tests.
AUTHORITATIVE ORACLE: D1 + shadow comparison.
PASS CRITERIA:         New code passes same differential contract. Semantic rename permitted only with separate evidence.
FAIL CRITERIA:         Differential tests fail, or provenance is lost.
WHAT PASS WOULD PROVE: AI-assisted refactoring is safe under differential constraint.
WHAT PASS WOULD NOT PROVE: AI semantic names are correct; AI can work without mechanical base.
WHAT FAIL WOULD MEAN:  Constrain AI role further or use manual recovery.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
RE-ENTRY CONDITION IF DEFERRED: When D8 has more verified blocks.
```

### V-14 — Progressive Standalone Extraction

```
EXPERIMENT ID:         V-14
SOURCE METHOD / PROJECT: Project methodology
CAPABILITY IT MAY ENABLE: D17 — Progressive Standalone Runtime
FALSIFIABLE HYPOTHESIS: Proven native blocks and subsystems can gradually exit emulator-owned execution into a standalone deterministic Thor 2 runtime.
WHY TEST IT:           The end goal requires eventual emulator independence.
PREREQUISITES:         D8 (multiple proven blocks), D16 (at least one native subsystem).
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; one subsystem with minimal hardware contract.
MINIMUM EXPERIMENT:    Move one subsystem with explicit inputs/outputs to standalone path. Compare against oracle on a regression corpus.
AUTHORITATIVE ORACLE: D1 dynamic oracle.
PASS CRITERIA:         Standalone path produces identical agreed observable state on regression corpus.
FAIL CRITERIA:         Observable divergence from oracle.
WHAT PASS WOULD PROVE: Progressive extraction is viable.
WHAT PASS WOULD NOT PROVE: All subsystems can be extracted; complete game coverage.
WHAT FAIL WOULD MEAN:  Keep hybrid runtime; investigate divergence cause.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
RE-ENTRY CONDITION IF DEFERRED: When more subsystems and blocks are proven.
```

---

## Current experiment

The next experiment to activate is **V-01** (Dynamic Oracle via Instrumented Emulator), which enables development capability **D1**.

All other experiments remain `PROPOSED` and queued.
