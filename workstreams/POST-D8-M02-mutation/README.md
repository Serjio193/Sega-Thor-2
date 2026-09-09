# Workstream POST-D8-M02: SaturnAutoRE Mutation Fault-Injection Experiment

## Overview

- **Milestone**: Post-D8 Second Pass Exploration
- **Method Candidate**: M-02 — SaturnAutoRE NOP / Byte-Mutation Fault Injection
- **Baseline**: `8d8a797aca8707b19118c564c0bbea2e2d882e85` (D8 BOUNDED_PROOF, V-07C PASS)
- **Target Block**: `bb_06004000` (Master SH-2, `0TH2.BIN`, `0x06004000..0x0600400B`)
- **Status**: COMPLETE
- **Disposition**: `ADOPT_PARTIAL` (Role: `NEGATIVE_CONTROL_HARNESS` / `FAULT_INJECTION_TESTING`)

## Objectives

1. Audit the pinned SaturnAutoRE mutation fault-injection methodology (`auto_re.py` and Mednafen automation IPC).
2. Implement a reusable, fail-closed C++ mutation test harness within the Thor 2 recompilation pipeline.
3. Validate fail-closed rejection across all 12 bytes of `bb_06004000` (12/12 single-byte mutations) and instruction-level NOP substitutions.
4. Validate live Mednafen IPC mutation detection, fallback execution, and state restoration without contamination.
5. Formally evaluate M-02 on Evidence Strength vs Workflow Utility and define its exact operational role.

## Artifacts

- C++ Harness: `include/thor/recomp/mutation_harness.hpp`, `src/recomp/mutation_harness.cpp`
- Unit Tests: `tests/recomp/test_mutation_harness.cpp`
- Live Automation Tool: `tools/recomp/mutation_harness.py`
- Detailed Evidence: `workstreams/POST-D8-M02-mutation/experiment_evidence.md`
