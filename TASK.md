# Current task

TASK: T2-ASM-01 — First Bounded SH-2 ASM Round-Trip & Runtime Proof
WHY: Implement the first bounded experiment of ADR D-015 (ASM_FIRST_RECOVERY); pin an open GNU Binutils SH toolchain (zero proprietary SDK); mechanically emit real SH-2 assembly mnemonics for startup block bb_06004000; assemble and link at original Saturn VMA (0x06004000); prove zero unresolved relocations; prove byte-exact extraction (12 bytes, canonical SHA-256 83795110...); verify private module splice (0TH2.BIN SHA-256 c1cc4117...); verify bounded runtime substitution in Mednafen oracle in pure interpreter mode (0-cycle timing divergence at entry/target, 27 cycles block duration, 23/23 registers match); pass 12/12 negative controls.
CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
TASK STATUS: PASS (bb_06004000: ASM_BYTE_EXACT = PASS, ASM_RUNTIME_VERIFIED = PASS; 12/12 negative controls PASS; toolchain pinned)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Pinned GNU Binutils SH cross-toolchain (binutils-sh-elf 2.40+2, exact binary SHA-256 hashes recorded); mechanically generated real SH-2 assembly (asm/generated/bb_06004000.s); linker script (asm/linker/bb_06004000.ld) with VMA assertions; provenance manifest (asm/manifests/bb_06004000.json); 12-byte raw extraction byte-exact to canonical slice; Thor decoder re-decode verified; private 0TH2.BIN splice hash bit-identical; Mednafen cold-boot runtime substitution matches ORIGINAL in cycle (305462360 entry, 305462387 target, 27 duration) and all 23 registers; 12/12 negative controls fail closed.
ACCEPTANCE CRITERIA:
- [x] select exactly one open SH-2 assembler/linker toolchain (GNU Binutils sh-elf);
- [x] pin and record executable SHA-256 hashes, options, and commands (no proprietary/leaked SDK);
- [x] mechanically emit real SH-2 assembly for bb_06004000 (real mnemonics, no raw .word opcode copying);
- [x] assemble and link at original Saturn VMA 0x06004000;
- [x] verify zero unresolved relocations and exactly 12 bytes output section;
- [x] extract raw machine code and prove byte-exact match (12 == 12, diff 0, canonical SHA-256 83795110...);
- [x] independent decode cross-check against Thor SH-2 decoder contract;
- [x] deterministic build proof (0 differing bytes across independent runs);
- [x] private module splice test (0TH2.BIN SHA-256 c1cc4117... remains exact);
- [x] bounded runtime substitution proof in clean Mednafen oracle (entry cycle 305462360, target 305462387, duration 27, 23/23 registers match);
- [x] 12/12 negative controls verified to fail closed;
- [x] evidence recorded in workstreams/T2-ASM-01/;
- [x] line limit <= 500 lines satisfied;
- [x] commit and push to origin/main verified.
EVIDENCE AVAILABLE:
- Machine-readable evidence: workstreams/T2-ASM-01/experiment_evidence.json;
- Experiment documentation: workstreams/T2-ASM-01/experiment_evidence.md;
- Workstream README: workstreams/T2-ASM-01/README.md;
- Generated assembly specimen: asm/generated/bb_06004000.s;
- Linker script: asm/linker/bb_06004000.ld;
- Provenance manifest: asm/manifests/bb_06004000.json;
- Pipeline tools: tools/asm/generate_asm_slice.py, tools/asm/assemble_roundtrip.py, tools/asm/verify_roundtrip.py, tools/asm/runtime_substitution_proof.py;
- Integration test: tests/asm/test_asm_roundtrip.py.
KNOWN UNKNOWNS:
- Scaling mechanical assembly emission to full module skeleton (0TH2.BIN) with mixed CODE/DATA/UNKNOWN sections without losing literal pools or unclassified regions.
ALLOWED SCOPE:
- Bounded SH-2 assembly emission and round-trip verification for bb_06004000, pinned GNU toolchain integration, runtime substitution proof in Mednafen, negative controls, documentation.
OUT OF SCOPE:
- Broad C++ translation (frozen per ADR D-015), native-promotion of additional blocks, execution of M-03, full module assembly generation.

## Last verified result

`T2-ASM-01_FIRST_BOUNDED_SH2_ASM_ROUNDTRIP_VERIFIED`: Toolchain binutils-sh-elf 2.40+2 pinned; real SH-2 mnemonics emitted for bb_06004000; VMA 0x06004000 linked with zero unresolved relocations; 12 bytes byte-exact (SHA-256 83795110...); private 0TH2.BIN splice matches baseline SHA-256 c1cc4117...; Mednafen cold-boot runtime substitution matches ORIGINAL (cycles 305462360 -> 305462387, duration 27, 23/23 registers bit-identical); 12/12 negative controls pass.

## Session checkpoint

CURRENT MILESTONE: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
CURRENT TASK: T2-ASM-01 — First Bounded SH-2 ASM Round-Trip & Runtime Proof
TASK STATUS: PASS (bb_06004000: ASM_BYTE_EXACT = PASS, ASM_RUNTIME_VERIFIED = PASS)
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: First SH-2 assembly round-trip proven byte-exact and runtime-verified in clean Mednafen; 20/20 CTest suites pass across MinGW and Linux WSL.
FILES CHANGED: asm/generated/bb_06004000.s, asm/linker/bb_06004000.ld, asm/manifests/bb_06004000.json, tools/asm/generate_asm_slice.py, tools/asm/assemble_roundtrip.py, tools/asm/verify_roundtrip.py, tools/asm/runtime_substitution_proof.py, tests/asm/test_asm_roundtrip.py, CMakeLists.txt, workstreams/T2-ASM-01/README.md, workstreams/T2-ASM-01/experiment_evidence.md, workstreams/T2-ASM-01/experiment_evidence.json, docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/WORKLOG.md, docs/FILE_MAP.md, TASK.md.
TESTS RUN: tests/asm/test_asm_roundtrip.py, tools/asm/verify_roundtrip.py (12/12 negative controls), tools/asm/runtime_substitution_proof.py (Mednafen dual cold-boot parity), test_d9_plan.py, test_post_d8_closure.py, 20/20 CTest suites on MinGW and Linux WSL; line limit checks; git diff --check.
NEW KNOWLEDGE: Open GNU Binutils SH toolchain (binutils-sh-elf 2.40+2) with `-isa=sh2` and `-big`/`-EB` is fully capable of byte-exact SH-2 Saturn code reproduction and relocatable symbolic reference resolution without any proprietary Sega SDK components.
OPEN QUESTIONS: Strategy for automated extraction and lossless asm representation of interleaved data tables and literal pools across the full 535,552 bytes of 0TH2.BIN.
EXACT NEXT ACTION: T2-ASM-02 — Module Assembly Skeleton & Lossless CODE/DATA/UNKNOWN Emission for 0TH2.BIN (define module skeleton, generate lossless data/code directives, assemble and verify full module round-trip).
