# Current task

TASK: T2-P0 Dual-Track Development / Verification Plan Hardening
WHY: decouple development capabilities (what we build) from external verification experiments (what evidence candidate tools must produce), ensuring external tool failure never invalidates project goals.
CURRENT MILESTONE: T2-P0 planning checkpoint
TASK STATUS: DONE
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 95%
SLICE CONFIDENCE EVIDENCE: Full review of existing governance, T2-M0 evidence, and method proposals; clean separation established in DEVELOPMENT_PLAN.md (D0–D18) and PIPELINE_VALIDATION_PLAN.md (V-01–V-14); ADR D-008 accepted.
ACCEPTANCE CRITERIA:
- [x] audit current planning model and identify conflations of capabilities and candidate tools;
- [x] build capability-oriented Development Track (D0–D18) independent of external vendor choice;
- [x] rebuild Verification/Adoption Track (V-01–V-14) with smallest falsifiable experiments;
- [x] establish explicit development/verification coupling matrix;
- [x] challenge next step (evaluate M1 / V-01 readiness and prerequisites);
- [x] produce risk/proof map for all major Saturn technical uncertainties;
- [x] define planning status vocabulary (PROPOSED, VALIDATED, ADOPTED, SUPERSEDED, REJECTED, DEFERRED);
- [x] update project records (DEVELOPMENT_PLAN.md, PIPELINE_VALIDATION_PLAN.md, ROADMAP.md, PROJECT_STATE.md, DECISIONS.md, FILE_MAP.md, WORKLOG.md, TASK.md).
EVIDENCE AVAILABLE:
- T2-M0 confirmed substrate `thor2_ntsc_patched_fe11d2fb`;
- `disc_manifest.tsv`, `executable_candidates.tsv`, `static_load_evidence.md`;
- proven rules transfer from `Serjio193/Sega-Thor` (`RULES_TRANSFER_AUDIT.md`);
- candidate method proposals (SaturnAutoRE, Daytona, Splat, Ghidra, Catherine, SaturnRecomp, Azel, Baroque).
KNOWN UNKNOWNS:
- exact Mednafen build / automation reliability for this revision (deferred to V-01);
- whether `TH2.LOW` is direct-loaded or transformed (deferred to D2 / V-10);
- Slave SH-2 involvement in game logic (deferred to D1 observation).
ALLOWED SCOPE:
- planning and governance hardening only;
- creating and updating Markdown documentation, roadmap, and ADR records.
OUT OF SCOPE:
- running Mednafen / SaturnAutoRE;
- implementing SH-2 recompiler or runtime code;
- importing external codebases;
- modifying confirmed T2-M0 evidence.

## Last verified result

T2-P0 dual-track planning model established (decision D-008).

## Session checkpoint

CURRENT MILESTONE: T2-P0 completed; D1 / V-01 queued
CURRENT TASK: T2-P0 Dual-Track Development / Verification Plan Hardening
TASK STATUS: DONE
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 95%
LAST VERIFIED RESULT: D0–D18 Development Track and V-01–V-14 Verification Track established; D-008 recorded
FILES CHANGED: docs/DEVELOPMENT_PLAN.md, docs/PIPELINE_VALIDATION_PLAN.md, docs/ROADMAP.md, docs/PROJECT_STATE.md, docs/DECISIONS.md, docs/FILE_MAP.md, docs/WORKLOG.md, TASK.md
TESTS RUN: documentation cross-consistency check; git status check; source line limit check
NEW KNOWLEDGE: confirmed that M1 was conflating capability (dynamic oracle) with technology (SaturnAutoRE); established that V-01 can adopt Mednafen even if SaturnAutoRE automation fails; mapped all 13 critical technical risks to non-blocking milestones
OPEN QUESTIONS: which exact Mednafen version/commit produces deterministic save-state execution on this host?
BLOCKERS: none
EXACT NEXT ACTION: prepare bounded V-01 experiment (pin Mednafen version, define minimal boot observation, test reproducibility without broad instrumentation).
