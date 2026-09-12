# Reverse engineering record

## Confirmed substrate: `thor2_ntsc_patched_fe11d2fb`

T2-M0 reproducibility gate: **PASS**.

Two independent executions of `tools/disc/census_saturn_cd.py` produced identical `disc_manifest.tsv` and summary outputs from the same private input image.

### Disc identity

| Item | Value | Status |
|---|---|---|
| Image SHA-256 | `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8` | CONFIRMED |
| CUE SHA-256 | `afc0b101bbb493adbd43fd44ffd76959484d67cf0b566137dd145f1c68d411e0` | CONFIRMED |
| Format | `MODE1/2352` | CONFIRMED |
| Raw sectors | 52,224 | CONFIRMED |
| Volume ID | `THE STORY OF THOR 2` | CONFIRMED |
| Files | 33 | CONFIRMED |
| Product code | `MK-81302` | CONFIRMED |
| Version | `V1.000` | CONFIRMED |
| Header date | `19960618` | CONFIRMED |
| Header title | `THE STORY OF      THOR 2 (patched for NTSC)` | CONFIRMED |
| First-read address | `0x06004000` | CONFIRMED header field |

Full per-file identity is in `workstreams/T2-M0-disc-census/disc_manifest.tsv`.

## Executable module `0TH2.BIN`

Module status: `EXECUTABLE_MODULE / RUNTIME_MAPPING_EXACT / FULL_EXACT_MATCH / DIRECT_PROVENANCE_PROVEN` (V-02a proven direct runtime mapping; ADR D-011).
Byte classification: `CONFIRMED_CODE / EXECUTED` for dynamically observed instructions at `0x06004000..0x0600400B` (Basic Block 0, 12 bytes); unexecuted remainder `0x0600400C..0x06086BFF` remains `PROBABLE_CODE / HIGH` (mapped byte-exact to disc; complete code/data/unknown ownership queued for D4).

- SHA-256: `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64`
- Disc extent: ISO9660 LBA 24..285 (262 sectors, 535,552 bytes / `0x82C00`)
- CD Block FAD: `0x0000AE` .. `0x0001B3` (LBA + 150)
- Runtime load base: `0x06004000`
- Runtime load end: `0x06086BFF`
- Transfer mechanism: `DIRECT_CPU_COPY_OBSERVED` (BIOS Master SH-2 copy loop at PC `0x00002368`, zero SCU DMA to High Work RAM)
- Pre-entry live RAM hash: `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64` (0 differing bytes vs disc, `FULL_EXACT_MATCH` across Run A and Run B)
- Execution: Master SH-2 entry breakpoint hit at cycle `305462360`; initial instructions executed at `0x06004000..0x06004008`

Evidence:

- Saturn header first-read address is `0x06004000`;
- it is the first ISO9660 file record;
- **Dynamic proof (V-01-core / V-01-automation)**: Master SH-2 hit breakpoint on candidate entry `0x06004000` from BIOS (`ret=0x06002244`) at frame 680, cycle `305462360` (debugger hook PC `0x06004002` via `pc - 2` fallback). Startup sequence: Step 2 retires `0x6611` (`MOV.W @R1, R6`, setting R6=`0x6611`); Step 3 retires `0x6F03` (`MOV R0, R15`, switching SP from header default `0x06001000` to target `0x06002EDC`); Step 4 retires `0xD417` (`MOV.L @(0x5C, PC), R4`, loading pointer `0x06081C10`); Step 5 executes `0x6442` (`MOV.L @R4, R4`), dynamically triggering `read_watchpoint 06081C10` with value `0x060917DC` (BSS start pointer); Step 6 completes R4 writeback to `0x060917DC`.
- **Dynamic provenance proof (V-02a)**: Proved direct byte identity between disc file and live pre-execution RAM at `0x06004000..0x06086BFF` across two independent cold boots (`FULL_EXACT_MATCH`). CD Block trace `cdb.log` proved 262-sector transfer (`Get and Delete Sector Data`) across FAD `0x0000AE..0x0001B3` terminating with `End Data Transfer`. Traces `dma.log` and `mem.log` proved zero SCU DMA to High Work RAM and transfer via BIOS Master SH-2 CPU copy loop at PC `0x00002368` (`MOV.B @R0, R1` / `MOV.B R1, @R7`).

Next proof: exact SH-2 decode / L0 semantics (D3).

## Executable module `TH2.LOW`

Module status: `EXECUTABLE_MODULE / RUNTIME_MAPPING_EXACT / FULL_EXACT_MATCH / DIRECT_PROVENANCE_PROVEN` (V-02b proven direct runtime mapping).
Byte classification: `CONFIRMED_CODE / EXECUTED` for dynamically observed instructions at `0x002E9910..0x002E9914`; unexecuted remainder `0x002DA000..0x002FE7FF` remains `PROBABLE_CODE / HIGH` (mapped byte-exact to disc; complete code/data/unknown ownership queued for D4).

- SHA-256: `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224`
- Disc extent: ISO9660 LBA 52123..52195 (73 sectors, 149,504 bytes / `0x24800`)
- CD Block FAD: `0x00CC31` .. `0x00CC79` (LBA + 150)
- Runtime load base: `0x002DA000`
- Runtime load end: `0x002FE7FF`
- Transfer mechanism: `DIRECT_CPU_COPY_OBSERVED` (Master SH-2 CPU write loop at PC `0x0607DF08`, zero SCU DMA to Low Work RAM)
- Pre-load live RAM hash: `71ba98cb5315c867d5670e7d214b2369d52235d1182658413d3890cfb982be6e`
- Post-load live RAM hash: `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224` (0 differing bytes vs disc, `FULL_EXACT_MATCH` across Run A and Run B)
- Execution: Master SH-2 breakpoint at `0x002E9910` hit at cycle `387459915` (called from `0x060042E0`, `PR=0x060042E4`), executed `0x2FE6` (`MOV.L R14, @-R15`) advancing to `0x002E9914`.

Evidence:
- **Static evidence**: recorded in `workstreams/T2-M0-disc-census/static_load_evidence.md`. Call-site in `0TH2.BIN` at `0x06004280..0x06004286` prepares `R4 -> "TH2.LOW"` (`0x06081C20`), `R5 = 0x002DA000`, and `JSR @R3` (`R3 = 0x0600A0F8`).
- **Dynamic call-site proof (V-02b)**: CPU state confirmed before call: `R3 = 0x0600A0F8`, `R4 = 0x06081C20` (memory read dynamically confirmed ASCII `"TH2.LOW"`), `R5 = 0x002DA000`, `PR = 0x0600428A`.
- **Dynamic transfer & mapping proof (V-02b)**: CD Block trace `cdb.log` recorded 73-sector read (`CMD Play; Start=0x80cc31, End=0x800049`) across FAD `0x00CC31..0x00CC79`. Memory trace `mem.log` recorded 37,376 32-bit writes ($37376 \times 4 = 149,504$ bytes) into `0x002DA000..0x002FE7FF` by Master SH-2 at PC `0x0607DF08`. SCU DMA trace recorded zero DMA to Low Work RAM. Live RAM snapshot post-transfer matches disc file byte-for-byte (`FULL_EXACT_MATCH`, 0 differing bytes).
- **Dynamic execution proof (V-02b)**: Called from `0x060042E0` (`PR=0x060042E4`), Master SH-2 executed instruction at `0x002E9910` (offset `0xF910`, cycle `387459915`), retiring `MOV.L R14, @-R15` (`0x2FE6`) and advancing PC to `0x002E9914`.

Next proof: D3 opcode corpus expansion / D4 code/data ownership.

## Executed startup opcode slice (`0x06004000..0x06004008`)

Slice status: `DECODE_VERIFIED` / `INSTRUCTION_SEMANTICS_VERIFIED` / `MEMORY_SEMANTICS_VERIFIED` (T2-D3.1).
Decoder: `thor::sh2::decode_sh2` (fail-closed C++20 implementation; V-06 cross-check passed with 0 disagreements).
Executor: `thor::sh2::execute_sh2_instruction` / `thor::sh2::step_sh2` (L0 semantic test suite and real Thor 2 startup vector passed with 0 divergences).

- `0x06004000`: `0x6611` — `MOV.W @R1, R6` (reads 16-bit word from `R1=0x06004000`, sign-extends to 32 bits into `R6=0x00006611`, advances PC to `0x06004002`).
- `0x06004002`: `0x6F03` — `MOV R0, R15` (copies stack pointer `R0=0x06002EDC` into `R15`, advances PC to `0x06004004`).
- `0x06004004`: `0xD417` — `MOV.L @(0x5C, PC), R4` (reads 32-bit word from `((PC & ~3) + 4) + 0x5C = 0x06004064` containing `0x06081C10` into `R4`, advances PC to `0x06004006`).
- `0x06004006`: `0x6442` — `MOV.L @R4, R4` (reads 32-bit word from `R4=0x06081C10` containing `0x060917DC` before writeback to `R4`, advances PC to `0x06004008`).
- `0x06004008`: `0xA003` — `BRA 0x06004012` (unconditional delayed branch to `PC + 4 + (3 * 2) = 0x06004012`; advances PC to delay slot `0x0600400A`).
- `0x0600400A`: `0x0009` — `NOP` (delay slot instruction, no architectural side-effects, completes block retirement with target jump to `0x06004012`).

## Basic Block `bb_06004000` Record

```text
ID: bb_06004000
STATUS: CONFIRMED_CODE / EXECUTED / BEHAVIOR_VERIFIED / NATIVE_OVERRIDE_PROVEN
REVISION/HASH: thor2_ntsc_patched_fe11d2fb
DISC FILE: 0TH2.BIN
FILE RANGE: 0x00000000..0x0000000B (12 bytes)
RUNTIME RANGE: 0x06004000..0x0600400B (12 bytes, 6 instructions)
CPU: MASTER_SH2
MODULE/GENERATION: 0TH2.BIN (High Work RAM initial execution)
STATIC EVIDENCE: ISO9660 root directory extent LBA 24..285, first-read entry 0x06004000
DYNAMIC EVIDENCE: V-01-core breakpoint trigger, multi-step retirement, V-02a byte-exact live RAM match, block replay vs Mednafen oracle, minimum event safety audit
EVENT SAFETY: PRE_D8_MINIMUM_EVENT_SAFETY_PASS (atomic 27-cycle block duration [305462360..305462387, observation window through next instruction boundary 305462388 delta 28; earlier '18-cycle' was an arithmetic/typographical error for 28], 0 MMIO, 0 IRQ, 0 SCU DMA, Slave SH-2 inactive)
IDENTITY GUARD: PRE_D8_EXECUTABLE_IDENTITY_GUARD_PASS (bound to revision, module, provenance, CPU, address range, byte identity, validity state; negative controls verified; non-contaminating peek8)
READS/WRITES: Read 16-bit at 0x06004000 (0x6611); read 32-bit at 0x06004064 (0x06081C10); read 32-bit at 0x06081C10 (0x060917DC)
CONTROL FLOW: Straight-line 0x06004000..0x06004006; terminator BRA 0x06004012 at 0x06004008; delay slot NOP at 0x0600400A; direct taken exit 0x06004012; fallthrough nullopt
HARDWARE INTERACTION: Zero MMIO or peripheral access in this block; pure CPU/WRAM execution
HYPOTHESIS: Standard Sega Saturn CD application startup bootstrap block
CONFIDENCE: CONFIRMED (100%)
VERIFICATION: 0 decode disagreements (Hitachi manual / Mednafen / Catherine); 0 semantic divergences; 0 oracle state divergences; V-07A transition divergences = 0 across 3 synthetic vectors and real Thor 2 startup; link-isolated 0 interpreter dependencies; V-07B shadow validation PASS (0 divergences across 4 positive vectors, 100% negative control detection across 24 injection cases, complete pre-state storage isolation proven); V-07C authoritative native override PASS (retirements_in_interval = 0, bit-identical cold-boot reproduction, 0 register divergences and 0 cycle drift [delta = 0 at cycle 307090585] vs baseline interpreter at continuation checkpoint 0x06004280, 100% fail-closed fallback under memory corruption).
NEGATIVE EVIDENCE: None
NEXT ACTION: Post-D8 second-pass method execution (ADR D-012 / docs/POST_D8_SECOND_PASS_PLAN.md) and D9 multi-block recompilation scaling.
```

## Public-research address anchors queued for revision validation

Prior public Thor 2 research has reported:

- `0x06009CC4` — debug-related routine;
- `0x002E55A4` — Low Work RAM code;
- `0x002E8A38` — Low Work RAM code.

For the confirmed current substrate:

These public labels/semantics remain revision hints until independently behavior-verified.

## Confirmed Resource & Graphics Architecture (T2-GFX-01)

### 1. Ancient SpriteArchive Architecture & In-Game Loader
- **Format**: 12-byte header (`header_size=12`, `anim_script_offset`, `sprite_data_offset`), 16-bit offset table, 6-byte animation frame records (`[hotspot_x, width_extent, hotspot_y, height_extent, sprite_index]`), and 14-byte sprite descriptor records (`[x_off, width, y_off, height, z_anchor, flags, 0x7FFF]`) preceding uncompressed 4bpp linear VDP1 pixel data.
- **In-Game Loader Routine**: `0TH2.BIN` runtime address `0x060147D4` (`sub_147d4`, file offset `0x0107D4`). Disassembles header into pointer table in RAM:
  - `0x060147D4`: reads `@r5` (12), computes `r5 + 12` (animation offset table pointer);
  - `0x060147DC`: reads `@(r5 + 4)` (`anim_script_offset`), computes `r5 + anim_script_offset` (script pointer);
  - `0x060147F0`: reads `@(r5 + 8)` (`sprite_data_offset`), computes `r5 + sprite_data_offset` (sprite pixel pointer).
- **Confirmed Standalone Packages**: `ARELE.BIN`, `BAW.BIN`, `BRAS.BIN`, `DIT.BIN`, `EFREET.BIN`, `SHADE.BIN`, `P0.BIN`, `P1.BIN`, `P2.BIN`, `P3.BIN` (all 10 verified bit-exact roundtrip, total 2,371,588 bytes).

### 2. Multi-Archive Container MONS.BIN
- **Format**: 50 sector-aligned subarchives (at multiples of 2,048 bytes).
- **Prefix**: 4-byte sector header `[prefix_w0, prefix_w1]` followed immediately by standard 12-byte `SpriteArchive` header (`0x0000000C`, `s_off`, `g_off`).
- **Status**: 48 of 50 confirmed directly as valid `SpriteArchive` instances (1,490,944 bytes).

### 3. VDP2 CRAM Palette Recovery
- **Storage**: Defined in `TH2.LOW` as standard 16-bit RGB555 words:
  - Bank 0: `0x002FCDB6` (file offset `0x22DB6`) -> uploaded to CRAM `0x25F00000` (ANSI/system palette);
  - Bank 1: `0x002FCFB6` (file offset `0x22FB6`) -> uploaded to CRAM `0x25F00400` (Leon Primary Character Palette: `#296B63`, `#311808`, `#5A2921`, `#7B4229`, `#9C5A31`, `#4A4A00`, `#8C8C31`, `#CEB521`, `#DEE763`, `#002963`, `#004AAD`, `#9C9C7B`, `#C6C694`, `#E7E7B5`, `#000000`, `#FFFFEF`);
  - Bank 2: `0x002FD1B6` (file offset `0x231B6`) -> uploaded to CRAM `0x25F00420` (Leon Equipment/Shadow Palette).
- **In-Game Upload Routine**: `0TH2.BIN` runtime `0x0600A9E8`..`0x0600AA1C`.

### 4. VDP1 VRAM Upload Routine
- **Address**: `0TH2.BIN` runtime `0x0600A8A6` (file offset `0x068A6`).
- **Function**: Width/alignment-aware fast memory copy routine transferring character/sprite texture buffers to VDP1 VRAM addresses `0x25C18400`..`0x25C24400`.

### 5. MAP.BIN & SCU DSP Microcode
- **Header**: File offset `0x000000` begins with `0x4453503C` (`DSP<`).
- **Loader**: `0TH2.BIN` runtime `0x060148B6` loads microprogram to SCU Program/Data RAM at `0x25A00000` and activates DSP execution via control registers `0x25A004E0` and `0x25A004E1`.
- **Room Packages**: 45 packages aligned to 11 sectors (22,528 bytes per room), marked by `[ID] 50 3C 00 50 3C 01 50 3C ...`.

### 6. CHR.BIN Differential & Font Structure
- **1bpp Font Sheet**: Starts at `0x29030` in USA and `0x2B030` in RUS.
- **Differential Shift**: Meduza Team inserted Cyrillic font glyphs by shifting all subsequent blocks by exactly `+0x2000` (8,192 bytes / 4 sectors), maintaining identical relative internal layouts.

## Confirmed Universal Decompression & Full Graphics Recovery (T2-GFX-02)

### 1. Universal Ancient Decompressor Routine (`sub_4108`)
- **Location**: `0TH2.BIN` runtime address `0x06004108` (file offset `0x00108`), called from 12 distinct sites including `load_chr` at `0x0600A480`.
- **Calling Convention**: `R4` = pointer to compressed source bitstream, `R5` = pointer to destination uncompressed buffer in Work RAM or VRAM.
- **Control Flow & Bitstream Grammar**:
  - Each sub-block begins with a 16-bit little-endian length word.
  - Byte-oriented command tokens with bitfield dispatch:
    - `token & 0x80`: **Backreference copy**. Base length = `((token & 0x60) >> 5) + 4`, distance = `((token & 0x1F) << 8) | next_byte`. Peek loop: while `(peek & 0xE0) == 0x60`, copies `peek & 0x1F` more bytes from same continuing pointer.
    - `(token & 0xC0) == 0x40`: **RLE fill**. Value = `next_byte`, length = `(token & 0x1F) + 4` or 12-bit extended length if `(token & 0x1F) == 0`.
    - `(token & 0xC0) == 0x00`: **Literal copy**. Length = `token & 0x1F` or 13-bit extended length if `token & 0x1F == 0`.
    - Stream terminator: zero-length sub-block exits.

### 2. Complete CHR.BIN Layout
- **Total Size**: 370,688 bytes (USA: 362,496 bytes). 100% structured.
- **Block Layout**: 12 physical blocks:
  - 11 compressed graphics blocks (Blocks 0..4, 6..11) decompressed via `sub_4108` to VDP1/VDP2 sprite and tile data.
  - 1 uncompressed 1bpp font sheet (Block 5 at `0x29000` USA / `0x2B000` RUS).

### 3. MAP.BIN Decompression & Whole-File Ownership
- **Room Packages**: 45 packages (`00P<`..`44P<`) at 22,528-byte strides. Each decompresses via `sub_4108` to **exactly 49,152 bytes (48 KB)** of VDP2 tile patterns (1,536 8x8 4bpp tiles per room, 2,211,840 bytes total).
- **SCU DSP Microprogram**: 2,048-byte microcode at offset `0x0000`..`0x0800` executes 3D projection and affine transformation matrices for VDP2 RBG0 rotation plane.
- **Whole-File Ownership**: 4,036,608 bytes partitioned into 107 non-overlapping intervals (0 gaps):
  - `VDP2_TILEMAP_PLANE_MATRIX`: 2,351,104 bytes (58.24%) — global 16-bit pattern-name tilemaps and plane grids.
  - `ROOM_COMPRESSED_GRAPHICS`: 928,872 bytes (23.01%) — 45 compressed room packages.
  - `STRUCTURED_MAP_METADATA_UNKNOWN`: 708,608 bytes (17.55%) — non-room metadata tables (triggers, meshes, object tables).
  - `PADDING`: 48,024 bytes (1.19%).

### 4. ED.BIN Ending Graphics Architecture
- **Format**: Uncompressed 8bpp raster illustration container (616,480 bytes, 100% structured).
- **Header & Palettes**: Offset `0x0000`..`0x0820` (2,080 bytes) containing four 256-color RGB555 palettes and frame descriptor table.
- **Image Frames**: Offset `0x0820`..`0x96820` (614,400 bytes) containing 8 full-screen 320x240 8bpp frames (76,800 bytes each). Frames 6 and 7 contain localized text (replaced at `0x72200` in RUS revision).

### 5. P4.BIN Format Resolution
- **Structure**: 2,893-byte SpriteArchive container prefixed with a 4-byte header `4C 0B 20 8B`, followed by canonical 12-byte header (`anim_off=1888`, `sprite_off=2082`, 938 animation offsets). Verified 100% bit-exact roundtrip.

## MAP.BIN Complete Metadata, Room Logic & SCU DSP Recovery (T2-MAP-01)

### 1. 100% Whole-File Interval Ownership V2
- **Total Size**: 4,036,608 bytes. 100% structured (0 unknown bytes, 0 gaps, 107 contiguous intervals).
- **Classification Breakdown**:
  - `VDP2_TILEMAP_PLANE_MATRIX`: 2,351,104 bytes (58.24%) — 104 room pointer table sectors + 1,044 tilemap plane sectors.
  - `ROOM_COMPRESSED_GRAPHICS`: 928,872 bytes (23.01%) — 45 primary room graphics packages.
  - `COLLISION_HEIGHTFIELD`: 555,008 bytes (13.75%) — 12 compressed packages decompressed with `sub_4108` to 48KB collision buffer at `0x060D3D34`.
  - `SECONDARY_VDP2_PLANE`: 153,600 bytes (3.81%) — 5 compressed packages decompressed with `sub_4108` to 48KB VDP2 plane buffer at `0x25E20000`.
  - `PADDING`: 48,024 bytes (1.19%) — sector zero-padding between streams.

### 2. Collision & Walkability Engine
- **Staging RAM**: `0x060D3D34` (High Work RAM).
- **Consumer Routine**: `0x060784B4` (evaluated per-frame for actor movement).
- **Buffer Geometry**: 49,152 bytes = 1,536 tiles $\times$ 32 bytes/tile.
- **Cell Structure**: 8x8 cells per tile; 4-bit nibbles encoding height (0..15) and terrain flags (`WALKABLE`, `BLOCKED_WALL`, `WATER_DEEP`, `LEDGE_JUMP_SOUTH`, `PIT_VOID`, `HAZARD_DAMAGE`).

### 3. Room Headers, Spawns, Triggers, and Exits
- **104 Rooms Analyzed**: Sectors 823..1970 contain 104 pointer table sectors.
- **Record 0**: Room Header & Camera Deadzone descriptor (`width_px`, `height_px`, `cam_mode`, `min_x`, `min_y`, `max_x`, `max_y`).
- **Entity Spawns**: 1,277 entities parsed with $(X, Y, Z)$ spawn coordinates and script IDs, dispatched by `0x06014A94`.
- **Exit / Warp Transitions**: 527 transitions connecting the 104 rooms, validated by `0x0600A416`.
- **Trigger Volumes**: 79 trigger bounding boxes evaluated by `0x0604B070` and dispatched to script handler `0x0601CA56`.

### 4. SCU DSP Microcode Engine
- **Program RAM**: `0x25A00000` (128 instructions, 512 bytes).
- **Transfer Routine**: `0x060799A8` (called at `0x06014886`).
- **Equation**: 60Hz real-time 2D affine transformation matrix ($A, B, C, D, X_0, Y_0$) for VDP2 RBG0 rotation background from camera coordinates ($X, Y, Z, \theta, \phi$) written directly to `0x25E00000`..`0x25E00020`.

## Struct Function Pointer & Callback Recovery (T2-ASM-07)

### 1. Object Instance Taxonomy & Struct Field Layouts
- **6 Concrete Object Archetypes**:
  - `ACTOR_ENTITY`: Player, enemy, NPC, projectile, room object instances (`0x060828CC`, `0x06094F58`, `0x06096504`).
  - `ENGINE_STATE`: Global coordinator singleton at `0x06088D14` referenced across >150 functions.
  - `SCRIPT_VM`: Bytecode execution context with dynamic opcode handlers.
  - `SYSTEM_VECTOR`: Sega Saturn low RAM (`0x06000000`..`0x06004000`) BIOS/SMPC/sound jump vectors.
  - `JUMP_TABLE_DISPATCH`: Indexed branch arrays.
  - `LOCAL_STACK_FRAME`: Stack frame preserved function pointers.
- **15 Struct Callback Fields**: Displacements +0x00 through +0x28 mapped with semantic roles (State action, animation, render, interaction, damage, despawn, secondary action, collision, timer).
- **Static Field Writers**: 427 static field store instructions proved across the binary.
- **Callback Tables**: 808 static function pointer tables cataloged in read-only data pools.

## Procedure Register Provenance & Full Indirect Control-Flow Closure (T2-ASM-08)

### 1. Final 43 Call/Jump Resolution
- **36 Residual JSR Sites**: Verified directly from raw binary bytes via forward reaching-definitions dataflow with SH-2 branch delay slots; proven invariant single targets with zero clobbers.
- **7 Pointer-Table BSRF Decodes Removed**: Proved that the 7 sites (`0x06039ABC`, `0x06039AC0`, `0x06039AC4`, `0x06039ACC`, `0x06039BB8`, `0x06039BC8`, `0x06039EEC`) are data halfwords `0x0603` representing the high 16 bits of 32-bit function pointers in 3 literal pointer tables (`TABLE_06039AA8`, `TABLE_06039BB0`, `TABLE_06039EE8`). Reclassified as `FUNCTION_POINTER_TABLE_DATA`, correcting canonical indirect denominator to **2,226** and canonical BSRF count to **0**.
- **Resolution**: `INDIRECT_CALL_JUMP` reached **100.00%** resolution (1,588 / 1,588).

### 2. PR Lifecycle & Return Domains
- **Path-Sensitive Symbolic Tracking**: Modeled exact $R15$ delta, exact slot $S-4$ spill/reload pairing, and leaf zero PR-write checks across all 638 RTS sites.
- **Audited Caller Domains (Zero Placeholders)**: Disallowed synthetic `CALLERS_OF_*` placeholders. Enforced that an RTS is certified resolved only when incoming callers are bounded concrete static call sites and the function has no open address-taken references.
- **Resolution**: Certified **217 / 638 RTS sites** (34.01%) as `RESOLVED_FINITE_SET`, while honestly retaining 421 sites with open/unmodeled caller domains as `UNRESOLVED`.

### 3. Whole-Module Executable Byte Carving
- Injected only audited JSR targets and certified RTS return domains; protected literal pointer tables as data.
- Retracted 1,292 invalid code bytes from pre-audit overpromotion back to UNKNOWN/DATA.
- Reduced executable UNKNOWN bytes by **-66,203 bytes** (from 1,251,863 baseline down to 1,185,660).
- Confirmed code bytes established at 156,238 bytes across all modules.

## Residual RTS Caller-Domain Closure, Address-Taken Function Recovery & Control-Flow Proof (T2-ASM-09)

### 1. Canonical Indirect Inventory Audit
- Re-audited the legitimacy of the entire 2,226 canonical indirect site inventory (1,465 JSR, 121 JMP, 2 BRAF, 638 RTS).
- Confirmed that 2,226 / 2,226 reside entirely within `CONFIRMED_CODE` with zero `PROVEN_DATA` or `PROVEN_PADDING` overlap.
- Confirmed that the 7 false BSRF sites remain quarantined as `FUNCTION_POINTER_TABLE_DATA` with 0 false instruction decodes.

### 2. Address-Taken Function Reference Recovery & Operational Sinks
- Analyzed all 421 residual RTS sites from T2-ASM-08: 340 `ADDRESS_TAKEN_UNBOUNDED` and 81 `FUNCTION_BOUNDARY_AMBIGUOUS`.
- Proved that the T2-ASM-08 heuristic ("any literal reference forces caller domain incomplete") was overly conservative: 340 of those sites had fully balanced stack frames and verified PR paths.
- Indexed all 1,206 references to residual RTS functions across the binary:
  - **838 references** were literal pool entries loaded by already-resolved JSR instructions (`REACHES_PROVEN_CALL_SITE`).
  - **264 references** were static non-call data (entity configuration templates, save structure descriptors, sprite tables) that are never dispatched as call targets (`NONCALL_REFERENCE`).
  - Only **104 references** remained truly open or ambiguous (`DOMAIN_OPEN`).

### 3. Call-Sink vs Data Table Invariant (Rule #5)
- Disallowed data table addresses as call edge sources: In SH-2, CPU instructions execute in CODE. Data tables store pointers. PR is loaded with `PC + 4` of the call instruction (`JSR @Rn` or `BSR`), NEVER `table_address + 4`.
- Replaced table addresses with their genuine consumer JSR instructions (e.g. `0x060044A6`), ensuring return PCs point strictly into executable code.

### 4. Closed-World Theorem & UNKNOWN Threat Accounting
- A closed-world proof over currently decoded call sites is invalid if UNKNOWN regions can harbor executable call instructions.
- Partitioned UNKNOWN regions:
  - 0TH2.BIN + TH2.LOW: 511,452 SH-2 UNKNOWN bytes.
  - BGM.BIN: 673,762 M68K sound processor UNKNOWN bytes.
- Audited all 309 functions owning residual RTS sites against UNKNOWN regions for direct branch displacements (`BSR`, `BRA`) and 32-bit absolute function pointers:
  - **252 functions** are proven 100% threat-free from UNKNOWN regions.
  - **57 functions** have potential caller threats in UNKNOWN regions, correctly blocking caller closure fail-closed.

### 5. Final Control-Flow Resolution & Partition V2
- **RTS Resolution**: Certified **456 / 638 RTS sites** (71.47%) as resolved (253 exact single return, 203 finite set).
- **Residual Unresolved RTS**: Reduced from **421 down to 182** (net reduction of 239 sites; 81 UNRESOLVED_EXTERNAL_ENTRY, 81 UNRESOLVED_PR_PATH, 20 UNRESOLVED_CALLER_DOMAIN).
- **Overall Canonical Indirect Resolution**: **2,044 / 2,226 (91.82%)** (1,588 / 1,588 call/jump [100.0%], 456 / 638 RTS [71.47%]).
- **CFG Reclosure V2**: Injected certified return targets into CFG closure worklist:
  - `CONFIRMED_CODE`: Expanded from 156,238 to **156,694 bytes** (+456 bytes).
  - `PROVEN_DATA`: **55,900 bytes**.
  - `PROVEN_PADDING`: **59,344 bytes**.
  - `UNKNOWN`: Reduced from 1,185,660 to **1,185,214 bytes** (-446 bytes).
  - Total binary bytes: 1,457,152 bytes (exact arithmetic balance across all 4 modules).
- **Negative Controls**: 58 / 58 PASS (including 8 new P8 controls NC-AQ .. NC-AX in `tests/asm/negative_controls_p8.py`).

## Record template

For each new finding record:

```text
ID:
STATUS:
REVISION/HASH:
DISC FILE:
FILE RANGE:
RUNTIME RANGE:
CPU:
MODULE/GENERATION:
STATIC EVIDENCE:
DYNAMIC EVIDENCE:
READS/WRITES:
CONTROL FLOW:
HARDWARE INTERACTION:
HYPOTHESIS:
CONFIDENCE:
VERIFICATION:
NEGATIVE EVIDENCE:
NEXT ACTION:
```
