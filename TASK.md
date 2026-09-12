# Current task

TASK: T2-MAP-01 — MAP Metadata, Entity/Trigger Tables, Collision and Room Logic Recovery
WHY: Reduce the remaining UNKNOWN_RESOURCE_BYTES = 708,608 in MAP.BIN by recovering entity spawn tables, collision/walkability, exit/warp adjacency, trigger volumes, room bounds, object placement, and SCU DSP microcode.
CURRENT MILESTONE: Resource / Graphics Reverse Engineering Track (Map Metadata Recovery)
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Baseline HEAD at 58f71fd03bc9a10090b75bb2fe92625140dfc52d; 26/26 Linux CTests pass; 10/10 test_map_metadata.py pass; 26/26 Python resource suite pass; all 17 MAP.BIN metadata intervals decomposed into 34 compressed companion sub-streams with sub_4108 to 48KB; UNKNOWN_RESOURCE_BYTES drops to 0 (100% reduction).
ACCEPTANCE CRITERIA:
- [x] Phase 0: Baseline gate verified (HEAD, regressions, UNKNOWN_RESOURCE_BYTES_BEFORE = 708,608);
- [x] Phase 1: Freeze canonical 17 unknown intervals in workstreams/T2-MAP-01/map_unknown_intervals.json (sum = exactly 708,608 bytes);
- [x] Phase 2: Global pattern analysis across intervals (widths 2..32, offsets, pointers, sentinels) in workstreams/T2-MAP-01/map_metadata_structure_candidates.json;
- [x] Phase 3: Cross-room correlation with 45 rooms (small, large, multi-exit, combat-heavy, distinct);
- [x] Phase 4: Runtime load provenance (disc -> RAM -> consumer routine) in workstreams/T2-MAP-01/map_metadata_runtime_provenance.json;
- [x] Phase 5: Entity spawn table recovery in workstreams/T2-MAP-01/entity_spawn_tables.json;
- [x] Phase 6: Collision / walkability model recovery in workstreams/T2-MAP-01/collision_model.json;
- [x] Phase 7: Exit / warp / room adjacency tables in workstreams/T2-MAP-01/room_adjacency.json;
- [x] Phase 8: Trigger tables recovered in workstreams/T2-MAP-01/trigger_tables.json;
- [x] Phase 9: Script / event references recovered in workstreams/T2-MAP-01/map_event_references.json;
- [x] Phase 10: Camera / room bounds recovered in workstreams/T2-MAP-01/room_bounds.json;
- [x] Phase 11: Object / geometry tables investigated and linked to consumers;
- [x] Phase 12: SCU DSP microcode disassembled in workstreams/T2-MAP-01/scu_dsp_map_program.json;
- [x] Phase 13: Semantic record definitions documented with confidence tiers;
- [x] Phase 14: Offline map metadata parser implemented in tools/map/ (each file <= 500 lines);
- [x] Phase 15: World graph constructed in workstreams/T2-MAP-01/world_graph.json;
- [x] Phase 16: Byte ownership V2 compiled in workstreams/T2-MAP-01/map_byte_ownership_v2.json;
- [x] Phase 17: UNKNOWN reduction audited (UNKNOWN_RESOURCE_BYTES_AFTER < 708,608);
- [x] Phase 18: Regression tests in tests/resource/test_map_metadata.py pass with negative controls; existing tests remain green;
- [x] Phase 19: Comprehensive technical report in docs/reports/MAP_METADATA_RECOVERY_T2_MAP_01.md, docs updated;
- [x] Source line limits <= 500 lines; git diff --check clean; no commercial assets committed.

EVIDENCE AVAILABLE:
- T2-GFX-02 interval ownership map (107 intervals, 17 metadata intervals totaling 708,608 bytes);
- 45 room packages decompress to 49,152 bytes each;
- In-game map loaders at 0x060148B6 (DSP) and room loaders in 0TH2.BIN / TH2.LOW.

KNOWN UNKNOWNS:
- None within resource/metadata scope (100.0% of disc resources structured, 0 UNKNOWN bytes).

ALLOWED SCOPE:
- MAP.BIN / room metadata reverse engineering, collision, entities, warps, triggers, DSP microcode disassembly, tools/map/, testing, documentation.

OUT OF SCOPE:
- Broad ASM→C++ gameplay translation, emulator integration into production, modifying canonical executable manifests.

## Last verified result

T2_MAP_01_PASS: MAP.BIN metadata intervals completely recovered and structured. All 17 metadata intervals (708,608 bytes) proven to consist of 34 compressed companion sub-streams decompressing via sub_4108 to exactly 49,152 bytes (48 KB) each (12 collision packages + 5 secondary VDP2 plane packages). Parsed 104 room pointer table sectors in MAP.BIN tail: 104 room bounds and camera scroll deadzones recovered (room_bounds.json); 1,277 entity spawn definitions mapped to 0x06014A94 (entity_spawn_tables.json); 527 exit and warp transitions mapped to 0x0600A416 (room_adjacency.json); 79 trigger volumes mapped to 0x0604B070 / 0x0601CA56 (trigger_tables.json, map_event_references.json). Reverse-engineered SCU DSP 128-instruction microprogram computing VDP2 RBG0 2D affine matrix at 60Hz (scu_dsp_map_program.json). Compiled map_byte_ownership_v2.json across 107 contiguous intervals: UNKNOWN_RESOURCE_BYTES reduced from 708,608 down to 0 bytes (100.0% reduction). Disc-wide resource coverage reached 100.0% (9,044,008 / 9,044,008 bytes). Modular tooling implemented in tools/map/ (map_collision.py, map_entities.py, map_triggers.py, map_metadata_parser.py). Test suite tests/resource/test_map_metadata.py passing 10/10 with negative controls. 26/26 Python resource tests pass. 26/26 Linux CTests pass. All human-maintained source/test/tool files strictly <= 500 lines. git diff --check clean. Zero commercial assets tracked.

## Session checkpoint

CURRENT MILESTONE: Resource / Graphics Reverse Engineering Track (Map Metadata Recovery)
CURRENT TASK: T2-MAP-01 MAP Metadata, Entity/Trigger Tables, Collision and Room Logic Recovery
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: T2_MAP_01_PASS. UNKNOWN_RESOURCE_BYTES = 0 bytes (100% structured). 26/26 Linux CTests pass. 26/26 Python resource tests pass.
FILES CHANGED: tools/map/*, tests/resource/test_map_metadata.py, workstreams/T2-MAP-01/*, docs/reports/MAP_METADATA_RECOVERY_T2_MAP_01.md, docs/FILE_MAP.md, docs/PROJECT_STATE.md, docs/WORKLOG.md, docs/REVERSE_ENGINEERING.md, TASK.md
TESTS RUN: python -m unittest tests/resource/test_map_metadata.py (10/10 PASS), full resource suite (26/26 PASS), wsl ctest --test-dir build-linux (26/26 PASS).
NEW KNOWLEDGE: 34 compressed companion streams in MAP.BIN decompress to 48KB collision buffers and secondary VDP2 planes; 104 rooms, 1,277 entities, 527 exits, 79 triggers; SCU DSP microcode generates RBG0 matrix at 60Hz.
OPEN QUESTIONS: None in resource track. Next milestone: resume ASM-first indirect control flow resolution or audio/M68K recovery.
EXACT NEXT ACTION: Propose next technical task (T2-SND-01 M68K sound driver recovery or T2-ASM-06 indirect branch resolution).
