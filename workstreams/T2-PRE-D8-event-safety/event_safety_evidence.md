# Event Safety Evidence — `bb_06004000`

Status: **`PRE_D8_MINIMUM_EVENT_SAFETY_PASS` (bounded execution only)**  
Environment: Pinned Mednafen oracle, North American / European BIOS (`mpr-17933.bin`)  
Media: Canonical Thor 2 image (`fe11d2fb...`)

---

## 1. Multi-Run Independent Cold Boot Verification

Two independent cold boot runs (Run A and Run B) were executed with isolated HOME, IPC, and fresh temporary state directories.

| Metric | Run A | Run B | Match Status |
|---|---|---|---|
| Deterministic Init Ack | `ok deterministic cycle=433495 seq=2` | `ok deterministic cycle=433495 seq=2` | EXACT |
| Entry Breakpoint Hit | `break pc=0x06004002 addr=0x06004000 frame=680` | `break pc=0x06004002 addr=0x06004000 frame=680` | EXACT |
| Step 1 Retirement PC | `done step pc=0x06004004 frame=680` | `done step pc=0x06004004 frame=680` | EXACT |
| Step 2 Retirement PC | `done step pc=0x06004006 frame=680` | `done step pc=0x06004006 frame=680` | EXACT |
| Step 3 Retirement PC | `done step pc=0x06004008 frame=680` | `done step pc=0x06004008 frame=680` | EXACT |
| Step 4 Retirement PC | `done step pc=0x0600400A frame=680` | `done step pc=0x0600400A frame=680` | EXACT |
| Step 5 Retirement PC | `done step pc=0x0600400C frame=680` | `done step pc=0x0600400C frame=680` | EXACT |
| Step 6 Retirement PC | `done step pc=0x06004014 frame=680` | `done step pc=0x06004014 frame=680` | EXACT |
| Step 7 Retirement PC | `done step pc=0x06004016 frame=680` | `done step pc=0x06004016 frame=680` | EXACT |
| Architectural Exit PC | `0x06004012` | `0x06004012` | EXACT |
| Post-Exit R0..R15 | Matches exactly | Matches exactly | EXACT |
| SCU DMA in Window | 0 | 0 | EXACT |
| Slave SH-2 Activity | Inactive (`active=0`) | Inactive (`active=0`) | EXACT |

---

## 2. Event Safety Audits

### 2.1 MMIO Instruction Access Audit
The memory references performed by the 6 instructions in `bb_06004000` are:
1. `0x06004000`: `MOV.W @R1, R6` -> reads address `0x06004000` (High Work RAM).
2. `0x06004002`: `MOV R0, R15` -> no memory access.
3. `0x06004004`: `MOV.L @(0x5C, PC), R4` -> reads literal pool at `0x06004064` (High Work RAM).
4. `0x06004006`: `MOV.L @R4, R4` -> reads `0x06081C10` (High Work RAM).
5. `0x06004008`: `BRA 0x06004012` -> no memory access.
6. `0x0600400A`: `NOP` -> no memory access.

Zero accesses occur in Saturn MMIO spaces (`0x20000000..0x25FFFFFF` or `0xFFFFFE00..0xFFFFFFFF`).

### 2.2 Interrupt Audit
- At entry: `SR = 0x00000001` (`I3..I0 = 0`).
- No interrupts are asserted or acknowledged during steps 1 through 7.
- Under the Hitachi SH-1/SH-2 Programming Manual (Section 2.3), interrupts are strictly prohibited from being accepted between a delayed branch instruction (`BRA`) and its delay slot (`NOP`).
- The block executes without interrupt disruption.

### 2.3 SCU DMA Audit
- `dma_trace` log recorded all DMA channel activity from emulator startup through completion of step 7.
- The last pre-entry DMA transfer occurred at cycle `153,570,917` (BIOS CD buffer setup).
- Between entry at cycle `305,462,360` and exit at cycle `305,462,388` (spanning exactly 28 master cycles: 305,462,388 - 305,462,360 = 28), zero SCU DMA transfers were scheduled or active.

### 2.4 Multiprocessor Interaction Audit
- The slave SH-2 CPU was inspected via emulator hooks and stderr monitoring:
  - `SH2_SETACTIVE: cpu=SH2-S active=0`
  - `SH2_DEACTIVATED: cpu=SH2-S last_PC=00000000`
- Slave SH-2 remains completely dormant during this execution window.

---

## 3. Verdict

`bb_06004000` satisfies all requirements for atomic state transition under the declared bounded contract:
**`PRE_D8_MINIMUM_EVENT_SAFETY_PASS`**.
