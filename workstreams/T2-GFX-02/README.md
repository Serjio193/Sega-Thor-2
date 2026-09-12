# Workstream T2-GFX-02 — Full Remaining Graphics Recovery

This workstream establishes the complete recovery, decompression, and whole-file ownership of the remaining visual assets of **The Story of Thor 2 / The Legend of Oasis**.

## Major Discoveries and Results

1. **Universal Ancient Decompressor (`sub_4108` at `0x06004108`)**:
   - Discovered in `0TH2.BIN` at runtime address `0x06004108` (file offset `0x00108`).
   - Implemented in `tools/gfx/chr_decompressor.py` with strict fail-closed guards.
   - Command grammar reconstructed: 16-bit LE sub-block length, token byte with bit 7 (LZSS backreference with chained copy extension), bit 6 (RLE fill), and bits 7/6 clear (Literal stream).
   - Proven to power both `CHR.BIN` (11 compressed blocks) and `MAP.BIN` (all 45 room packages).

2. **`CHR.BIN` Block Architecture (12 Physical Blocks)**:
   - Resolved the 11 vs 12 block ambiguity: exactly 11 compressed graphics/palette blocks (Blocks 0..4 and 6..11) and 1 uncompressed 1bpp font block (Block 5 / Font 0 at sector 0x29000 USA / 0x2B000 RUS).
   - 100% of `CHR.BIN` bytes are structured (256,828 compressed bytes + 98,304 font bytes + 15,556 alignment padding = 370,688 bytes).

3. **`MAP.BIN` Room Decompression & Whole-File Ownership**:
   - All 45 room packages decompressed cleanly via `sub_4108`, each producing exactly 49,152 bytes (48 KB) of VDP2 tile patterns and structures (totaling 2,211,840 decompressed room bytes).
   - Whole-file ownership partitioned into 107 contiguous, non-overlapping intervals:
     - `VDP2_TILEMAP_PLANE_MATRIX`: 2,351,104 bytes (58.24%) — global 16-bit pattern-name tilemaps and plane grids.
     - `ROOM_COMPRESSED_GRAPHICS`: 928,872 bytes (23.01%) — all 45 room packages.
     - `STRUCTURED_MAP_METADATA_UNKNOWN`: 708,608 bytes (17.55%) — non-room metadata tables between packages.
     - `PADDING`: 48,024 bytes (1.19%) — sector alignment padding.
   - All 45 rooms rendered to offline PNG tile sheets via `tools/gfx/map_renderer.py`.

4. **`ED.BIN` Ending Artwork Recovery**:
   - Completely decoded as an uncompressed 8bpp raster illustration package.
   - Contains 2,080 bytes of RGB555 palette/descriptor headers followed by exactly 8 full-screen 320x240 8bpp frames (76,800 bytes each = 614,400 bytes, total 616,480 bytes = 100% structured).
   - Russian localization differential isolated: Frames 0..5 bit-identical; Frames 6..7 contain translated Cyrillic epilogue text starting at offset `0x72200`.
   - All 16 ending frames (8 USA + 8 RUS) rendered to PNG via `tools/gfx/ed_extractor.py`.

5. **`P4.BIN` Container Resolution**:
   - Proved to be a canonical `SpriteArchive` preceded by a 4-byte container prefix (`4C 0B 20 8B`).
   - Header at offset +4 has `header_size = 12`, `anim_script_offset = 1888`, `sprite_data_offset = 2082`.
   - Verified 100% bit-exact roundtrip (`roundtrip=True`).

6. **Audited Asset Census V3**:
   - `STRUCTURED_RESOURCE_BYTES_BEFORE`: 5,836,258 (64.53%)
   - `STRUCTURED_RESOURCE_BYTES_AFTER`: 8,335,400 (92.16%)
   - `UNKNOWN_RESOURCE_BYTES_BEFORE`: 3,207,750
   - `UNKNOWN_RESOURCE_BYTES_AFTER`: 708,608
   - `EXACT_UNKNOWN_BYTE_REDUCTION`: **2,499,142 bytes** (77.91% reduction of remaining unknowns).

## Workstream Artifacts

- `chr_blocks.json`: Detailed specification of all 12 physical blocks in `CHR.BIN`.
- `chr_decompressor_map.json`: Reverse engineering record of `sub_4108` and calling conventions.
- `chr_decompression_traces.json`: Runtime-correlated decompression traces across title, UI, and stages.
- `map_room_layouts.json`: Census and byte bounds of all 45 room packages in `MAP.BIN`.
- `map_interval_ownership.json`: Exact whole-file interval ownership map for `MAP.BIN` (107 intervals).
- `map_runtime_provenance.json`: VRAM and CRAM mapping for representative rooms.
- `ed_bin_metadata.json`: Ending illustration geometry, palettes, and localization differential.
- `graphics_unknown_intervals.json`: Inventory of the 17 remaining non-room metadata intervals in `MAP.BIN`.
- `byte_ownership.json`: Byte ownership breakdown across `CHR.BIN`, `MAP.BIN`, `ED.BIN`, `MONS.BIN`, and `P4.BIN`.
- `asset_census_v3.json`: Audited resource classification metrics.
- `graphics_database.json`: Unified graphics asset registry.
