# Current task

TASK: D2 / V-02b — TH2.LOW Executable Provenance
WHY: prove or falsify the runtime provenance hypothesis for TH2.LOW (disc extent -> 0x002DA000 destination -> byte match -> execution).
CURRENT MILESTONE: D2 / V-02b
TASK STATUS: PASS (D2 at BOUNDED_PROOF for 0TH2.BIN and TH2.LOW)
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 95%
SLICE CONFIDENCE EVIDENCE: Two independent cold boots proved 100% byte match (SHA-256 `78139689...`) between disc `TH2.LOW` and live RAM at `0x002DA000..0x002FE7FF`; CD Block FAD trace proved 73-sector read (`0x00CC31..0x00CC79`); memory trace proved transfer via Master SH-2 copy loop at PC `0x0607DF08` (`DIRECT_CPU_COPY_OBSERVED`); Master SH-2 executed instructions within mapped extent at `0x002E9910..0x002E9914`.
ACCEPTANCE CRITERIA:
- [x] verify canonical input hashes and static ISO file extent (`TH2.LOW`: LBA 52123, 73 sectors, 149,504 bytes, SHA-256 `78139689...`);
- [x] verify call-site arguments in `0TH2.BIN` (`0x06004280..0x06004286`: `R4 -> "TH2.LOW"`, `R5 = 0x002DA000`, `R3 = 0x0600A0F8`);
- [x] execute two independent deterministic cold boots (Run A and Run B);
- [x] dump pre-load and post-load live RAM at candidate range `0x002DA000..0x002FE7FF`;
- [x] prove byte identity via SHA-256 comparison against disc file (`FULL_EXACT_MATCH`);
- [x] analyze CD Block trace and memory/DMA traces to prove transfer mechanism (`DIRECT_CPU_COPY_OBSERVED`);
- [x] confirm execution within mapped extent (`0x002E9910..0x002E9914`);
- [x] separate module-level status and byte-level classification (`CONFIRMED_CODE / EXECUTED` strictly for observed instructions);
- [x] update project governance / worklog / roadmap / file map / RE records.
EVIDENCE AVAILABLE:
- canonical revision `thor2_ntsc_patched_fe11d2fb`;
- disc BIN SHA-256 `fe11d2fb...`, CUE SHA-256 `afc0b101...`, BIOS `mpr-17933.bin` SHA-256 `96e106f7...`;
- disc file `TH2.LOW` SHA-256 `78139689...`, LBA 52123, size 149,504 bytes;
- `workstreams/T2-V02b-th2-low-provenance/README.md`;
- `workstreams/T2-V02b-th2-low-provenance/provenance_evidence.md`.
KNOWN UNKNOWNS:
- full SH-2 instruction set decoder and semantics (queued under D3);
- complete code/data/unknown ownership across modules (queued under D4).
ALLOWED SCOPE:
- `TH2.LOW` provenance proof and documentation;
- private runtime artifacts outside GitHub;
- legal-safe evidence summaries in GitHub.
OUT OF SCOPE:
- SH-2 decoder/recompiler implementation (`D3`);
- code/data boundary classification (`D4`);
- autonomous RE cycles (`auto_re.py`).

## Last verified result

`V02B_DIRECT_PROVENANCE_PROVEN`: disc file `TH2.LOW` is loaded directly into Low Work RAM at `0x002DA000..0x002FE7FF` without transformation via Master SH-2 CPU copy loop (`PC=0x0607DF08`, zero SCU DMA to Low Work RAM) and executed by Master SH-2 at `0x002E9910..0x002E9914`. D2 state advanced to `BOUNDED_PROOF for 0TH2.BIN and TH2.LOW`.

## Session checkpoint

CURRENT MILESTONE: D2 (V-02a and V-02b completed; BOUNDED_PROOF for 0TH2.BIN and TH2.LOW)
CURRENT TASK: D2 / V-02b — TH2.LOW Executable Provenance
TASK STATUS: PASS (D2 at BOUNDED_PROOF for 0TH2.BIN and TH2.LOW)
MILESTONE UNDERSTANDING CONFIDENCE: 95%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 95%
LAST VERIFIED RESULT: V-02b executable provenance proof complete; TH2.LOW module status recorded as EXECUTABLE_MODULE / RUNTIME_MAPPING_EXACT / FULL_EXACT_MATCH (DIRECT_PROVENANCE_PROVEN); byte classification scoped strictly to CONFIRMED_CODE / EXECUTED for dynamically observed instructions 0x002E9910..0x002E9914 with unexecuted remainder retaining PROBABLE_CODE / HIGH; D2 BOUNDED_PROOF for 0TH2.BIN and TH2.LOW
FILES CHANGED: docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/REVERSE_ENGINEERING.md, docs/WORKLOG.md, workstreams/T2-V02b-th2-low-provenance/README.md, workstreams/T2-V02b-th2-low-provenance/provenance_evidence.md, TASK.md
TESTS RUN: git diff --check; source line limit check; unittest suite
NEW KNOWLEDGE: TH2.LOW (149,504 bytes, LBA 52123..52195, FAD 0x00CC31..0x00CC79) loaded directly to 0x002DA000..0x002FE7FF via Master SH-2 CPU loop (PC=0x0607DF08), exact byte match across 149,504 bytes, execution confirmed at 0x002E9910
OPEN QUESTIONS: none for module provenance; ready for D3 exact SH-2 decode / L0 semantics
BLOCKERS: none
EXACT NEXT ACTION: Review V-02b evidence before starting D3 exact SH-2 decode / L0 semantics.
