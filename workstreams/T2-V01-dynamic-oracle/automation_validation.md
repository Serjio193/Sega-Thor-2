# V-01-automation — Control-Layer Validation Evidence

Status: **PASS (V01_AUTOMATION_ADOPT_PARTIAL / LOW_LEVEL_CONTROL_LAYER_PROVEN)**
Target: Pinned `MednafenBot` IPC automation control layer from `AJBats/SaturnAutoRE`
Target Revision: `thor2_ntsc_patched_fe11d2fb`

## 1. Experiment Scope & Objectives

The experiment evaluates whether the low-level automation control layer (`MednafenBot` in `AJBats/SaturnAutoRE/mednafen/mednafen_bot.py`, commit `4662aad69f95222fe37c5e6b98f2285b1a7e4653`) can reliably control the pinned Mednafen debug oracle (commit `155426661b7ac3152e2c93a98da60ac33002b908`) and reproduce the accepted `V-01-core` bounded observation without altering emulator semantics.

### Scope Boundaries
- **Tested**: Low-level scripted IPC control (`MednafenBot`: process launch, action/ack protocol, deterministic mode, breakpoint installation, free run, instruction stepping, register queries, and memory read watchpoint capture).
- **Not Tested / Out of Scope**: High-level autonomous RE loops (`auto_re.py pick/explore/verify`), NOP mutation tests, claim generation, function graduation, call-graph inference, and whole-game determinism.

---

## 2. Launch & Configuration Delta Audit

The stock `MednafenBot.start()` implementation was compared against the accepted `V-01-core` launch recipe in `environment_pin.yaml`:

| Parameter | V-01-core Recipe | MednafenBot Launch | Classification |
|---|---|---|---|
| Binary | `src/mednafen` | `src/mednafen` (via `_find_mednafen`) | `IDENTICAL` |
| Sound | `--sound 0` | `--sound 0` (with `sound=False`) | `IDENTICAL` |
| Automation Flag | `--automation <dir>` | `--automation <dir>` | `IDENTICAL` |
| CUE Path | Explicit target CUE | Explicit target CUE | `IDENTICAL` |
| Image Memcache | Default (`0`) | `-cd.image_memcache 1` | `CONFIG_DELTA_PROVEN_NEUTRAL` |
| Crash Dump Dir | Unset | `MEDNAFEN_CRASH_DUMP_DIR` set | `CONFIG_DELTA_PROVEN_NEUTRAL` |
| WSL Interop Var | Unset | `WSLENV` updated | `CONFIG_DELTA_PROVEN_NEUTRAL` |
| Emulator Home | Explicit isolated dir | Explicit isolated dir (`home_dir`) | `IDENTICAL` |

Controlled comparison proved that `-cd.image_memcache 1` does not alter CPU cycles, frame progression, instruction retirements, or memory access behavior during the canonical Thor 2 boot sequence.

---

## 3. Scripted Control Protocol Resolution

Mednafen's automation interface emits distinct response keywords depending on command types:
1. `deterministic`: Acknowledged synchronously as `ok deterministic cycle=433495`.
2. `breakpoint 06004000`: Acknowledged synchronously as `ok breakpoint 0x06004000 total=1`.
3. `run`: Unpauses frame advance without intermediate ack; next ack is the breakpoint hit event `break pc=0x06004002 addr=0x06004000 frame=680 bp_total=1`.
4. `dump_regs`: Emits complete register line (`R0=... R15=... PC=...`).
5. `step 1`: Acknowledged upon step completion with `done step pc=0x... frame=680` (auto-appending registers and callstack).
6. `read_watchpoint 06081C10`: Acknowledged synchronously as `ok read_watchpoint 0x06081C10`.
7. Watchpoint Hit: When `step 1` executes opcode `0x6442`, the bus access triggers `hit read_watchpoint pc=0x0600400A pr=0x00000000 addr=0x06081C10 val=0x060917DC frame=680`.

---

## 4. Independent Automation Runs

### 4.1 Run A vs Run B Comparison

Two independent runs were performed from clean cold boots in isolated environments (`/tmp/t2_v01_auto_run_a` and `/tmp/t2_v01_auto_run_b`):

| Checkpoint | Automation Run A | Automation Run B | Match |
|---|---|---|---|
| Deterministic Ack | `ok deterministic cycle=433495 seq=2` | `ok deterministic cycle=433495 seq=2` | **EXACT** |
| Breakpoint Hit Ack | `break pc=0x06004002 addr=0x06004000 frame=680` | `break pc=0x06004002 addr=0x06004000 frame=680` | **EXACT** |
| Master Cycle at Entry | `305,462,360` | `305,462,360` | **EXACT** |
| Initial R15 (SP) | `0x06001000` | `0x06001000` | **EXACT** |
| Initial R0 (Target SP) | `0x06002EDC` | `0x06002EDC` | **EXACT** |
| All Entry Regs (23) | Identical across R0–R15, PC, SR, PR, GBR, VBR, MACH, MACL | Identical across R0–R15, PC, SR, PR, GBR, VBR, MACH, MACL | **EXACT** |
| Step 1 (`pc`, cycle) | `0x06004004`, `305462361` | `0x06004004`, `305462361` | **EXACT** |
| Step 2 (`pc`, cycle, R6) | `0x06004006`, `305462362`, `0x00006611` | `0x06004006`, `305462362`, `0x00006611` | **EXACT** |
| Step 3 (`pc`, cycle, R15) | `0x06004008`, `305462363`, `0x06002EDC` | `0x06004008`, `305462363`, `0x06002EDC` | **EXACT** |
| Step 4 (`pc`, cycle, R4) | `0x0600400A`, `305462371`, `0x06081C10` | `0x0600400A`, `305462371`, `0x06081C10` | **EXACT** |
| Step 5 Watchpoint Hit | `hit read_watchpoint pc=0x0600400A addr=0x06081C10 val=0x060917DC cycle=305462372` | `hit read_watchpoint pc=0x0600400A addr=0x06081C10 val=0x060917DC cycle=305462372` | **EXACT** |
| Step 6 (`pc`, cycle, R4) | `0x0600400C`, `305462372`, `0x060917DC` | `0x0600400C`, `305462372`, `0x060917DC` | **EXACT** |
| Clean Shutdown | Completed cleanly | Completed cleanly | **EXACT** |

### 4.2 Comparison Against Accepted V-01-core Baseline

Both Automation Run A and Run B matched the accepted `V-01-core` baseline identically across all 23 CPU registers, deterministic cycle timestamps, instruction pipeline progression, and dynamic memory watchpoint values.

---

## 5. Fault / Negative Control Sanity Check

To verify that the evaluation harness detects divergences rather than unconditionally passing:
- Five deliberate corruptions were injected into expected baseline values (hook PC `0x06004008`, cycle `999999999`, R15 `0xDEADBEEF`, Step 2 R6 `0x00009999`, Step 5 watchpoint value `0x00000000`).
- The evaluation script reported `FAIL` and caught all 5 discrepancies without false negatives.

---

## 6. Adoption Decision & Scope

- **Decision**: **`ADOPT_PARTIAL`** (ADR D-010).
- **Adopted Scope**: `LOW_LEVEL_CONTROL_LAYER_PROVEN` — `MednafenBot` is adopted as a reliable low-level Python harness for scripted control and deterministic observation extraction.
- **Unverified Scope**: Higher-level SaturnAutoRE autonomous workflows (`auto_re.py`, function discovery heuristics, NOP experiments, and graduation logic) remain unverified and unadopted.
- **D1 Milestone State**: Remains **`BOUNDED_PROOF`**.
