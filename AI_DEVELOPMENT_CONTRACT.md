# AI Development Contract

This document defines mandatory operating discipline for AI-assisted development in Sega-Thor-2. It adapts the proven contract from `Serjio193/Sega-Thor` to the Sega Saturn / Thor 2 project.

## Core execution rules

1. Track **milestone understanding** and **current implementation-slice understanding** separately when useful.
2. Start or extend semantic production C++ for a specific slice only when `CURRENT SLICE UNDERSTANDING CONFIDENCE >= 90%` and that confidence is justified by concrete evidence for the slice.
3. If slice confidence remains below 90% after inspecting the repository record and available evidence, do not implement speculative semantic production behavior. Continue RE, probes, tests, documentation, or other bounded evidence gathering until the slice reaches the gate, becomes objectively `BLOCKED`, or requires `USER DECISION REQUIRED`.
4. Low milestone confidence does not block a well-bounded >=90% slice. High milestone confidence never authorizes a <90% slice.
5. Mechanically generated machine-equivalent code is a special case: it may precede semantic understanding only when exact instruction semantics and the declared differential contract are independently verified. It remains non-semantic until evidence supports structure/naming.
6. Define explicit acceptance criteria before substantive implementation.
7. Do not declare a task DONE until implementation/result, required verification, documentation, limitations, and exact next step are recorded.
8. If blocked, prove the blocker: record what was checked, what evidence/input is missing, why safe continuation is impossible, and the smallest next action.
9. Work on one active technical result at a time. Only one unproven methodological experiment may be active at once.
10. Do not expand scope, redesign architecture, or add speculative frameworks without a documented need and an ADR when architectural.
11. Prefer evidence over elegance. Never turn a hypothesis into fact without new evidence.
12. Never rename an unknown original routine/object to a confident semantic name without evidence.
13. Keep human-maintained executable/source/build/test/tool files at or below 500 lines. Documentation is exempt; generated sources may exceed the limit only when explicitly marked generated.
14. Do not change tests merely to make a failing implementation pass. Determine whether implementation, understanding, oracle, or test is wrong.
15. Prefer two independent verification methods for critical reverse-engineered behavior when practical.
16. Keep commits/tasks small and single-purpose.
17. Every meaningful task updates the project record: WORKLOG; REVERSE_ENGINEERING when applicable; DECISIONS when applicable; FILE_MAP when structure changes; ROADMAP/PROJECT_STATE when status changes.
18. If a previous implementation/classification/test/claim is wrong, state that directly and record the reason and correction.
19. Do not optimize without measurement.
20. Faithful behavior comes first; enhancements follow verified parity unless explicitly authorized by roadmap/ADR.
21. Historical SDK/toolchain/library evidence follows `docs/RE_TOOLCHAIN_GUIDE.md` and never becomes authority merely through ecosystem plausibility.
22. Exact decode/disassembly/reassembly does not imply execution or behavioral correctness. Weak evidence chains may not bootstrap trust.

## Confidence interpretation

Use confidence narrowly and operationally:

```text
MILESTONE UNDERSTANDING CONFIDENCE:
CURRENT SLICE UNDERSTANDING CONFIDENCE:
```

A low milestone score with a high slice score can be valid. A high milestone score with a sub-90% slice does not authorize semantic production implementation of that slice.

Confidence is not a subjective optimism score. State briefly what evidence justifies >=90% when semantic production implementation begins.

Project confidence vocabulary should use the repository's standard labels where practical:

- `CONFIRMED`
- `HIGH`
- `MEDIUM`
- `LOW`
- `HYPOTHESIS`
- `UNKNOWN`
- `UNVERIFIED`

## Required task lifecycle

Every substantive task follows:

```text
UNKNOWN
  -> EVIDENCE
  -> UNDERSTOOD
  -> IMPLEMENTED
  -> VERIFIED
  -> DOCUMENTED
```

For a research-only task, `IMPLEMENTED` may mean the intended probe/tool/report exists rather than production game code. The lifecycle still ends at DOCUMENTED.

## Required task header

Before substantive implementation/code changes, record in `TASK.md` or the active workstream record:

```text
TASK:
WHY:
CURRENT MILESTONE:
TASK STATUS:
MILESTONE UNDERSTANDING CONFIDENCE:
CURRENT SLICE UNDERSTANDING CONFIDENCE:
SLICE CONFIDENCE EVIDENCE:
ACCEPTANCE CRITERIA:
EVIDENCE AVAILABLE:
KNOWN UNKNOWNS:
ALLOWED SCOPE:
OUT OF SCOPE:
```

If `CURRENT SLICE UNDERSTANDING CONFIDENCE < 90%`, the task is in evidence-gathering mode and semantic production C++ changes for that slice are prohibited. Verified mechanical translation may proceed only under the explicit exception in the core rules.

## Allowed stop states

Work on the active task may stop only as one of these states:

### DONE

All acceptance criteria are met with recorded verification/documentation.

### BLOCKED

Continuation is objectively impossible without missing evidence/input/capability, and the blocker is documented with the smallest next action.

### USER DECISION REQUIRED

Multiple materially different valid choices remain and repository goals/evidence do not determine the choice.

### DEFERRED BY PLAN

The bounded experiment is complete enough to decide that further work is intentionally postponed by the validated pipeline plan. The reason and re-entry condition must be recorded.

Otherwise continue the current bounded task rather than silently switching scope.

## Method-experiment outcomes

A methodological experiment also receives one of:

- `ADOPT`
- `ADOPT_PARTIAL`
- `REJECT`
- `DEFER`

`PROVEN` describes evidence; `ADOPT` describes a pipeline decision. Do not conflate them.

## Evidence trust rules

Representation trust and behavior trust are separate.

Useful levels include:

```text
BYTE_OR_ASM_ROUNDTRIP_EXACT
STATIC_SUPPORTED
EXECUTED
BEHAVIOR_VERIFIED
```

Rules:

1. Round-trip exactness proves representation correspondence only.
2. `STATIC_SUPPORTED` requires independent evidence such as exact xrefs, vector/load provenance, well-bounded tables, or other non-circular static support.
3. `EXECUTED` requires dynamic observation tied to revision/module/CPU identity.
4. `BEHAVIOR_VERIFIED` requires the declared state/output contract to match an authoritative/independent reference.
5. A caller may raise confidence in a callee only when the edge is exact and the caller already has independently justified trust. Weak caller chains do not recursively bootstrap themselves.
6. Downgrades and invalidated evidence are valid results and must be preserved when useful.

## Session checkpoint

At the end of every substantive work session record:

```text
CURRENT MILESTONE:
CURRENT TASK:
TASK STATUS:
MILESTONE UNDERSTANDING CONFIDENCE:
CURRENT SLICE UNDERSTANDING CONFIDENCE:
LAST VERIFIED RESULT:
FILES CHANGED:
TESTS RUN:
NEW KNOWLEDGE:
OPEN QUESTIONS:
BLOCKERS:
EXACT NEXT ACTION:
```

For repository-only documentation/research tasks, mark unavailable build/test fields explicitly rather than inventing validation.

## Validation discipline

Before pushing implementation changes, run the locally available CI-equivalent checks relevant to the changed surface. When build targets exist, normally include:

- Debug build/tests;
- Release build/tests;
- `git diff --check`;
- source-code file-limit check;
- GNU/Linux-equivalent build/link check for portability/toolchain-sensitive changes.

If a required toolchain is unavailable, record the limitation before push. Do not use GitHub Actions as the first compile/link test for a work-in-progress implementation.

Research-only metadata/docs commits should still verify internal consistency, referenced hashes/paths where practical, and repository hygiene.

## User-facing reporting

Keep progress reports concise and factual:

- what was found;
- what changed;
- how it was verified;
- what remains unknown;
- exact next action.

Do not overstate evidence or imply background/asynchronous completion.

## Primary project question

Before any change ask:

> What exactly does this change prove, reproduce, or make verifiable about the original Thor 2 behavior?

If the answer is unclear, do not make the change.
