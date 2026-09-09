# Decisions

## D-001 — Split public source from private commercial inputs

**Status:** ACCEPTED

GitHub contains only legal-safe source, tools, configs, tests, hashes/manifests, evidence summaries, and documentation. Commercial/raw binary inputs remain external/private.

## D-002 — One methodological experiment at a time

**Status:** ACCEPTED

Do not integrate several new external techniques simultaneously. Each method must be independently tested on Thor 2 and end in `ADOPT`, `ADOPT_PARTIAL`, `REJECT`, or `DEFER`.

## D-003 — Mechanical translation may precede semantic understanding

**Status:** WORKING HYPOTHESIS

The project will attempt machine-equivalent explicit-state translation before semantic naming. This becomes accepted only after Thor 2 SH-2 shadow/native proof.

## D-004 — Basic block is the initial translation unit

**Status:** WORKING HYPOTHESIS

Function boundaries are not required for correctness. They remain evidence-backed annotations until proven useful.

## D-005 — Unknown is a first-class classification

**Status:** ACCEPTED

`not executed` does not imply data. The project preserves unknown regions explicitly.

## D-006 — No wholesale Saturn runtime import

**Status:** ACCEPTED

External Saturn runtime components, including SaturnRecomp, are evaluated component-by-component against Thor 2 requirements and oracle evidence.

## D-007 — Transfer Sega-Thor governance, adapt platform-specific scope

**Status:** ACCEPTED

The transferable development/RE discipline proven in `Serjio193/Sega-Thor` is mandatory for Sega-Thor-2: confidence gating, evidence-first lifecycle, task/stop/checkpoint discipline, hard source-size limits, local validation, evidence-integrity rules, historical-toolchain boundaries, focused scope/commits, and synchronized project documentation.

Mega Drive/Beyond Oasis-specific roadmap instructions, addresses, milestone IDs, and platform-specific implementation facts are not copied. Their general governing principle is adapted to Saturn only when applicable.

The canonical transfer record is `docs/RULES_TRANSFER_AUDIT.md`. Future material governance changes in Sega-Thor require a new explicit audit rather than assumed automatic inheritance.

## D-008 — Dual-track planning and decoupled method validation

**Status:** ACCEPTED

The project planning model is rebuilt into two synchronized tracks:
1. **Development Track** (`docs/DEVELOPMENT_PLAN.md`): defines capabilities D0–D18 in dependency order, specifying what the project builds regardless of candidate tool choice.
2. **Verification Track** (`docs/PIPELINE_VALIDATION_PLAN.md`): defines bounded experiments V-01–V-14, specifying what evidence an external method must produce before adoption into the build path.

A candidate external method's failure (e.g. SaturnAutoRE in V-01) does not invalidate the development capability (D1 deterministic dynamic oracle); the project retains the requirement and tests alternative candidate tools. Planning documents distinguish `PROPOSED`, `VALIDATED`, `ADOPTED`, `SUPERSEDED`, `REJECTED`, and `DEFERRED`.
