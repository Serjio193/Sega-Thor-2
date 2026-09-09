# Pipeline Validation Plan

Status: `ADOPTED`

This document defines the method/component experiments and adoption gates for The Story of Thor 2. Every external technique or component is treated as a hypothesis. It enters the project pipeline only after a bounded experiment on a Thor 2 slice ends in `ADOPT` or `ADOPT_PARTIAL`.

For the capability-oriented development sequence these experiments feed into, see `DEVELOPMENT_PLAN.md`.

## Experiment states

### Method / Adoption Decisions (Verification Track)
- `PROPOSED` — method identified; not yet tested on Thor 2.
- `TESTING` — one bounded experiment is actively executing.
- `VALIDATED` — hypothesis demonstrated on a bounded Thor 2 slice.
- `ADOPT` — method enters the project pipeline.
- `ADOPT_PARTIAL` — only the proven, bounded part enters.
- `REJECT` — method does not pass Thor 2 validation.
- `DEFER` — potentially useful but intentionally postponed.
- `SUPERSEDED` — replaced by a different approach.

### Capability Scope States (Development Track)
- `PROPOSED` — capability defined, no verification started.
- `READY_FOR_BOUNDED_TEST` — preconditions and slice bounded, ready to test.
- `BOUNDED_PROOF` — verified on at least one specific slice/path/range.
- `EXPANDED_PROOF` — verified across multiple modules/subsystems.
- `DONE` — verified across agreed required Thor 2 workload.

`VALIDATED` describes evidence. `ADOPT` describes a project decision. They are separate.

**Core Rule:** `V-xx PASS` does NOT automatically imply `Dxx DONE`. An accepted experiment establishes evidence strictly for its declared revision, CPU, module/range, workload/window, configuration, and observation contract.

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

### V-01-core — Bounded Emulator Observation

```
EXPERIMENT ID:         V-01-core
SOURCE METHOD / PROJECT: Instrumented Mednafen
CAPABILITY IT MAY ENABLE: D1 — Deterministic Dynamic Oracle (bounded proof)
FALSIFIABLE HYPOTHESIS: From a completely specified canonical boot recipe, a pinned emulator/instrumentation configuration reproduces the same bounded CPU-labelled execution transition and selected memory effect.
WHY TEST IT:           All behavioral claims require dynamic proof; this is the critical first capability after disc identity.
PREREQUISITES:         D0 DONE; working Mednafen build that loads this image.
PINNED CONFIGURATION:
  1. Thor 2 image SHA-256: fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8
  2. CUE SHA-256: afc0b101bbb493adbd43fd44ffd76959484d67cf0b566137dd145f1c68d411e0
  3. BIOS SHA-256: recorded pinned BIOS hash
  4. Emulator source version / commit hash
  5. Instrumentation revision / script version
  6. Executable / build hash of emulator binary where practical
  7. Build options / compiler flags
  8. Region configuration (JTU match)
  9. Video / timing configuration
  10. Cache-emulation configuration
  11. Backup RAM / NVRAM initial state (clean/zeroed)
  12. RTC initialization policy / fixed timestamp
  13. Cartridge / peripheral topology (no expansion cart unless declared)
  14. Disc / tray state (closed at boot)
  15. Controller type (standard Saturn digital pad in port 1)
  16. Input stream (idle / no inputs during boot window)
  17. Start condition (power-on reset from cold boot)
  18. Observation trigger (specific Master SH-2 PC hit or memory write address)
  19. Observation occurrence number (e.g. 1st occurrence after reset)
  - Stop condition: fixed cycle / instruction count or target state reached.
EVENT SEMANTICS:
  Observation records must explicitly distinguish event semantics:
  instruction fetch, pre-execution, completed instruction, memory read, memory write, interrupt event, DMA event, other.
  Rule: A pre-execution callback is NOT proof that an instruction completed.
MINIMUM EXPERIMENT:
  Execute canonical boot recipe under pinned configuration. Observe one bounded CPU-labelled transition (CPU identity, PC, register state before/after) and one selected memory effect (address, width, value). Repeat from identical start recipe.
  Optional cheap census (if already exposed by instrumentation without expanding tooling scope): Master SH-2 activity count/ranges, Slave SH-2 activity count/ranges, executed RAM ranges. For M68K / SCU DSP: distinct OBSERVED, ZERO_FROM_VALID_COUNTER, NOT_INSTRUMENTED.
AUTHORITATIVE ORACLE: Mednafen execution itself (defines the oracle baseline for this experiment).
INDEPENDENT CHECK:     Same observation via manual debugger or second emulator build if practical.
RAW EVIDENCE TO RETAIN: Save states, trace logs (private).
LEGAL-SAFE EVIDENCE TO COMMIT: Evidence summary, emulator version/commit hash, observation record without copyrighted bytes.
PASS CRITERIA:
  - At least two independently initialized runs from identical start recipe;
  - declared bounded observation contract matches identically;
  - matching selected pre/post state and memory effect;
  - CPU identity explicit (Master vs Slave);
  - observation semantics explicit;
  - emulator configuration identity recorded.
  NOTE: TH2.LOW provenance is explicitly removed from V-01-core PASS criteria and belongs to D2 / V-02b.
FAIL CRITERIA:         Non-deterministic results from same state, or inability to boot/observe this revision.
WHAT PASS WOULD PROVE: Bounded D1 oracle capability for this specific build/configuration/window.
WHAT PASS WOULD NOT PROVE: Hardware accuracy of Mednafen; complete trace correctness; all device-event visibility; deterministic entire-game execution; save-state correctness; SaturnAutoRE automation correctness.
WHAT FAIL WOULD MEAN:  Try another emulator or build. Oracle capability still required by D1.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
RE-ENTRY CONDITION IF DEFERRED: Re-test when emulator/tooling improves or alternative oracle candidate appears.
```

### V-01-automation — Automation and Control Layer

```
EXPERIMENT ID:         V-01-automation
SOURCE METHOD / PROJECT: AJBats/SaturnAutoRE automation scripts
CAPABILITY IT MAY ENABLE: D1 — Automation and reproducible scripting layer
FALSIFIABLE HYPOTHESIS: SaturnAutoRE automation scripts can reliably control Mednafen and reproduce/extract the accepted V-01-core observation.
WHY TEST IT:           Scripted control accelerates observation collection if reliable.
PREREQUISITES:         V-01-core PASS.
PINNED THOR 2 REVISION: thor2_ntsc_patched_fe11d2fb.
MINIMUM EXPERIMENT:    Execute the accepted V-01-core observation through the SaturnAutoRE script harness.
AUTHORITATIVE ORACLE: V-01-core verified observation.
PASS CRITERIA:         Script harness reproduces the accepted V-01-core observation contract without divergence.
FAIL CRITERIA:         Script harness fails to boot, crashes, produces non-deterministic traces, or alters emulator configuration.
DIVERGENCE CLASSIFICATION: If Mednafen core PASS, SaturnAutoRE automation FAIL -> ADOPT_PARTIAL for Mednafen oracle, REJECT SaturnAutoRE automation scripts. Automation failure must not reject D1.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
```

### V-02a — 0TH2.BIN Executable Provenance

```
EXPERIMENT ID:         V-02a
SOURCE METHOD / PROJECT: AJBats/saturn-daytona-cce-re module/provenance methodology
CAPABILITY IT MAY ENABLE: D2 — Executable Module Provenance (0TH2.BIN path)
FALSIFIABLE HYPOTHESIS: Disc file 0TH2.BIN is loaded to High Work RAM at 0x06004000 and executed from that range without intermediate transformation.
WHY TEST IT:           Must prove runtime executable identity for the main game binary.
PREREQUISITES:         D0, D1 (V-01-core working oracle).
PINNED THOR 2 REVISION: thor2_ntsc_patched_fe11d2fb; 0TH2.BIN.
MINIMUM EXPERIMENT:    Trace disc file 0TH2.BIN extent read -> RAM write at 0x06004000 -> instruction fetch from 0x06004000..0x06086BFF.
AUTHORITATIVE ORACLE: D1 dynamic oracle.
PASS CRITERIA:         Observed RAM writes match disc file 0TH2.BIN bytes and instruction fetch occurs from candidate range.
FAIL CRITERIA:         Bytes differ, destination differs, or no execution observed.
COMPLETION RULE:       PASS establishes D2 BOUNDED_PROOF for 0TH2.BIN only.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
```

### V-02b — TH2.LOW Executable Provenance

```
EXPERIMENT ID:         V-02b
SOURCE METHOD / PROJECT: AJBats/saturn-daytona-cce-re module/provenance methodology
CAPABILITY IT MAY ENABLE: D2 — Executable Module Provenance (TH2.LOW path)
FALSIFIABLE HYPOTHESIS: Disc file TH2.LOW is loaded to Low Work RAM at 0x002DA000 and executed from that range, confirming or falsifying the static call-site hypothesis.
WHY TEST IT:           Second major code candidate; static call-site evidence exists but runtime provenance is unproven.
PREREQUISITES:         D0, D1 (V-01-core working oracle), V-02a in progress or complete.
PINNED THOR 2 REVISION: thor2_ntsc_patched_fe11d2fb; TH2.LOW.
MINIMUM EXPERIMENT:    Trace disc file TH2.LOW extent read -> RAM write -> check whether write targets 0x002DA000 -> check whether bytes match disc -> observe subsequent instruction fetch.
AUTHORITATIVE ORACLE: D1 dynamic oracle.
PASS CRITERIA:         Either: (a) Direct loading proven (bytes match, destination 0x002DA000, instruction fetch observed); or (b) Transformed/relocated loading proven with explicit transformation graph.
FAIL CRITERIA:         No provenance established (inconclusive).
COMPLETION RULE:       PASS establishes D2 BOUNDED_PROOF for TH2.LOW only. Falsifying the 0x002DA000 candidate mapping is a valid evidence result; do not invent replacement mappings without evidence.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
```

### V-03 — Code/Data Boundary Discovery

```
EXPERIMENT ID:         V-03
SOURCE METHOD / PROJECT: Daytona funcfinder methodology
CAPABILITY IT MAY ENABLE: D4 — Code/Data/Unknown Ownership; D5 — Basic-Block CFG
FALSIFIABLE HYPOTHESIS: Code/data boundaries can be discovered via AI/static hypotheses + oracle scoring without forced semantic naming on a bounded candidate batch.
WHY TEST IT:           Need to classify bytes before translating.
PREREQUISITES:         D3 (decoder), D1 (oracle for scoring).
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; bounded candidate batch within confirmed 0TH2.BIN code.
MINIMUM EXPERIMENT:    Generate candidates from direct calls/branches/prologue evidence/dynamic entries for the pinned batch. Separate results into: (a) independently supported entries; (b) rejected entries; (c) unresolved entries.
AUTHORITATIVE ORACLE: D1 dynamic oracle.
INDEPENDENT CHECK:     Manual review of a random subset.
PASS CRITERIA:         Real code entries and code/data/unknown separated without forced code/data classification on unresolved bytes; false positives remain rejected/unknown.
FAIL CRITERIA:         Cannot reliably distinguish code from data in the test range.
WHAT PASS WOULD PROVE: Semi-automated boundary discovery works on bounded Thor 2 batches.
WHAT PASS WOULD NOT PROVE: Complete coverage; function semantics; boundaries outside the tested range.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
```

### V-04 — Persistent Segmentation Schema

```
EXPERIMENT ID:         V-04
SOURCE METHOD / PROJECT: Xeeynamo/sotn-decomp (Splat-style YAML)
CAPABILITY IT MAY ENABLE: D4 — Code/Data/Unknown Ownership (persistent representation)
FALSIFIABLE HYPOTHESIS: YAML or compatible schema is a useful persistent byte-ownership database for Thor 2 modules, supporting evidence-linked classification upgrades and downgrades.
WHY TEST IT:           Need a persistent, version-controlled representation of ownership that grows monotonically.
PREREQUISITES:         D4 (at least partial classification exists).
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; one module.
MINIMUM EXPERIMENT:    Describe one module using all project classifications: CONFIRMED_CODE, PROBABLE_CODE, UNKNOWN, PROBABLE_DATA, CONFIRMED_DATA, CODE_AND_DATA, PADDING. Verify 100% byte coverage with exactly one owner; UNKNOWN must remain representable.
AUTHORITATIVE ORACLE: Existing D4 classification.
INDEPENDENT CHECK:     Regenerate from schema and verify byte-identical split.
PASS CRITERIA:         Representation/serialization/ownership-partition integrity verified: every byte has exactly one owner; UNKNOWN is preserved; schema supports evidence-linked upgrades and downgrades.
WHAT PASS WOULD PROVE: Representation and serialization integrity for the tested module.
WHAT PASS WOULD NOT PROVE: That the classification labels themselves are correct (label correctness requires D4 evidence).
FAIL CRITERIA:         Schema cannot represent Thor 2 module structure or forces classification on unknown bytes.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
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
OUTCOME SEPARATION:    Outcomes for (a) Ghidra state-import usefulness, and (b) library/signature identification usefulness are strictly separate. One does not validate the other.
PASS CRITERIA:         Independently confirmed library identifications, or useful RAM-state import proven.
FAIL CRITERIA:         No confirmed identifications and no useful state import.
RULE:                  A Ghidra label alone is NEVER CONFIRMED.
WHAT PASS WOULD PROVE: Ghidra loader and/or signatures are useful on the evaluated scope.
WHAT PASS WOULD NOT PROVE: All Ghidra labels are correct; unverified hits are code.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
```

### V-06 — Independent SH-2 Decoder Cross-Check

```
EXPERIMENT ID:         V-06
SOURCE METHOD / PROJECT: hazzaclark/catherine
CAPABILITY IT MAY ENABLE: D3 — Exact SH-2 Decode (cross-check gate)
FALSIFIABLE HYPOTHESIS: Catherine can independently validate the project's SH-2 instruction decoder on the Thor 2 executed opcode corpus.
WHY TEST IT:           Wrong decode = wrong translation. Independent cross-check is cheap insurance.
PREREQUISITES:         D3 (our decoder exists), D1 (executed opcode corpus).
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; corpus of actually executed opcodes.
MINIMUM EXPERIMENT:    Compare decode output (opcode, mnemonic, operands, flow type, delay slot) across our decoder, Catherine, and at least one other reference.
AUTHORITATIVE ORACLE: SH7604/SH7095 hardware manual.
INDEPENDENT CHECK:     Third reference decoder (e.g., Mednafen disassembler).
PASS CRITERIA:         No unexplained semantic decode disagreements on the executed corpus. Disagreements become regression test vectors.
FAIL CRITERIA:         Persistent unexplained decode disagreements.
RULE:                  Decoder agreement is strictly a DECODE cross-check. It does NOT prove instruction execution semantics or memory access behavior (which are governed by L0 semantic suites).
WHAT PASS WOULD PROVE: Decoder syntactic correctness for the evaluated opcode corpus.
WHAT PASS WOULD NOT PROVE: Execution semantics correctness (flags, delay slots, memory access width/ordering).
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
```

### V-07A — Generated Transition Proof

```
EXPERIMENT ID:         V-07A
SOURCE METHOD / PROJECT: Mechanical C++ translation pipeline
CAPABILITY IT MAY ENABLE: D6 — Mechanical Explicit-State C++ Generation
FALSIFIABLE HYPOTHESIS: A mechanically generated explicit-state C++ block reproduces the exact declared architectural state transition for a verified SH-2 basic block under its L0 semantic contract.
WHY TEST IT:           Ensures generated code is mathematically and semantically correct before running in shadow comparison.
PREREQUISITES:         D3 target-subset decode proof + verified L0 semantic test suite + PRE_D8 identity/event guards.
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; one RAM-only block from 0TH2.BIN without MMIO/DMA/IRQ boundary.
MINIMUM EXPERIMENT:    Execute generated C++ block against declared input vectors in an isolated harness. Verify output state (R0-R15, PC, SR, PR, GBR, VBR, MACH, MACL, memory writes).
AUTHORITATIVE ORACLE: D3/L0 synthetic test suite.
PASS CRITERIA:         Zero divergence on declared architectural state transitions across all test vectors.
FAIL CRITERIA:         Any arithmetic flag, register, or memory effect discrepancy.
PIPELINE DECISION:     ADOPT / REJECT
```

### V-07B — Shadow Checker Validation

```
EXPERIMENT ID:         V-07B
SOURCE METHOD / PROJECT: Differential shadow execution infrastructure
CAPABILITY IT MAY ENABLE: D7 — Shadow Comparison Infrastructure
FALSIFIABLE HYPOTHESIS: The shadow comparison framework reliably detects intentional state divergences between oracle execution and translated execution without state pollution.
WHY TEST IT:           Prevents accepting generated code via a broken or no-op checker.
PREREQUISITES:         D1 (oracle), D6 / V-07A (candidate block).
PINNED THOR 2 REVISION: thor2_ntsc_patched_fe11d2fb.
MINIMUM EXPERIMENT:    Inject intentional divergences in: (1) register value; (2) PC / SR flags; (3) omitted/corrupted memory write; (4) out-of-order writes; (5) timing/event discrepancy. Ensure oracle and candidate paths start from isolated equivalent pre-states rather than sharing mutable post-state.
AUTHORITATIVE ORACLE: Controlled synthetic fault injection.
PASS CRITERIA:         Shadow checker detects and halts on 100% of injected faults; zero false passes; isolation of pre-states verified.
FAIL CRITERIA:         Any injected fault passes undetected or candidate mutates oracle memory prior to comparison.
PIPELINE DECISION:     ADOPT / REJECT
```

### V-07C — Real Native Override Proof

```
EXPERIMENT ID:         V-07C
SOURCE METHOD / PROJECT: Serjio193/Sega-Thor native promotion methodology
CAPABILITY IT MAY ENABLE: D8 — First Native Promotion Proof
FALSIFIABLE HYPOTHESIS: One executed Thor 2 SH-2 basic block can execute via authoritative native dispatch in place of the interpreter with zero divergence, allowing normal execution continuation.
WHY TEST IT:           The central proof that native recompiled execution works in practice.
PREREQUISITES:         V-07A PASS, V-07B PASS, PRE_D8_EXECUTABLE_IDENTITY_GUARD, PRE_D8_MINIMUM_EVENT_SAFETY.
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; one RAM-only block from 0TH2.BIN without MMIO/DMA/IRQ boundary.
MINIMUM EXPERIMENT:    Run natural game invocation with native override enabled. Record and verify:
  1. Actual dispatch entered native code;
  2. Original interpreter did not execute the replaced interval;
  3. Generated effects became authoritative continuation state;
  4. Execution successfully continued afterward;
  5. Checkpoint/state remains equivalent to separate oracle run.
RECORDED METRICS:      Native dispatch count, shadow comparison count, interpreter starts inside replaced interval, divergence count.
AUTHORITATIVE ORACLE: D1 dynamic oracle.
PASS CRITERIA:         All executions zero divergence; native override actively used; continuation verified.
COMPLETION RULE:       Establishes D8 BOUNDED_PROOF for the candidate block only. Does not imply other blocks are safe.
FAIL CRITERIA:         Any unexplained state divergence or failure to execute natively.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
```

### V-08 — SaturnRecomp Component Testing

```
EXPERIMENT ID:         V-08
SOURCE METHOD / PROJECT: sonsegajp/SaturnRecomp
CAPABILITY IT MAY ENABLE: D15, D16 — hardware-subsystem contracts and native replacement
FALSIFIABLE HYPOTHESIS: Individual SaturnRecomp components can serve as independent references or bounded adoption candidates for Thor 2 subsystem contracts.
WHY TEST IT:           SaturnRecomp has implemented Saturn subsystems; bounded reuse or cross-reference may accelerate D15/D16.
PREREQUISITES:         D1 (oracle for differential testing); D15 in progress.
RULE:                  Never wholesale-import the runtime. Test components strictly one at a time. Every adopted component result binds strictly to: exact component/subsystem, tested contract subset, Thor 2 workload, configuration, unsupported behavior. One passing operation does not validate a whole subsystem.

Sub-experiments, each requiring independent bounded testing:
  V-08a: SH-2 state/semantics
  V-08b: Memory map/helpers
  V-08c: Scheduler/event model
  V-08d: SCU DMA/interrupt behavior
  V-08e: VDP1
  V-08f: VDP2
  V-08g: M68K/SCSP
  V-08h: CD/SMPC

PINNED THOR 2 REVISION: thor2_ntsc_patched_fe11d2fb; subsystem-specific workload.
MINIMUM EXPERIMENT:    For each component: compare bounded subsystem behavior against oracle on Thor 2 workload.
AUTHORITATIVE ORACLE: D1 dynamic oracle.
PASS CRITERIA:         Component passes bounded differential test on Thor 2 workload.
FAIL CRITERIA:         Semantic or behavioral mismatch that cannot be cleanly isolated.
PIPELINE DECISION:     ADOPT_PARTIAL per component / REJECT per component / DEFER
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
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
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
PIPELINE DECISION:     ADOPT (transformation model) / ADOPT (direct-load confirmation) / DEFER
```

### V-11 — Resource Round-Trip Proof

```
EXPERIMENT ID:         V-11
SOURCE METHOD / PROJECT: Princess Crown tools, sf3tools, similar Saturn translation projects
CAPABILITY IT MAY ENABLE: D14 — Resource Decoding/Reencoding
FALSIFIABLE HYPOTHESIS: Game resources can be decoded to a neutral representation and reencoded to byte-identical output.
WHY TEST IT:           Native runtime needs to load resources; modification/localization requires decode/reencode.
PREREQUISITES:         D0 (disc files). Pure structural round-trip does NOT unconditionally require D1 when static evidence is sufficient. D1 is required when analyzing runtime loading or consumer behavior.
PINNED THOR 2 REVISION / MODULE / SLICE: thor2_ntsc_patched_fe11d2fb; one small non-code resource.
MINIMUM EXPERIMENT:    Recover parser for one resource type. Export to neutral representation. Rebuild. Compare with original.
AUTHORITATIVE ORACLE: Byte comparison with original disc file extent.
PASS CRITERIA:         BYTE_ROUNDTRIP_EXACT requires zero byte differences. Decoded semantic fields must be distinguished from opaque byte preservation. Lossy or normalized re-encoding cannot claim exact status.
FAIL CRITERIA:         Cannot achieve byte-identical round-trip and differences are unexplained.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
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
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
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
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
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
SCOPE DISTINCTION:     Distinguishes: (1) isolated extraction proof; (2) integrated bounded runtime proof; (3) measured dependency reduction; (4) final agreed dependency/coverage completion. No isolated subsystem experiment implies standalone-game completion.
PASS CRITERIA:         Standalone path produces identical agreed observable state on regression corpus.
FAIL CRITERIA:         Observable divergence from oracle.
PIPELINE DECISION:     ADOPT / ADOPT_PARTIAL / REJECT / DEFER
```

---

## Current experiment

The next experiment to activate is **V-01-core** (Bounded Emulator Observation), which enables bounded development capability **D1**.

All other experiments remain `PROPOSED` and queued.
