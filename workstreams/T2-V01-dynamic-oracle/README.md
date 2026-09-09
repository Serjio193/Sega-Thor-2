
# T2-V01 — SaturnAutoRE / Mednafen Setup + V-01-core Execution

Status: **DONE (V01_CORE_BOUNDED_PROOF)**
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

## 3. Bounded Observation Results (V-01-core)

Two independent cold-boot runs (`RUN_A` and `RUN_B`) were executed from fresh isolated environments with zero reused state or save states.

Results:
1. **Entry Point Reached**: Master SH-2 entered `0TH2.BIN` boot code at `0x06004000` at frame 680, cycle `305462360`.
2. **Pre-State Parity**: All 23 CPU registers (R0-R15, PC, SR, PR, GBR, VBR, MACH, MACL) matched identically between Run A and Run B.
3. **Instruction Step Transition**: `step 1` advanced PC from `0x06004002` to `0x06004004`, incrementing cycle count from `305462360` to `305462361` (+1 cycle) identically in both runs.
4. **Memory Effect Observed**: Memory read from `0x06081C10` (width: 4 bytes, value: `0x060917DC`) matched identically in both runs.
5. **Slave CPU**: Remained inactive (`SH2_SETACTIVE: cpu=SH2-S active=0`) during this initial boot window.

Detailed comparison tables and raw traces are documented in `bounded_observation.md`.

---

## 4. Acceptance Criteria Audit

- [x] Pin exact Mednafen version/commit, build hash/flags, and complete 19-parameter configuration recipe (`environment_pin.yaml`).
- [x] Execute canonical boot recipe for Thor 2 image `fe11d2fb...`.
- [x] Observe at least one bounded CPU-labelled execution transition in `0TH2.BIN` boot code with explicit event semantics (`MASTER_SH2`, `PRE_EXECUTION` at `0x06004000`, `COMPLETED_EXECUTION` at `0x06004002` -> `0x06004004`).
- [x] Observe at least one selected memory effect (address `0x06081C10`, width 4, value `0x060917DC`).
- [x] Reproduce the exact observation identically across at least two independent cold-boot runs (Run A and Run B).
- [x] Record emulator version, CPU identity, and observation semantics without committing copyrighted bytes.
- [x] Decide `ADOPT` for bounded Mednafen oracle capability.

---

## 5. Next Action

Review V-01-core evidence before authorizing V-01-automation.
