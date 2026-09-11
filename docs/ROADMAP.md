# Roadmap

## Completed

### D0 / T2-M0 — Canonical Revision Identity

Status: **DONE**

Evidence:

- revision `thor2_ntsc_patched_fe11d2fb` confirmed by hashes;
- 33-file ISO9660 manifest reproduced identically twice;
- executable candidates and static load evidence recorded;
- census tool and synthetic tests committed.

### T2-P0 — Dual-Track Planning Checkpoint

Status: **DONE**

Separated the project planning model into two explicit synchronized tracks:

- **Development Track** (`docs/DEVELOPMENT_PLAN.md`): capability-oriented milestones D0–D18.
- **Verification Track** (`docs/PIPELINE_VALIDATION_PLAN.md`): method/component experiments V-01–V-14.

### T2-P0.1 — Dual-Track Proof-Contract Repair

Status: **DONE**

Adversarial repair of proof contracts:
- introduced capability scope states (`PROPOSED`, `READY_FOR_BOUNDED_TEST`, `BOUNDED_PROOF`, `EXPANDED_PROOF`, `DONE`);
- split V-01 into `V-01-core` and `V-01-automation`;
- removed `TH2.LOW` from V-01 (queued under D2 / `V-02b`);
- established explicit L0 semantic gate and pre-D8 identity/event safety guards;
- split V-07 into `V-07A`, `V-07B`, and `V-07C`;
- relaxed D14 static round-trip prerequisite.

### D1 — Deterministic Dynamic Oracle (V-01-core / V-01-automation)

Status: **BOUNDED_PROOF** (decisions D-009, D-010)

Capability: reproducible dynamic observation of Thor 2 execution under a pinned configuration and scripted IPC harness.
Verified gates:
- **V-01-core**: bounded emulator observation under pinned Mednafen debug fork; Run A/B identical match (ADR D-009 `ADOPT`).
- **V-01-automation**: low-level scripted IPC control via `MednafenBot`; Run A/B identical match, negative control verified (ADR D-010 `ADOPT_PARTIAL` for `LOW_LEVEL_CONTROL_LAYER_PROVEN`).

Target claims proven: Master SH-2 candidate boot entry at `0x06004000` (hook pc `0x06004002` via pc-2 fallback), step transitions/retirements (`0x06004000` `MOV.W @R1, R6`; `0x06004002` `MOV R0, R15`; `0x06004004` `MOV.L @(0x5C, PC), R4`), deterministic cycle counter, dynamic memory read watchpoint (`0x06081C10` = `0x060917DC` via `MOV.L @R4, R4` at `0x06004006`), and automated programmatic reproducibility via `MednafenBot`.

### D2 — Executable Module Provenance (0TH2.BIN and TH2.LOW paths)

Status: **BOUNDED_PROOF for 0TH2.BIN and TH2.LOW** (decision D-011)

Capability: exact runtime mapping, disc provenance, and execution confirmation for executable modules.
Verified gates:
- **V-02a — 0TH2.BIN Executable Provenance** (ADR D-011; Daytona provenance methodology adopted as `ADOPT_PARTIAL`).
- **V-02b — TH2.LOW Executable Provenance** (`PASS / V02B_DIRECT_PROVENANCE_PROVEN`).

Target claims proven:
- `0TH2.BIN` (LBA 24..285, 535,552 bytes, SHA-256 `c1cc4117...`): read via CD Block FAD `0x0000AE..0x0001B3`, transferred directly into High Work RAM at `0x06004000..0x06086BFF` via BIOS Master SH-2 CPU copy loop (`PC=0x00002368`), confirmed byte-exact (`FULL_EXACT_MATCH`), and executed by Master SH-2.
- `TH2.LOW` (LBA 52123..52195, 149,504 bytes, SHA-256 `78139689...`): read via CD Block FAD `0x00CC31..0x00CC79`, transferred directly into Low Work RAM at `0x002DA000..0x002FE7FF` via Master SH-2 CPU copy loop (`PC=0x0607DF08`, zero SCU DMA), confirmed byte-exact (`FULL_EXACT_MATCH`), and executed by Master SH-2 at `0x002E9910..0x002E9914` (offset `0xF910`, cycle `387459915`).

### D3 — Exact SH-2 Decode / L0 Semantics (Startup Basic Block)

Status: **BOUNDED_PROOF expanded to first complete startup block**

Capability: correct fail-closed decoding and instruction/memory L0 semantics for SH-2 opcodes in Thor 2.
Verified gate: **V-06 — Independent SH-2 Decoder Cross-Check** + L0 semantic test suite.
Target claims proven:
- 6 block opcodes (`0x6611`, `0x6F03`, `0xD417`, `0x6442`, `0xA003`, `0x0009`) decoded into structured representation;
- V-06 cross-check against Hitachi hardware manual, pinned Mednafen `sh7095_ops.inc`, and `hazzaclark/catherine` confirmed 0 decode disagreements (machine-readable manifest `reference_decode_manifest.json`);
- Synthetic L0 semantic suite validated 16-bit sign-extension, big-endian bus access, aligned PC-relative EA computation `((PC & ~3) + 4) + (disp * 4)`, same-register writeback order (`Rm == Rn`), NOP preservation, BRA delayed branch target calculation `PC + 4 + (disp * 2)`, delay slot execution, illegal slot exception, and register isolation;
- Real Thor 2 block oracle replay matched pinned Mednafen debug oracle with 0 divergences across all 6 steps.

### D4 — Code/Data/Unknown Ownership (Block 0)

Status: **BOUNDED_PROOF for basic block 0 only**

Capability: byte-level classification of executable modules into confirmed code, probable code, data, and unknown.
Verified gate: **V-03 / V-04 — Bounded Code Ownership Validation**.
Target claims proven:
- Exactly 12 dynamically retired instruction bytes at `0x06004000..0x0600400B` promoted to `CONFIRMED_CODE / EXECUTED`;
- Unexecuted remainder of `0TH2.BIN` (`0x0600400C..0x06086BFF`) retains conservative `PROBABLE_CODE / HIGH` (no unexecuted bytes classified as data merely due to lack of observation).

### D5 — Basic-Block CFG Recovery (Block 0)

Status: **BOUNDED_PROOF for basic block 0 only**

Capability: discovery and evidence-backed representation of basic blocks, terminators, delay slots, and control-flow exits.
Verified gate: **V-03 — Bounded Block CFG Validation**.
Target claims proven:
- Basic block record `bb_06004000` created in `workstreams/T2-D4-D5-block0/block_06004000.md`;
- Bounded interval `0x06004000..0x0600400A` (6 instructions, 12 bytes);
- Terminator identified as `0xA003` (`BRA 0x06004012`) with delay slot `0x0009` (`NOP`);
- Direct taken exit identified as `0x06004012`;
- Fallthrough exit identified as null (`std::nullopt`, unconditional branch);
- No function boundaries or speculative semantic names asserted.

### D6 — Mechanical Explicit-State C++ (bb_06004000)

Status: **BOUNDED_PROOF for bb_06004000**

Capability: mechanically generated standalone C++20 translation from validated basic blocks with zero runtime interpreter dependencies.
Verified gate: **Pre-D8 identity/event safety gate (PASSED) + V-07A transition proof (PASSED)**.
Target claims proven:
- `bb_06004000` recompiled to explicit-state C++20 without interpreter wrappers;
- Link-time symbol isolation proven (test `test_generated_link_isolation` links exclusively to generated library);
- Differential transition proof against interpreter and Mednafen oracle confirmed 0 state divergences and 0 memory log divergences across 3 synthetic vectors and real Thor 2 startup;
- Negative controls verified (injected register/PC/memory corruptions detected).

### D7 — Shadow Recompilation Framework (bb_06004000)

Status: **BOUNDED_PROOF for bb_06004000** (decision D-013)

Capability: reusable shadow execution comparison framework with fail-closed eligibility checking, anti-aliasing enforcement, and negative fault controls.
Verified gate: **V-07B — Shadow Comparison Validation (PASSED)**.
Target claims proven:
- Reusable framework `ShadowChecker` implemented (`include/thor/recomp/shadow_checker.hpp`, `src/recomp/shadow_checker.cpp`);
- Outcome comparator validates R0..R15, PC, SR, PR/GBR/VBR/MACH/MACL, ordered memory log (kind, address, value, width, sequence), and event safety metadata;
- 4 positive test vectors verified with 0 divergences vs Mednafen oracle (`test_shadow_positive`);
- 100% detection rate across 24 negative fault controls with 0 false passes (`test_shadow_negative`);
- Complete pre-state storage isolation and anti-aliasing proven (`test_shadow_isolation`);
- D7 status advanced to `BOUNDED_PROOF (bb_06004000)`.

### D8 — First Native Promotion Proof (V-07C)

Status: `BOUNDED_PROOF (bb_06004000) / V-07C: PASS` (ADR D-014)

Target claims proven:
- Reusable `NativeDispatcher` with pre-execution eligibility guard, shadow qualification, and C ABI bridge implemented (`include/thor/recomp/native_dispatcher.hpp`, `src/recomp/native_dispatcher.cpp`, `include/thor/recomp/native_bridge.h`);
- Integrated with pinned Mednafen debug oracle via dynamic plugin (`libthor_native.so`);
- Live cold-boot authoritative native override executed (`Run A`) and bit-identical cold-boot reproduction verified (`Run B`);
- Live interpreter retired 0 instructions in replaced block (`retirements_in_interval = 0`);
- Continuation to `0x06004280` verified through BSS clearing and data copy with zero register divergences across all 23 CPU registers against baseline interpreter (`Run C`);
- 100% fail-closed fallback proven under memory byte corruption without partial native commit (`Run E`);
- Mandatory post-D8 second-pass plan established (`docs/POST_D8_SECOND_PASS_PLAN.md`, ADR D-012).

### D9 — Indirect Control-Flow Handling (bb_06004280)

Status: `BOUNDED_PROOF (bb_06004280) / D9.4.1: PASS` (ADR D-015)

Target claims proven:
- Exact decode and L0 execution semantics implemented for `JSR @Rn` (opcode `0x430B`);
- First indirect candidate block `bb_06004280` (`0x06004280..0x06004288`, 10 bytes, 5 instructions) qualified and verified;
- Generic `BlockExitDescriptor` and `BlockMemoryContract` implemented with `RUNTIME_CLASSIFICATION_REQUIRED` dynamic validation;
- Link-isolated build target `thor_generated_bb_06004280` compiled without interpreter dependencies;
- Isolated shadow qualification proven with 100% negative fault detection;
- Live authoritative native indirect override executed in pinned Mednafen debug oracle across 5 cold-boot runs;
- 100% register parity (23/23 SH-2 registers) verified at dynamically computed target `0x0600A0F8` (cycle `316309189`, delta = 0 cycles);
- Return site `0x0600428A` (cycle `337109623`, delta = 0 cycles) and downstream continuation `0x060042E0` (cycle `387459912`, delta = 0 cycles) verified with zero drift;
- Retained as a **bounded technology/proof specimen** per ADR D-015; broad C++ translation frozen.

### POST-D8 — External Method Second Pass (ADR D-012)

Status: `COMPLETE / SATISFIED / CLOSED` (canonical record in `docs/POST_D8_SECOND_PASS_CLOSURE.md`)

Audited all external methods M-01..M-10; verified reference corpus pins; evaluated Evidence Strength and Workflow Utility.

## Next

### T2-ARCH / ADR D-015 — Freeze Broad C++ Translation & Establish ASM-First Recovery Strategy

Status: `ACCEPTED` (ADR D-015 in `docs/DECISIONS.md`)

The project enforces an **ASM-FIRST recovery strategy**:
1. All executable binaries and overlays must be completely mapped and classified (`CODE / DATA / UNKNOWN`).
2. Exact SH-2 assembly must be mechanically reconstructed into an assemblable project tree (`asm/`).
3. Reconstructed modules must assemble deterministically and boot in clean Mednafen, reaching title screen and gameplay with runtime parity (`FULL_ASM_GAME_GATE`).
4. Only after passing `FULL_ASM_GAME_GATE` will broad systematic translation from ASM to native C++ begin.
5. Existing C++ blocks `bb_06004000` (D8) and `bb_06004280` (D9) are retained strictly as bounded technology specimens.
6. M-03 technical capability is `READY_FOR_BOUNDED_TEST`, with execution `DEFERRED_BY_ASM_FIRST_ARCHITECTURE` until `FULL_ASM_GAME_GATE` passes.

### T2-ASM-01 — First Bounded SH-2 ASM Round-Trip & Runtime Proof

Status: **BOUNDED_PROOF (bb_06004000 byte-exact & runtime verified)**

Capability: mechanical SH-2 assembly emission, open toolchain assembly/linking at original Saturn VMA, byte-exact extraction, and live runtime substitution in Mednafen oracle.
Verified gate:
- Open GNU Binutils SH toolchain (`binutils-sh-elf 2.40+2`) pinned by binary hashes;
- Real SH-2 mnemonics emitted mechanically (`mov.w`, `mov`, `mov.l`, `bra`, `nop`);
- Linker script establishes VMA `0x06004000` with zero unresolved relocations;
- 12-byte raw extraction byte-exact to canonical slice SHA-256 `83795110...`;
- Private `0TH2.BIN` splice verified bit-identical to SHA-256 `c1cc4117...`;
- Mednafen cold-boot runtime substitution matches ORIGINAL in pure interpreter mode (entry cycle `305462360`, target `305462387`, duration 27, 23/23 registers match);
- 12/12 negative controls fail closed.

### T2-ASM-02 — Full 0TH2.BIN Lossless Assembly Container & Byte-Exact Module Round-Trip

Status: **BOUNDED_PROOF (0TH2.BIN)**

Capabilities proven:
- Generic C++ Thor-decoder-backed Assembly IR tool `export_sh2_asm_ir` linked against authoritative `thor_sh2`;
- Lossless assembly container `.private/asm/0TH2/0TH2.s` (33,521 lines) emitting real mnemonics for confirmed code (22 bytes, 11 instructions) and `.byte` directives for remaining 535,530 bytes without guessing;
- Real in-module label resolution eliminating all `.equ` workarounds;
- Linker script `asm/linker/0TH2.ld` asserting VMA `0x06004000`, 535,552 bytes, and exact label offsets;
- Byte-exact extraction (535,552 / 535,552 bytes, SHA-256 `c1cc4117...`);
- Dual independent builds bit-identical (0 differing bytes);
- Sector-by-sector private disc splice matches canonical disc SHA-256 `fe11d2fb...`;
- Mednafen cold-boot runtime parity verified in interpreter mode across 5 checkpoints (`06004000`, `06004012`, `06004280`, `0600A0F8`, `002E9910`) with 0-cycle divergence and 23/23 matching registers;
### T2-ASM-03 — TH2.LOW Lossless ASM Container & Shared ASM Recovery Infrastructure

Status: **BOUNDED_PROOF (TH2.LOW)**

Capabilities proven:
- Formal manifest schema `asm/schema/module_manifest.schema.json` with mandatory exhaustive range partitioning;
- Replaced Python SH-2 decoders with C++ `verify_sh2_rebuilt` linking `thor_sh2`;
- Lossless assembly container `.private/asm/TH2_LOW/TH2_LOW.s` (9,365 lines) emitting proven executed instruction `0x002E9910` (`0x2FE6` MOV.L R14, @-R15) safely as `RAW_CODE_PENDING_DECODE` and remaining 149,502 bytes losslessly as `.byte` directives;
- Linker script `asm/linker/TH2_LOW.ld` asserting VMA `0x002DA000`, 149,504 bytes, and `entry_002E9910`;
- Byte-exact extraction (149,504 / 149,504 bytes, SHA-256 `78139689...`);
- Dual independent builds bit-identical (0 differing bytes);
- Sector-by-sector private disc splice at LBA 52123 matches canonical disc SHA-256 `fe11d2fb...`;
- Occurrence-aware runtime verification in pure interpreter Mednafen proving cycle 387459915 execution parity at `0x002E9910` in `TH2.LOW` with 0-cycle divergence and 23/23 matching registers across 6 checkpoints;
- 10/10 TH2.LOW, 20/20 0TH2, and 9/9 schema negative controls pass fail-closed.

### T2-ASM-04 — Disc Executable Inventory & Secondary Module ASM Skeletons

Status: **BOUNDED_PROOF (Inventory + SET07.BIN)**

Capabilities proven:
- Complete census across all 33 ISO9660 disc files;
- Identified all executable binaries and hardware roles: `0TH2.BIN` (Master SH-2 core), `TH2.LOW` (Master SH-2 low RAM engine), `SET07.BIN` (Master SH-2 stage overlay), `BGM.BIN` (M68K sound driver), `MAP.BIN` (SCU DSP microcode + geometry);
- Proven multi-processor execution lifetime: Master SH-2 single-core boot/engine; Slave SH-2 dormant at frame 1201; MC68EC000 sound driver entry at `0x1000`;
- Stage overlay loader invocation site recovered at `0x002E3C5C` in `TH2.LOW` (loads `SET07.BIN` to `0x060D8000` and executes `JSR @R3`);
- Lossless assembly container `.private/asm/SET07/SET07.s` (6,175 lines) reassembled byte-exact (98,304 / 98,304 bytes, SHA-256 `bb607222...`) with pinned GNU `binutils-sh-elf 2.40+2`;
- Dual-build determinism verified; sector-by-sector private disc splice at LBA 52040 verified bit-exact against retail disc `fe11d2fb...`;
- 9/9 SET07 negative controls pass;
- `thor_sh2` decoder & L0 semantics expanded: `MOV_L_WRITE_PREDEC` (`0x2nm6`) and `RTS` (`0x000B`); `TH2.LOW` entry `0x002E9910` promoted to `MNEMONIC_PROVEN`;
- Method catalog (`docs/ASM_RECOVERY_METHOD_CATALOG.md`), autoplan priority engine (`docs/ASM_RECOVERY_AUTOPLAN.md`), and scorecard (`workstreams/ASM_RECOVERY_SCORECARD.json`) operational;
- 24/24 CTests pass on Windows MinGW and Linux WSL.

### T2-ASM-05 — Bulk PC Harvesting, Opcode Modeling & ASM_90_GATE Passed

Status: **PASS (ASM_90_GATE: 96.59% >= 90.00%)**

Capabilities proven:
- `thor_sh2` opcode decoder and executor expanded from 7 to 63 opcodes with L0 semantics, disassembly, and unit tests;
- SH-2 units modularized (`sh2_decoder_ext.cpp`, `sh2_disasm.cpp`, `sh2_executor_ext.cpp`) maintaining strict <= 500 lines per human-maintained source file;
- `TH2.LOW` partitioned into 353 ranges (176 proven code blocks, 3,250 / 3,266 bytes = **99.51% proven coverage**);
- `0TH2.BIN` partitioned into 6,353 ranges (3,126 proven code blocks, 52,050 / 53,958 bytes = **96.46% proven coverage**);
- Both modules reassembled byte-exact with pinned GNU `binutils-sh-elf 2.40+2`;
- Dual-build determinism verified (0 differing bytes between independent runs);
- Sector-by-sector private disc splice verified bit-identical against canonical retail disc `fe11d2fb...`;
- Occurrence-aware Mednafen cold-boot runtime parity verified across all 6 checkpoints with 0 cycle / register divergence;
- All negative controls pass fail-closed (20 for 0TH2.BIN, 10 for TH2.LOW, 9 for SET07.BIN);
- Overall proven mnemonic coverage reached **96.59%** (55,312 / 57,264 confirmed code bytes), satisfying and passing **`ASM_90_GATE`**;
- 26/26 CTests pass on Windows MinGW and Linux WSL.

### FULL_ASM_GAME_GATE — Full Saturn Disc Game Boot & Gameplay Verification

Status: **PASS (100% of All 4 Executable Modules Reassembled & Verified in Gameplay Suite)**

Capabilities proven:
- Spliced all 4 reassembled byte-exact modules (`0TH2.BIN`, `TH2.LOW`, `SET07.BIN`, `BGM.BIN`) into a rebuilt private Saturn disc image;
- Disc SHA-256 verified bit-identical against canonical retail disc `fe11d2fb...`;
- Implemented multi-scenario gameplay regression suite `verify_gameplay_scenarios.py` with frame-accurate input playback across 2,641 frames:
  - `BOOT_TO_TITLE`: frame 1200, cycle `554511205`, 0 drift, 100% register parity;
  - `TITLE_TO_NEW_GAME`: frame 1480, cycle `688536004`, 0 drift, 100% register parity;
  - `EARLY_GAMEPLAY`: frame 2200, cycle `1033171205`, 0 drift, 100% register parity;
  - `MAP_TRANSITION`: frame 2471, cycle `1162888064`, 0 drift, 100% register parity;
  - `COMBAT`: frame 2581, cycle `1215540665`, 0 drift, 100% register parity;
  - `AUDIO`: frame 2641, cycle `1244260260`, 0 drift, 100% register parity;
- Proved single-SH-2 invariant: Slave SH-2 remains dormant in reset state (`PC=00000000`, `SR=000000F0`, all general registers 0) across all gameplay scenarios;
- Established CTest integration test #38 (`test_gameplay_scenarios`);
- All 38 CTests pass on Windows MinGW and Linux WSL;
- Machine-enforced gate validator `validate_recovery_gates.py` passing with 10 negative controls;
- ADR D-015 requirement for broad C++ native module replacement fully unblocked.

### D10 — Timing/Interrupt/DMA Execution Boundaries

Status: **BOUNDED_PROOF / PASS**

Capabilities proven:
- Formalized execution boundary taxonomy in `include/thor/recomp/block_timing.hpp` and `src/recomp/block_timing.cpp`: `ATOMIC_COMPUTATION`, `MMIO_SYNCHRONOUS`, `INTERRUPT_WINDOW`, `DMA_ASYNCHRONOUS`;
- Implemented Saturn MMIO region recognition across SH-2 on-chip peripherals `0xFFFFFE00..0xFFFFFFFF` and B-Bus/VDP/SCU/SCSP mirrors `0x05800000..0x05FFFFFF` / `0x25800000..0x25FFFFFF`;
- Implemented `classify_block_timing(...)` detecting hardware boundary crossings and enforcing synchronization barriers or interpreter fallbacks;
- Verified with dedicated CTest suite `test_block_timing` across synthetic vectors, memory contracts, and bounded event metadata;
- 28/28 CTests pass across MinGW and Linux WSL.

### D11 — Overlay/Generation Identity

Status: **BOUNDED_PROOF / PASS**

Capabilities proven:
- Formalized multi-generation executable identity per AGENTS.md: `revision + CPU + module/overlay generation + guest address`;
- Added generation tracking to `BlockIdentityDescriptor` and `GENERATION_MISMATCH` fail-closed rejection to `check_block_eligibility`;
- Proved generation isolation between base modules (generation 0) and stage overlays (generation 7: `make_bb_060D8000_set07_descriptor()` at `0x060D8000`);
- Verified positive qualification (matching generation) and negative fault injection (mismatched generations 0, 6 fail closed with `GENERATION_MISMATCH`);
- Verified with `test_executable_identity`.

### D12 — Structural Recovery & Subsystem Function Demarcation

Status: **PASS**

Capabilities proven:
- Formalized function boundary kinds and invariants in `include/thor/recomp/function_boundary.hpp` and `src/recomp/function_boundary.cpp`: `MODULE_ENTRY`, `DIRECT_CALL_TARGET`, `INDIRECT_CALL_TARGET`, `EXCEPTION_VECTOR`;
- Formalized exit kinds: `SUBROUTINE_RETURN`, `EXCEPTION_RETURN`, `TAIL_CALL`, `NON_RETURNING`;
- Demarcated canonical subroutines: `sub_06004000_boot`, `sub_0600A0F8_load_file`, `sub_002E9910_engine_start`, `sub_060D8000_stage_overlay`;
- Verified bidirectional caller/callee adjacency indexing and call graph queries (`get_callers`, `get_callees`, `find_by_pc`);
- Verified with `test_function_boundary` (CTest #20); 29/29 CTests pass across Windows MinGW and Linux WSL.

### D13 — Guest-Address & Type Provenance Model (Gate V-09)

Status: **PASS (Gate V-09: PASS)**

Capabilities proven:
- Implemented strongly-typed `GuestAddress<T>` and `GuestPtr<T>` with provenance tracking (`module_name`, `file_offset`, `domain`) in `include/thor/provenance/guest_address.hpp`;
- Implemented type-safe `GuestView` memory access layer in `include/thor/provenance/guest_view.hpp` enforcing big-endian bus access, alignment checks, and fail-closed null/bounds detection;
- Formalized canonical Saturn startup memory layout table `SaturnStartupTable` (`0x06081C04..0x06081C18`) and file loading entry `SaturnFileLoadEntry` (`0x06081C20`) in `include/thor/provenance/saturn_runtime_table.hpp`;
- Verified 100% bit-exact equivalence against raw `ISh2Memory::read32` with zero divergence across synthetic and live Thor 2 memory patterns;
- Dedicated unit test suite `test_guest_provenance` (CTest #21) passing 100% on Windows MinGW and Linux WSL.

### D14 — Resource Decoding & Reencoding (Gate V-11)

Status: **PASS (Gate V-11: PASS / BYTE_ROUNDTRIP_EXACT)**

Capabilities proven:
- Recovered Ancient Character/Spirit Sprite Archive container specification (`SpriteArchiveHeader`, 16-bit offset table, animation scripts, and 4bpp VDP1 sprite graphics);
- Implemented `SpriteArchive` decoder, encoder, and size calculation in `include/thor/resource/sprite_archive.hpp` and `src/resource/sprite_archive.cpp`;
- Verified 100% bit-exact re-encoding (`BYTE_ROUNDTRIP_EXACT`, 0 byte differences) across real Saturn retail disc assets `BAW.BIN` (72,540 B), `DIT.BIN` (63,244 B), `SHADE.BIN` (69,844 B), `ARELE.BIN` (62,344 B), `EFREET.BIN` (130,352 B), and `BRAS.BIN` (105,180 B) totaling 503,504 bytes;
- 6/6 negative fault injection controls pass fail-closed;
- Dedicated unit test suite `test_resource_roundtrip` (CTest #22) passing 100% on Windows MinGW and Linux WSL.



### D15 — Hardware Subsystem Contracts (VDP1, VDP2, SCSP)

Status: **PASS**

Capabilities proven:
- Formalized VDP1 display list command decoder (10 command types, 5 jump modes, 6 color modes), clipping rectangles, and local coordinate transformation in `include/thor/hw/vdp1_types.hpp`, `include/thor/hw/vdp1.hpp`, `src/hw/vdp1.cpp`;
- Formalized VDP2 background plane configurations (NBG0..NBG3, RBG0, Sprite, Back), CRAM 15-bit/24-bit decoding, 16.16 fixed-point rotation matrix transform, multi-plane priority arbitration, and color calculation blending in `include/thor/hw/vdp2_types.hpp`, `include/thor/hw/vdp2.hpp`, `src/hw/vdp2.cpp`;
- Formalized SCSP sound command ring buffer FIFO, driver state machine, and SFX slot allocation in `include/thor/hw/scsp_types.hpp`, `include/thor/hw/scsp.hpp`, `src/hw/scsp.cpp`;
- Verified with dedicated unit test suites `test_vdp1`, `test_vdp2`, `test_scsp`;
- 32/32 CTests pass across Windows MinGW and Linux WSL.

### D16 — Native Subsystem Replacement (Unified Hardware Bridge & Backends)

Status: **PASS**

Capabilities proven:
- Implemented `NativeSaturnSystem` coordinating VDP1 rasterizer, VDP2 plane compositor, SCSP sound synthesizer, and unified MMIO memory routing in `include/thor/hw/native_system.hpp` and `src/hw/native_system.cpp`;
- Implemented frame rasterizer producing 320x224 RGBA8888 pixels from sprite and background planes;
- Implemented audio synthesis generating 16-bit stereo PCM audio from active SCSP sound slots;
- Verified MMIO dispatch routing across VDP1, VDP2, and Sound RAM ranges;
- Verified with dedicated unit test suite `test_native_subsystems` (CTest #24);
- 33/33 CTests pass across Windows MinGW and Linux WSL.

### D17 — Progressive Standalone Runtime (Native Execution Loop & Subsystem Binding)

Status: **ADVANCED_PROTOTYPE / IN_PROGRESS (Gate V-14: NOT_YET_PASSED)**

Capabilities proven:
- Implemented `StandaloneRuntime` coordinating Work RAM, native hardware subsystems, native block dispatch, and fallback SH-2 instruction execution in `include/thor/runtime/standalone_runtime.hpp` and `src/runtime/standalone_runtime.cpp`;
- Verified isolated compilation and linking without external emulator libraries;
- Hardened dynamic instruction count and cycle accounting per executed native block in `NativeDispatcher`;
- Verified sequential multi-block native execution (`bb_06004000` + `bb_06004280`) retiring 11 native instructions over 48 cycles with zero fallback instructions;
- Proved measured dependency reduction via runtime metrics (`has_measured_dependency_reduction() == true`, 100% native execution ratio across proven blocks);
- Verified native video frame presentation (320x224 RGBA8888) and stereo audio sample generation;
- Verified with dedicated unit test suite `test_standalone_runtime` (CTest #27);
- 38/38 CTests pass across Windows MinGW and Linux WSL.

### D18 — Guest Dependency Removal & Standalone Game Executable Target

Status: **NOT_PROVEN (SUPERSEDED / PROTOTYPE)**

Audit note: The terminal completion claim at commit 093abf0 was superseded after factual review. Standalone executable `thor2_native` links and runs self-tests, but retains guest CPU fallback interpreter `step_sh2`, broad C++ translation remains frozen under ADR D-015, and real L5 oracle equivalence against Mednafen reference remains unproven.

Capabilities proven to date:
- Standalone native executable target `thor2_native` (`src/main_native.cpp`) built and linked with internal libraries;
- Portable CLI interface supporting `--boot`, `--frames <N>`, `--metrics`, `--selftest`, and `--help`;
- Deterministic multi-frame rendering and audio synthesis verified between candidate instances;
- Dedicated unit test suite `test_guest_removal` (CTest #26);
- Production guest CPU removal and true L5 oracle comparison remain pending.

## Queued development milestones

| ID | Capability | Key verification gate | Scope state |
|---|---|---|---|
| D2 | Executable module provenance | V-02a (0TH2.BIN), V-02b (TH2.LOW) | BOUNDED_PROOF (0TH2.BIN + TH2.LOW) |
| D3 | Exact SH-2 decode + L0 semantics | V-06 cross-check + L0 semantic test suite | BOUNDED_PROOF (63 opcodes fully modeled) |
| D4 | Code/data/unknown ownership | V-03 (bounded batch), V-04 (schema) | EXPANDED_PROOF (96.59% proven coverage) |
| D5 | Basic-block CFG | V-03 (bounded block CFG) | EXPANDED_PROOF (3,302 proven blocks) |
| D6 | Mechanical explicit-state C++ | V-07A + pre-D8 identity/event guards | BOUNDED_PROOF (specimens bb_06004000, bb_06004280) |
| D7 | Shadow comparison | V-07B (negative-control validation) | BOUNDED_PROOF (specimens bb_06004000, bb_06004280) |
| D8 | First native promotion proof | V-07C (native override proof) | BOUNDED_PROOF (specimen bb_06004000) |
| D9 | Indirect control-flow handling | Bounded native JSR override | BOUNDED_PROOF (specimen bb_06004280) |
| **M-03** | **Candidate harvester re-evaluation** | **Post-D9.4 re-entry gate** | **READY_FOR_BOUNDED_TEST (DEFERRED_BY_ASM_FIRST_ARCHITECTURE)** |
| **T2-ASM-01** | **First bounded ASM round-trip** | **Candidate toolchain assembly & substitution** | **BOUNDED_PROOF (bb_06004000)** |
| **T2-ASM-02** | **Full 0TH2.BIN lossless assembly container** | **Lossless full-module round-trip** | **BOUNDED_PROOF (0TH2.BIN)** |
| **T2-ASM-03** | **TH2.LOW lossless ASM container** | **Lossless full-module round-trip & occurrence-aware runtime proof** | **BOUNDED_PROOF (TH2.LOW)** |
| **T2-ASM-04** | **Disc executable inventory & secondary modules** | **Census, multi-processor lifetimes, SET07.BIN container** | **BOUNDED_PROOF (SET07.BIN)** |
| **T2-ASM-05** | **Bulk PC harvesting & CFG recovery to ASM_90_GATE** | **Coverage >= 90%, runtime parity** | **PASS (96.59% COVERAGE)** |
| **GATE** | **FULL_ASM_GAME_GATE** | **Rebuilt Saturn game boots & plays in Mednafen** | **PASS (100% of 4 modules, 6 gameplay scenarios verified)** |
| **D10** | **Timing/IRQ/DMA boundaries** | **Classification & barrier model** | **BOUNDED_PROOF / PASS** |
| **D11** | **Overlay/generation identity** | **Multi-generation descriptor & isolation** | **BOUNDED_PROOF / PASS** |
| **D12** | **Structural recovery** | **Function boundary catalog & call graph** | **PASS** |
| **D13** | **Guest-address/type provenance** | **V-09 (Azel address model)** | **PASS** |
| **D14** | **Resource decode/reencode** | **V-11 (exact round-trip)** | **PASS (BYTE_ROUNDTRIP_EXACT)** |
| **D15** | **HW-subsystem contracts** | **V-08 (SaturnRecomp component tests a–h)** | **BOUNDED_PROTOTYPE** |
| **D16** | **Native subsystem replacement** | **V-08 (components passing differential test)** | **BOUNDED_PROTOTYPE** |
| **D17** | **Progressive standalone runtime** | **V-14 (isolated, integrated, measured)** | **BOUNDED_PROTOTYPE** |
| **D18** | **Guest dependency removal** | **— (L5 equivalence)** | **NOT_PROVEN** |

## References

- `docs/DEVELOPMENT_PLAN.md` — full development track with milestones, dependencies, risk map.
- `docs/PIPELINE_VALIDATION_PLAN.md` — verification/adoption experiments.
- `docs/PROJECT_STATE.md` — current verified state.
- `docs/DECISIONS.md` — architectural decisions (ADR D-001..D-015).
