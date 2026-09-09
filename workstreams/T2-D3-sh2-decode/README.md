# T2-D3 — SH-2 Exact Decode & L0 Semantics

Status: **BOUNDED_PROOF (Target Startup Subset)**
Capability: **D3 — Exact SH-2 Decode / L0 Semantics**
Gate: **V-06 (Independent SH-2 Decoder Cross-Check) + L0 Semantic Verification**

## 1. Overview

This workstream establishes the first verified exact SH-2 decoder and L0 semantic execution slice for Thor 2, targeting the verified 4-instruction startup sequence in `0TH2.BIN`:

- `0x06004000`: `0x6611` — `MOV.W @R1, R6`
- `0x06004002`: `0x6F03` — `MOV R0, R15`
- `0x06004004`: `0xD417` — `MOV.L @(0x5C, PC), R4`
- `0x06004006`: `0x6442` — `MOV.L @R4, R4`

## 2. Methodology & Evidence Separation

Per the project evidence model:
- **`DECODE_VERIFIED`** (Gate V-06): The decoder structure was cross-checked against three independent authorities:
  1. Hitachi SH7604 Hardware Manual (authoritative standard);
  2. Pinned Mednafen SH-2 core (`sh7095_ops.inc`);
  3. Independent reference decoder (`hazzaclark/catherine`).
  Result: **0 unexplained decode disagreements**.
- **`INSTRUCTION_SEMANTICS_VERIFIED` & `MEMORY_SEMANTICS_VERIFIED`** (L0 Gate):
  1. Synthetic tests covering signed 16-bit extension, big-endian bus ordering, aligned PC-relative effective address computation `((PC & ~3) + 4) + (disp * 4)`, same-register writeback order (`Rm == Rn`), and architectural register isolation.
  2. Real Thor 2 startup vector replay against the pinned Mednafen debug oracle.
  Result: **0 semantic divergences**.

## 3. Workstream Deliverables

- `include/thor/sh2/sh2_types.hpp`: structured instruction representations and opcode categories;
- `include/thor/sh2/sh2_decoder.hpp`, `src/sh2/sh2_decoder.cpp`: fail-closed production C++20 decoder;
- `include/thor/sh2/sh2_state.hpp`: explicit architectural CPU register state (`R0..R15`, `PC`, `PR`, `SR/T`, `GBR`, `VBR`, `MACH`, `MACL`);
- `include/thor/sh2/sh2_memory.hpp`: big-endian memory interface with access logging;
- `include/thor/sh2/sh2_executor.hpp`, `src/sh2/sh2_executor.cpp`: L0 instruction execution harness;
- `tests/sh2/`: unit tests (`test_sh2_decoder`, `test_sh2_l0_semantics`, `test_sh2_oracle_vector`);
- `decode_crosscheck_evidence.md`: detailed multi-reference cross-check matrix.

## 4. Next Action

Review T2-D3.1 evidence before expanding D3 opcode corpus or proceeding to **D4 — Code/Data/Unknown Ownership**.
