# Current task

TASK: D1 — Deterministic Dynamic Oracle (T2-V01.1 Oracle Event-Semantics Repair)
WHY: establish reproducible dynamic execution observation of Thor 2 from a fixed canonical start recipe before attempting executable provenance, decode, or code translation.
CURRENT MILESTONE: D1 / V-01-core
TASK STATUS: BOUNDED_PROOF
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 95%
SLICE CONFIDENCE EVIDENCE: V-01-core event semantics repaired and verified across two independent cold-boot runs with deterministic mode, exact entry pipeline resolution (pc-2 fallback, MOV.W @R1,R6 retirement at step 2, MOV R0,R15 retirement at step 3), and direct dynamic read_watchpoint proof at 0x06081C10.
ACCEPTANCE CRITERIA:
- [x] reverify canonical BIN/CUE SHA-256 against T2-M0;
- [x] pin SaturnAutoRE source commit used to identify the oracle candidate;
- [x] pin the SaturnAutoRE Mednafen debug-fork source commit;
- [x] pin runnable Mednafen binary SHA-256 and build flags;
- [x] pin BIOS SHA-256, effective Saturn region, and remaining V-01-core configuration;
- [x] enable debugger `deterministic` mode and verify ack before free execution;
- [x] execute canonical cold-boot recipe;
- [x] observe runtime execution at candidate entry `0x06004000` with explicit pipeline / pc-2 event semantics;
- [x] directly prove selected memory read via dynamic `read_watchpoint 06081C10` hit (`0x060917DC`);
- [x] reproduce the declared observation identically across at least two independently initialized cold boots;
- [x] correct documentation overclaims (cycle-repeatable baseline; no unsupported L0/L1/L2 claims);
- [x] decide `ADOPT`, `ADOPT_PARTIAL`, `REJECT`, or `DEFER` for the bounded Mednafen oracle capability.
EVIDENCE AVAILABLE:
- canonical revision `thor2_ntsc_patched_fe11d2fb`;
- reverified image SHA-256 `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8`;
- reverified CUE SHA-256 `afc0b101bbb493adbd43fd44ffd76959484d67cf0b566137dd145f1c68d411e0`;
- SaturnAutoRE source pin `4662aad69f95222fe37c5e6b98f2285b1a7e4653`;
- Mednafen debug source pin `155426661b7ac3152e2c93a98da60ac33002b908`;
- `workstreams/T2-V01-dynamic-oracle/README.md`;
- `workstreams/T2-V01-dynamic-oracle/environment_pin.yaml`;
- `workstreams/T2-V01-dynamic-oracle/bounded_observation.md`.
KNOWN UNKNOWNS:
- exact runnable Mednafen binary/build flags for the V-01-core baseline (RESOLVED: gcc 13.3.0 native build SHA-256 861f03f3...);
- effective emulated Saturn region for this patched JTU image (RESOLVED: 0x4 SMPC_AREA_NA with mpr-17933.bin);
- next verification gate: V-01-automation scripting validation (deferred);
- `TH2.LOW` dynamic provenance (queued under D2 / V-02b).
ALLOWED SCOPE:
- V-01-core bounded Mednafen execution only;
- private BIOS/build/runtime artifacts outside GitHub;
- legal-safe source pins, hashes, configuration metadata, and evidence summaries in GitHub.
OUT OF SCOPE:
- public acquisition or redistribution of Saturn BIOS bytes;
- SaturnAutoRE automation validation (`V-01-automation` is later);
- `TH2.LOW` provenance (`V-02b`);
- SH-2 decoder/translator/native runtime work.

## Blocker resolution

The initial preflight was blocked pending user-supplied Saturn BIOS. The user subsequently provided retail firmware (`mpr-17933.bin` and `sega_101.bin`) in the local private workspace. `mpr-17933.bin` (NA/EU v1.00) was automatically selected by Mednafen for the canonical image's `JTU` region code (effective region `0x4` / `SMPC_AREA_NA`). The blocker is fully resolved.

## Last verified result

V-01-core event semantics repaired: identical execution verified across Run A and Run B with deterministic mode, pc-2 pipeline resolution, and dynamic read watchpoint hit at `0x06081C10`.

## Session checkpoint

CURRENT MILESTONE: D1 (V-01-core repaired; BOUNDED_PROOF maintained)
CURRENT TASK: D1 — Deterministic Dynamic Oracle (T2-V01.1 Repair)
TASK STATUS: BOUNDED_PROOF
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 95%
LAST VERIFIED RESULT: T2-V01.1 repair passed identically on Run A and Run B; deterministic mode ack verified; entry breakpoint pc-2 fallback documented; exact opcode retirements (Steps 1-6) cross-checked; dynamic read_watchpoint 06081C10 hit verified (0x060917DC at cycle 305462372)
FILES CHANGED: workstreams/T2-V01-dynamic-oracle/README.md, workstreams/T2-V01-dynamic-oracle/environment_pin.yaml, workstreams/T2-V01-dynamic-oracle/bounded_observation.md, docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/WORKLOG.md, docs/REVERSE_ENGINEERING.md, docs/DECISIONS.md, TASK.md
TESTS RUN: git diff --check; source line limit check; unittest suite; dual cold-boot test comparison (RUN_A vs RUN_B)
NEW KNOWLEDGE: Mednafen Automation_DebugHook pc-2 fallback catches delayed branches where PC advances to target+2; opcode 0x6611 (MOV.W @R1,R6) retires at step 2 loading R6=0x6611; opcode 0x6F03 (MOV R0,R15) retires at step 3 loading R15=0x06002EDC; read_watchpoint 06081C10 dynamically traps the 32-bit load by MOV.L @R4,R4 at 0x06004006; deterministic mode pins cycle repeatable baseline
OPEN QUESTIONS: none for V-01-core; authorization needed before proceeding to V-01-automation
BLOCKERS: none
EXACT NEXT ACTION: Review repaired V-01-core and authorize V-01-automation.
