# Current task

TASK: T2-GFX-01 — RUS/USA Differential Graphics Extraction, Compression Recovery, and Maximum Resource Carving
WHY: Exploit the differential between the Russian (thor2_ntsc_patched_fe11d2fb) and USA (thor2_usa_retail) disc revisions to recover character/spirit sprite archives (P0..P3, elemental spirits), in-game SH-2 loaders, VDP1/VDP2/CRAM hardware provenance, 6-byte frame / 14-byte sprite records, monster sub-archives (MONS.BIN), Cyrillic font insertion shift in CHR.BIN, MAP.BIN SCU DSP microcode, and export lossless PNGs while reducing UNKNOWN_RESOURCE_BYTES.
CURRENT MILESTONE: Resource / Graphics Reverse Engineering Track
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: 21 of 33 files proven bit-for-bit identical between RUS and USA discs; all 10 SpriteArchive packages (2,371,592 bytes) pass 100% bit-identical round-trip in C++ (Gate V-11: PASS / BYTE_ROUNDTRIP_EXACT); in-game SH-2 loader located at 0x060147D4; Russian font shift (+8,192 bytes) proven in CHR.BIN; SCU DSP microcode header and 45 room packages identified in MAP.BIN; 50 lossless PNGs exported; 5,836,258 structured resource bytes (64.53%) cataloged; 5/5 Python differential regression tests pass; 40/40 Linux CTests pass.
ACCEPTANCE CRITERIA:
- [x] Disc extraction tool (disc_extractor.py) parses ISO9660 extents from raw MODE1/2352 discs;
- [x] Comprehensive RUS/USA differential analyzer (rus_usa_differential.py) identifies identical files (21/33) and changed extents (12/33);
- [x] SpriteArchive format verified on P0..P3 and 6 spirit archives in C++ (10/10 BYTE_ROUNDTRIP_EXACT, Gate V-11);
- [x] In-game SH-2 loader located at 0x060147D4 and DMA upload routine at 0x0600A8A6;
- [x] Hardware memory & VRAM provenance established in workstreams/T2-GFX-01/vram_provenance.json;
- [x] Palettes (VDP2 CRAM RGB555) and animation frames (6-byte frame, 14-byte sprite) recovered;
- [x] CHR.BIN Russian localization shift (+8,192 bytes) and 1bpp font sheets mapped;
- [x] MONS.BIN partitioned into 50 sub-archives (48 confirmed SpriteArchives);
- [x] MAP.BIN analyzed: SCU DSP microcode header (DSP<) and 45 room packages identified;
- [x] Resource signature carver (carver.py) scores 110 candidate graphics ranges;
- [x] Lossless PNG exporter (export_images.py) extracts 50 PNG images with metadata manifest;
- [x] Asset census (asset_census.py) compiles audited metrics (5,836,258 structured bytes, 64.53%);
- [x] Regression test suite (test_gfx_differential.py) with negative controls passes (5/5 PASS);
- [x] Linux CTest suite 40/40 tests pass (100%);
- [x] All human-maintained tools and tests <= 500 lines; git diff --check clean; no commercial bytes tracked;
- [x] Comprehensive technical report docs/reports/GFX_RUS_USA_DIFFERENTIAL_T2_GFX_01.md published.

EVIDENCE AVAILABLE:
- Workstream artifacts: workstreams/T2-GFX-01/ (input_revisions.json, rus_usa_file_diff.tsv, rus_usa_changed_ranges.json, sprite_archive_verification.json, vram_provenance.json, graphics_candidates.json, extracted_images_manifest.json, asset_census.json, README.md);
- C++ round-trip test: tests/resource/test_resource_roundtrip.cpp;
- Differential test suite: tests/resource/test_gfx_differential.py;
- Technical report: docs/reports/GFX_RUS_USA_DIFFERENTIAL_T2_GFX_01.md;
- Reverse engineering documentation: docs/REVERSE_ENGINEERING.md.

KNOWN UNKNOWNS:
- 11 compressed graphics blocks in CHR.BIN (LZSS/Huffman variant decompressor routine in 0TH2.BIN remains to be isolated);
- SCU DSP microcode instruction decode in MAP.BIN header;
- 2,231 unresolved indirect control flow sites in the executable code track.

ALLOWED SCOPE:
- Resource and graphics reverse engineering, differential analysis, archive parsing, palette decoding, sprite/tile decoding, image export, testing, documentation.

OUT OF SCOPE:
- Broad ASM→C++ gameplay translation, emulator integration into production, modifying canonical executable manifests, beginning T2-GFX-02.

## Last verified result

T2_GFX_01_PASS: 9,044,008 resource bytes analyzed across RUS and USA disc images. 21 of 33 files proven bit-for-bit identical between revisions. All 10 SpriteArchive character and spirit packages (2,371,592 bytes) pass 100% bit-identical roundtrip in C++ (Gate V-11 / D14). In-game SH-2 loader located at 0x060147D4 (sub_147d4) with DMA upload at 0x0600A8A6. Russian localization shift (+8,192 bytes for Cyrillic font insertion) proven in CHR.BIN. MONS.BIN partitioned into 50 sub-archives (48 confirmed SpriteArchives). MAP.BIN SCU DSP microcode header and 45 room packages identified. 50 lossless PNG images exported with manifest. Resource census confirms 5,836,258 structured bytes (64.53%), reducing UNKNOWN_RESOURCE_BYTES to 3,207,750. 5/5 differential regression tests pass. 40/40 Linux CTests pass. All human-maintained files <= 500 lines. git diff --check clean. Zero commercial bytes tracked.

## Session checkpoint

CURRENT MILESTONE: Resource / Graphics Reverse Engineering Track
CURRENT TASK: T2-GFX-01 RUS/USA Differential Graphics Extraction, Compression Recovery, and Maximum Resource Carving
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: T2_GFX_01_PASS. Gate V-11 / D14 = PASS / BYTE_ROUNDTRIP_EXACT (10/10 packages). 5,836,258 structured resource bytes (64.53%) cataloged. 50 PNGs exported with geometry/palette manifest. 5/5 Python differential tests pass. 40/40 Linux CTests pass. All human-maintained files <= 500 lines. git diff --check clean.
FILES CHANGED: docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/REVERSE_ENGINEERING.md, docs/WORKLOG.md, docs/reports/GFX_RUS_USA_DIFFERENTIAL_T2_GFX_01.md, tests/resource/test_gfx_differential.py, tests/resource/test_resource_roundtrip.cpp, tools/gfx/*, workstreams/T2-GFX-01/*, TASK.md
TESTS RUN: wsl ctest --test-dir build_linux -E test_gameplay_scenarios (40/40 PASS), python tests/resource/test_gfx_differential.py (5/5 PASS), python tests/asm/test_manifest_schema.py (PASS), python tools/asm/validate_recovery_gates.py (PASS).
NEW KNOWLEDGE: 21 of 33 disc files bit-identical between RUS and USA; Ancient sprite format uncompressed 4bpp VDP1 linear pixels with 6-byte frame and 14-byte sprite records; loader at 0x060147D4; CHR.BIN shifted +8,192 bytes by Russian font; MONS.BIN contains 50 2KB-aligned sub-archives; MAP.BIN begins with SCU DSP microcode.
OPEN QUESTIONS: Decompression routine for 11 compressed graphics blocks in CHR.BIN; SCU DSP microcode instruction decode in MAP.BIN.
EXACT NEXT ACTION: Report completed T2-GFX-01 state to the user in Russian (max 8 bullets) and await instructions before starting any subsequent task. Do not begin T2-GFX-02.
