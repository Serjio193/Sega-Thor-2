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
