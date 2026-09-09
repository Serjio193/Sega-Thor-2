# T2-V01 — SaturnAutoRE / Mednafen Setup + V-01-core Execution

Status: **DONE (V01_CORE_REPAIR_PASS / BOUNDED_PROOF)**
Target: Establish deterministic dynamic oracle capability via pinned Mednafen debug fork
Baseline commit: `229bfb6449a4e37b71d506b32f8454318209e699`

## 1. Overview

This workstream established the local pinned Mednafen debug oracle environment and executed the first `V-01-core` bounded emulator observation on canonical Thor 2 media (`fe11d2fb...`).

Per project rules:
- SaturnAutoRE is used solely as the reproducible source/container for the pinned debug Mednafen fork.
- Autonomous RE automation (`auto_re.py status`, `pick`, `explore`, `verify`, `graduate`, NOP tests) was NOT run and remains deferred to later verification stages (`V-01-automation`).
- Commercial and private firmware (`sega_101.bin`, `mpr-17933.bin`) and disc images remain strictly untracked and protected outside git.
- The external tool repositories (`SaturnAutoRE`, `mednafen`) are kept external as sibling directories, never vendored into `Sega-Thor-2`.

---

## 2. Environment Pin

Exact pinned metadata is documented in `environment_pin.yaml`:
- **SaturnAutoRE commit**: `4662aad69f95222fe37c5e6b98f2285b1a7e4653`
- **Mednafen debug submodule commit**: `155426661b7ac3152e2c93a98da60ac33002b908`
- **Mednafen binary SHA-256**: `861f03f36882ac2cff9334e3bdb54c8a29991f711ff81cb1132183ade9828c49` (size: 22,723,160 bytes)
- **Host OS**: `Linux 6.18.33.2-microsoft-standard-WSL2 x86_64 (Ubuntu 24.04.1 LTS)`
- **Toolchain**: `gcc / g++ 13.3.0`
- **Build Method**: Supported Native Linux automation build documented in `mednafen/BUILD_WINDOWS.md` line 84. Zero C++ source modifications.
- **Active Firmware**: `mpr-17933.bin` (SHA-256: `96e106f740ab448cf89f0dd49dfbac7fe5391cb6bd6e14ad5e3061c13330266f`) selected automatically by Mednafen's built-in disc header detection for region `0x4` (`SMPC_AREA_NA`).

---

## 3. Bounded Observation Results (V-01-core Repaired)

Two independent cold-boot runs (`RUN_A` and `RUN_B`) were executed from fresh isolated environments with zero reused state or save states.

Results:
1. **Deterministic Mode Ack**: `deterministic` command sent before free execution acknowledged identically (`ok deterministic cycle=433495`).
2. **Entry Point Reached**: Master SH-2 hit breakpoint on requested `0x06004000` at frame 680, cycle `305462360`. Pipeline hook PC reported `0x06004002` due to `pc - 2` fallback after delayed branch from BIOS `0x06003FFE`.
3. **Pre-State Parity**: All 23 CPU registers matched identically between Run A and Run B (initial SP: `0x06001000`).
4. **Step Transitions & Opcode Retirements**:
   - Step 1 (`pc=0x06004004`, cycle 305462361): Pipeline fill advance.
   - Step 2 (`pc=0x06004006`, cycle 305462362): Opcode `0x6611` (`MOV.W @R1, R6`) retires, setting `R6 = 0x00006611`.
   - Step 3 (`pc=0x06004008`, cycle 305462363): Opcode `0x6F03` (`MOV R0, R15`) retires, setting `R15 = 0x06002EDC`.
   - Step 4 (`pc=0x0600400A`, cycle 305462371): Opcode `0xD417` (`MOV.L @(0x5C, PC), R4`) retires, setting `R4 = 0x06081C10`.
   - Step 5 (`pc=0x0600400A`, cycle 305462372): Opcode `0x6442` (`MOV.L @R4, R4`) reads memory, dynamically triggering `read_watchpoint 06081C10` with value `0x060917DC`.
   - Step 6 (`pc=0x0600400C`, cycle 305462372): Writeback completes, setting `R4 = 0x060917DC`.
5. **Slave CPU**: Remained inactive (`SH2_SETACTIVE: cpu=SH2-S active=0`) during this initial boot window.

Detailed comparison tables and raw traces are documented in `bounded_observation.md`.

---

## 4. Acceptance Criteria Audit

- [x] Pin exact Mednafen version/commit, build hash/flags, and complete configuration recipe (`environment_pin.yaml`).
- [x] Enable debugger `deterministic` mode and verify ack before free execution.
- [x] Execute canonical boot recipe for Thor 2 image `fe11d2fb...`.
- [x] Observe runtime execution transition at candidate entry `0x06004000` with explicit pipeline/pc-2 event semantics.
- [x] Directly prove selected memory read via dynamic `read_watchpoint 06081C10` hit (PC `0x06004006`, width 4, value `0x060917DC`, cycle `305462372`).
- [x] Reproduce the exact observation identically across at least two independent cold-boot runs (Run A and Run B).
- [x] Record emulator version, CPU identity, and observation semantics without committing copyrighted bytes.
- [x] Decide `ADOPT` for bounded Mednafen oracle capability.

---

## 5. Automation Validation Results (V-01-automation)

The low-level IPC control harness `MednafenBot` (`AJBats/SaturnAutoRE/mednafen/mednafen_bot.py`) was evaluated against the accepted `V-01-core` bounded observation.

Results:
1. **Reproducibility**: Two independent automation runs (`RUN_A` and `RUN_B`) achieved 100% parity across all commands, registers, cycles, steps, and watchpoints.
2. **Oracle Baseline Match**: 100% identical match against accepted `V-01-core` baseline.
3. **Launch Delta Audit**: Stock `MednafenBot.start()` unconditionally injects `-cd.image_memcache 1`; controlled comparison proved this delta neutral.
4. **Negative Control**: 5 deliberate baseline corruptions were tested; comparator flagged all 5 divergences without false negatives.
5. **Decision**: `ADOPT_PARTIAL` (ADR D-010) for `LOW_LEVEL_CONTROL_LAYER_PROVEN`. Higher-level autonomous RE workflows (`auto_re.py`) remain unverified.

Detailed logs and tables are documented in `automation_validation.md`.

---

## 6. Next Action

Proceed to capability **D2 — Executable Module Provenance** via verification experiment **V-02a — 0TH2.BIN Executable Provenance**.
