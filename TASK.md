# Current task

TASK: D1 — Deterministic Dynamic Oracle (V-01-core Bounded Emulator Observation)
WHY: establish reproducible dynamic execution observation of Thor 2 from a fixed canonical start recipe before attempting executable provenance, decode, or code translation.
CURRENT MILESTONE: D1 / V-01-core
TASK STATUS: BOUNDED_PROOF
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 95%
SLICE CONFIDENCE EVIDENCE: V-01-core passed identically across two independent cold-boot runs under pinned Mednafen debug fork with exact CPU, PC, register, cycle, and memory read parity.
ACCEPTANCE CRITERIA:
- [x] reverify canonical BIN/CUE SHA-256 against T2-M0;
- [x] pin SaturnAutoRE source commit used to identify the oracle candidate;
- [x] pin the SaturnAutoRE Mednafen debug-fork source commit;
- [x] pin runnable Mednafen binary SHA-256 and build flags;
- [x] pin BIOS SHA-256, effective Saturn region, and remaining V-01-core configuration;
- [x] execute canonical cold-boot recipe;
- [x] observe at least one bounded CPU-labelled completed execution transition in `0TH2.BIN` with explicit event semantics;
- [x] observe at least one selected memory effect (address, width, value, actor/event semantics);
- [x] reproduce the declared observation identically across at least two independently initialized cold boots;
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

V-01-core bounded emulator observation passed identically across two independent cold-boot runs (Run A and Run B).

## Session checkpoint

CURRENT MILESTONE: D1 (V-01-core completed; BOUNDED_PROOF achieved)
CURRENT TASK: D1 — Deterministic Dynamic Oracle
TASK STATUS: BOUNDED_PROOF
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 95%
LAST VERIFIED RESULT: V-01-core passed identically on Run A and Run B; 19-parameter configuration pinned; CPU (Master SH-2), entry transition (0x06004000 -> 0x06004002 -> 0x06004004), cycle (305462360 -> 305462361), and memory read effect (0x06081C10 = 0x060917DC) confirmed
FILES CHANGED: workstreams/T2-V01-dynamic-oracle/README.md, workstreams/T2-V01-dynamic-oracle/environment_pin.yaml, workstreams/T2-V01-dynamic-oracle/bounded_observation.md, docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/WORKLOG.md, docs/REVERSE_ENGINEERING.md, docs/DECISIONS.md, docs/FILE_MAP.md, TASK.md
TESTS RUN: git diff --check; source line limit check; dual cold-boot test comparison (RUN_A vs RUN_B)
NEW KNOWLEDGE: confirmed Master SH-2 boot entry into 0TH2.BIN at 0x06004000 from BIOS at frame 680, cycle 305462360; autodetected region 0x4 (NA) with mpr-17933.bin; initial BSS zeroing loop clears High WRAM 0x060917DC..0x060B29CC; Mednafen debug fork provides cycle-accurate deterministic baseline for Thor 2
OPEN QUESTIONS: none for V-01-core; authorization needed before proceeding to V-01-automation
BLOCKERS: none
EXACT NEXT ACTION: Review V-01-core evidence before authorizing V-01-automation.
