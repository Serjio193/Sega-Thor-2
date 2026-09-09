# Post-D8 Second-Pass Plan (ADR D-012)

## 1. Governance Context and Purpose

As mandated by **ADR D-012**, reaching `D8 — First Native Promotion Proof` (`V-07C PASS`, `D8: BOUNDED_PROOF for bb_06004000`) is a planning checkpoint, not permission to permanently discard external ideas that were skipped, deferred, considered weak, or not yet testable during the first pass.

Before proceeding with multi-block scaling (D9+), this document establishes the synchronized second-pass plan for all inventoried external projects, methods, and toolchain artifacts.

Evaluation follows two independent axes:
1. **Evidence Strength** — whether the method can support a proof claim directly.
2. **Workflow Utility** — whether the method materially accelerates discovery, candidate generation, classification, automation, implementation, or review when followed by independent verification.

A method is never rejected solely because it cannot serve as a proof mechanism; it may be retained as `DISCOVERY_METHOD`, `HEURISTIC`, `ACCELERATOR`, or `REFERENCE`.

---

## 2. Inventory of External Methods and Tools

| ID | Origin / Project | Method / Technique | First-Pass Status | Second-Pass Evaluation Candidate Role | Evaluation Gate / Prerequisite |
|---|---|---|---|---|---|
| **M-01** | `AJBats/SaturnAutoRE` | Low-level IPC control harness (`MednafenBot`) | `ADOPT_PARTIAL` (ADR D-010) | `ACTIVE_INFRASTRUCTURE` (Proof & Automation) | Operational (D1/V-01, V-07C) |
| **M-02** | `AJBats/SaturnAutoRE` | NOP / byte-mutation fault injection | `ADOPT_PARTIAL` | `NEGATIVE_CONTROL_HARNESS` / `FAULT_INJECTION_TESTING` | Evaluated & Adopted (T2-POST-D8.1) |
| **M-03** | `AJBats/SaturnAutoRE` | Autonomous loop / claim generator (`auto_re.py`) | `REJECT` (Unsupervised claim gen) | `HEURISTIC_DISCOVERY_ACCELERATOR` | Gated by multi-block scaling and D9 (Indirect Control-Flow) |
| **M-04** | `AJBats/SaturnAutoRE` | Automated function boundary heuristics | `DEFERRED` | `CANDIDATE_BOUNDARY_PROPOSAL` | Gated by multi-block call/ret CFG and D12 (Structural Recovery) |
| **M-05** | `saturn-daytona-cce-re` | Module RAM mapping verification via SHA-256 | `ADOPT_PARTIAL` (ADR D-011) | `ACTIVE_INFRASTRUCTURE` (Proof) | Operational (D2/V-02a) |
| **M-06** | `saturn-daytona-cce-re` | Linker script / relocatable section reconstruction | `DEFERRED` | `BINARY_TOPOLOGY_REFERENCE` | Gated by D12 (Structural Recovery) & D13 (Guest-Address/Type Provenance) |
| **M-07** | `SaturnRecomp` | C-source translation patterns for SH-2 instructions | `DEFERRED` | `CODEGEN_PATTERN_REFERENCE` | Gated by D3/D6 opcode coverage expansion |
| **M-08** | `SaturnRecomp` | Wholesale Saturn system runtime / emulator fallback | `REJECT` (ADR D-006) | `REJECT_MAINTAINED` (No wholesale emulator) | Architectural constraint |
| **M-09** | Sega Saturn SDK / SGI | Official Sega header structures & peripheral MMIO layouts | `REFERENCE_ONLY` | `SEMANTIC_TYPE_CANDIDATES` | Gated by D15 (HW-Subsystem Contracts) |
| **M-10** | Historical Toolchains | Compiler fingerprinting / optimization matching (GCC 2.7 / Cygnus) | `HEURISTIC` | `CFG_RECONSTRUCTION_ACCELERATOR` | Gated by D12 (Structural Recovery) |

---

## 3. Second-Pass Experiment Schedule

### Phase 2A — Pre-D9 Method Experiments (Current Horizon)
- **M-02 (Mutation / Fault Injection)**: Evaluated under `T2-POST-D8.1`. Disposition: `ADOPT_PARTIAL` as `NEGATIVE_CONTROL_HARNESS` / `FAULT_INJECTION_TESTING` (not positive equivalence proof). Status: `COMPLETE`.
- **M-07 (Recompilation Instruction Codegen Reference)**: Cross-reference instruction decode/codegen templates from `SaturnRecomp` for remaining unmodeled SH-2 opcodes (conditional branches, MAC, DIV, shifts). Status: `ACTIVE_NEXT` (Human review reference).

### Phase 2B — D9 Indirect Control-Flow Horizon (`PREREQUISITE_BLOCKED` until D9)
- **M-03 (SaturnAutoRE Autonomous Batch Scanning)**:
  - *Prerequisite*: Deterministic CFG walker, multi-block dispatcher, and D9 indirect branch resolution.
  - *Experiment*: Run offline trace harvester to generate candidate basic block ranges without allowing it to author commit claims.
  - *Disposition Target*: `DISCOVERY_METHOD` (offline candidate scanner feeding `ShadowChecker`).

### Phase 2C — D12 Structural Recovery Horizon (`PREREQUISITE_BLOCKED` until D12)
- **M-04 (Function Boundary Heuristics)**:
  - *Prerequisite*: Multi-block CFG connected via call/return edges under D12 structural recovery.
  - *Experiment*: Evaluate prologue/epilogue detectors against grounded call stack traces from Mednafen oracle.
  - *Disposition Target*: `HEURISTIC` (boundary hypothesis generator).
- **M-06 (Linker Script / Topology Reconstruction)**:
  - *Prerequisite*: Cross-module reference map under D12 and D13 (Guest-Address/Type Provenance).
  - *Disposition Target*: `BINARY_TOPOLOGY_REFERENCE`.
- **M-10 (Compiler Optimization Matching)**:
  - *Prerequisite*: Multi-block CFG of complex game subroutines under D12.
  - *Experiment*: Match prologue/epilogue and register allocation idioms against GCC 2.7-96q1 / Cygnus SH-2 output.
  - *Disposition Target*: `ACCELERATOR`.

### Phase 2D — D15 HW-Subsystem Contracts Horizon (`PREREQUISITE_BLOCKED` until D15)
- **M-09 (Official SDK Structure & Peripheral Layouts)**:
  - *Prerequisite*: Peripheral MMIO and event boundary contracts under D15.
  - *Disposition Target*: `SEMANTIC_TYPE_CANDIDATES`.

---

## 4. Exit Criteria for Second Pass

1. Every inventoried method M-01 through M-10 has an explicit record, evidence citation, and documented role.
2. No method is discarded merely on subjective or heuristic grounds without an explicit bounded test or prerequisite tracking gate.
3. Proof infrastructure remains 100% fail-closed and independent of heuristic accelerators.
