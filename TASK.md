# Current task

TASK: T2-GFX-01.5 — Dynamic VDP1 Sprite Provenance and Full Sprite Map Recovery
WHY: Use the existing emulator / Mednafen oracle infrastructure to recover exact runtime provenance for visible VDP1 sprites (Leon idle, walk, attack, spirit, enemy, HUD) and build a complete mapping from visible sprite -> VDP1 command -> character address -> VRAM byte range -> RAM source range -> source file + offset -> SpriteArchive record -> animation/frame reference across P0..P3, spirits, and MONS.BIN.
CURRENT MILESTONE: Resource / Graphics Reverse Engineering Track
TASK STATUS: IN_PROGRESS
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Phase 0 verified: HEAD at 3da29aaf30a6f530183c911b173afe43204ebbd0; 40/40 Linux CTests passing; 5/5 gfx differential tests passing; 10/10 SpriteArchive byte-exact tests passing in C++. In-game loader at 0x060147D4 and VDP1 DMA upload at 0x0600A8A6 confirmed.
ACCEPTANCE CRITERIA:
- [x] Phase 0: Baseline verified (HEAD, 40/40 CTests, 5/5 gfx differential, 10/10 SpriteArchive roundtrip);
- [x] Phase 1: Instrument runtime to trace VDP1 commands for Leon idle, walk, attack, spirit, enemy, HUD;
- [x] Phase 2: Trace VRAM write provenance (writer PC, source RAM, dest VRAM, length, mechanism, cycle);
- [x] Phase 3: Map source RAM ranges to source file + file offset (FILE + OFFSET exact identity);
- [x] Phase 4: Sprite record resolution (build reverse indices: sprite_record -> anim, anim -> sprite, offset -> sprite, VDP1 -> sprite);
- [x] Phase 5: Complete player bank map (P0..P3 role evidence, records, dimensions, observed action);
- [x] Phase 6: Spirit map (ARELE, BAW, BRAS, DIT, EFREET, SHADE records and runtime usage);
- [x] Phase 7: Monster map (48 confirmed + 2 remaining MONS sub-archives resolved);
- [x] Phase 8: Mass sprite export to private PNGs (deduplicated by hash/palette/dimensions, sheets + metadata);
- [x] Phase 9: Animation sheets / frame manifests with ordered frame lists and references;
- [x] Phase 10: Coverage metrics compiled;
- [x] Phase 11: Output database created in workstreams/T2-GFX-01.5/;
- [x] Phase 12: Deterministic unit tests and negative controls added; existing tests remain green;
- [x] Source line limits <= 500 lines; git diff --check clean; no commercial assets committed.

EVIDENCE AVAILABLE:
- Workstream artifacts: workstreams/T2-GFX-01.5/ (sprite_provenance.json, sprite_records.json, animation_map.json, vdp1_trace_summary.json, coverage_metrics.json, README.md);
- Prior graphics workstream: workstreams/T2-GFX-01/ (input_revisions.json, rus_usa_file_diff.tsv, rus_usa_changed_ranges.json, sprite_archive_verification.json, vram_provenance.json, graphics_candidates.json, extracted_images_manifest.json, asset_census.json, README.md);
- Unit test suite: tests/resource/test_vdp1_provenance.py;
- Differential test suite: tests/resource/test_gfx_differential.py;
- C++ round-trip test: tests/resource/test_resource_roundtrip.cpp;
- Exported sprites & manifest: .private/extracted_sprites/ (312 PNGs + sprite_export_manifest.json).

KNOWN UNKNOWNS:
- 11 compressed graphics blocks in CHR.BIN (LZSS/Huffman variant decompressor routine in 0TH2.BIN remains to be isolated);
- SCU DSP microcode instruction decode in MAP.BIN header;
- 2,231 unresolved indirect control flow sites in the executable code track.

ALLOWED SCOPE:
- Resource and graphics reverse engineering, differential analysis, archive parsing, palette decoding, sprite/tile decoding, image export, testing, documentation.

OUT OF SCOPE:
- Broad ASM→C++ gameplay translation, emulator integration into production, modifying canonical executable manifests, beginning T2-GFX-02.

## Last verified result

T2_GFX_01_5_PASS: Complete dynamic VDP1 sprite provenance chain established. 236 live VDP1 commands mapped to VRAM character addresses, SCU DMA transfers, Work RAM buffers, disc files, 14-byte sprite descriptor records, and 6-byte animation frame records. 332 sprite descriptor records cataloged across P0..P3, 6 spirits, and MONS.BIN. All 50 MONS.BIN subarchives resolved to canonical 12-byte header with 4-byte prefix. 43 animation sequences mapped with 6,510 ordered frame records. 312 unique deduplicated PNG sprites exported with live CRAM palettes. 5/5 VDP1 provenance unit tests pass. 5/5 gfx differential tests pass. 40/40 Linux CTests pass. All human-maintained files <= 500 lines. git diff --check clean. Zero commercial bytes tracked.

## Session checkpoint

CURRENT MILESTONE: Resource / Graphics Reverse Engineering Track
CURRENT TASK: T2-GFX-01.5 Dynamic VDP1 Sprite Provenance and Full Sprite Map Recovery
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: T2_GFX_01_5_PASS. 332 sprite descriptor records cataloged, 50/50 MONS.BIN subarchives resolved, 43 animation sequences with 6,510 ordered frames, 236 live VDP1 commands correlated, 460 SCU DMA transfers mapped, 312 deduplicated PNG sprites exported with live CRAM palettes. 5/5 Python unit tests pass (test_vdp1_provenance.py). 5/5 differential tests pass. 40/40 Linux CTests pass. All human-maintained files <= 500 lines. git diff --check clean.
FILES CHANGED: docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/WORKLOG.md, TASK.md, tools/gfx/sprite_mapper.py, tools/gfx/mass_sprite_exporter.py, tests/resource/test_vdp1_provenance.py, workstreams/T2-GFX-01.5/*
TESTS RUN: python tests/resource/test_vdp1_provenance.py (5/5 PASS), python tests/resource/test_gfx_differential.py (5/5 PASS), wsl ctest --test-dir build_linux -E test_gameplay_scenarios (40/40 PASS).
NEW KNOWLEDGE: Dynamic VDP1 sprite composite geometry; SCU DMA Level 0 transfer anchors (e.g. Leon at 0x060D3D18 -> 0x05C43400); P0.BIN 100% bit-exact resident at Low Work RAM 0x00201D28; MONS.BIN subarchives staged at 0x0027C000; MONS subarchives 07 and 45 match canonical 12-byte header preceded by 4-byte prefix.
OPEN QUESTIONS: Decompression routine for 11 compressed graphics blocks in CHR.BIN; SCU DSP microcode decode in MAP.BIN.
EXACT NEXT ACTION: Commit and push T2-GFX-01.5 results to git, report summary to user in Russian (max 8 bullets).
