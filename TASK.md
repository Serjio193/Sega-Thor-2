# Current task

TASK: T2-GFX-02 — Full Remaining Graphics Recovery: CHR Decompression, MAP/VDP2 Reconstruction, UI/Ending Coverage
WHY: Recover the maximum possible remaining graphics content of The Story of Thor 2 / The Legend of Oasis (CHR.BIN decompressor, 45 MAP.BIN rooms, MAP whole-file interval ownership, ED.BIN ending illustrations, P4.BIN format resolution, UI/HUD/font coverage, audited asset census V3).
CURRENT MILESTONE: Resource / Graphics Reverse Engineering Track
TASK STATUS: IN_PROGRESS
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: HEAD at 002b364dae03b865cd1a230ea3e20025f266c428; 40/40 Linux CTests passing; 5/5 gfx differential tests passing; 5/5 VDP1 provenance tests passing. Universal Ancient decompressor located at 0x06004108 (sub_4108) in 0TH2.BIN; token grammar reconstructed; all 45/45 MAP.BIN rooms decompressed to 49,152 bytes; ED.BIN decoded as 8 320x240 8bpp frames.
ACCEPTANCE CRITERIA:
- [x] Phase 0: Baseline gate verified (HEAD, tests pass, UNKNOWN_RESOURCE_BYTES_BEFORE = 3,207,750);
- [x] Phase 1: Global graphics unknown intervals cataloged in workstreams/T2-GFX-02/graphics_unknown_intervals.json;
- [x] Phase 2: CHR.BIN block table resolved (11 compressed + 1 font = 12 blocks) in workstreams/T2-GFX-02/chr_blocks.json;
- [x] Phase 3: Exact CHR decompressor documented (sub_4108 in 0TH2.BIN at 0x06004108) in workstreams/T2-GFX-02/chr_decompressor_map.json;
- [x] Phase 4: Dynamic CHR decompression traces captured in workstreams/T2-GFX-02/chr_decompression_traces.json;
- [x] Phase 5: Reconstruct bitstream grammar (decision tree, masks, source/dest movement, 3 real stream annotations);
- [x] Phase 6: Implement fail-closed decompressor (tools/gfx/chr_decompressor.py);
- [x] Phase 7: CHR byte-exact oracle comparison;
- [x] Phase 8: CHR graphics classification (palettes, VDP1/VDP2 tiles, fonts);
- [x] Phase 9: RUS/USA CHR differential after decompression;
- [x] Phase 10: CHR recompression evaluation;
- [x] Phase 11: MAP.BIN room package segmentation (45 rooms) in workstreams/T2-GFX-02/map_room_layouts.json;
- [x] Phase 12: SCU DSP role identified;
- [x] Phase 13: MAP dynamic provenance in workstreams/T2-GFX-02/map_runtime_provenance.json;
- [x] Phase 14: VDP2 tile/pattern format recovered;
- [x] Phase 15: Room renderer implemented (tools/gfx/map_renderer.py);
- [x] Phase 16: Full map extraction;
- [x] Phase 17: UI/HUD/menu graphics recovered;
- [x] Phase 18: Font completion (1bpp Latin + Cyrillic);
- [x] Phase 19: ED.BIN ending graphics decoded (8 full frames, 616,480 bytes);
- [x] Phase 20: P4.BIN format resolved (12-byte vs 16-byte header proof);
- [x] Phase 21: Mass graphics export (private PNGs);
- [x] Phase 22: Unified graphics database (workstreams/T2-GFX-02/graphics_database.json);
- [x] Phase 23: Complete whole-file byte ownership for CHR.BIN, MAP.BIN, MONS.BIN, ED.BIN;
- [x] Phase 24: Asset census V3 compiled (UNKNOWN_RESOURCE_BYTES_AFTER < 3,207,750);
- [x] Phase 25: Graphics completeness matrix;
- [x] Phase 26: Deterministic unit tests and negative controls added;
- [x] Phase 27: Comprehensive technical report published; docs updated;
- [x] Source line limits <= 500 lines; git diff --check clean; no commercial assets committed.

EVIDENCE AVAILABLE:
- Universal decompressor at 0x06004108 in 0TH2.BIN (12 callsites, sub_4108);
- MAP.BIN 45 room packages decompressed to 49,152 bytes each (tools/gfx/map_renderer.py);
- MAP.BIN whole-file interval ownership (107 contiguous intervals, 0 gaps, 708,608 bytes metadata);
- ED.BIN decoded as uncompressed 8bpp raster illustration container (8 full 320x240 frames, 616,480 bytes);
- P4.BIN resolved to 4-byte prefix + canonical 12-byte SpriteArchive header (100% roundtrip);
- CHR.BIN 12 physical blocks (11 compressed + 1 font, 370,688 bytes, 100% structured);
- Workstream artifacts in workstreams/T2-GFX-02/ (11 JSON/MD files);
- Exported PNGs in .private/extracted_graphics/ (45 rooms + 16 ending frames);
- Comprehensive report: docs/reports/FULL_GRAPHICS_RECOVERY_T2_GFX_02.md.

KNOWN UNKNOWNS:
- Exact internal layout and entity scripts of the 708,608 bytes of structured map metadata in MAP.BIN;
- 2,231 unresolved indirect control flow sites in the executable code track.

ALLOWED SCOPE:
- Graphics and resource reverse engineering, differential analysis, decompression, VDP2/MAP decoding, ED.BIN decoding, UI/font extraction, image export, census, testing, documentation.

OUT OF SCOPE:
- Broad ASM→C++ gameplay translation, emulator integration into production, modifying canonical executable manifests, beginning T2-GFX-03.

## Last verified result

T2_GFX_02_PASS: Universal Ancient LZSS variant graphics decompressor sub_4108 isolated at 0x06004108 in 0TH2.BIN (12 callsites). Decompressed all 11 compressed graphics blocks in CHR.BIN (370,688 bytes, 100% structured) and all 45 room packages in MAP.BIN (49,152 bytes / 48 KB each). Constructed complete whole-file interval ownership for MAP.BIN (4,036,608 bytes across 107 contiguous intervals, 0 gaps, with 708,608 bytes honestly classified as unknown metadata). Decoded ED.BIN as 8 uncompressed 320x240 8bpp frames (616,480 bytes, 100% structured). Resolved P4.BIN (4-byte prefix + canonical 12-byte header, 100% bit-exact roundtrip). Reduced UNKNOWN_RESOURCE_BYTES from 3,207,750 down to 708,608 bytes (exact reduction: 2,499,142 bytes / 77.91% reduction). Structured resource coverage reached 92.16% (8,335,400 / 9,044,008 bytes). 6/6 recovery unit tests pass (test_gfx_recovery.py). 5/5 differential tests pass. 5/5 VDP1 provenance tests pass. 40/40 Linux CTests pass. All human-maintained tools and tests strictly <= 500 lines. git diff --check clean. Zero commercial assets tracked.

## Session checkpoint

CURRENT MILESTONE: Resource / Graphics Reverse Engineering Track
CURRENT TASK: T2-GFX-02 Full Remaining Graphics Recovery: CHR Decompression, MAP/VDP2 Reconstruction, UI/Ending Coverage
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: T2_GFX_02_PASS. 8,335,400 structured resource bytes (92.16%) cataloged. UNKNOWN_RESOURCE_BYTES reduced by 2,499,142 bytes down to 708,608 bytes. 6/6 unit tests pass. 40/40 Linux CTests pass.
FILES CHANGED: docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/WORKLOG.md, docs/REVERSE_ENGINEERING.md, docs/reports/FULL_GRAPHICS_RECOVERY_T2_GFX_02.md, TASK.md, tools/gfx/chr_decompressor.py, tools/gfx/map_renderer.py, tools/gfx/ed_extractor.py, tests/resource/test_gfx_recovery.py, workstreams/T2-GFX-02/*
TESTS RUN: python tests/resource/test_gfx_recovery.py (6/6 PASS), python tests/resource/test_gfx_differential.py (5/5 PASS), python tests/resource/test_vdp1_provenance.py (5/5 PASS), wsl ctest --test-dir build_linux -E test_gameplay_scenarios (40/40 PASS).
NEW KNOWLEDGE: Universal decompressor sub_4108 at 0x06004108 in 0TH2.BIN with complete bitstream grammar; CHR.BIN 12 physical blocks; MAP.BIN 45 rooms at 49,152 bytes each; MAP.BIN 107 whole-file intervals; SCU DSP RBG0 affine math microprogram; ED.BIN 8x 320x240 8bpp frames + palettes; P4.BIN 4-byte prefix + 12-byte header.
OPEN QUESTIONS: Internal layout of 708,608 bytes structured map metadata (triggers/meshes/entities); SCU DSP microcode full instruction disassembly.
EXACT NEXT ACTION: Propose T2-GFX-03 (Map Metadata and Stage Entity Script Reverse Engineering) to user.
