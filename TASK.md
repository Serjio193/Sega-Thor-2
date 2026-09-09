# Current task

# Current task

TASK: D2 — Executable Module Provenance (T2-V02a 0TH2.BIN Provenance Proof)
WHY: prove or falsify the exact runtime provenance of disc file `0TH2.BIN` on Sega Saturn.
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
CURRENT TASK: D2 — Executable Module Provenance (T2-V02a 0TH2.BIN Provenance Proof)
TASK STATUS: BOUNDED_PROOF (for 0TH2.BIN only)
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 95%
LAST VERIFIED RESULT: T2-V02a provenance experiment passed; 0TH2.BIN runtime extent 0x06004000..0x06086BFF proved identical to disc file across all 535,552 bytes in Run A and Run B; transfer mechanism DIRECT_CPU_COPY_OBSERVED; entry execution confirmed; ADR D-011 accepted as ADOPT_PARTIAL (Daytona provenance methodology)
FILES CHANGED: workstreams/T2-V02a-0th2-provenance/README.md, workstreams/T2-V02a-0th2-provenance/provenance_evidence.md, docs/DECISIONS.md, docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/REVERSE_ENGINEERING.md, docs/WORKLOG.md, TASK.md
TESTS RUN: git diff --check; source line limit check; unittest suite; dual provenance cold-boot comparison; byte-by-byte disc comparison; trace analysis
NEW KNOWLEDGE: Saturn BIOS loads 0TH2.BIN via Master SH-2 CPU byte copy loop at PC 0x00002368 directly from CD Block buffer into High Work RAM with zero SCU DMA; 0TH2.BIN is 100% byte-exact in RAM; FAD range 0x0000AE..0x0001B3
OPEN QUESTIONS: none for 0TH2.BIN; ready for TH2.LOW provenance (V-02b)
BLOCKERS: none
EXACT NEXT ACTION: Review V-02a evidence before authorizing V-02b TH2.LOW provenance.
