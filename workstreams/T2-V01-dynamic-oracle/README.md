# V-01-core — Bounded Emulator Observation

Status: **BLOCKED — REQUIRED PRIVATE BIOS INPUT MISSING**

Baseline project commit: `229bfb6449a4e37b71d506b32f8454318209e699`

## Objective

Establish the first bounded D1 dynamic-oracle proof using a pinned Mednafen Saturn debug build and the canonical Thor 2 revision. This workstream is intentionally limited to the V-01-core observation contract. SaturnAutoRE automation, `TH2.LOW` provenance, decoding, and recompilation remain out of scope.

## Canonical input re-check

The mounted private inputs were re-hashed immediately before the attempted experiment:

- disc image SHA-256: `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8`
- CUE SHA-256: `afc0b101bbb493adbd43fd44ffd76959484d67cf0b566137dd145f1c68d411e0`

They match revision `thor2_ntsc_patched_fe11d2fb` from T2-M0.

## Candidate oracle source pins

SaturnAutoRE is not adopted by this result. It is used only to identify the exact debug-emulator source candidate for V-01-core.

- `AJBats/SaturnAutoRE` source pin: `4662aad69f95222fe37c5e6b98f2285b1a7e4653`
- pinned `mednafen` submodule repository: `AJBats/mednafen-saturn-debug`
- pinned debug Mednafen source commit: `155426661b7ac3152e2c93a98da60ac33002b908`

At that pin, the debugger documentation defines automation launch mode, explicit Master/Slave register dumps, instruction stepping/breakpoints, memory reads, watchpoints, and event/cycle reporting. This is source capability evidence only; no binary build has been accepted yet.

## BIOS requirement and blocker proof

Mednafen's Saturn documentation requires a Saturn BIOS image. The documented default firmware identities are:

- `sega_101.bin` — Japan BIOS — SHA-256 `dcfef4b99605f872b6c3b6d05c045385cdea3d1b702906a0ed930df7bcb7deac`
- `mpr-17933.bin` — North America / Europe BIOS — SHA-256 `96e106f740ab448cf89f0dd49dfbac7fe5391cb6bd6e14ad5e3061c13330266f`

The Thor 2 image header records regions `JTU`, so this workstream will not guess the effective emulated region or BIOS. Region selection, BIOS filename, BIOS hash, and Mednafen region settings must be pinned together before execution.

Preflight checks performed:

1. Local execution environment contains the canonical BIN/CUE but no `sega_101.bin`, `mpr-17933.bin`, or Saturn-BIOS-labelled file in the mounted private paths checked.
2. Connected private Drive searches for `mpr-17933`, `sega_101`, `Saturn BIOS`, and `mednafen` found no usable BIOS or debug-emulator binary.
3. No `mednafen` executable is installed in the current execution environment.
4. The debug-emulator source candidate and source commit are pinned, but a runnable binary hash/build flags cannot be recorded before a build exists.

The missing user-owned BIOS alone is sufficient to prevent a valid Saturn boot under Mednafen. The project will not obtain proprietary BIOS bytes from public download sites.

## Result

`V01_CORE_PRE_EXECUTION_BLOCKED_BIOS`

This is **not** a `REJECT` result for Mednafen or SaturnAutoRE. V-01-core has not executed, so no oracle adoption decision is permitted.

D1 remains `READY_FOR_BOUNDED_TEST` as a capability, while the current task stop state is `BLOCKED` until the required private firmware input is supplied.

## Re-entry condition

Provide a legally owned Saturn BIOS image privately. Before boot, the next execution session must:

1. hash the BIOS;
2. pin the effective Saturn region and BIOS selection;
3. build or otherwise obtain the pinned debug Mednafen candidate from source `155426661b7ac3152e2c93a98da60ac33002b908` and record executable hash/build flags;
4. complete the remaining V-01-core configuration fields;
5. run two independently initialized cold boots and compare the declared bounded observation contract.

No `TH2.LOW` provenance work begins until V-01-core passes.
