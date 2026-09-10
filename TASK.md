# Current task

TASK: T2-ASM-02 — Full 0TH2.BIN Lossless Assembly Container & Byte-Exact Module Round-Trip
WHY: Implement the second experiment of ADR D-015 (ASM_FIRST_RECOVERY); repair ASM-01 tooling provenance debt by creating generic C++ Thor-decoder-backed IR exporter (export_sh2_asm_ir); mechanically generate private lossless assembly container for entire primary Saturn binary 0TH2.BIN (535,552 bytes, VMA 0x06004000) with all proven code (bb_06004000 and bb_06004280, 22 bytes, 11 insns) emitted as real SH-2 mnemonics, all labels resolved at real in-module offsets without .equ hacks, and RAW_UNKNOWN emitted losslessly via .byte directives; link at VMA 0x06004000 with zero unresolved relocations; prove byte-exact extraction (535,552 / 535,552 bytes, canonical SHA-256 c1cc4117...); prove dual-build determinism (0 diffs); verify sector-by-sector private disc splice (clean disc SHA-256 fe11d2fb...); verify bounded Mednafen interpreter runtime parity across 5 checkpoints (0x06004000, 0x06004012, 0x06004280, 0x0600A0F8, 0x002E9910) with zero cycle or register divergence; pass 28/28 negative controls.
CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
TASK STATUS: PASS (0TH2.BIN: ASM_BYTE_EXACT = PASS, ASM_RUNTIME_VERIFIED = PASS; 28/28 negative controls PASS; zero commercial payload in git)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Generic C++ tool export_sh2_asm_ir.cpp linked against thor_sh2; machine-readable Assembly IR JSON exported; private assembly container .private/asm/0TH2/0TH2.s (33,521 lines) generated; linker script asm/linker/0TH2.ld with size/VMA/label assertions; public manifest asm/manifests/0TH2.BIN.json (zero commercial bytes); 535,552 bytes extracted byte-exact to canonical 0TH2.BIN (SHA-256 c1cc4117...); dual independent builds bit-identical; sector-by-sector retail disc splice matches canonical disc SHA-256 fe11d2fb...; pure interpreter Mednafen cold-boot runtime parity verified across all 5 checkpoints with 0-cycle timing divergence and 23/23 matching registers; 28/28 negative controls pass; 21/21 CTest suites pass on Windows and Linux WSL.
ACCEPTANCE CRITERIA:
- [x] repair ASM-01 tooling provenance debt (generic C++ export_sh2_asm_ir linking thor_sh2);
- [x] generate machine-readable Assembly IR JSON (assembly_ir.json);
- [x] mechanically generate private lossless assembly container (.private/asm/0TH2/0TH2.s);
- [x] emit all currently confirmed code as real SH-2 mnemonics (bb_06004000 and bb_06004280, 22 bytes, 11 insns);
- [x] emit DATA/UNKNOWN losslessly via .byte directives without guessing;
- [x] resolve labels at real in-module offsets (loc_06004012, lit_06004064, lit_0600435C, lit_06004360, lit_06004364) with zero .equ hacks;
- [x] link complete module at original VMA 0x06004000 with zero unresolved relocations;
- [x] reproduce all 535,552 original bytes exactly (SHA-256 c1cc4117...);
- [x] prove dual-build determinism (0 differing bytes between independent runs);
- [x] verify sector-by-sector private disc splice (SHA-256 fe11d2fb... matches clean disc);
- [x] prove interpreter-only Mednafen runtime parity across 5 checkpoints (06004000, 06004012, 06004280, 0600A0F8, 002E9910) with 0 cycle / 0 register divergence;
- [x] 28/28 negative controls verified to fail closed;
- [x] git publication hygiene verified (zero commercial bytes tracked);
- [x] evidence recorded in workstreams/T2-ASM-02/;
- [x] line limit <= 500 lines satisfied across all human-maintained files;
- [x] 21/21 CTest suites pass on Windows and Linux WSL.
EVIDENCE AVAILABLE:
- Machine-readable evidence: workstreams/T2-ASM-02/experiment_evidence.json;
- Experiment documentation: workstreams/T2-ASM-02/experiment_evidence.md;
- Workstream README: workstreams/T2-ASM-02/README.md;
- Linker script: asm/linker/0TH2.ld;
- Provenance manifest: asm/manifests/0TH2.BIN.json;
- Pipeline tools: tools/asm/export_sh2_asm_ir.cpp, tools/asm/generate_full_module_asm.py, tools/asm/build_full_module.py, tools/asm/verify_full_module.py, tools/asm/runtime_substitution_proof.py;
- Integration test: tests/asm/test_full_module_asm.py.
KNOWN UNKNOWNS:
- Boundaries and symbol maps for secondary Saturn binaries and sound drivers (SLAVE SH-2, M68K sound program, graphic overlays).
ALLOWED SCOPE:
- Full module assembly container and round-trip verification for 0TH2.BIN, generic C++ Assembly IR exporter, runtime substitution proof in Mednafen across 5 checkpoints, negative controls, documentation.
OUT OF SCOPE:
- Broad C++ translation (frozen per ADR D-015), native-promotion of additional blocks, execution of M-03, full disc reassembly.

## Last verified result

`T2-ASM-02_FULL_MODULE_0TH2_ASM_ROUNDTRIP_VERIFIED`: Full 0TH2.BIN lossless assembly container (.private/asm/0TH2/0TH2.s, 535,552 bytes) assembled with pinned GNU binutils-sh-elf 2.40+2 and linked at VMA 0x06004000 with zero unresolved relocations; all proven code emitted as real SH-2 mnemonics; real in-module label resolution (zero .equ hacks); 535,552 bytes byte-exact (SHA-256 c1cc4117...); dual independent builds bit-identical; sector-by-sector private disc splice matches baseline SHA-256 fe11d2fb...; Mednafen cold-boot runtime parity verified in interpreter mode across 5 checkpoints (06004000, 06004012, 06004280, 0600A0F8, 002E9910) with 0-cycle timing divergence and 23/23 matching registers; 28/28 negative controls pass; 21/21 CTest suites pass on Windows and Linux WSL.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
CURRENT TASK: T2-ASM-02 — Full 0TH2.BIN Lossless Assembly Container & Byte-Exact Module Round-Trip
TASK STATUS: PASS (0TH2.BIN: ASM_BYTE_EXACT = PASS, ASM_RUNTIME_VERIFIED = PASS)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: Full 0TH2.BIN assembly round-trip proven byte-exact and runtime-verified in clean Mednafen across 5 architectural checkpoints; 21/21 CTest suites pass across MinGW and Linux WSL.
FILES CHANGED: asm/linker/0TH2.ld, asm/manifests/0TH2.BIN.json, tools/asm/export_sh2_asm_ir.cpp, tools/asm/generate_full_module_asm.py, tools/asm/build_full_module.py, tools/asm/verify_full_module.py, tools/asm/runtime_substitution_proof.py, tests/asm/test_full_module_asm.py, CMakeLists.txt, .gitignore, workstreams/T2-ASM-02/README.md, workstreams/T2-ASM-02/experiment_evidence.md, workstreams/T2-ASM-02/experiment_evidence.json, docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/WORKLOG.md, docs/FILE_MAP.md, TASK.md.
TESTS RUN: tests/asm/test_full_module_asm.py, tools/asm/verify_full_module.py (28/28 negative controls), tools/asm/runtime_substitution_proof.py (Mednafen dual cold-boot 5-checkpoint parity), 21/21 CTest suites on MinGW and Linux WSL; line limit checks; git diff --check.
NEW KNOWLEDGE: The entire 535,552-byte primary retail module (0TH2.BIN) can be represented losslessly as a reassemblable SH-2 assembly container with real mnemonics for confirmed code, exact symbolic label resolution across the single .text section (eliminating all .equ workarounds), zero relocations left in the final binary, and 100% bit-exact parity across sectors and cold-boot execution.
OPEN QUESTIONS: Scaling the lossless assembly container methodology to auxiliary Saturn disc files (slave SH-2 code, sound DSP code) and systematically classifying internal basic blocks into confirmed code.
EXACT NEXT ACTION: T2-ASM-03 — Progressive Multi-Module Assembly Skeleton & Systematic Function Disassembly Pipeline (extend assembly containers to remaining disc binaries, establish systematic boundary & CFG recovery under ASM-first gate).
