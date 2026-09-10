# ADR D-012 Post-D8 Second-Pass Closure Audit

- **Audit Date**: 2026-09-10
- **Governing ADR**: [ADR D-012](DECISIONS.md#D-012)
- **Status**: **POST_D8_SECOND_PASS = SATISFIED / CLOSED**
- **D9 Status**: **UNBLOCKED_FOR_PLANNING**
- **Next Milestone**: **D9 — Multi-Block Expansion & Indirect Control-Flow Architecture**

---

## 1. Executive Summary

Under **ADR D-012**, reaching the `D8` milestone (`V-07C PASS`, `D8: BOUNDED_PROOF for bb_06004000`) served as a mandatory governance checkpoint. The project was forbidden from discarding external methods on subjective or first-pass grounds and required an exhaustive second-pass audit of all inventoried techniques (M-01 through M-10) before authorizing multi-block scaling (D9+).

This document forms the canonical closure record of that audit. Every candidate method has been investigated, tested where feasible with current D8 capabilities, or bound to a concrete prerequisite and future milestone gate.

### Summary Disposition Table

| ID | Origin / Project | Technique | Second-Pass Status | Evidence Strength | Workflow Utility | Pipeline Role | Prerequisite / Future Gate |
|---|---|---|---|---|---|---|---|
| **M-01** | `AJBats/SaturnAutoRE` | Low-level IPC harness (`MednafenBot`) | `ADOPT_PARTIAL` | `HIGH` | `HIGH` | `ACTIVE_INFRASTRUCTURE` | Operational (`V-01`, `V-07C`) |
| **M-02** | `AJBats/SaturnAutoRE` | NOP / byte-mutation fault injection | `ADOPT_PARTIAL` | `LOW` | `HIGH` | `NEGATIVE_CONTROL_HARNESS` | Operational (`test_mutation_harness`) |
| **M-03** | `AJBats/SaturnAutoRE` | Autonomous loop / candidate scanner (`auto_re.py`) | `DEFER` | `N/A` | `MEDIUM` | `DISCOVERY_METHOD` | Blocked at `D9` (Multi-block CFG) |
| **M-04** | `AJBats/SaturnAutoRE` | Function boundary heuristics | `DEFER` | `N/A` | `MEDIUM` | `CANDIDATE_BOUNDARY_PROPOSAL` | Blocked at `D12` (Structural Recovery) |
| **M-05** | `saturn-daytona-cce-re` | Module RAM mapping verification via SHA-256 | `ADOPT_PARTIAL` | `HIGH` | `HIGH` | `ACTIVE_INFRASTRUCTURE` | Operational (`V-02a`, `V-02b`) |
| **M-06** | `saturn-daytona-cce-re` | Linker script / section reconstruction | `DEFER` | `N/A` | `HIGH` | `BINARY_TOPOLOGY_REFERENCE` | Blocked at `D12 & D13` (Provenance) |
| **M-07A** | `SaturnRecomp` | SH-2 decoder & semantic reference corpus | `ADOPT_PARTIAL` | `MEDIUM` | `HIGH` | `DECODER_AND_SEMANTIC_REFERENCE` | Operational (`test_m07_reference.py`) |
| **M-07B** | `SaturnRecomp` | Public AOT translation emitter / C codegen | `NOT_PRESENT_AT_PIN` | `N/A` | `N/A` | `NONE` | Absent upstream at commit `26c9715` |
| **M-08** | Saturn Emulators / Runtimes | Wholesale Saturn runtime / emulator fallback | `REJECT_MAINTAINED` | `N/A` | `LOW` | `NONE` | Architectural Constraint (ADR D-006) |
| **M-09** | Sega Saturn SDK / SGI | Header structures & peripheral layouts | `DEFER` | `N/A` | `HIGH` | `SEMANTIC_TYPE_CANDIDATES` | Blocked at `D15` (HW Subsystems) |
| **M-10** | Historical Toolchains | Compiler fingerprinting (GCC 2.7 / Cygnus) | `DEFER` | `N/A` | `HIGH` | `CFG_RECONSTRUCTION_ACCELERATOR` | Blocked at `D12` (Structural Recovery) |

---

## 2. Exhaustive Method Audit (M-01 through M-10)

### M-01 — SaturnAutoRE Low-Level IPC Control Harness (`MednafenBot`)
- **External Project / Method**: `AJBats/SaturnAutoRE` low-level IPC control harness (`MednafenBot`) driving target debug oracle (`AJBats/mednafen-saturn-debug`).
- **Pinned Artifact / Commit**: `AJBats/SaturnAutoRE` commit `4662aad69f95222fe37c5e6b98f2285b1a7e4653` (`MednafenBot`); target oracle submodule `AJBats/mednafen-saturn-debug` commit `155426661b7ac3152e2c93a98da60ac33002b908`.
- **First-Pass Status**: `ADOPT_PARTIAL` under [ADR D-010](DECISIONS.md#D-010).
- **Second-Pass Concrete Evidence**: Powers dynamic ground-truth trace harvesting and lockstep differential execution across D1 (`V-01`), V-07A, V-07B, and V-07C (`D8`). IPC harness controls execution down to single-cycle step granularity, reads architectural registers (R0-R15, PC, PR, GBR, VBR, MACH, MACL, SR), and extracts memory-effect diffs.
- **Evidence Strength**: `HIGH`
- **Workflow Utility**: `HIGH`
- **Final Disposition**: `ADOPT_PARTIAL`
- **Pipeline Role**: `ACTIVE_INFRASTRUCTURE` (Proof & Differential Automation).
- **Testability NOW**: Fully operational and testable now (demonstrated in `V-01`, `V-07A`, `V-07B`, `V-07C`).
- **Prerequisite / Future Gate**: None (Operational).
- **Evidence Path**: `workstreams/T2-V01-dynamic-oracle/automation_validation.md`, `workstreams/T2-V01-dynamic-oracle/README.md`, `workstreams/T2-D8-V07C-native/native_override_evidence.md`, `docs/DECISIONS.md`.
- **Closure Verdict**: **PASS / OPERATIONAL**.

---

### M-02 — SaturnAutoRE NOP / Byte-Mutation Fault Injection
- **External Project / Method**: `AJBats/SaturnAutoRE` automated NOP and byte mutation fault-injection technique (`automation.cpp` / `auto_re.py`).
- **Pinned Artifact / Commit**: `AJBats/SaturnAutoRE` commit `4662aad69f95222fe37c5e6b98f2285b1a7e4653`.
- **First-Pass Status**: `DEFERRED / PROPOSED`.
- **Second-Pass Concrete Evidence**: Evaluated under `T2-POST-D8.1` and `T2-POST-D8.2`. Designed and implemented `MutationHarness` (`src/recomp/mutation_harness.cpp`, `tools/recomp/mutation_harness.py`). Tested across 13 mutation vectors on `bb_06004000` (including single-byte flips, multi-byte mutations, opcode replacements, and unaligned writes). Falsification proved: mutating block bytes immediately induces detectable CPU register and memory-effect divergence against the oracle. Harness hardened with fail-closed checked 64-bit arithmetic against 32-bit address-space overflow / exclusive-end range overflow (`MAX_ADDRESS_EXCLUSIVE = 0x100000000ULL`) and non-overlapping block protection.
- **Evidence Strength**: `LOW` (Mutation/fault injection is a negative falsification and boundary harness; direct positive equivalence proof capability remains `LOW`).
- **Workflow Utility**: `HIGH` (Automated negative regression testing preventing false-positive candidate promotions).
- **Final Disposition**: `ADOPT_PARTIAL`
- **Pipeline Role**: `NEGATIVE_CONTROL_HARNESS` / `FAULT_INJECTION_TESTING`.
- **Testability NOW**: Fully operational and testable now (`tests/recomp/test_mutation_harness.cpp`).
- **Prerequisite / Future Gate**: None (Operational).
- **Evidence Path**: `src/recomp/mutation_harness.cpp`, `include/thor/recomp/mutation_harness.hpp`, `tools/recomp/mutation_harness.py`, `tests/recomp/test_mutation_harness.cpp`, `workstreams/POST-D8-M02-mutation/README.md`, `workstreams/POST-D8-M02-mutation/experiment_evidence.md`.
- **Closure Verdict**: **PASS / ADOPTED**.

---

### M-03 — SaturnAutoRE Autonomous Loop / Candidate Scanner (`auto_re.py`)
- **External Project / Method**: `AJBats/SaturnAutoRE` autonomous RE loop (`auto_re.py`).
- **Pinned Artifact / Commit**: `AJBats/SaturnAutoRE` commit `4662aad69f95222fe37c5e6b98f2285b1a7e4653`.
- **First-Pass Status**: `REJECT` (Unsupervised claim authoring rejected under AGENTS.md).
- **Second-Pass Concrete Evidence**: Evaluated under post-D8 audit. Unsupervised autonomous commit/claim generation remains strictly rejected by project rules. However, offline batch harvesting of executed basic block candidates is useful when feeding into `ShadowChecker`. At D8, only a single isolated basic block (`bb_06004000`) is active; batch scanning across multiple connected blocks requires multi-block flow and branch target resolution.
- **Evidence Strength**: `N/A` (Untested in pipeline).
- **Workflow Utility**: `MEDIUM` (Candidate harvester feeding verified shadow-mode pipeline).
- **Final Disposition**: `DEFER`
- **Pipeline Role**: `DISCOVERY_METHOD` / `OFFLINE_CANDIDATE_HARVESTER`.
- **Testability NOW**: Not testable now; requires multi-block execution harness and indirect branch dispatch.
- **Prerequisite / Future Gate**: Blocked until multi-block candidate/CFG/indirect-control substrate is available at `D9 (Multi-Block Expansion Architecture)`.
- **Evidence Path**: `docs/POST_D8_SECOND_PASS_PLAN.md`, `workstreams/POST-D8-M02-mutation/experiment_evidence.md`.
- **Closure Verdict**: **PREREQUISITE_BLOCKED_AT_D9**.

---

### M-04 — SaturnAutoRE Automated Function Boundary Heuristics
- **External Project / Method**: `AJBats/SaturnAutoRE` prologue/epilogue detection and boundary slicing.
- **Pinned Artifact / Commit**: `AJBats/SaturnAutoRE` commit `4662aad69f95222fe37c5e6b98f2285b1a7e4653`.
- **First-Pass Status**: `DEFERRED`.
- **Second-Pass Concrete Evidence**: Evaluated under post-D8 audit. Function boundary heuristics (RTS/JSR detection, stack-pointer adjustment patterns) operate at the subroutine level. At D8, our atomic unit of verified recompilation is the single basic block. Function boundaries cannot be verified without multi-block control-flow graphs, stack-frame semantics, and procedure linkage analysis.
- **Evidence Strength**: `N/A` (Untested on multi-block subroutines).
- **Workflow Utility**: `MEDIUM` (Candidate boundary proposal for human review).
- **Final Disposition**: `DEFER`
- **Pipeline Role**: `CANDIDATE_BOUNDARY_PROPOSAL`.
- **Testability NOW**: Not testable now; current execution model is single-block.
- **Prerequisite / Future Gate**: Blocked until independently grounded multi-block call/return structure exists at `D12 (Structural Recovery)`.
- **Evidence Path**: `docs/POST_D8_SECOND_PASS_PLAN.md`, `AGENTS.md`.
- **Closure Verdict**: **PREREQUISITE_BLOCKED_AT_D12**.

---

### M-05 — saturn-daytona-cce-re Module RAM Mapping Verification
- **External Project / Method**: `saturn-daytona-cce-re` module RAM mapping verification via SHA-256 byte comparison.
- **Pinned Artifact / Commit**: `AJBats/saturn-daytona-cce-re` inspected at commit `bf2ea285e0dc699b659c4d2cdd0a59d07f92d276` (ADR D-011).
- **First-Pass Status**: `ADOPT_PARTIAL` under [ADR D-011](DECISIONS.md#D-011).
- **Second-Pass Concrete Evidence**: Module RAM layout and byte identity verified dynamically under D2 (`V-02a` for `0TH2.BIN` at `0x06004000..0x06086BFF`, and `V-02b` for `TH2.LOW` at `0x002DA000..0x002FE7FF`), proving direct CPU copy without byte transformation and 100% exact SHA-256 byte match vs disc files.
- **Evidence Strength**: `HIGH` (Direct byte-level proof of binary identity and load mapping).
- **Workflow Utility**: `HIGH` (Ensures binary integrity and prevents reverse engineering corrupted/transformed memory).
- **Final Disposition**: `ADOPT_PARTIAL`
- **Pipeline Role**: `ACTIVE_INFRASTRUCTURE` (Binary Integrity & Memory Map Verification).
- **Testability NOW**: Fully operational and verified (`V-02a` and `V-02b`).
- **Prerequisite / Future Gate**: None (Operational).
- **Evidence Path**: `workstreams/T2-V02a-0th2-provenance/README.md`, `workstreams/T2-V02a-0th2-provenance/provenance_evidence.md`, `workstreams/T2-V02b-th2-low-provenance/README.md`, `workstreams/T2-V02b-th2-low-provenance/provenance_evidence.md`, `docs/DECISIONS.md`.
- **Closure Verdict**: **PASS / OPERATIONAL**.

---

### M-06 — saturn-daytona-cce-re Linker Script / Relocatable Section Reconstruction
- **External Project / Method**: `saturn-daytona-cce-re` GNU ld linker script and section re-slicing.
- **Pinned Artifact / Commit**: `AJBats/saturn-daytona-cce-re` inspected at commit `bf2ea285e0dc699b659c4d2cdd0a59d07f92d276`.
- **First-Pass Status**: `DEFERRED`.
- **Second-Pass Concrete Evidence**: Evaluated under post-D8 audit. Reconstructing relocatable ELF sections (`.text`, `.rodata`, `.data`, `.bss`) requires full symbol table recovery, cross-module call topology, and separation of data tables from code. At D8, native code runs at fixed guest virtual addresses without relocatable sectioning.
- **Evidence Strength**: `N/A` (Untested in pipeline).
- **Workflow Utility**: `HIGH` (Reference for long-term native linking).
- **Final Disposition**: `DEFER`
- **Pipeline Role**: `BINARY_TOPOLOGY_REFERENCE`.
- **Testability NOW**: Not testable now; requires global cross-module reference topology.
- **Prerequisite / Future Gate**: Blocked until relocatable sectioning and topology reconstruction can be evaluated against recovered structure and address/type provenance at `D12 (Structural Recovery) & D13 (Guest-Address/Type Provenance)`.
- **Evidence Path**: `docs/POST_D8_SECOND_PASS_PLAN.md`.
- **Closure Verdict**: **PREREQUISITE_BLOCKED_AT_D12_D13**.

---

### M-07A — SaturnRecomp SH-2 Decoder & Semantic Reference Corpus
- **External Project / Method**: `SaturnRecomp` clean-room SH-2 decoder (`sh2_decoder.c`) and semantic test suite (`tests/sh2_semantics.c`).
- **Pinned Artifact / Commit**: Commit `26c9715e5493054b8a205aa31d73d8f125fdd8f5`.
  - `external/sh2-recomp-core/common/sh2_decoder.c` (blob: `6a5f7e06606c2dab20e84b5c014c014647be70e4`)
  - `external/sh2-recomp-core/common/sh2_isa.h` (blob: `709f92437990a2a0fe6b69d34565cea9d432a844`)
- **First-Pass Status**: `DEFERRED / UNTESTED`.
- **Second-Pass Concrete Evidence**: Evaluated under `T2-POST-D8.2` and `T2-POST-D8.3`. 20 full-field decoded vectors (6 startup overlap + 14 synthetic probes) compared across all structural attributes (valid, raw, addr, class, Rn, Rm, size, branch, cond, delay, indirect, load, store, imm, disp, target) with zero disagreements. 8 live dynamic semantic execution cases tested against compiled SaturnRecomp runner with zero disagreements. 18 fail-closed negative corruption controls implemented and passing. Verified via `test_m07_reference.py --require-external` across Windows MinGW and Linux WSL. Legal hygiene preserved: zero upstream code committed to Sega-Thor-2.
- **Evidence Strength**: `MEDIUM` (Clean-room reference code; authoritative ground truth remains Hitachi manual and Mednafen dynamic oracle).
- **Workflow Utility**: `HIGH` (Rapidly accelerates decoding expansion, operand shape validation, and edge-case disambiguation).
- **Final Disposition**: `ADOPT_PARTIAL`
- **Pipeline Role**: `DECODER_AND_SEMANTIC_REFERENCE`.
- **Testability NOW**: Fully operational and testable now (`tests/recomp/test_m07_reference.py`).
- **Prerequisite / Future Gate**: None (Operational).
- **Evidence Path**: `workstreams/POST-D8-M07-saturnrecomp/reference_vectors.json`, `tools/recomp/saturnrecomp_adapter.py`, `tests/recomp/test_m07_reference.py`, `workstreams/POST-D8-M07-saturnrecomp/README.md`, `workstreams/POST-D8-M07-saturnrecomp/experiment_evidence.md`.
- **Closure Verdict**: **PASS / ADOPTED**.

---

### M-07B — SaturnRecomp Public AOT Translation Emitter / C Codegen
- **External Project / Method**: `SaturnRecomp` ahead-of-time C translation generator.
- **Pinned Artifact / Commit**: Commit `26c9715e5493054b8a205aa31d73d8f125fdd8f5`.
- **First-Pass Status**: `DEFERRED / UNTESTED`.
- **Second-Pass Concrete Evidence**: Rigorous structural audit of the pinned repository. Upstream `README.md` explicitly documents: *"The decoder and module-analysis foundation for ahead-of-time recompilation are present, but a complete public AOT emitter is not."* Only disc header parsing, ISO extraction, and disassembly formatting exist in `recompiler/`. No public C code emitter exists at this commit.
- **Evidence Strength**: `N/A` (Absent upstream).
- **Workflow Utility**: `N/A` (Absent upstream).
- **Final Disposition**: `NOT_PRESENT_AT_PIN`
- **Pipeline Role**: `NONE`.
- **Testability NOW**: Cannot be tested; code is absent upstream.
- **Prerequisite / Future Gate**: Gated by future upstream release if an AOT emitter is ever published.
- **Evidence Path**: `workstreams/POST-D8-M07-saturnrecomp/README.md`, `workstreams/POST-D8-M07-saturnrecomp/experiment_evidence.md`.
- **Closure Verdict**: **NOT_PRESENT_AT_PIN**.

---

### M-08 — Wholesale Saturn System Runtime / Emulator Fallback
- **External Project / Method**: Whole-system Saturn emulation runtime (e.g. libretro core, Mednafen, or Kronos) as production architecture.
- **Pinned Artifact / Commit**: Architectural constraint review under [ADR D-006](DECISIONS.md#D-006) and `AGENTS.md` Rule 15.
- **First-Pass Status**: `REJECT` under ADR D-006.
- **Second-Pass Concrete Evidence**: Re-evaluated under post-D8 audit. Replacing native C++20 reverse engineering with a full Saturn system emulator as production architecture fundamentally violates project mission. Emulators are authorized strictly as bounded differential oracles and validation harnesses (M-01), never as the shipping runtime. (Note: this rejection applies strictly to wholesale emulator runtime import; it does NOT reject SaturnRecomp as a source of component-level reference methods such as M-07A).
- **Evidence Strength**: `N/A` (Architectural rejection).
- **Workflow Utility**: `LOW` (Wholesale emulator runtime violates core project mission).
- **Final Disposition**: `REJECT_MAINTAINED`
- **Pipeline Role**: `NONE` (Strictly prohibited in production by ADR D-006 / AGENTS.md).
- **Testability NOW**: N/A.
- **Prerequisite / Future Gate**: None (Permanent architectural constraint).
- **Evidence Path**: `docs/DECISIONS.md`, `AGENTS.md`.
- **Closure Verdict**: **REJECT_MAINTAINED / ARCHITECTURAL_CONSTRAINT**.

---

### M-09 — Sega Saturn SDK / SGI Header Structures & Peripheral Layouts
- **External Project / Method**: Official Sega Saturn SDK (SGL 3.02 / SBL 6.01) hardware headers and peripheral register structs.
- **Pinned Artifact / Commit**: Sega Saturn SDK documentation and historical header corpora (candidate reference corpus per `docs/RE_TOOLCHAIN_GUIDE.md`).
- **First-Pass Status**: `REFERENCE_ONLY`.
- **Second-Pass Concrete Evidence**: Evaluated under post-D8 audit. Official headers define register structures for VDP1, VDP2, SCU, and SMPC. At D8, execution is strictly confined to basic block 0 (`bb_06004000`), which accesses only CPU registers and general RAM, with zero MMIO or peripheral interaction. Meaningful peripheral semantic-type evaluation requires actual HW subsystem contracts.
- **Evidence Strength**: `N/A` (Untested against hardware subsystem interactions).
- **Workflow Utility**: `HIGH` (Reference for peripheral struct and MMIO register layout candidates).
- **Final Disposition**: `DEFER`
- **Pipeline Role**: `SEMANTIC_TYPE_CANDIDATES`.
- **Testability NOW**: Not testable now; bb_06004000 executes zero peripheral MMIO operations.
- **Prerequisite / Future Gate**: Blocked until native execution loop interacts with hardware subsystems and rendering pipelines at `D15 (HW-Subsystem Contracts)`.
- **Evidence Path**: `docs/POST_D8_SECOND_PASS_PLAN.md`, `docs/RE_TOOLCHAIN_GUIDE.md`.
- **Closure Verdict**: **PREREQUISITE_BLOCKED_AT_D15**.

---

### M-10 — Historical Toolchains & Compiler Fingerprinting (GCC 2.7 / Cygnus)
- **External Project / Method**: Historical compiler matching and optimization fingerprinting per `docs/RE_TOOLCHAIN_GUIDE.md`.
- **Pinned Artifact / Commit**: Historical SH-2 compiler candidates per `docs/RE_TOOLCHAIN_GUIDE.md` (e.g. Hitachi/Cygnus GCC 2.7-96q1 proposed candidate compiler).
- **First-Pass Status**: `HEURISTIC`.
- **Second-Pass Concrete Evidence**: Evaluated under post-D8 audit. Compiler fingerprinting matches register allocation conventions, stack frame layout, and instruction scheduling patterns. At D8, known basic blocks are non-discriminating for compiler matching; instruction semantics are verified mechanically at basic block granularity. Semantic decompilation matching requires recovered multi-block function CFGs and structural subroutines.
- **Evidence Strength**: `N/A` (Untested on multi-block subroutines).
- **Workflow Utility**: `HIGH` (Accelerates semantic C recovery once function boundaries are reconstructed).
- **Final Disposition**: `DEFER`
- **Pipeline Role**: `CFG_RECONSTRUCTION_ACCELERATOR`.
- **Testability NOW**: Not testable now; current known blocks are non-discriminating and require structural subroutines.
- **Prerequisite / Future Gate**: Blocked until multi-block subroutine CFGs and structural recovery exist at `D12 (Structural Recovery)`.
- **Evidence Path**: `docs/POST_D8_SECOND_PASS_PLAN.md`, `docs/RE_TOOLCHAIN_GUIDE.md`.
- **Closure Verdict**: **PREREQUISITE_BLOCKED_AT_D12**.

---

## 3. Audit Conclusion & Phase Transition

Every candidate method (M-01 through M-10) has been rigorously evaluated in accordance with ADR D-012:
1. **Adopted Operational Infrastructure**:
   - `M-01`: Active IPC differential harness.
   - `M-02`: Active mutation fault-injection negative control harness.
   - `M-05`: Active RAM hash integrity verification and module provenance.
   - `M-07A`: Active SH-2 decoder and semantic execution reference corpus.
2. **Maintained Architectural Rejection**:
   - `M-08`: Wholesale emulator production architecture rejected.
   - `M-07B`: Public AOT translation emitter absent upstream.
3. **Explicitly Tracked Prerequisite Gates**:
   - `M-03`: Blocked at `D9`.
   - `M-04`: Blocked at `D12`.
   - `M-06`: Blocked at `D12 & D13`.
   - `M-09`: Blocked at `D15`.
   - `M-10`: Blocked at `D12`.

There are **zero remaining untested methods** that can be meaningfully tested with current D8 capabilities.

### Governance Verdict
- **`POST_D8_SECOND_PASS`**: **SATISFIED / CLOSED**
- **`ADR D-012`**: **PASS**
- **`D9 (Multi-Block Expansion Architecture)`**: **UNBLOCKED_FOR_PLANNING**

**Exact Next Milestone Action**: Begin planning and architectural design for `D9 — Multi-Block Expansion & Indirect Control-Flow Architecture`.
