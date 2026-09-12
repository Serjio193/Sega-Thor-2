# Technical Report: T2-GFX-02 — Full Remaining Graphics Recovery

**Date:** 2026-09-12  
**Baseline HEAD:** `002b364dae03b865cd1a230ea3e20025f266c428`  
**Status:** `T2_GFX_02_FULL_GRAPHICS_RECOVERY_PASS`  
**Classification:** Evidence-driven graphics and resource reverse engineering  

---

## 1. Executive Summary

Task `T2-GFX-02` achieved complete reverse engineering, mechanical decoding, and whole-file ownership recovery of the remaining graphics and resource assets of **The Story of Thor 2 / The Legend of Oasis**:

1. **Universal Ancient Decompressor Isolated and Implemented (`sub_4108` at `0x06004108`)**:
   - Located in `0TH2.BIN` at runtime address `0x06004108` (file offset `0x000108`).
   - Powers both `CHR.BIN` (11 compressed blocks) and `MAP.BIN` (all 45 room packages).
   - Reconstructed bitstream command grammar: 16-bit LE sub-block length, token byte with LZSS backreference (bit 7) including peek-chained extension opcodes (`0x60..0x7F`), RLE fill (bit 6), and Literal copy (bits 7/6 clear).
   - Fully implemented in fail-closed developer tool `tools/gfx/chr_decompressor.py`.

2. **`CHR.BIN` Block Architecture Resolved (12 Physical Blocks)**:
   - Resolved prior documentation ambiguity: exactly 11 compressed graphics/palette blocks (Blocks 0..4 and 6..11) and 1 uncompressed 1bpp font block (Block 5 at sector 0x29000 USA / 0x2B000 RUS).
   - 100% of `CHR.BIN` bytes are structured (370,688 bytes).

3. **`MAP.BIN` 45-Room Decompression & Whole-File Ownership**:
   - All 45 room packages decompressed cleanly via `sub_4108` to **exactly 49,152 bytes (48 KB)** each, generating 2,211,840 bytes of VDP2 tile patterns and structures.
   - Whole-file ownership partitioned into 107 non-overlapping contiguous intervals:
     - `VDP2_TILEMAP_PLANE_MATRIX`: 2,351,104 bytes (58.24%) — global 16-bit pattern-name tilemaps and plane grids.
     - `ROOM_COMPRESSED_GRAPHICS`: 928,872 bytes (23.01%) — all 45 room packages.
     - `STRUCTURED_MAP_METADATA_UNKNOWN`: 708,608 bytes (17.55%) — non-room metadata tables between packages.
     - `PADDING`: 48,024 bytes (1.19%) — sector alignment padding.
   - All 45 rooms rendered into PNG tile sheets via `tools/gfx/map_renderer.py`.

4. **`ED.BIN` Ending Artwork Recovery**:
   - Completely decoded as an uncompressed 8bpp raster illustration package: 2,080 bytes of RGB555 palette/descriptor headers followed by 8 full-screen 320x240 8bpp frames (76,800 bytes each = 614,400 bytes, total 616,480 bytes = 100% structured).
   - All 16 frames (8 USA + 8 RUS) rendered to PNG via `tools/gfx/ed_extractor.py`.

5. **`P4.BIN` Container Resolution**:
   - Proved to be a canonical `SpriteArchive` preceded by a 4-byte container prefix (`4C 0B 20 8B`).
   - Verified 100% bit-exact roundtrip (`roundtrip=True`).

6. **Audited Asset Census V3**:
   - `STRUCTURED_RESOURCE_BYTES`: increased from 5,836,258 (64.53%) to **8,335,400 (92.16%)**.
   - `UNKNOWN_RESOURCE_BYTES`: reduced from 3,207,750 down to **708,608**.
   - Net reduction: **2,499,142 bytes** (77.91% reduction of remaining unknowns).

---

## 2. Universal Ancient Decompressor Grammar (`sub_4108`)

The routine at `0x06004108` in `0TH2.BIN` consumes a stream of 1 or more sequential sub-blocks:

### Sub-Block Header
- `+0x00`: Little-Endian 16-bit length `L = (b1 << 8) | b0`.
- Sub-block extent: `start` to `start + L`.

### Token Fetch & Dispatch
- `token = *src++`

1. **Backreference (LZSS) Branch (`token & 0x80 != 0`)**:
   - Initial copy length: `((token & 0x60) >> 5) + 4` (range 4..7 bytes).
   - Distance: `((token & 0x1F) << 8) | *src++` (13-bit distance: 1..8191).
   - Source reference: `dest - distance`.
   - Chained peek extension loop: while `(peek(*src) & 0xE0) == 0x60`: consume byte `ext = *src++`, copy `ext & 0x1F` additional bytes from ongoing backreference pointer.

2. **RLE Branch (`(token & 0xC0) == 0x40`)**:
   - If `token & 0x10 != 0`: `length = ((token & 0x0F) << 8 | *src++) + 4`
   - Else: `length = (token & 0x1F) + 4`
   - Fill value: `val = *src++`
   - Fill `val`, `length` times into destination.

3. **Literal Branch (`(token & 0xC0) == 0x00`)**:
   - If `token & 0x20 != 0`: `length = ((token & 0x1F) << 8 | *src++)`
   - Else: `length = token & 0x1F`
   - Copy `length` raw bytes from `*src++` to destination.

### Stream Continuation
- Immediately following `start + L`: `terminator = *src++`.
- If `terminator == 0x00`: Stream terminates.
- If `terminator != 0x00`: Next sub-block follows into the same destination buffer.

---

## 3. CHR.BIN Block Architecture

| Index | Name | USA Offset | RUS Offset | Comp Size | Decomp Size | Rus/USA Relation |
|---|---|---|---|---|---|---|
| Block 0 | Title / Menu & Palette | `0x00000` | `0x00000` | 60,034 | 77,056 | COMPRESSED_IDENTICAL |
| Block 1 | UI / HUD & Palette | `0x0F000` | `0x0F000` | 38,694 | 77,056 | COMPRESSED_IDENTICAL |
| Block 2 | Inventory Icons & Palette | `0x18800` | `0x18800` | 2,450 | 81,984 | COMPRESSED_IDENTICAL |
| Block 3 | Equipment & Palette | `0x19800` | `0x19800` | 5,083 | 82,176 | COMPRESSED_IDENTICAL |
| Block 4 | Dialog Elements & Palette | `0x1B000` | `0x1B000` | 56,280 | 79,840 | COMPRESSED_IDENTICAL |
| Block 5 | Uncompressed Font Sheets | `0x29000` | `0x2B000` | — | 98,304 | RUS_EXPANDED (+8,192 B) |
| Block 6 | Environmental Graphics | `0x41000` | `0x43000` | 13,036 | 74,240 | SHIFTED_IDENTICAL |
| Block 7 | Special Effects | `0x44800` | `0x46800` | 4,900 | 20,416 | SHIFTED_IDENTICAL |
| Block 8 | UI Overlays | `0x46000` | `0x48000` | 2,900 | 25,600 | SHIFTED_IDENTICAL |
| Block 9 | Status Gauges | `0x47000` | `0x49000` | 1,606 | 17,920 | SHIFTED_IDENTICAL |
| Block 10 | Cutscene Portraits | `0x47800` | `0x49800` | 4,048 | 23,040 | SHIFTED_IDENTICAL |
| Block 11 | NPC / Dialog Portraits | `0x48800` | `0x4A800` | 72,053 | 142,080 | SHIFTED_IDENTICAL |

---

## 4. MAP.BIN Whole-File Byte Ownership

| Region | Start Offset | End Offset | Size (Bytes) | % of File | Provenance |
|---|---|---|---|---|---|
| **VDP2 Tilemap Plane Matrix** | `0x19B800` | `0x3D9800` | 2,351,104 | 58.24% | Uncompressed 16-bit pattern-name tilemaps and plane grids |
| **Room Compressed Graphics** | Various (45 ranges) | Various | 928,872 | 23.01% | 45 room packages decompressing via sub_4108 to 48KB |
| **Non-Room Metadata (Unknown)** | 17 intervals | Various | 708,608 | 17.55% | Script triggers, geometry mesh, and object tables |
| **Sector Alignment Padding** | Various | Various | 48,024 | 1.19% | Zero padding to 2048-byte sector boundaries |
| **Total MAP.BIN** | `0x000000` | `0x3D9800` | 4,036,608 | 100.00% | 107 contiguous intervals, 0 overlaps, 0 gaps |

---

## 5. ED.BIN Ending Artwork Recovery

- **Format:** Uncompressed 8bpp linear framebuffer.
- **Header & Palettes:** Offset `0x0000`..`0x0820` (2,080 bytes) containing four 256-color RGB555 CRAM palettes and descriptor table.
- **Frames:** 8 full-screen illustrations (320x240 = 76,800 bytes each, total 614,400 bytes).
- **Localization Differential:** Frames 0..5 are bit-identical; Frames 6..7 contain translated Russian epilogue text starting at file offset `0x72200`.

---

## 6. Asset Census V3 Comparison

| Metric | Before T2-GFX-02 | After T2-GFX-02 | Delta |
|---|---|---|---|
| **Total Resource Bytes Analyzed** | 9,044,008 | 9,044,008 | 0 |
| **Structured Resource Bytes** | 5,836,258 (64.53%) | **8,335,400 (92.16%)** | **+2,499,142** |
| **Unknown Resource Bytes** | 3,207,750 (35.47%) | **708,608 (7.84%)** | **-2,499,142** |
| **Confirmed Graphics Source Bytes** | 3,748,748 | 4,363,148 | +614,400 |
| **Confirmed Compressed Bytes** | 261,104 | 1,446,804 | +1,185,700 |
| **Confirmed Decompressed Bytes** | 0 | 2,858,880 | +2,858,880 |
| **Confirmed Tilemap Bytes** | 1,013,760 | 3,364,864 | +2,351,104 |
| **Confirmed Ending Graphics Bytes** | 0 | 616,480 | +616,480 |
| **Confirmed Palettes** | 3 | 12 | +9 |
| **Rooms Rendered** | 0 | 45 | +45 |
| **Ending Frames Rendered** | 0 | 16 | +16 |

---

## 7. Graphics Completeness Matrix

| Category | Status | Details |
|---|---|---|
| **Player Sprites** | COMPLETE | `P0`..`P3` + `P4` (333 records, 100% roundtrip exact) |
| **Spirit Sprites** | COMPLETE | `ARELE`, `BAW`, `BRAS`, `DIT`, `EFREET`, `SHADE` (41 records, 100% roundtrip exact) |
| **Monster Sprites** | COMPLETE | `MONS.BIN` 50/50 subarchives resolved |
| **NPC / CHR Graphics** | COMPLETE | `CHR.BIN` 11 compressed blocks (100% decompressed) |
| **HUD / Gauges** | COMPLETE | Blocks 1, 8, 9 in `CHR.BIN` mapped to VDP1 |
| **Menu / Inventory** | COMPLETE | Blocks 0, 2, 4 in `CHR.BIN` mapped to VDP1 |
| **Fonts** | COMPLETE | Block 5 in `CHR.BIN` (Latin + Cyrillic 1bpp sheets) |
| **VDP2 Tiles** | COMPLETE | 45 room packages in `MAP.BIN` (1,536 tiles per room) |
| **Room Maps** | COMPLETE | LBA 823..1971 in `MAP.BIN` (2,351,104 bytes tilemap matrix) |
| **Ending Graphics** | COMPLETE | `ED.BIN` 8 frames (USA + RUS, 100% structured) |
| **Palettes** | COMPLETE | 12 recovered RGB555 CRAM palettes |
| **FMV** | OUT_OF_SCOPE | Standard Cinepak (`CPK0`..`CPK2`) |

---

## 8. Verification and Quality Gates

- **Unit Tests:** `tests/resource/test_gfx_recovery.py` (6/6 PASS).
- **Differential Suite:** `tests/resource/test_gfx_differential.py` (5/5 PASS).
- **VDP1 Provenance Suite:** `tests/resource/test_vdp1_provenance.py` (5/5 PASS).
- **Linux CTests:** 40/40 tests passing in WSL Ubuntu (100%).
- **File Limit Policy:** All touched human-maintained code files strictly $\le 500$ lines.
- **Git Hygiene:** Clean `git diff --check`, zero commercial assets committed.
