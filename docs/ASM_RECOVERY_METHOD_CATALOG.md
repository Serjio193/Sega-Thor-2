# ASM Recovery Method Catalog

This catalog documents all formal recovery methods, pipelines, and discovery accelerators used in the *The Story of Thor 2 / The Legend of Oasis* ASM-first native recovery project under ADR D-015 and ADR D-016.

---

## 1. Core Recovery Methods (M-01 .. M-10)

### M-01: Disc Layout & Hash Census
- **Objective:** Establish an immutable baseline of every file on the retail Saturn disc.
- **Process:** Parse ISO9660 filesystem, compute SHA-256 and MD5 for all 33 disc files, determine LBAs and exact byte lengths.
- **Status:** `OPERATIONAL` (verified across European retail image `fe11d2fb...`).

### M-02: Runtime Load Path & Overlay Mapping
- **Objective:** Track dynamic loading of executable modules and overlays into Saturn work RAM.
- **Process:** Monitor CD block transfers, DMA transfers, and CPU copy loops in Mednafen oracle; trace disc source LBA, target VMA, load size, and entry point PC.
- **Status:** `OPERATIONAL` (0TH2.BIN at 0x06004000, TH2.LOW at 0x002DA000 proven).

### M-03: SaturnAutoRE Recompilation Harvester
- **Objective:** Systematic mechanical C++ decompilation of verified SH-2 basic blocks.
- **Status:** `DEFERRED_BY_ASM_FIRST_ARCHITECTURE` (per ADR D-015; unblocked only after `FULL_ASM_GAME_GATE`).

### M-04: Static Direct Recursive CFG Descent
- **Objective:** Discover reachable code blocks by following direct unconditional and conditional branches (`BRA`, `BSR`, `BF`, `BT`, `JMP`, `JSR`).
- **Process:** Starting from proven entry points, decode instructions sequentially, add branch targets to discovery queue, stop at unconditional exits (`RTS`, `BRA`, `JMP`) or unverified indirect branches.
- **Trust Level:** Promotes to `PROBABLE_CODE` when statically traversed; promotes to `CONFIRMED_CODE` when bounded by verified entry or dynamic trace.

### M-05: Dynamic Execution PC Harvester
- **Objective:** Collect actual executed Program Counter addresses across diverse runtime sessions.
- **Process:** Instrument Mednafen debug oracle to log unique retired PCs for Master SH-2, Slave SH-2, and MC68EC000 during cold boot, title sequence, attract demo, menus, and gameplay.
- **Trust Level:** Directly establishes `EXECUTED` / `CONFIRMED_CODE`.

### M-06: Literal Pool & Pointer Table Discriminator
- **Objective:** Distinguish literal pools, pointer tables, and embedded data from executable instructions.
- **Process:** Analyze PC-relative load instructions (`mov.w @(disp,PC), Rn`, `mov.l @(disp,PC), Rn`); record referenced data ranges; flag aligned address tables following function tails.
- **Trust Level:** `CONFIRMED_DATA` when referenced exclusively by PC-relative loads.

### M-07: Static Differential Compiler Fingerprinting
- **Objective:** Identify compiler idioms, optimization flags, and calling conventions used by Ancient/Sega.
- **Process:** Match register usage patterns (R14 frame pointer, R15 stack pointer, PR link register, caller-saved R0-R7, callee-saved R8-R14), prologue/epilogue templates, and synthetic instruction sequences.

### M-08: Occurrence-Aware Mednafen Differential Verification
- **Objective:** Verify behavioral parity between original Saturn disc and reassembled modules.
- **Process:** Substitute rebuilt modules into disc sectors; run identical inputs in clean Mednafen interpreter mode; verify register states, memory checkpoints, and cycle timing at specific execution occurrences.
- **Status:** `OPERATIONAL` (used in ASM-01, ASM-02, ASM-03).

### M-09: Shadow Execution with Cycle-Accurate Checkpoints
- **Objective:** Differential verification of recompiled or native routines running in parallel with original emulation.
- **Status:** `OPERATIONAL` for proof specimens `bb_06004000` and `bb_06004280`.

### M-10: Native Subsystem Promotion & Fallback
- **Objective:** Progressive migration of verified ASM modules to standalone native C++20 subsystems with fail-closed fallback.
- **Status:** `DEFERRED` until `FULL_ASM_GAME_GATE`.

---

## 2. ASM-First Pipeline Methods (ASM-01 .. ASM-04)

### ASM-01: Bounded ASM Round-Trip & Toolchain Pinning
- **Scope:** Single proven basic block (`bb_06004000`, 12 bytes).
- **Result:** Pinned GNU `binutils-sh-elf 2.40+2`; proved byte-exact reassembly and runtime parity.

### ASM-02: Full Lossless Assembly Container
- **Scope:** Complete main executable module (`0TH2.BIN`, 535,552 bytes, VMA `0x06004000`).
- **Result:** Lossless `.s` assembly container emitting confirmed code as SH-2 mnemonics and unknown regions as `.byte`; byte-exact round-trip; clean Mednafen cold-boot parity.

### ASM-03: Shared Manifest-Driven ASM Infrastructure & Occurrence Tracking
- **Scope:** Secondary loaded module (`TH2.LOW`, 149,504 bytes, VMA `0x002DA000`).
- **Result:** Formal schema `module_manifest.schema.json`; C++ `verify_sh2_rebuilt` tool; occurrence-aware checkpointing at cycle 387,459,915; byte-exact round-trip.

### ASM-04: Complete Saturn Executable Inventory & Secondary Modules
- **Scope:** All 33 disc files, Master SH-2 overlays, Slave SH-2 tasks, and MC68EC000 sound programs.
- **Result:** Exhaustive identification of all executable modules and generation of lossless reassembly skeletons.

---

## 3. Discovery Accelerator Tracks (Tracks A .. R)

Under ADR D-016, the following accelerator tracks generate candidates under the strict rule: **DISCOVERY $\ne$ PROOF**.

| Track | Name | Description | Output Hypothesis | Proof Gate |
|---|---|---|---|---|
| **Track A** | Headless Ghidra Analysis | Automated disassembly & decompilation parsing | Candidate function boundaries | Dynamic trace or CFG closure |
| **Track B** | Thor In-Game Debug Menu | Triggering debug menu (`0x06009CC4`), sound test, map warps | Traversed code paths | Mednafen retired PC log |
| **Track C** | RAM-to-Disc Signature Match | Matching dynamic RAM buffers against raw disc sectors | Overlay source LBA & generation | Sector splice validation |
| **Track D** | Dynamic PC Harvester | Logging executed PCs across scripted gameplay runs | Executed instruction set | `CONFIRMED_CODE` |
| **Track E** | Dynamic Callgraph Recovery | Logging `BSR`, `JSR`, and `RTS` transitions | Caller-callee call tree | Architectural stack trace |
| **Track F** | Direct CFG Closure | Recursive static descent along proven branch targets | Extended reachable code blocks | Decoder verification |
| **Track G** | Literal Pool Extractor | PC-relative offset tracking to isolate data constants | Embedded constant ranges | `CONFIRMED_DATA` |
| **Track H** | Jump Table Discriminator | Detecting `jmp @(r0, rn)` and jump table arrays | Switch-case targets | Boundary validation |
| **Track I** | Saturn SDK Signatures | Fingerprinting SGL/SBL/SYS standard library routines | Library boundaries & roles | Static binary pattern |
| **Track J** | Normalized Byte Hashing | Identifying duplicated code routines across modules | Shared code templates | Hash equivalence |
| **Track K** | Saturn-Splitter Splitting | Structural splitting into logical compilation units | File topology & linker map | Byte-exact relinking |
| **Track L** | Compiler Idiom Matching | Recognizing GCC SH-2 register allocation conventions | Function ABI & frame layout | Static proof |
| **Track M** | Saturn MMIO Labeling | Categorizing reads/writes to Saturn VDP1/VDP2/SCU/SCSP | Hardware interface mapping | Address map validation |
| **Track N** | Resource Recognizer | Differentiating sprites, tilemaps, PCM from code | Data file categorization | Format validation |
| **Track O** | SCSP/M68K Sound Discovery | Isolating 68000 sound driver code in Sound RAM | Sound CPU code ownership | M68K trace & byte exactness |
| **Track P** | Master/Slave SH-2 Separation| Tracking FRT interrupts and Slave SH-2 boot vector | Multi-core task ownership | CPU core tagging |
| **Track Q** | Dynamic RAM Code Lifecycle | Tracking code overwritten or relocated dynamically | Executable generation index | RAM state snapshot |
| **Track R** | Coverage-Guided Play Script | Scripting controller inputs to maximize executed code | Expanded test coverage | High PC retirement count |
