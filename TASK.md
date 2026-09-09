# Current task

TASK: D1 — Deterministic Dynamic Oracle (V-01-core Bounded Emulator Observation)
WHY: establish reproducible dynamic execution observation of Thor 2 from a fixed canonical start recipe before attempting executable provenance, decode, or code translation.
CURRENT MILESTONE: D1 / V-01-core
TASK STATUS: BLOCKED
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 90%
SLICE CONFIDENCE EVIDENCE: T2-M0 established canonical disc bytes and boot metadata; T2-P0.1 tightened V-01-core to a bounded pinned observation contract; current preflight pinned the SaturnAutoRE/Mednafen source candidates and reverified the private game-image hashes, but execution cannot begin without a user-owned Saturn BIOS.
ACCEPTANCE CRITERIA:
- [x] reverify canonical BIN/CUE SHA-256 against T2-M0;
- [x] pin SaturnAutoRE source commit used to identify the oracle candidate;
- [x] pin the SaturnAutoRE Mednafen debug-fork source commit;
- [ ] pin runnable Mednafen binary SHA-256 and build flags;
- [ ] pin BIOS SHA-256, effective Saturn region, and remaining V-01-core configuration;
- [ ] execute canonical cold-boot recipe;
- [ ] observe at least one bounded CPU-labelled completed execution transition in `0TH2.BIN` with explicit event semantics;
- [ ] observe at least one selected memory effect (address, width, value, actor/event semantics);
- [ ] reproduce the declared observation identically across at least two independently initialized cold boots;
- [ ] decide `ADOPT`, `ADOPT_PARTIAL`, `REJECT`, or `DEFER` for the bounded Mednafen oracle capability.
EVIDENCE AVAILABLE:
- canonical revision `thor2_ntsc_patched_fe11d2fb`;
- reverified image SHA-256 `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8`;
- reverified CUE SHA-256 `afc0b101bbb493adbd43fd44ffd76959484d67cf0b566137dd145f1c68d411e0`;
- SaturnAutoRE source pin `4662aad69f95222fe37c5e6b98f2285b1a7e4653`;
- Mednafen debug source pin `155426661b7ac3152e2c93a98da60ac33002b908`;
- `workstreams/T2-V01-dynamic-oracle/README.md`;
- `workstreams/T2-V01-dynamic-oracle/environment_pin.yaml`.
KNOWN UNKNOWNS:
- exact runnable Mednafen binary/build flags for the V-01-core baseline;
- effective emulated Saturn region for this patched `JTU` image under the final pinned configuration;
- exact Master SH-2 boot PC sequence and selected memory effect, because execution has not begun.
ALLOWED SCOPE:
- V-01-core preflight and bounded Mednafen execution only;
- private BIOS/build/runtime artifacts outside GitHub;
- legal-safe source pins, hashes, configuration metadata, and evidence summaries in GitHub.
OUT OF SCOPE:
- public acquisition or redistribution of Saturn BIOS bytes;
- SaturnAutoRE automation validation (`V-01-automation` is later);
- `TH2.LOW` provenance (`V-02b`);
- SH-2 decoder/translator/native runtime work.

## Blocker proof

Mednafen's Saturn core requires a Saturn BIOS. No usable Saturn BIOS was found in the mounted private workspace or connected Drive searches performed for this task. The project will not source proprietary BIOS bytes from public download sites.

This blocker is input-specific; it is not evidence against Mednafen and does not justify `REJECT`.

## Last verified result

T2-P0.1 proof-contract repair is complete. V-01-core preflight has pinned the candidate source revisions and reverified the canonical game input, but no emulator observation has executed.

## Session checkpoint

CURRENT MILESTONE: D1 / V-01-core
CURRENT TASK: D1 — Deterministic Dynamic Oracle (V-01-core Bounded Emulator Observation)
TASK STATUS: BLOCKED
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 90%
LAST VERIFIED RESULT: canonical BIN/CUE hashes reverified; SaturnAutoRE and Mednafen debug-fork source commits pinned; BIOS requirement confirmed; no valid BIOS available in private workspace
FILES CHANGED: workstreams/T2-V01-dynamic-oracle/README.md, workstreams/T2-V01-dynamic-oracle/environment_pin.yaml, TASK.md, docs/PROJECT_STATE.md, docs/FILE_MAP.md, docs/WORKLOG.md
TESTS RUN: SHA-256 recheck of mounted BIN/CUE; local executable/BIOS preflight; connected Drive BIOS/Mednafen searches; source-pin verification against public repositories
NEW KNOWLEDGE: V-01-core can use the SaturnAutoRE-pinned debug Mednafen source at `155426661...`; current execution is blocked before boot because required private firmware is absent
OPEN QUESTIONS: which user-owned Saturn BIOS and effective region will be pinned for this patched JTU image?
BLOCKERS: required user-owned Saturn BIOS is not available in the private workspace; runnable Mednafen binary hash/build flags remain unpinned until execution environment is prepared
EXACT NEXT ACTION: provide a legally owned Saturn BIOS privately; then hash it, pin region/build configuration, and resume V-01-core cold-boot execution.
