# V-06 — SH-2 Target Opcode Decode Cross-Check & L0 Semantics Evidence

Status: **PASS (0 disagreements, 0 semantic divergences)**
Capability: **D3 — Exact SH-2 Decode / L0 Semantics (BOUNDED_PROOF for target subset)**
Target Slice: 0TH2.BIN startup sequence (`0x06004000..0x06004008`)

## 1. Independent Decode Cross-Check Matrix (Gate V-06)

Comparison across 4 independent sources:
1. **Hardware Authority**: Hitachi SH7604 Hardware Manual / SH-1/SH-2 Programming Manual.
2. **Dynamic Oracle Reference**: Pinned Mednafen debug core (`sh7095_ops.inc` at commit `155426661b7ac3152e2c93a98da60ac33002b908`).
3. **Independent Static Reference**: `hazzaclark/catherine` instruction definitions (`instruction.c`, `instruction_decode.c`, `instruction.h`).
4. **Thor 2 Decoder**: `thor::sh2::decode_sh2` (`include/thor/sh2/sh2_decoder.hpp`).

| Opcode | Mnemonic | Hardware Authority | Mednafen Implementation | Catherine Reference | Thor 2 Decoder | Disagreements |
|---|---|---|---|---|---|---|
| `0x6611` | `MOV.W @R1, R6` | `(Rm) -> Sign extension -> Rn` (16-bit to 32-bit) | `MOV_W_REGINDIR_REG`, `WB_READ16` (`(int16)memrv`) | `MOVWL`, Rm=1, Rn=6, signed 16-bit | `OpcodeId::MOV_W_READ_MEM`, `Rm=1`, `Rn=6`, `READ_S16` | **0** |
| `0x6F03` | `MOV R0, R15` | `Rm -> Rn` | `MOV_REG_REG`, `R[n] = R[m]` | `MOV`, Rm=0, Rn=15 | `OpcodeId::MOV_REG`, `Rm=0`, `Rn=15`, `NONE` | **0** |
| `0xD417` | `MOV.L @(0x5C, PC), R4` | `(disp * 4 + PC) -> Rn`, PC base `(PC & ~3) + 4` | `MOV_L_PCREL_REG`, `(PC & ~3) + (d << 2)` | `MOVLL4`, disp=0x17, Rn=4 | `OpcodeId::MOV_L_PC_REL`, `Rn=4`, `disp=0x17`, `READ_U32` | **0** |
| `0x6442` | `MOV.L @R4, R4` | `(Rm) -> Rn` (read before writeback) | `MOV_L_REGINDIR_REG`, `WB_READ32` | `MOVLL`, Rm=4, Rn=4 | `OpcodeId::MOV_L_READ_MEM`, `Rm=4`, `Rn=4`, `READ_U32` | **0** |

All four independent representations agree 100% on instruction class, mnemonic, operand registers, displacement scaling, memory access width, and delay slot status (`has_delay_slot = false`).

## 2. PC-Relative Effective Address Computation Rules

Hitachi SH-2 architecture specifies that for `MOV.L @(disp, PC), Rn`:
- Base address is the PC value 4 bytes after the instruction with the lowest 2 bits cleared: `(PC & ~3) + 4`.
- For instruction at `0x06004004`, `(0x06004004 & ~3) + 4 = 0x06004008`.
- Displacement `0x17` (23) is scaled by 4: `23 * 4 = 92 = 0x5C`.
- Effective address = `0x06004008 + 0x5C = 0x06004064`.
- If instruction were at unaligned PC `0x06004002`, `(0x06004002 & ~3) + 4 = 0x06004000 + 4 = 0x06004004`.
Our implementation and tests cover both cases and confirm exact hardware compliance.

## 3. L0 Semantic Verification

1. **Sign Extension**: `MOV.W @Rm, Rn` sign-extends 16-bit loads to 32 bits (`0x8000 -> 0xFFFF8000`, `0xFFFF -> 0xFFFFFFFF`, `0x1234 -> 0x00001234`).
2. **Byte Order**: Explicit big-endian byte order verified on all memory reads.
3. **Writeback Ordering**: For `MOV.L @Rm, Rn` when `Rm == Rn` (`0x6442`), memory address `Rm` is read prior to destination writeback.
4. **Register Isolation**: Non-destination registers (`R0..R15`), status register flags (`SR/T`), `PR`, `GBR`, `VBR`, `MACH`, and `MACL` remain strictly unmodified.
5. **Memory Effects**: Memory log records read sequence in deterministic order.

## 4. Real Thor 2 Startup Vector Verification

Replay against pinned Mednafen debug oracle (`workstreams/T2-V01-dynamic-oracle/bounded_observation.md`):

| Step | Address | Opcode | Instruction | Pre-State | Post-State | Memory Access | Oracle Parity |
|---|---|---|---|---|---|---|---|
| 1 | `0x06004000` | `0x6611` | `MOV.W @R1, R6` | `R1=0x06004000, R6=0x0` | `R6=0x00006611, PC=0x06004002` | Read 16-bit at `0x06004000`: `0x6611` | **EXACT** |
| 2 | `0x06004002` | `0x6F03` | `MOV R0, R15` | `R0=0x06002EDC, R15=0x06001000` | `R15=0x06002EDC, PC=0x06004004` | None | **EXACT** |
| 3 | `0x06004004` | `0xD417` | `MOV.L @(0x5C, PC), R4` | `R4=0x00002650` | `R4=0x06081C10, PC=0x06004006` | Read 32-bit at `0x06004064`: `0x06081C10` | **EXACT** |
| 4 | `0x06004006` | `0x6442` | `MOV.L @R4, R4` | `R4=0x06081C10` | `R4=0x060917DC, PC=0x06004008` | Read 32-bit at `0x06081C10`: `0x060917DC` | **EXACT** |

Result: **0 divergences**.
