# Current task

TASK: T2-INTEGRITY-01 Repair Premature Terminal Completion Claims & Resume Real Recovery
WHY: Factual review identified that terminal completion claims at commit 093abf0 were premature:
1. BGM.BIN (MC68EC000 sound driver, 673,792 bytes) is CATALOGED but not reassembled byte-exact, disassembled into mnemonics, or runtime-verified.
2. FULL_ASM_GAME_GATE is NOT_SATISFIED: only 6 startup checkpoints were verified; full gameplay (title->gameplay, map transitions, combat, sound) is not verified.
3. StandaloneRuntime still links and executes guest CPU fallback interpreter (`thor::sh2::step_sh2`), so D18 guest CPU removal is NOT_PROVEN.
4. Only two mechanically generated native game blocks exist (`bb_06004000`, `bb_06004280`); broad C++ translation remains frozen under ADR D-015 until real FULL_ASM_GAME_GATE.
5. test_guest_removal compares two candidate instances (self-consistency), which does not establish L5 oracle equivalence against Mednafen reference.
6. Native VDP1, VDP2, and SCSP implementations are reference prototypes, not verified replacements against live Thor 2 workloads.
7. Canonical milestones D13 (Guest Address/Type Provenance) and D14 (Resource Decode/Reencode) were skipped.

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015, ADR D-016)
TASK STATUS: IN_PROGRESS
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Factual audit completed; documentation and scorecards updated to represent evidence honestly; recovery loop resumed toward real FULL_ASM_GAME_GATE and progressive C++ recovery.
ACCEPTANCE CRITERIA:
- [x] update ASM_RECOVERY_SCORECARD.json, TASK.md, PROJECT_STATE.md, ROADMAP.md, WORKLOG.md, DECISIONS.md;
- [x] set PROJECT_COMPLETION_STATE = IN_PROGRESS, FULL_ASM_GAME_GATE = NOT_SATISFIED, STANDALONE_NATIVE_GATE = NOT_SATISFIED;
- [x] re-freeze broad C++ translation per ADR D-015 until real FULL_ASM_GAME_GATE;
- [ ] establish machine-enforced gate validators;
- [ ] re-audit ASM_90 denominator by processor;
- [ ] implement M68K assembly toolchain and build BGM.BIN lossless assembly container;
- [ ] prove M68K sound driver runtime in Mednafen;
- [ ] audit Slave SH-2 across broad gameplay/debug scenarios;
- [ ] build multi-scenario gameplay regression harness.

EVIDENCE AVAILABLE:
- Proven SH-2 assembly containers for 0TH2.BIN, TH2.LOW, SET07.BIN;
- Discrete startup verification across 6 checkpoints;
- Prototype native subsystems and StandaloneRuntime.
KNOWN UNKNOWNS:
- M68K sound driver code/data boundary in BGM.BIN;
- Slave SH-2 activity during late gameplay or combat;
- Live Thor 2 VDP1/VDP2 command streams during active combat.
ALLOWED SCOPE:
- Documentation correction, gate validators, BGM.BIN recovery, M68K tooling, gameplay regression harness.
OUT OF SCOPE:
- Premature D18 completion claims.

## Last verified result

`T2_INTEGRITY_01_STARTED`: Factual audit completed; premature terminal claims superseded; project status honestly reset to IN_PROGRESS.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015, ADR D-016)
CURRENT TASK: T2-INTEGRITY-01 Gate Hardening & BGM.BIN/M68K Pipeline
TASK STATUS: IN_PROGRESS
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: Integrity audit documented; scorecard and roadmap updated.
FILES CHANGED: workstreams/ASM_RECOVERY_SCORECARD.json, TASK.md, docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/WORKLOG.md, docs/DECISIONS.md.
TESTS RUN: 35/35 CTests passing; line limits clean.
NEW KNOWLEDGE: Real completion requires M68K assembly reconstruction, multi-scenario gameplay verification, removal of guest CPU fallback, and true L5 oracle parity.
OPEN QUESTIONS: Location and boundaries of M68K executable routines in BGM.BIN.
EXACT NEXT ACTION: Push integrity repair commit and establish machine-enforced gate validators.
