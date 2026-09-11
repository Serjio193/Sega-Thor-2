# Current task

TASK: T2-ASM-CARVER-01 — Thor Saturn Recovery Carver: Interval Database + UNKNOWN Audit + Executable Candidate Discovery
WHY: The user confirmed strict return to ASM-first completion before any broad C++ translation. The scorecard mnemonic coverage denominator (~96.6%) only counted previously confirmed code (57,266 bytes) while leaving 1,399,886 bytes as unexamined UNKNOWN. An evidence-driven forensic carver was required to systematically audit all UNKNOWN ranges, enforce fail-closed execution conflict invariants, discover hidden code/data/padding structures, and honestly re-audit the denominator.

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015, ADR D-019)
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Central Interval Database (`IntervalDatabase`) and 8 Saturn-specific detectors implemented in `tools/carver/`; converged to fixed point in 3 passes with 0 conflicts; discovered 2,842 newly confirmed executable code bytes, 81,435 bytes of structured data (literal pools, pointer tables, MMIO pointers, strings), and 82,562 bytes of padding; reduced UNKNOWN by 166,839 bytes; Provenance DAG generated with 13,780 nodes; 7/7 carver unit tests passing; `validate_recovery_gates.py` passing with audited 92.07% coverage.

ACCEPTANCE CRITERIA:
- [x] Freeze broad C++ translation scaling (D17, D18, StandaloneRuntime) per explicit user instruction;
- [x] Central Interval Database (`tools/carver/interval_db.py`): canonical non-overlapping partition covering 100% of bytes across all modules;
- [x] Saturn-Specific Detector Registry (`tools/carver/detector_registry.py`, `detectors_code.py`, `detectors_data.py`) with 8 detectors;
- [x] R-Studio Style RAM → Disc Signature Carver (`tools/carver/ram_disc_carver.py`) scanning all 33 ISO files;
- [x] Execution Conflict Rule (Rule 4): dynamically retired bytes promoted to CONFIRMED_CODE fail-closed; proven DATA never decoded as code;
- [x] Graph Expansion & Provenance DAG (`tools/carver/provenance_dag.py`): Rule 5 enforced (only CONFIRMED nodes expand);
- [x] Fixed-Point Loop (`tools/carver/carver_pipeline.py`): iterative loop converging in 3 passes with 0 conflicts;
- [x] UNKNOWN Gap Report (`tools/carver/gap_reporter.py`): residual gaps audited and grouped into 43 campaigns; P1 execution gaps = 0;
- [x] Denominator Re-audit: expanded confirmed code from 57,266 to 60,108 bytes; coverage honestly adjusted to 92.07% (passing ASM_90_GATE >= 90.00%);
- [x] Evidence artifacts: `workstreams/T2-ASM-CARVER/` generated with README, interval_db_summary, carver_passes, unknown_gap_report, provenance_graph_summary, carver_evidence;
- [x] Scorecard updated with track separation: CPLUSPLUS_TRANSLATION = FROZEN_BY_ASM_FIRST_ARCHITECTURE;
- [x] Maintain <= 500 lines limit across all human-maintained files.

EVIDENCE AVAILABLE:
- Carver evidence directory: `workstreams/T2-ASM-CARVER/*`;
- Audited scorecard: `workstreams/ASM_RECOVERY_SCORECARD.json`;
- Test suite: `tests/carver/test_carver_pipeline.py`.

KNOWN UNKNOWNS:
- Exact mechanical decoding of the 2,842 newly confirmed code bytes into mnemonics to advance mnemonic coverage towards 100%.

ALLOWED SCOPE:
- Forensic carver, interval database, detector registry, provenance DAG, gap reporting, evidence artifacts, scorecard update, documentation.

OUT OF SCOPE:
- Broad C++ translation before FULL_ASM_GAME_GATE; unverified promotion of heuristic candidates.

## Last verified result

`T2_ASM_CARVER_01_PASS`: Central Interval Database and 8 Saturn-specific detectors implemented; fixed-point convergence reached in 3 passes with 0 conflicts; discovered 2,842 newly confirmed executable code bytes (expanding denominator to 60,108 bytes), 81,435 bytes structured data, and 82,562 bytes padding; reduced UNKNOWN by 166,839 bytes; 0 residual P1 execution gaps in UNKNOWN; audited mnemonic coverage confirmed at 92.07% (passing ASM_90_GATE); 7/7 carver unit tests pass; `validate_recovery_gates.py` passes.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015, ADR D-019)
CURRENT TASK: T2-ASM-CARVER-01 Saturn Recovery Carver & Denominator Re-Audit
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: Fixed point reached in 3 passes, 0 conflicts, 2,842 new code bytes discovered, 163,997 data+padding bytes classified, audited mnemonic coverage 92.07%, 7/7 carver tests pass.
FILES CHANGED: tools/carver/*, tests/carver/*, workstreams/T2-ASM-CARVER/*, workstreams/ASM_RECOVERY_SCORECARD.json, docs/DECISIONS.md, TASK.md
TESTS RUN: `python tests/carver/test_carver_pipeline.py` (7/7 PASS), `python tools/asm/validate_recovery_gates.py` (PASS), `ctest --test-dir build -E test_gameplay_scenarios` (40/40 PASS).
NEW KNOWLEDGE: 0TH2.BIN has 2,670 uncataloged executed code bytes and 43,297 bytes structured data; SET07.BIN contains 39,598 bytes alignment padding and 3,647 bytes data; denominator honestly updated to 60,108 bytes yielding 92.07% coverage.
OPEN QUESTIONS: None for carver slice.
EXACT NEXT ACTION: T2-ASM-06: Mechanically decode the 2,842 newly confirmed code bytes into real SH-2 mnemonics using `thor_sh2`, update module manifests, and regenerate lossless assembly containers.
