# Current task

TASK: T2-ASM-04 — Disc Executable Inventory & Secondary Module ASM Skeletons
WHY: Implement the fourth experiment of ADR D-015 (ASM_FIRST_RECOVERY) and implement ADR D-016 (Proof-Gated Discovery Accelerators); establish a complete executable census across all 33 ISO9660 disc files; identify executable modules (0TH2.BIN, TH2.LOW, SET07.BIN), sound programs (BGM.BIN for MC68EC000), and DSP microcode (MAP.BIN); prove multi-processor execution lifetimes (single-core Master SH-2 boot/gameplay, dormant Slave SH-2, MC68EC000 sound driver); recover overlay call site at 0x002E3C5C in TH2.LOW loading SET07.BIN; generate private lossless assembly container for SET07.BIN (98,304 bytes, VMA 0x060D8000); reassemble byte-exact with pinned GNU binutils-sh-elf 2.40+2 (98,304 / 98,304 bytes, SHA-256 bb607222...); prove dual-build determinism; verify sector-by-sector private disc splice at LBA 52040 against clean retail disc fe11d2fb...; pass 9/9 SET07 negative controls; expand thor_sh2 decoder for MOV_L_WRITE_PREDEC (0x2nm6) and RTS (0x000B); promote TH2.LOW entry 0x002E9910 to MNEMONIC_PROVEN; establish method catalog, autoplan, and live scorecard.
CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015, ADR D-016)
TASK STATUS: PASS (SET07.BIN: ASM_BYTE_EXACT = PASS; TH2.LOW: PROVEN_CODE_EMITTED = PASS; 9/9 SET07 negative controls PASS; 10/10 TH2.LOW negative controls PASS; 24/24 CTests pass across MinGW and Linux WSL)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Complete 33-disc-file census documented in workstreams/T2-ASM-04/; multi-processor life cycle proven dynamically in Mednafen (Master SH-2 active, Slave SH-2 dormant at cycle 554989864, MC68EC000 sound driver at 0x1000); SET07.BIN manifest asm/manifests/SET07.BIN.json and linker script asm/linker/SET07.ld created; private container .private/asm/SET07/SET07.s (6,175 lines) reassembled byte-exact (SHA-256 bb607222...); dual independent builds bit-identical; sector-by-sector retail disc splice at LBA 52040 matches clean disc SHA-256 fe11d2fb...; 9/9 SET07 negative controls pass fail-closed; thor_sh2 decoder expanded with MOV_L_WRITE_PREDEC and RTS; TH2.LOW entry 0x002E9910 promoted to MNEMONIC_PROVEN; 24/24 CTests pass on Windows and Linux WSL.
ACCEPTANCE CRITERIA:
- [x] complete disc inventory of all 33 files, code/data/overlay/sound classification;
- [x] prove multi-processor execution lifetime (Master SH-2, Slave SH-2, M68K, SCU DSP);
- [x] establish lossless assembly container for SET07.BIN (.private/asm/SET07/SET07.s);
- [x] reassemble entire SET07.BIN module byte-exact (98,304 / 98,304 bytes, SHA-256 bb607222...);
- [x] prove dual-build determinism (0 diffs);
- [x] verify sector-by-sector private disc splice at LBA 52040 (SHA-256 fe11d2fb...);
- [x] 9/9 SET07 negative controls pass fail-closed;
- [x] expand thor_sh2 decoder for MOV_L_WRITE_PREDEC (0x2nm6) and RTS (0x000B);
- [x] promote TH2.LOW entry 0x002E9910 to MNEMONIC_PROVEN in asm/manifests/TH2.LOW.json;
- [x] establish method catalog, autoplan priority engine, and live scorecard;
- [x] git publication hygiene verified (zero commercial bytes tracked);
- [x] evidence recorded in workstreams/T2-ASM-04/;
- [x] line limit <= 500 lines satisfied across all human-maintained files;
- [x] 24/24 CTest suites pass on Windows MinGW and Linux WSL.
EVIDENCE AVAILABLE:
- Machine-readable evidence: workstreams/T2-ASM-04/experiment_evidence.json;
- Experiment documentation: workstreams/T2-ASM-04/experiment_evidence.md;
- Workstream README: workstreams/T2-ASM-04/README.md;
- Manifest schema & manifests: asm/manifests/0TH2.BIN.json, asm/manifests/TH2.LOW.json, asm/manifests/SET07.BIN.json, asm/manifests/BGM.BIN.json;
- Linker scripts: asm/linker/0TH2.ld, asm/linker/TH2_LOW.ld, asm/linker/SET07.ld;
- C++ tool: tools/asm/verify_sh2_rebuilt.cpp, tools/asm/export_sh2_asm_ir.cpp;
- Method catalog & Autoplan: docs/ASM_RECOVERY_METHOD_CATALOG.md, docs/ASM_RECOVERY_AUTOPLAN.md, workstreams/ASM_RECOVERY_SCORECARD.json.
KNOWN UNKNOWNS:
- Exact internal basic block graph and literal pools of 0TH2.BIN, TH2.LOW, and SET07.BIN beyond the proven initial entry blocks.
ALLOWED SCOPE:
- Full disc census, multi-processor lifetimes, lossless container and round-trip verification for SET07.BIN, sound driver manifest for BGM.BIN, decoder expansion, negative controls, documentation.
OUT OF SCOPE:
- Broad C++ translation (frozen per ADR D-015), native promotion of additional blocks, execution of M-03.

## Last verified result

`T2-ASM-04_DISC_INVENTORY_AND_SET07_ASM_VERIFIED`: Full 33-disc-file inventory established; Master SH-2 single-core boot/engine, dormant Slave SH-2, MC68EC000 sound driver at 0x1000 proven dynamically; overlay load call site at 0x002E3C5C in TH2.LOW discovered; lossless assembly container for SET07.BIN (.private/asm/SET07/SET07.s, 98,304 bytes) reassembled byte-exact (SHA-256 bb607222...) with pinned GNU binutils-sh-elf 2.40+2 and linked at VMA 0x060D8000; dual-build determinism verified; sector-by-sector private disc splice at LBA 52040 matches canonical retail disc SHA-256 fe11d2fb...; 9/9 SET07 negative controls pass fail-closed; thor_sh2 decoder expanded with MOV_L_WRITE_PREDEC and RTS; TH2.LOW entry 0x002E9910 promoted to MNEMONIC_PROVEN; 24/24 CTests pass across MinGW and Linux WSL.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015, ADR D-016)
CURRENT TASK: T2-ASM-04 — Disc Executable Inventory & Secondary Module ASM Skeletons
TASK STATUS: PASS (SET07.BIN: ASM_BYTE_EXACT = PASS; TH2.LOW: PROVEN_CODE_EMITTED = PASS)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: Full disc inventory established; SET07.BIN assembly round-trip proven byte-exact and sector-spliced; 24/24 CTest suites pass across MinGW and Linux WSL.
FILES CHANGED: asm/manifests/SET07.BIN.json, asm/manifests/BGM.BIN.json, asm/manifests/TH2.LOW.json, asm/linker/SET07.ld, include/thor/sh2/sh2_types.hpp, src/sh2/sh2_decoder.cpp, src/sh2/sh2_executor.cpp, tests/sh2/test_sh2_decoder.cpp, tests/sh2/test_sh2_l0_semantics.cpp, tests/asm/test_manifest_schema.py, tests/asm/test_set07_asm.py, tools/asm/generate_full_module_asm.py, tools/asm/build_full_module.py, tools/asm/verify_full_module.py, tools/asm/export_sh2_asm_ir.cpp, CMakeLists.txt, docs/DECISIONS.md, docs/ASM_RECOVERY_METHOD_CATALOG.md, docs/ASM_RECOVERY_AUTOPLAN.md, docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/WORKLOG.md, workstreams/ASM_RECOVERY_SCORECARD.json, workstreams/T2-ASM-04/README.md, workstreams/T2-ASM-04/experiment_evidence.md, workstreams/T2-ASM-04/experiment_evidence.json, TASK.md.
TESTS RUN: tests/sh2/test_sh2_decoder.cpp, tests/sh2/test_sh2_l0_semantics.cpp, tests/asm/test_manifest_schema.py, tests/asm/test_full_module_asm.py, tests/asm/test_th2_low_asm.py, tests/asm/test_set07_asm.py, 24/24 CTests on Windows MinGW and Linux WSL; line limit checks; git diff --check.
NEW KNOWLEDGE: The disc contains 3 SH-2 modules (0TH2.BIN, TH2.LOW, SET07.BIN), 1 M68K sound driver container (BGM.BIN), and 1 SCU DSP container (MAP.BIN). The Saturn game runs entirely on Master SH-2 during boot and core game loop with Slave SH-2 dormant. SET07.BIN is loaded to 0x060D8000 by 0x0600A0F8 called from 0x002E3C5C in TH2.LOW.
OPEN QUESTIONS: Harvesting all retired Master SH-2 PCs across attract mode, menus, and gameplay to drive recursive CFG recovery and mnemonic emission toward ASM_90_GATE.
EXACT NEXT ACTION: T2-ASM-05 — Bulk Retired PC Harvesting & Recursive CFG Recovery toward ASM_90_GATE.
