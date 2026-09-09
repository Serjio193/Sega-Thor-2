# T2-D3 — Exact SH-2 Decode and L0 Semantics

Status: **PASS (BOUNDED_PROOF for startup basic block)**
Capability: **D3 — Exact SH-2 Instruction Decoding & L0 Semantics**
Target Scope: All instruction forms executed in `0TH2.BIN` Basic Block 0 (`0x06004000..0x0600400A`)

## 1. Supported Instruction Set Architecture

Fail-closed structured decoder in `src/sh2/sh2_decoder.cpp` and L0 executor in `src/sh2/sh2_executor.cpp`:

| Form | Opcode Mask | Mnemonic | Flow Type | Delay Slot | Memory Width | Architectural Role |
|---|---|---|---|---|---|---|
| `0x6nm1` | `0110nnnnmmmm0001` | `MOV.W @Rm, Rn` | SEQUENTIAL | No | READ_S16 | Sign-extended 16-bit word load |
| `0x6nm2` | `0110nnnnmmmm0010` | `MOV.L @Rm, Rn` | SEQUENTIAL | No | READ_U32 | 32-bit longword load (read before writeback) |
| `0x6nm3` | `0110nnnnmmmm0011` | `MOV Rm, Rn` | SEQUENTIAL | No | NONE | General register copy |
| `0xDndd` | `1101nnnndddddddd` | `MOV.L @(disp, PC), Rn` | SEQUENTIAL | No | READ_U32 | PC-relative longword load with `((PC & ~3) + 4) + (disp * 4)` base |
| `0xAddd` | `1010dddddddddddd` | `BRA label` | BRANCH | Yes | NONE | Unconditional delayed branch with 12-bit signed displacement |
| `0x0009` | `0000000000001001` | `NOP` | SEQUENTIAL | No | NONE | No-operation, delay-slot safe |

All unmodeled opcodes fail closed returning `OpcodeId::UNKNOWN` and `ControlFlowType::ILLEGAL`.

## 2. Independent Cross-Check (Gate V-06)

Complete decode agreement across:
1. **Hitachi SH7604 Hardware Manual / SH-1/SH-2 Programming Manual** (authoritative hardware specification);
2. **AJBats/mednafen-saturn-debug** (pinned commit `155426661b7ac3152e2c93a98da60ac33002b908`);
3. **hazzaclark/catherine** (pinned commit `462f483c6563604f32997da6eb6d3d49f1db7eb9`).

Machine-readable manifest: `reference_decode_manifest.json`.
Disagreements: **0**.

## 3. Test Suites

- `tests/sh2/test_sh2_decoder.cpp`: validates decode against manifest vectors, PC-relative EA alignment, BRA displacement edge cases, and fail-closed unmodeled opcodes.
- `tests/sh2/test_sh2_l0_semantics.cpp`: synthetic edge-case tests (sign extension, writeback order, NOP preservation, BRA delayed branches, illegal slot exceptions).
- `tests/sh2/test_sh2_block.cpp`: block discovery, CFG verification, and full-block replay against Mednafen oracle.
- `tests/sh2/test_sh2_oracle_vector.cpp`: 4-step startup trace verification.
