# V-01-core — Bounded Emulator Observation Evidence

Status: **PASS (V01_CORE_REPAIR_PASS / BOUNDED_PROOF)**
Target: Runtime execution observation at candidate entry `0x06004000` under pinned Mednafen debug fork
Target Revision: `thor2_ntsc_patched_fe11d2fb`

## 1. Experiment Definition & Contract

The experiment executes a strictly bounded observation from cold boot on canonical Thor 2 disc media (`fe11d2fb...`) under the pinned Mednafen environment defined in `environment_pin.yaml`.

- **Observation Target**: Runtime execution at High Work RAM address `0x06004000` (candidate first-read entry; full disc-file provenance of `0TH2.BIN` is deferred to `V-02a`).
- **Target CPU**: `MASTER_SH2` (`CPU[0]`).
- **Deterministic Baseline Setup**: `deterministic` command sent before free execution (ack: `ok deterministic cycle=433495`).
- **Entry Event**: Breakpoint hit on requested `0x06004000` (arrives at hook `pc=0x06004002` via `pc - 2` fallback due to delayed branch pipeline advance from BIOS `0x06003FFE`).
- **Step Transitions**: Step-by-step instruction retirement verified against canonical startup opcodes.
- **Memory Read Effect**: Dynamically proven via `read_watchpoint 06081C10` hit during execution of opcode `0x6442` (`MOV.L @R4, R4`) at `0x06004006`.
- **Reproduction Requirement**: Identical result across at least two completely independent cold-boot runs (fresh isolated environment, zero prior save state or mutable NVRAM).

---

## 2. Independent Cold Boot Runs

### Run A
- Isolated HOME: `/tmp/t2_v01_repair_run_a/home`
- Isolated IPC: `/tmp/t2_v01_repair_run_a/ipc`
- Clean initialization: firmware staged, no prior state
- Execution mode: `--sound 0 --automation /tmp/t2_v01_repair_run_a/ipc`

### Run B
- Isolated HOME: `/tmp/t2_v01_repair_run_b/home`
- Isolated IPC: `/tmp/t2_v01_repair_run_b/ipc`
- Clean initialization: firmware staged, no prior state
- Execution mode: `--sound 0 --automation /tmp/t2_v01_repair_run_b/ipc`

---

## 3. Pinned Initialization & Entry Observation

### 3.1 Startup & Deterministic Mode

| Command | Run A Ack | Run B Ack | Match |
|---|---|---|---|
| Startup | `ready frame=0 cycle=0 seq=1` | `ready frame=0 cycle=0 seq=1` | EXACT |
| `deterministic` | `ok deterministic cycle=433495 seq=2` | `ok deterministic cycle=433495 seq=2` | EXACT |
| `breakpoint 06004000` | `ok breakpoint 0x06004000 total=1 cycle=433495 seq=3` | `ok breakpoint 0x06004000 total=1 cycle=433495 seq=3` | EXACT |

### 3.2 Entry Breakpoint Hit Semantics (`pc - 2` Fallback)

In Mednafen's SH-2 core, delayed branch instructions (`JMP`, `JSR`, `RTS`, `BRA`) set `PC = target` and execute the delay slot instruction. When the delay slot completes, pipeline advance (`DoIDIF`) leaves `CPU[0].PC = target + 2`. The debugger inline hook `Automation_DebugHook(pc)` checks `pc`, misses, and checks `pc - 2`, correctly catching the branch target.

| Field | Run A | Run B | Match |
|---|---|---|---|
| Requested Breakpoint | `0x06004000` | `0x06004000` | EXACT |
| Debugger Hook PC | `0x06004002` | `0x06004002` | EXACT |
| Effective Hit Addr | `0x06004000` | `0x06004000` | EXACT |
| Frame Counter | 680 | 680 | EXACT |
| Master Cycle | 305,462,360 | 305,462,360 | EXACT |
| Prev PC Ring | `0x06004004, 0x06004002, 0x06004000, 0x06003FFE` | `0x06004004, 0x06004002, 0x06004000, 0x06003FFE` | EXACT |
| Previously Retired PC | `0x06003FFE` (BIOS delay slot) | `0x06003FFE` (BIOS delay slot) | EXACT |
| Callstack | `PC=0x06004002 SP=0x06001000 PR=0x00000000 \| 0x06002240->0x06002D88 ret=0x06002244 \| depth=1` | `PC=0x06004002 SP=0x06001000 PR=0x00000000 \| 0x06002240->0x06002D88 ret=0x06002244 \| depth=1` | EXACT |

### 3.3 Pre-State Architectural Registers at Entry

| Register | Value (Run A & Run B) | Role / Provenance |
|---|---|---|
| R0 | `0x06002EDC` | Target stack pointer passed from BIOS loader |
| R1 | `0x06004000` | Entry address pointer |
| R2 | `0x00000000` | Initialized |
| R3 | `0x00002650` | Initialized |
| R4 | `0x00002650` | Initialized |
| R5 | `0x060002DC` | Initialized |
| R6 | `0x00000000` | Initialized |
| R7 | `0x06000D00` | Initialized |
| R8–R14 | `0x00000000` | Initialized |
| R15 (SP) | `0x06001000` | Initial Master stack pointer from Saturn CD header |
| PC | `0x06004002` | Pipeline hook PC |
| SR | `0x00000001` | Status register (T=1) |
| PR | `0x00000000` | Procedure register |
| GBR | `0x00000000` | Global base register |
| VBR | `0x06000000` | Vector base register |
| MACH / MACL | `0x00000000` | Multiply-accumulate registers |

---

## 4. Multi-Step Pipeline Resolution & Memory Read Proof

### 4.1 Canonical Startup Opcode Cross-Check

Inspection of the binary extents at `0x06004000` confirms the exact canonical instruction stream:
- `0x06004000`: `0x6611` — `MOV.W @R1, R6` (loads 16-bit word from `@0x06004000`, which is `0x6611`, into `R6`)
- `0x06004002`: `0x6F03` — `MOV R0, R15` (loads target stack pointer `0x06002EDC` into `R15`)
- `0x06004004`: `0xD417` — `MOV.L @(0x5C, PC), R4` (loads pointer `0x06081C10` from literal pool at `0x06004064` into `R4`)
- `0x06004006`: `0x6442` — `MOV.L @R4, R4` (dereferences `@0x06081C10`, loading `0x060917DC` into `R4`)

### 4.2 Step Execution Trace (Run A & Run B Identical)

| Step | Action / Command | Post-Step PC | Master Cycle | Cycle Delta | Register Delta & Semantics |
|---|---|---|---|---|---|
| — | Entry BP Hit | `0x06004002` | `305462360` | — | Initial state: `R15=0x06001000`, `R6=0x00000000`, `R4=0x00002650` |
| 1 | `step 1` | `0x06004004` | `305462361` | +1 | Delay branch pipeline fill; no register changes |
| 2 | `step 1` | `0x06004006` | `305462362` | +1 | Opcode `0x6611` (`MOV.W @R1, R6`) retires: **`R6` becomes `0x00006611`** |
| 3 | `step 1` | `0x06004008` | `305462363` | +1 | Opcode `0x6F03` (`MOV R0, R15`) retires: **`R15` becomes `0x06002EDC`** |
| 4 | `step 1` | `0x0600400A` | `305462371` | +8 | Opcode `0xD417` (`MOV.L @(0x5C, PC), R4`) retires: **`R4` becomes `0x06081C10`** |
| 5 | `step 1` | `0x0600400A` | `305462372` | +1 | Opcode `0x6442` (`MOV.L @R4, R4`) executes memory read: **`hit read_watchpoint` fires** |
| 6 | `step 1` | `0x0600400C` | `305462372` | 0 | Opcode `0x6442` writeback completes: **`R4` becomes `0x060917DC`** |

### 4.3 Direct Proof of Selected Memory Read (`read_watchpoint 06081C10`)

At Step 5, the emulator dynamically intercepted the bus read access:
- **Watchpoint Event**: `hit read_watchpoint pc=0x0600400A pr=0x00000000 addr=0x06081C10 val=0x060917DC frame=680`
- **CPU Actor**: `MASTER_SH2` (`CPU[0]`)
- **Load Instruction**: `0x6442` (`MOV.L @R4, R4`) located at PC `0x06004006` (hook reports `pc=0x0600400A`)
- **Address Accessed**: `0x06081C10` (High Work RAM)
- **Access Width**: 4 bytes (32-bit word)
- **Value Read**: `0x060917DC` (BSS start address)
- **Frame**: 680
- **Master Cycle**: `305,462,372`
- **Pre-access R4 state**: `0x06081C10` (pointer to variable)
- **Post-access R4 state**: `0x060917DC` (loaded value after step 6)

---

## 5. Cheap Census Observations

- Master SH-2 Execution: **OBSERVED** (active throughout boot and startup sequence).
- Slave SH-2 Execution: **OBSERVED_ZERO** in this bounded window (`SH2_SETACTIVE: cpu=SH2-S active=0`, `SH2_DEACTIVATED: cpu=SH2-S last_PC=00000000`).
- SCU DSP Activity: **NOT_INSTRUMENTED** (not probed in bounded window).
- M68K Activity: **NOT_INSTRUMENTED** (sound disabled via `--sound 0`).

---

## 6. Conclusion & Oracle Adoption

Both independent cold-boot runs under the pinned environment matched identically:
- Deterministic initialization ack;
- Entry breakpoint trigger (`0x06004000`) and pipeline hook PC (`0x06004002`);
- Pre-execution registers across all 23 CPU registers;
- Step 1–6 transitions, opcodes, and cycle counts;
- Dynamic memory read watchpoint hit at `0x06081C10` with value `0x060917DC`.

Verification status: **Bounded D1 oracle reproducibility achieved (cycle-stamped / cycle-repeatable emulator baseline)**.
Oracle capability decision: **`ADOPT`** (ADR D-009) for bounded execution observation of Thor 2.
Disc file provenance of `0TH2.BIN` remains scoped under D2 / `V-02a`.
