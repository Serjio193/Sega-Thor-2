# Current task

TASK: T2-M1 SaturnAutoRE Dynamic-Oracle Validation
WHY: prove or reject SaturnAutoRE/Mednafen as a reproducible dynamic observation/oracle layer for this exact Thor 2 revision before adopting any of its workflow or runtime assumptions.
CURRENT MILESTONE: T2-M1 method validation
TASK STATUS: QUEUED / PROPOSED — not yet adopted
MILESTONE UNDERSTANDING CONFIDENCE: 70%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 85%
SLICE CONFIDENCE EVIDENCE: T2-M0 proved canonical revision/file hashes and produced a strong static `TH2.LOW -> 0x002DA000` candidate mapping, but actual dynamic load/write/fetch behavior is not yet observed.
ACCEPTANCE CRITERIA:
- reproduce one deterministic Thor 2 dynamic observation from a fixed starting state;
- observation records emulator build/version, CPU, PC, and relevant memory effect/provenance;
- repeat the observation at least twice with matching bounded result;
- specifically attempt to confirm or falsify the `TH2.LOW` candidate mapping with runtime load/write and later instruction fetch evidence;
- store raw/private trace material outside GitHub and commit only legal-safe evidence summaries;
- decide `ADOPT`, `ADOPT_PARTIAL`, `REJECT`, or `DEFER` for SaturnAutoRE as a dynamic-oracle method.
EVIDENCE AVAILABLE:
- confirmed revision `thor2_ntsc_patched_fe11d2fb`;
- `workstreams/T2-M0-disc-census/disc_manifest.tsv`;
- `workstreams/T2-M0-disc-census/executable_candidates.tsv`;
- `workstreams/T2-M0-disc-census/static_load_evidence.md`;
- public SaturnAutoRE repository/method description previously reviewed.
KNOWN UNKNOWNS:
- whether the current SaturnAutoRE/Mednafen automation works unchanged with this image/revision;
- exact semantics of the `0x0600A0F8` callee;
- whether `TH2.LOW` is copied directly, transformed, relocated, or otherwise processed before execution;
- whether the chosen observation requires Master SH-2 only or additional CPU/device context.
ALLOWED SCOPE:
- bounded SaturnAutoRE setup/inspection;
- one deterministic dynamic observation;
- private save-state/trace artifacts outside GitHub;
- legal-safe configs/tools/evidence summaries needed for the experiment.
OUT OF SCOPE:
- mechanical SH-2 -> C++ recompilation;
- broad function discovery;
- native renderer/audio/runtime work;
- importing SaturnRecomp components;
- assuming `TH2.LOW` semantics before dynamic proof;
- combining another unproven external method into the same experiment.

## Last verified result

T2-M0 is complete at commit `5a0de2f33ddfb8423ce41214c4b3be65afdb64f9`.

## Session checkpoint

CURRENT MILESTONE: T2-M1 queued
CURRENT TASK: SaturnAutoRE Dynamic-Oracle Validation
TASK STATUS: QUEUED / PROPOSED
MILESTONE UNDERSTANDING CONFIDENCE: 70%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 85%
LAST VERIFIED RESULT: T2-M0 canonical substrate + executable census PASS
FILES CHANGED: governance/rules transfer only in the current audit task
TESTS RUN: documentation/rules cross-audit; no production build target exists yet
NEW KNOWLEDGE: initial Thor 2 rules transfer was incomplete; missing operational contracts were identified and repaired
OPEN QUESTIONS: can SaturnAutoRE deterministically confirm/falsify `TH2.LOW` runtime provenance?
BLOCKERS: none established yet
EXACT NEXT ACTION: start only the bounded T2-M1 SaturnAutoRE experiment; do not begin recompilation or other method adoption in parallel.
