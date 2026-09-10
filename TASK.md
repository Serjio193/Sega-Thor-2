# Current task

TASK: T2-ASM-03 — TH2.LOW Lossless ASM Container & Shared ASM Recovery Infrastructure
WHY: Implement the third experiment of ADR D-015 (ASM_FIRST_RECOVERY); harden shared ASM infrastructure by establishing formal module manifest schema (asm/schema/module_manifest.schema.json) with exhaustive range partitioning (CONFIRMED_CODE, UNKNOWN); eliminate Python SH-2 decoders in favor of C++ verify_sh2_rebuilt linked against thor_sh2; establish private lossless assembly container for TH2.LOW (149,504 bytes, VMA 0x002DA000) with proven executed instruction (0x002E9910, 0x2FE6 MOV.L R14, @-R15) preserved safely as RAW_CODE_PENDING_DECODE; reassemble byte-exact (149,504 / 149,504 bytes, SHA-256 78139689...); prove dual-build determinism (0 diffs); verify sector-by-sector private disc splice at LBA 52123 (clean disc SHA-256 fe11d2fb...); repair occurrence-aware runtime verification in clean interpreter-only Mednafen oracle, proving cycle 387459915 execution parity at 0x002E9910 in TH2.LOW with zero cycle or register divergence across 6 checkpoints; pass all negative controls and CTests.
CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
TASK STATUS: PASS (TH2.LOW: ASM_BYTE_EXACT = PASS, ASM_RUNTIME_VERIFIED = PASS; 10/10 TH2.LOW negative controls PASS; 20/20 0TH2 negative controls PASS; 9/9 schema negative controls PASS; zero commercial payload in git)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Module manifest schema asm/schema/module_manifest.schema.json established; asm/manifests/0TH2.BIN.json upgraded to exhaustive partition; asm/manifests/TH2.LOW.json created with 3-range partition (0..63760 UNKNOWN, 63760..63762 CONFIRMED_CODE / RAW_CODE_PENDING_DECODE, 63762..149504 UNKNOWN); linker script asm/linker/TH2_LOW.ld with VMA and size assertions; C++ verification tool tools/asm/verify_sh2_rebuilt.cpp linked against thor_sh2; private assembly container .private/asm/TH2_LOW/TH2_LOW.s (9,365 lines) generated; 149,504 bytes extracted byte-exact to original TH2.LOW (SHA-256 78139689...); dual independent builds bit-identical; sector-by-sector retail disc splice at LBA 52123 matches canonical disc SHA-256 fe11d2fb...; occurrence-aware runtime verification in Mednafen interpreter mode proves cycle 387459915 execution parity at 0x002E9910 in TH2.LOW with 0-cycle divergence and 23/23 matching registers across 6 checkpoints; 23/23 CTests pass on Windows and Linux WSL.
ACCEPTANCE CRITERIA:
- [x] harden shared ASM recovery infrastructure (manifest schema, C++ verify_sh2_rebuilt, env vars);
- [x] eliminate ad-hoc Python SH-2 decoders in verification scripts in favor of thor::sh2::decode_sh2;
- [x] create canonical manifest-driven CODE/DATA/UNKNOWN representation (asm/schema/module_manifest.schema.json);
- [x] create private lossless assembly container for TH2.LOW (.private/asm/TH2_LOW/TH2_LOW.s);
- [x] reassemble entire TH2.LOW module byte-exact (149,504 / 149,504 bytes, SHA-256 78139689...);
- [x] prove dual-build determinism (0 diffs);
- [x] verify sector-by-sector private disc splice at LBA 52123 (SHA-256 fe11d2fb...);
- [x] repair occurrence-aware runtime verification (explicit occurrence index, PR, and caller tracking);
- [x] prove real TH2.LOW execution occurrence in interpreter Mednafen (cycle 387459915 at 0x002E9910);
- [x] zero cycle or register divergence across 6 checkpoints;
- [x] 10/10 TH2.LOW negative controls, 20/20 0TH2 negative controls, 9/9 schema negative controls pass fail-closed;
- [x] git publication hygiene verified (zero commercial bytes tracked);
- [x] evidence recorded in workstreams/T2-ASM-03/;
- [x] line limit <= 500 lines satisfied across all human-maintained files;
- [x] 23/23 CTest suites pass on Windows MinGW and Linux WSL.
EVIDENCE AVAILABLE:
- Machine-readable evidence: workstreams/T2-ASM-03/experiment_evidence.json;
- Experiment documentation: workstreams/T2-ASM-03/experiment_evidence.md;
- Workstream README: workstreams/T2-ASM-03/README.md;
- Manifest schema: asm/schema/module_manifest.schema.json;
- Module manifests: asm/manifests/0TH2.BIN.json, asm/manifests/TH2.LOW.json;
- Linker scripts: asm/linker/0TH2.ld, asm/linker/TH2_LOW.ld;
- C++ tool: tools/asm/verify_sh2_rebuilt.cpp;
- Pipeline scripts: tools/asm/generate_full_module_asm.py, tools/asm/build_full_module.py, tools/asm/verify_full_module.py, tools/asm/runtime_substitution_proof.py;
- Integration tests: tests/asm/test_manifest_schema.py, tests/asm/test_full_module_asm.py, tests/asm/test_th2_low_asm.py.
KNOWN UNKNOWNS:
- Code/data boundaries within TH2.LOW beyond the proven entry point 0x002E9910;
- Secondary Saturn binaries and sound drivers (SLAVE SH-2, M68K sound program, graphical overlays).
ALLOWED SCOPE:
- Full module assembly container and round-trip verification for TH2.LOW, manifest schema, C++ verification tool, occurrence-aware runtime verification in Mednafen, negative controls, documentation.
OUT OF SCOPE:
- Broad C++ translation (frozen per ADR D-015), native-promotion of additional blocks, execution of M-03, full disc reassembly.

## Last verified result

`T2-ASM-03_TH2_LOW_ASM_CONTAINER_VERIFIED`: Full TH2.LOW lossless assembly container (.private/asm/TH2_LOW/TH2_LOW.s, 149,504 bytes) assembled with pinned GNU binutils-sh-elf 2.40+2 and linked at VMA 0x002DA000 with zero unresolved relocations; proven code at 0x002E9910 preserved losslessly as RAW_CODE_PENDING_DECODE; 149,504 bytes byte-exact (SHA-256 78139689...); dual independent builds bit-identical; sector-by-sector private disc splice at LBA 52123 matches canonical retail disc SHA-256 fe11d2fb...; Mednafen cold-boot runtime parity verified in interpreter mode across 6 occurrence-aware checkpoints (including TH2.LOW execution at cycle 387459915) with 0-cycle timing divergence and 23/23 matching registers; 10/10 TH2.LOW, 20/20 0TH2, and 9/9 schema negative controls pass fail-closed; 23/23 CTest suites pass on Windows and Linux WSL.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
CURRENT TASK: T2-ASM-03 — TH2.LOW Lossless ASM Container & Shared ASM Recovery Infrastructure
TASK STATUS: PASS (TH2.LOW: ASM_BYTE_EXACT = PASS, ASM_RUNTIME_VERIFIED = PASS)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: Full TH2.LOW assembly round-trip proven byte-exact and runtime-verified in clean Mednafen across 6 occurrence-aware checkpoints; 23/23 CTest suites pass across MinGW and Linux WSL.
FILES CHANGED: asm/schema/module_manifest.schema.json, asm/manifests/0TH2.BIN.json, asm/manifests/TH2.LOW.json, asm/linker/TH2_LOW.ld, tools/asm/verify_sh2_rebuilt.cpp, tools/asm/generate_full_module_asm.py, tools/asm/build_full_module.py, tools/asm/verify_full_module.py, tools/asm/runtime_substitution_proof.py, tests/asm/test_manifest_schema.py, tests/asm/test_th2_low_asm.py, CMakeLists.txt, workstreams/T2-ASM-03/README.md, workstreams/T2-ASM-03/experiment_evidence.md, workstreams/T2-ASM-03/experiment_evidence.json, docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/WORKLOG.md, docs/FILE_MAP.md, TASK.md.
TESTS RUN: tests/asm/test_manifest_schema.py (9 negative controls), tests/asm/test_full_module_asm.py (20 negative controls), tests/asm/test_th2_low_asm.py (10 negative controls), tools/asm/runtime_substitution_proof.py (Mednafen dual cold-boot 6-checkpoint occurrence-aware parity), 23/23 CTest suites on MinGW and Linux WSL; line limit checks; git diff --check.
NEW KNOWLEDGE: TH2.LOW is loaded to 0x002DA000 by 0x0600A0F8 called from 0x06004286 (occurrence 2) and entered at 0x002E9910 at cycle 387459915 (PR=0x060042E4). The entire module can be represented losslessly as a reassemblable SH-2 assembly container with byte-exact parity and verified runtime parity.
OPEN QUESTIONS: Classifying additional basic blocks within TH2.LOW and generating lossless assembly containers for remaining disc binaries (graphics/data overlays, sound drivers).
EXACT NEXT ACTION: T2-ASM-04 — Secondary Module Skeletons & Systematic Module Enumeration (extend lossless assembly containers to remaining Saturn disc binaries).
