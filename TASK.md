# Current task

TASK: D1 — Deterministic Dynamic Oracle (T2-V01.2 Automation Validation)
WHY: test whether the pinned SaturnAutoRE automation/control layer can reproduce the accepted V-01-core observation without silently changing configuration or execution semantics.
CURRENT MILESTONE: D1 / V-01-automation
TASK STATUS: BOUNDED_PROOF
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 95%
SLICE CONFIDENCE EVIDENCE: Pinned `MednafenBot` IPC control harness drove the pinned Mednafen debug oracle across two independent cold-boot runs with 100% parity to the accepted V-01-core baseline; launch configuration deltas audited and proven neutral; negative control verified.
ACCEPTANCE CRITERIA:
- [x] verify external tool pins (SaturnAutoRE commit, Mednafen debug commit, Mednafen binary hash);
- [x] re-verify canonical input hashes (BIN, CUE, selected BIOS) against `environment_pin.yaml`;
- [x] audit automation layer launch configuration deltas vs accepted V-01-core;
- [x] execute minimal scripted control probe using `MednafenBot` in isolated environments;
- [x] reproduce accepted entry observation, step progression, and dynamic read watchpoint hit;
- [x] compare Automation Run A vs Run B (100% reproducibility);
- [x] compare Automation runs against accepted repaired V-01-core baseline (100% match);
- [x] perform negative control sanity check (flag deliberate corruptions);
- [x] decide `ADOPT_PARTIAL` for `LOW_LEVEL_CONTROL_LAYER_PROVEN` (ADR D-010).
EVIDENCE AVAILABLE:
- canonical revision `thor2_ntsc_patched_fe11d2fb`;
- reverified image SHA-256 `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8`;
- reverified CUE SHA-256 `afc0b101bbb493adbd43fd44ffd76959484d67cf0b566137dd145f1c68d411e0`;
- selected BIOS SHA-256 `96e106f740ab448cf89f0dd49dfbac7fe5391cb6bd6e14ad5e3061c13330266f`;
- SaturnAutoRE source pin `4662aad69f95222fe37c5e6b98f2285b1a7e4653`;
- Mednafen debug source pin `155426661b7ac3152e2c93a98da60ac33002b908`;
- `workstreams/T2-V01-dynamic-oracle/README.md`;
- `workstreams/T2-V01-dynamic-oracle/environment_pin.yaml`;
- `workstreams/T2-V01-dynamic-oracle/bounded_observation.md`;
- `workstreams/T2-V01-dynamic-oracle/automation_validation.md`.
KNOWN UNKNOWNS:
- high-level autonomous RE workflows (`auto_re.py pick/explore/verify`, graduation, NOP tests) remain unverified;
- `0TH2.BIN` runtime extent provenance (queued under D2 / V-02a);
- `TH2.LOW` dynamic provenance (queued under D2 / V-02b).
ALLOWED SCOPE:
- low-level `MednafenBot` control layer validation only;
- private runtime artifacts outside GitHub;
- legal-safe evidence summaries in GitHub.
OUT OF SCOPE:
- autonomous RE cycles (`auto_re.py`);
- NOP mutation experiments or code modification;
- `0TH2.BIN` / `TH2.LOW` provenance (`V-02a` / `V-02b`);
- SH-2 decoder/recompiler implementation.

## Last verified result

V-01-automation control layer validated: `MednafenBot` drives pinned Mednafen debug oracle with 100% parity across Run A and Run B, 100% parity against accepted V-01-core baseline, and passes negative control test. ADR D-010 accepted as `ADOPT_PARTIAL` (`LOW_LEVEL_CONTROL_LAYER_PROVEN`).

## Session checkpoint

CURRENT MILESTONE: D1 (V-01-core and V-01-automation completed; BOUNDED_PROOF maintained)
CURRENT TASK: D1 — Deterministic Dynamic Oracle (T2-V01.2 Automation Validation)
TASK STATUS: BOUNDED_PROOF
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 95%
LAST VERIFIED RESULT: T2-V01.2 automation validation passed; MednafenBot IPC driver reproduced accepted V-01-core contract (entry cycle 305462360, steps 1-6, dynamic read_watchpoint 06081C10 hit 0x060917DC at cycle 305462372); negative control passed with 5/5 caught corruptions; ADR D-010 adopted as ADOPT_PARTIAL (LOW_LEVEL_CONTROL_LAYER_PROVEN)
FILES CHANGED: workstreams/T2-V01-dynamic-oracle/README.md, workstreams/T2-V01-dynamic-oracle/automation_validation.md, docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/WORKLOG.md, docs/DECISIONS.md, docs/FILE_MAP.md, TASK.md
TESTS RUN: git diff --check; source line limit check; unittest suite; dual automation cold-boot comparison; baseline comparison; negative control test
NEW KNOWLEDGE: MednafenBot IPC automation protocol uses 'run' for free execution until break, 'break pc=' for breakpoint hit events with auto-context, and 'done step' with auto-appended registers; stock -cd.image_memcache 1 injection is neutral for Thor 2 boot sequence; higher auto_re.py pipelines remain unverified
OPEN QUESTIONS: none for V-01; ready for D2 / V-02a
BLOCKERS: none
EXACT NEXT ACTION: Prepare V-02a 0TH2.BIN executable provenance experiment.
