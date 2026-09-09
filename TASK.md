# Current task

TASK: D2 — Executable Module Provenance (T2-V02a.1 Classification Repair)
WHY: correct evidence-classification overclaim in V-02a records while preserving proven provenance facts.
CURRENT MILESTONE: D2 / V-02a
TASK STATUS: BOUNDED_PROOF (for 0TH2.BIN only)
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 95%
SLICE CONFIDENCE EVIDENCE: Two independent cold boots proved 100% byte match (SHA-256 `c1cc4117...`) between disc `0TH2.BIN` and pre-execution live RAM at `0x06004000..0x06086BFF`; CD Block FAD trace proved 262-sector read; memory trace proved transfer via BIOS Master SH-2 copy loop at PC `0x00002368` (`DIRECT_CPU_COPY_OBSERVED`); Master SH-2 executed instructions within mapped extent.
ACCEPTANCE CRITERIA:
- [x] verify canonical input hashes and static ISO file extent (`0TH2.BIN`: LBA 24, 535,552 bytes, SHA-256 `c1cc4117...`);
- [x] inspect Daytona CCE provenance methodology (`saturn-daytona-cce-re` at pinned commit `bf2ea285...`);
- [x] audit Mednafen oracle commands (`dump_mem_bin`, `mem_profile`, `dma_trace`, `cdb_trace`);
- [x] execute two independent deterministic cold boots (Run A and Run B);
- [x] dump pre-execution live RAM at candidate range `0x06004000..0x06086BFF` before first game instruction retires;
- [x] prove byte identity via SHA-256 comparison against disc file (`FULL_EXACT_MATCH`);
- [x] analyze CD Block trace and memory/DMA traces to prove transfer mechanism (`DIRECT_CPU_COPY_OBSERVED`);
- [x] confirm execution within mapped extent;
- [x] record ADR D-011 and update project governance / worklog / roadmap / file map / RE records.
EVIDENCE AVAILABLE:
- canonical revision `thor2_ntsc_patched_fe11d2fb`;
- disc BIN SHA-256 `fe11d2fb...`, CUE SHA-256 `afc0b101...`, BIOS `mpr-17933.bin` SHA-256 `96e106f7...`;
- disc file `0TH2.BIN` SHA-256 `c1cc4117...`, LBA 24, size 535,552 bytes;
- `workstreams/T2-V02a-0th2-provenance/README.md`;
- `workstreams/T2-V02a-0th2-provenance/provenance_evidence.md`;
- ADR D-011.
KNOWN UNKNOWNS:
- `TH2.LOW` runtime provenance and loader mechanism (queued under V-02b);
- full SH-2 instruction set decoder and semantics (queued under D3).
ALLOWED SCOPE:
- `0TH2.BIN` provenance proof and documentation;
- private runtime artifacts outside GitHub;
- legal-safe evidence summaries in GitHub.
OUT OF SCOPE:
- `TH2.LOW` provenance (`V-02b`);
- SH-2 decoder/recompiler implementation (`D3`);
- autonomous RE cycles (`auto_re.py`).

## Last verified result

`V02A_DIRECT_PROVENANCE_PROVEN`: disc file `0TH2.BIN` is loaded directly into High Work RAM at `0x06004000..0x06086BFF` without transformation via BIOS Master SH-2 copy loop (`PC=0x00002368`, zero SCU DMA to High Work RAM) and executed by Master SH-2. ADR D-011 accepted. D2 state advanced to `BOUNDED_PROOF for 0TH2.BIN only`.

## Session checkpoint

CURRENT MILESTONE: D2 (V-02a completed; BOUNDED_PROOF for 0TH2.BIN only)
CURRENT TASK: D2 — Executable Module Provenance (T2-V02a.1 Classification Repair)
TASK STATUS: BOUNDED_PROOF (for 0TH2.BIN only)
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 95%
LAST VERIFIED RESULT: T2-V02a.1 evidence classification repair complete; 0TH2.BIN module status recorded as EXECUTABLE_MODULE / RUNTIME_MAPPING_EXACT / FULL_EXACT_MATCH (DIRECT_PROVENANCE_PROVEN); byte classification scoped strictly to CONFIRMED_CODE / EXECUTED for dynamically observed instructions 0x06004000..0x06004008 with unexecuted remainder retaining PROBABLE_CODE / HIGH; ADR D-011 and D2 BOUNDED_PROOF for 0TH2.BIN only preserved
FILES CHANGED: docs/REVERSE_ENGINEERING.md, docs/PROJECT_STATE.md, docs/WORKLOG.md, workstreams/T2-V02a-0th2-provenance/provenance_evidence.md, TASK.md
TESTS RUN: git diff --check; source line limit check; unittest suite
NEW KNOWLEDGE: Dynamic execution proves code only for observed instructions (0x06004000..0x06004008); full-extent byte match proves mapping exactness, not whole-module code ownership; unexecuted bytes retain PROBABLE_CODE until D4
OPEN QUESTIONS: none for 0TH2.BIN; ready for TH2.LOW provenance (V-02b)
BLOCKERS: none
EXACT NEXT ACTION: Review V-02a evidence before authorizing V-02b TH2.LOW provenance.
