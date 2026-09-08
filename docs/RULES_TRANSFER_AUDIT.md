# Rules Transfer Audit — Sega-Thor -> Sega-Thor-2

Status: **COMPLETE**

Purpose: verify that the working discipline proven in `Serjio193/Sega-Thor` is carried into `Serjio193/Sega-Thor-2` without blindly copying Mega Drive/game-specific scope.

## Source rule set audited

The audit reviewed these first-project governance/evidence sources:

- `AGENTS.md`
- `AI_DEVELOPMENT_CONTRACT.md`
- `docs/DEVELOPMENT_RULES.md`
- `docs/RE_TOOLCHAIN_GUIDE.md`
- `docs/EVIDENCE_INTEGRITY_AUDIT.md`
- `CONTRIBUTING.md`
- the task-state format used in `TASK.md`

This audit concerns operating rules and evidence discipline, not copying implementation code or game-specific conclusions.

## Already present before this audit

Thor 2 already had strong coverage of these inherited principles:

- legal repository hygiene;
- fidelity-first priority;
- revision/hash provenance;
- explicit confidence labels;
- separate milestone/slice confidence;
- >=90% semantic-production slice gate;
- mechanical-before-semantic exception only with verification;
- `UNKNOWN -> EVIDENCE -> UNDERSTOOD -> IMPLEMENTED -> VERIFIED -> DOCUMENTED` lifecycle;
- one unproven methodological experiment at a time;
- evidence-backed naming;
- code/data/unknown separation;
- function boundaries as hypotheses;
- basic-block-first mechanical recompilation;
- fail-closed unsupported semantics;
- interpreter/oracle fallback;
- shadow-before-native promotion;
- verification hierarchy L0-L5;
- static/dynamic evidence separation;
- emulator-is-not-hardware-truth rule;
- AI cannot promote hypotheses/alter oracle without proof;
- deterministic testing and negative-result preservation;
- focused commits;
- no optimization without measurement;
- documentation set and definition-of-done discipline.

## Gaps found

The initial Thor 2 bootstrap did **not** fully transfer the following rules, or expressed them more weakly than the first project:

1. The 500-line source/build/test/tool limit was phrased as guidance rather than a hard project limit.
2. No separate `AI_DEVELOPMENT_CONTRACT.md` existed.
3. The mandatory task header was missing.
4. Explicit allowed stop states (`DONE`, `BLOCKED`, `USER DECISION REQUIRED`) were missing.
5. The end-of-session checkpoint format was missing.
6. The rule to **prove a blocker** before stopping was missing.
7. The general "one active technical result" rule was weaker than the Thor 2-specific "one methodological experiment" rule.
8. The before/during/after task workflow was not explicit.
9. The local CI-equivalent pre-push gate (Debug/Release/tests, diff check, file-limit check, GNU/Linux-equivalent when relevant) was missing.
10. The rule that GitHub Actions must not be the first compile/link attempt was missing.
11. Detailed C++20 ownership/RAII/platform-boundary/endian-address discipline was missing.
12. "Bug found -> regression test" was not explicit.
13. Generated local artifacts were not explicitly excluded from source/commit by default.
14. PR description requirements were missing.
15. Explicit scope-control examples for premature frameworks/native replacements were missing.
16. Historical SDK/toolchain/library evidence had no dedicated Saturn-adapted guide.
17. The evidence-integrity lesson from Sega-Thor M11.15 was only partial: exact round-trip needed a separate trust level from static/executed/behavior-verified evidence.
18. Weak caller chains were not explicitly prohibited from recursively bootstrapping trust.
19. No explicit rule required direct acknowledgement/correction when a prior implementation or claim is found wrong.
20. The original project's "do not change project goal without ADR" rule was not explicit enough.
21. `CONTRIBUTING.md` and a root `TASK.md` governance surface were absent.

## Repair performed

The Thor 2 repository now contains/updates:

- `AGENTS.md` — full mandatory top-level rules and task workflow;
- `AI_DEVELOPMENT_CONTRACT.md` — confidence gate, task header, stop states, session checkpoint, evidence trust;
- `docs/DEVELOPMENT_RULES.md` — C++20/source/testing/PR/scope/stop-condition discipline;
- `docs/RE_TOOLCHAIN_GUIDE.md` — Saturn-adapted historical SDK/toolchain/library evidence boundary;
- `TASK.md` — current/next bounded-task state surface;
- `CONTRIBUTING.md` — contributor entry rules;
- this audit report.

## Intentionally adapted rather than copied

The following first-project rules are conceptually retained but platform-specific wording was changed:

- 68000/Genesis ROM address semantics -> SH-2/Saturn revision/module/guest-address semantics;
- ROM-only provenance -> disc file + load address + module/overlay generation provenance;
- RAM/VDP side effects -> RAM/MMIO/DMA/interrupt/dual-CPU/device effects;
- Mega Drive historical toolchain guide -> Saturn historical toolchain/SDK/library guide;
- `genesis:` commit prefix -> `saturn:`.

## Intentionally not copied

These first-project constraints are **not** transferable rules for Thor 2:

- the prohibition on working on The Story of Thor 2;
- Mega Drive-specific active roadmap direction (ROM loader, `0x3820` decompressor, etc.);
- specific 68000/Z80/VDP addresses and known Beyond Oasis routines;
- specific historical candidate-tool conclusions for the Genesis ecosystem;
- milestone IDs/results unique to Sega-Thor.

Not copying these is deliberate scope adaptation, not a rules-transfer omission.

## Evidence-trust rule carried forward from Sega-Thor

Thor 2 now explicitly separates:

```text
BYTE_OR_ASM_ROUNDTRIP_EXACT
STATIC_SUPPORTED
EXECUTED
BEHAVIOR_VERIFIED
```

A successful exact round-trip does not imply behavior. A direct caller can support a target only when the edge is exact and the caller already has independently justified trust. Weak/circular caller chains cannot bootstrap confidence.

## Final assessment

Before this audit: **PARTIAL TRANSFER**.

After this audit: **COMPLETE FOR TRANSFERABLE GOVERNANCE RULES**.

Future rules added to Sega-Thor are not automatically inherited. If the first project's governance materially changes later, run a new explicit rules-transfer audit rather than silently assuming parity.
