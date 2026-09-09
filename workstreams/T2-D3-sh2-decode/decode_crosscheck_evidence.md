# V-06 — SH-2 Target Opcode Decode Cross-Check & L0 Semantics Evidence

Status: **PASS (0 disagreements, 0 semantic divergences)**
Capability: **D3 — Exact SH-2 Decode / L0 Semantics (BOUNDED_PROOF for startup basic block)**
Target Slice: 0TH2.BIN Basic Block 0 (`0x06004000..0x0600400A`)

## 1. Independent Decode Cross-Check Matrix (Gate V-06)

Comparison across 4 independent sources:
1. **Hardware Authority**: Hitachi SH7604 Hardware Manual / SH-1/SH-2 Programming Manual (Rev 4.0, Sept 2004).
2. **Dynamic Oracle Reference**: Pinned Mednafen debug core (`sh7095_opdefs.inc`, `sh7095_ops.inc` at commit `155426661b7ac3152e2c93a98da60ac33002b908`).
3. **Independent Static Reference**: `hazzaclark/catherine` reference recompiler (`sh2_decoder.cpp` at commit `462f483c6563604f32997da6eb6d3d49f1db7eb9`).
4. **Thor 2 Decoder**: `thor::sh2::decode_sh2` (`include/thor/sh2/sh2_decoder.hpp`, `src/sh2/sh2_decoder.cpp`).

| Opcode | Mnemonic | Hardware Authority | Mednafen Implementation | Catherine Reference | Thor 2 Decoder | Disagreements |
|---|---|---|---|---|---|---|
| `0x6611` | `MOV.W @R1, R6` | `(Rm) -> Sign extension -> Rn` (16 to 32 bit) | `OP_MOV_W_REGINDIR_REG`, `WB_READ16` (`(int16)memrv`) | `MOVWL`, Rm=1, Rn=6 | `OpcodeId::MOV_W_READ_MEM`, Rm=1, Rn=6, `READ_S16` | **0** |
| `0x6F03` | `MOV R0, R15` | `Rm -> Rn` | `OP_MOV_REG_REG`, `R[n] = R[m]` | `MOV`, Rm=0, Rn=15 | `OpcodeId::MOV_REG`, Rm=0, Rn=15, `NONE` | **0** |
| `0xD417` | `MOV.L @(0x5C, PC), R4` | `(disp * 4 + PC) -> Rn`, base `(PC & ~3) + 4` | `OP_MOV_L_PCREL_REG`, `(PC & ~3) + (d << 2)` | `MOVLL4`, disp=0x17, Rn=4 | `OpcodeId::MOV_L_PC_REL`, Rn=4, disp=0x17, `READ_U32` | **0** |
| `0x6442` | `MOV.L @R4, R4` | `(Rm) -> Rn` (read before writeback) | `OP_MOV_L_REGINDIR_REG`, `WB_READ32` | `MOVLL`, Rm=4, Rn=4 | `OpcodeId::MOV_L_READ_MEM`, Rm=4, Rn=4, `READ_U32` | **0** |
| `0xA003` | `BRA 0x06004012` | `PC + 4 + disp * 2 -> PC`, delayed branch | `OP_BRA`, `UCRelDelayBranch((uint32)sign_x_to_s32(12, instr) << 1)` | `BRA`, disp=0x003, delay slot | `OpcodeId::BRA`, disp=3, target `0x06004012`, delay slot | **0** |
| `0x0009` | `NOP` | `PC + 2 -> PC`, no operation | `OP_NOP`, empty body | `NOP` | `OpcodeId::NOP`, sequential, `NONE` | **0** |

All four independent representations agree 100% on instruction class, mnemonics, operands, displacement scaling, memory access properties, and delay slot status.
Machine-readable manifest: `reference_decode_manifest.json`.

---

## 2. PC-Relative Effective Address & Branch Target Computation Rules

1. **PC-Relative Longword Load (`MOV.L @(disp, PC), Rn`)**:
   - Base address: `(PC & ~3) + 4`.
   - For instruction at `0x06004004`, `(0x06004004 & ~3) + 4 = 0x06004008`.
   - Scaled displacement: `0x17 * 4 = 0x5C`.
   - Effective address: `0x06004008 + 0x5C = 0x06004064`.
2. **Branch Displacement (`BRA label`)**:
   - Target address: `PC + 4 + (sign_extend_12(disp) * 2)`.
   - For instruction at `0x06004008` (`disp = 0x003`): `0x06004008 + 4 + 6 = 0x06004012`.
   - Delay slot: instruction at `PC + 2` (`0x0600400A`) executes before target jump.

---

## 3. L0 Semantic Verification

1. **Sign Extension**: `MOV.W` sign-extends 16-bit loads (`0x8000 -> 0xFFFF8000`).
2. **Same-Register Load Writeback**: Memory read completes before register is overwritten.
3. **NOP Preservation**: Zero registers or memory modified; PC advances sequentially.
4. **BRA Delayed Execution**: Instruction in delay slot executes with full register effects; subsequent instruction is branch destination.
5. **Illegal Slot Detection**: Branch inside an active delay slot triggers `ILLEGAL_SLOT_INSTRUCTION`.
6. **Register Isolation**: All unreferenced registers remain bit-identical.

---

## 4. Full Basic Block Replay vs Mednafen Oracle

- Block: `0x06004000..0x0600400A` (6 instructions).
- Pre-state: captured at cold boot entry breakpoint.
- Post-state: compared at block exit (`PC = 0x06004012`).
- Divergences across all 16 general registers, PC, PR, SR/T, GBR, VBR, MACH, MACL: **0**.
- Divergences across memory read/write logs: **0**.
