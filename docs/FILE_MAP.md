# File map

Current repository topology and ownership.

```text
README.md                         project entry point
AGENTS.md                         mandatory top-level project rules
AI_DEVELOPMENT_CONTRACT.md        mandatory AI/task confidence and stop-state contract
TASK.md                           current/next bounded task and session checkpoint
CONTRIBUTING.md                   contributor entry rules
.gitignore                        blocks commercial/private artifacts

docs/
  PROJECT_VISION.md               end goal and non-goals
  PROJECT_STATE.md                current verified state
  ARCHITECTURE.md                 current architectural hypothesis
  ROADMAP.md                      milestone sequence
  WORKLOG.md                      chronological evidence/work record
  DECISIONS.md                    accepted/working project decisions
  REVERSE_ENGINEERING.md          evidence index and RE anchors
  FILE_MAP.md                     this file
  DEVELOPMENT_PLAN.md             capability-oriented development sequence (D0–D18)
  PIPELINE_VALIDATION_PLAN.md     method/component experiment and adoption gates (V-01–V-14)
  DEVELOPMENT_RULES.md            source/C++/testing/PR/scope discipline
  POST_D8_SECOND_PASS_PLAN.md     mandatory external method second-pass plan (ADR D-012)
  POST_D8_SECOND_PASS_CLOSURE.md  canonical closure audit of external methods M-01..M-10
  D9_INDIRECT_CONTROL_FLOW_PLAN.md D9 architecture, dynamic exit model & candidate plan
  RE_TOOLCHAIN_GUIDE.md           historical Saturn SDK/toolchain evidence rules
  RULES_TRANSFER_AUDIT.md         Sega-Thor -> Sega-Thor-2 governance parity audit
  ASM_RECOVERY_METHOD_CATALOG.md  recovery methods M-01..M-10, ASM-01..04, and tracks A..R
  ASM_RECOVERY_AUTOPLAN.md        live priority queue and cost-benefit scoring engine
  reports/
    GFX_RUS_USA_DIFFERENTIAL_T2_GFX_01.md comprehensive technical report for RUS/USA graphics differential
    FULL_GRAPHICS_RECOVERY_T2_GFX_02.md   comprehensive technical report for CHR/MAP/ED full recovery
    MAP_METADATA_RECOVERY_T2_MAP_01.md    comprehensive technical report for MAP metadata and room logic recovery
    INDIRECT_CONTROL_FLOW_T2_ASM_06.md    comprehensive technical report for indirect control-flow resolution and jump tables


config/
  revisions/
    README.md                     revision schema rules
    thor2_ntsc_patched_fe11d2fb.yaml
                                  confirmed legal-safe substrate identity

CMakeLists.txt                    portable C++20 build and test definition

include/
  thor/
    sh2/
      sh2_types.hpp               instruction types, opcode categories, effective address, branch target
      sh2_decoder.hpp             fail-closed SH-2 instruction decoder declaration
      sh2_state.hpp               architectural CPU state (R0..R15, PC, PR, SR/T, delayed_pc)
      sh2_memory.hpp              big-endian memory interface and test harness (with non-contaminating peek8)
      sh2_executor.hpp            L0 instruction execution harness declaration
      sh2_block.hpp               evidence-backed basic block representation & discovery
    recomp/
      block_identity.hpp          fail-closed executable identity guard declaration
      block_compiler.hpp          mechanical basic-block C++20 compiler declaration
      block_exit.hpp              static exit descriptor & runtime resolution declaration
      block_memory.hpp            declarative memory dependency contract declaration
      shadow_checker.hpp          reusable shadow comparison framework declaration
      native_bridge.h             pure C ABI native dispatcher plugin interface
      native_dispatcher.hpp       reusable native dispatcher with shadow qualification
      mutation_harness.hpp        reusable mutation fault-injection harness declaration
      block_timing.hpp            D10 timing, interrupt, and DMA boundary classification declaration
      function_boundary.hpp       D12 evidence-backed function boundary & call-graph declaration
    provenance/
      guest_address.hpp           D13 strongly-typed guest address & pointer wrapper with provenance
      guest_view.hpp              D13 big-endian typed memory view with alignment & bounds enforcement
      saturn_runtime_table.hpp    D13 proven Saturn startup memory table & file load descriptor
    resource/
      sprite_archive.hpp          D14 Ancient character/spirit sprite package container declaration
    hw/
      vdp1_types.hpp              D15 VDP1 command, jump, color mode, and vertex types
      vdp1.hpp                    D15 VDP1 sprite, clipping, and display list engine declaration
      vdp2_types.hpp              D15 VDP2 plane, CRAM, color format, and rotation types
      vdp2.hpp                    D15 VDP2 background planes, rotation, and pixel arbitration declaration
      scsp_types.hpp              D15 SCSP sound command, driver status, and slot types
      scsp.hpp                    D15 SCSP sound engine, mailbox, and ring buffer declaration
      native_system.hpp           D16 unified Saturn hardware subsystem coordinator declaration
    runtime/
      standalone_runtime.hpp      D17 progressive standalone runtime and execution loop declaration


src/
  main_native.cpp               D18 standalone native Thor 2 game executable entry point
  sh2/
    sh2_decoder.cpp               target opcode decoding logic
    sh2_decoder_ext.cpp           extended opcode decoding logic (DT, MOVT, shift, bitwise, byte disp)
    sh2_disasm.cpp                instruction disassembly representation logic
    sh2_executor.cpp              target opcode execution semantics
    sh2_executor_ext.cpp          extended opcode execution semantics
    sh2_block.cpp                 basic block discovery and block execution
  recomp/
    block_identity.cpp            executable identity verification logic
    block_compiler.cpp            mechanical basic-block C++20 code generator
    block_exit.cpp                block exit derivation and runtime resolution logic
    block_memory.cpp              declarative memory dependency derivation logic
    shadow_checker.cpp            shadow comparison and differential outcome verification logic
    native_dispatcher.cpp         authoritative native dispatcher and C ABI export definitions
    mutation_harness.cpp          bounded mutation testing and restoration logic
    block_timing.cpp              D10 execution boundary and timing classification logic
    function_boundary.cpp         D12 function boundary catalog and call-graph resolution logic
  hw/
    vdp1.cpp                      D15 VDP1 display list parsing, clipping, and coordinate transformation
    vdp2.cpp                      D15 VDP2 color decode, RBG0 rotation matrix, and pixel arbitration
    scsp.cpp                      D15 SCSP sound command queue processing, slot configuration, and mailbox
    native_system.cpp             D16 unified Saturn hardware subsystem coordinator implementation
  resource/
    sprite_archive.cpp            D14 Ancient character/spirit sprite package decode & encode
  runtime/
    standalone_runtime.cpp        D17 progressive standalone runtime and execution loop implementation

asm/
  schema/
    module_manifest.schema.json   JSON schema for module partitioning manifests
  manifests/
    0TH2.BIN.json                 partition manifest for primary core module
    TH2.LOW.json                  partition manifest for secondary engine module
    SET07.BIN.json                partition manifest for stage overlay module
    BGM.BIN.json                  catalog manifest for M68K sound driver module
  linker/
    0TH2.ld                       linker script for 0TH2.BIN assembly container
    TH2_LOW.ld                    linker script for TH2.LOW assembly container
    SET07.ld                      linker script for SET07.BIN assembly container
    BGM.ld                        linker script for BGM.BIN sound container

tools/
  disc/
    census_saturn_cd.py           CUE/raw-sector/Saturn-header/ISO9660 census
  recomp/
    generate_sh2_block.cpp        build-time mechanical C++20 block generator CLI
    build_native_block_census.py  fail-closed 3,302-block mechanical compilation eligibility census
    generate_batch_native_blocks.py manifest-driven batch C++20 block generator & sharded catalog builder
    mutation_harness.py           live Mednafen IPC mutation and non-contamination harness
    saturnrecomp_adapter.py       external SaturnRecomp decoder probe adapter
  asm/
    generate_asm_slice.py         mechanical SH-2 assembly slice emitter
    assemble_roundtrip.py         pinned GNU toolchain assembly, linking & raw extraction pipeline
    verify_roundtrip.py           comprehensive round-trip verification & 12 negative controls
    runtime_substitution_proof.py Mednafen dual cold-boot runtime substitution proof
    export_sh2_asm_ir.cpp         generic Thor-decoder-backed SH-2 Assembly IR exporter CLI
    verify_sh2_rebuilt.cpp        authoritative C++ instruction verification linking thor_sh2
    generate_full_module_asm.py   manifest-driven lossless module assembly container generator
    build_full_module.py          manifest-driven full module assembly build and determinism pipeline
    verify_full_module.py         manifest-driven full module verification & negative controls suite
    verify_full_game_disc.py      full Saturn disc reassembled module verification in Mednafen
    verify_gameplay_scenarios.py  multi-scenario gameplay regression suite across 6 distinct scenarios
    validate_recovery_gates.py    machine-enforced recovery gate integrity validator
    constant_propagator.py        SH-2 basic-block constant propagator with call-clobber and memory safety
    register_provenance.py        architectural register provenance engine over canonical revision bytes
    indirect_resolver.py          master indirect control-flow resolver and category-separated scorecard generator
    struct_site_isolator.py       isolates struct-derived indirect sites and reconciles dynamic active sites
    object_provenance_analyzer.py classifies object instances and tracks struct field layouts
    callback_field_analyzer.py    discovers field writers and callback dispatch tables
    struct_callback_resolver.py   master multi-pass resolver for struct callbacks and callee-saved literals
    complete_cfg_closure.py       full CFG closure and gap reduction engine
  carver/
    interval_db.py                canonical central interval database & execution conflict engine
    provenance_dag.py             provenance DAG & graph expansion engine
    detector_base.py              detector base interfaces and candidate range structures
    detector_registry.py          prioritized Saturn detector registry
    detectors_code.py             executed PC, direct branch, and call target detectors
    detectors_data.py             literal pool, pointer table, MMIO pointer, string, and padding detectors
    ram_disc_carver.py            R-Studio style RAM to disc file signature carver
    gap_reporter.py               residual UNKNOWN gap auditor and campaign prioritization
    carver_pipeline.py            fixed-point carver convergence loop engine
  gfx/
    disc_extractor.py             ISO9660 extent extraction from raw Saturn MODE1 disc images
    rus_usa_differential.py       disc-wide differential analyzer and changed range locator
    sprite_archive_analyzer.py    container validator, animation offset extractor, and sprite analyzer
    carver.py                     Saturn graphics resource signature carver
    export_images.py              lossless PNG exporter and metadata manifest builder
    asset_census.py               audited resource breakdown and metrics compiler
    sprite_mapper.py              VDP1 sprite provenance, descriptor, and animation mapper
    mass_sprite_exporter.py       deduplicated 4bpp sprite exporter with palette application
    chr_decompressor.py           fail-closed Ancient LZSS variant graphics decompressor (sub_4108)
    map_renderer.py               VDP2 room package decoder and 48KB tile pattern extractor
    ed_extractor.py               uncompressed 8bpp ending illustration decoder and exporter
  map/
    map_collision.py              48KB collision heightfield and passability matrix decoder
    map_entities.py               entity spawn definitions and coordinate extractor
    map_triggers.py               trigger volume bounding boxes and exit warp extractor
    map_metadata_parser.py        master MAP.BIN disc sector and room header parser

tests/
  test_census_saturn_cd.py        synthetic tests for census parser
  sh2/
    test_framework.hpp            THOR_ASSERT macro
    reference_decode_manifest.hpp multi-reference decode vector manifest
    test_sh2_decoder.cpp          structured decode & Catherine/Mednafen cross-check
    test_sh2_decoder_extended.cpp extended opcode decoding test suite (63 opcodes)
    test_sh2_l0_semantics.cpp     synthetic L0 semantic test suite
    test_sh2_l0_extended.cpp      extended L0 semantics test suite
    test_sh2_oracle_vector.cpp    Thor 2 startup oracle vector validation
    test_sh2_block.cpp            first complete basic block discovery & oracle replay
  recomp/
    test_executable_identity.cpp  fail-closed identity guard test suite with negative controls
    test_sh2_block_compiler.cpp   mechanical block compiler determinism and fail-closed tests
    test_generated_link_isolation.cpp link-time isolation proof with zero interpreter dependencies
    test_v07a_transition.cpp      differential transition proof (synthetic + Thor 2 vectors + negative controls)
    test_shadow_positive.cpp      multi-vector positive shadow comparison test suite
    test_shadow_negative.cpp      24-fault negative control test suite (100% detection rate)
    test_shadow_isolation.cpp     pre-state storage isolation and anti-aliasing proof test suite
    test_native_dispatcher.cpp    authoritative native dispatcher and negative fallback test suite
    test_mutation_harness.cpp     12/12 single-byte and 6/6 NOP mutation unit tests
    test_block_exit.cpp           static exit descriptor & runtime resolution unit tests
    test_block_memory.cpp         declarative memory dependency contract unit tests
    test_block_timing.cpp         D10 execution boundary and timing classification unit tests
    test_m07_reference.py         SaturnRecomp reference manifest validation & negative control tests
    test_post_d8_closure.py       canonical POST-D8 closure audit validator with 9 negative controls
    test_d9_plan.py               D9 indirect plan and artifact validator with 19 negative controls
    test_native_pipeline.py       census, batch generator determinism, and shard catalog integrity test suite
  provenance/
    test_guest_provenance.cpp     D13 guest-address & type provenance test suite (Gate V-09)
  resource/
    test_resource_roundtrip.cpp   D14 resource byte-accurate round-trip proof (Gate V-11)
    test_gfx_differential.py      regression tests and negative controls for graphics tools
    test_vdp1_provenance.py       regression tests and negative controls for VDP1 sprite provenance
    test_gfx_recovery.py          regression tests and negative controls for T2-GFX-02 graphics recovery
    test_map_metadata.py          regression tests and negative controls for T2-MAP-01 map metadata recovery
  hw/
    test_vdp1.cpp                 D15 VDP1 command decoding, jump modes, clipping, and coordinate tests
    test_vdp2.cpp                 D15 VDP2 color decode, CRAM, RBG0 matrix, and pixel arbitration tests
    test_scsp.cpp                 D15 SCSP sound command ring buffer, transitions, and slot tests
    test_native_subsystems.cpp    D16 native hardware subsystems and MMIO routing test suite
  runtime/
    test_standalone_runtime.cpp   D17 standalone runtime boot, native execution, and metrics tests
    test_guest_removal.cpp        D18 guest dependency removal and L5 observable equivalence tests
  asm/
    test_asm_roundtrip.py         CTest integration test for SH-2 ASM round-trip verification
    test_full_module_asm.py       CTest integration test for full 0TH2.BIN module round-trip
    test_th2_low_asm.py           CTest integration test for full TH2.LOW module round-trip
    test_set07_asm.py             CTest integration test for full SET07.BIN overlay round-trip
    test_bgm_asm.py               CTest integration test for full BGM.BIN M68K sound driver round-trip
    test_manifest_schema.py       CTest integration test for module manifest schema & partition invariants
    test_full_game_disc.py        CTest integration test for FULL_ASM_GAME_GATE rebuilt disc verification
    test_recovery_gates.py        negative controls (40 total) & validation for recovery gates
    negative_controls_p5.py       8 adversarial negative controls (NC-Q..NC-X) for indirect flow integrity
    negative_controls_p6.py       8 adversarial negative controls (NC-Y..NC-AF) for struct callback integrity
    test_indirect_resolution.py   unit tests for constant propagation, jump tables, call graph, and accounting
    test_struct_callback_resolution.py unit tests for struct callbacks, object provenance, and accounting
  carver/
    test_carver_pipeline.py       carver pipeline, interval algebra, conflict, and determinism test suite

workstreams/
  ASM_RECOVERY_SCORECARD.json   machine-readable tracking metrics for ASM_90_GATE and FULL_ASM_GAME_GATE
  T2-M0-disc-census/
    README.md                     completed M0 proof
    disc_manifest.tsv             all 33 ISO logical files: LBA/size/SHA-256
    executable_candidates.tsv     confidence-scored executable census
    static_load_evidence.md       TH2.LOW static mapping evidence
  T2-V01-dynamic-oracle/
    README.md                     V-01-core and V-01-automation proof records
    environment_pin.yaml          19-parameter pinned boot recipe
    bounded_observation.md        Run A/B identical observation evidence
    automation_validation.md      MednafenBot low-level control layer validation evidence
  T2-V02a-0th2-provenance/
    README.md                     0TH2.BIN direct provenance proof summary
    provenance_evidence.md        pre-entry RAM snapshots, CD trace, transfer analysis
  T2-V02b-th2-low-provenance/
    README.md                     TH2.LOW direct provenance proof summary
    provenance_evidence.md        callsite proof, RAM snapshots, transfer and execution evidence
  T2-D3-sh2-decode/
    README.md                     D3 startup block decode & L0 summary
    reference_decode_manifest.json machine-readable multi-reference manifest
    decode_crosscheck_evidence.md multi-reference cross-check matrix and oracle parity
  T2-D4-D5-block0/
    README.md                     D4/D5 basic block 0 proof summary
    block_06004000.md             evidence-backed basic block CFG record (0x06004000..0x0600400A)
  T2-PRE-D8-event-safety/
    README.md                     Pre-D8 minimum event safety proof summary
    event_safety_evidence.md      two-run cold boot event audit (MMIO, IRQ, DMA, Slave SH-2)
  T2-D6-V07A-transition/
    README.md                     D6/V-07A mechanical transition proof summary
    identity_guard_evidence.md    fail-closed identity specification and negative control matrix
    transition_proof_evidence.md  differential transition proof and link isolation evidence
  T2-D7-V07B-shadow/
    README.md                     D7/V-07B shadow checker validation summary
    shadow_validation_evidence.md complete differential results, negative fault matrix, and isolation proofs
  T2-D8-V07C-native/
    README.md                     D8/V-07C authoritative native override proof summary
    native_override_evidence.md   complete dynamic verification matrix and fallback proofs
  POST-D8-M02-mutation/
    README.md                     M-02 mutation fault-injection experiment summary
    experiment_evidence.md        pinned audit, synthetic C++ matrix, live IPC matrix, and disposition
  POST-D8-M07-saturnrecomp/
    README.md                     M-07 SaturnRecomp reference corpus experiment summary
    experiment_evidence.md        decode and semantic cross-check results (0 disagreements)
    reference_vectors.json        derived legal-safe reference vectors (6 overlap + 14 probes)
  T2-D9-indirect/
    README.md                     D9 indirect control-flow workstream summary
    candidate_06004280.md         first candidate qualification record (bb_06004280)
    candidate_06004280.json       canonical machine-readable metadata record for bb_06004280
    d9_2_d8_live_regression.md    D8 live regression reproduction record under D9
    d9_4_native_indirect_evidence.md  D9.4.1 authoritative native indirect proof integrity record
    d9_4_native_indirect_evidence.json canonical raw JSON telemetry across all 5 experiment modes
    patches/
      mednafen_dut_integration.patch  isolated Mednafen DUT automation adapter patch
  T2-ASM-01/
    README.md                     T2-ASM-01 workstream record and proof summary
    experiment_evidence.md        detailed toolchain, assembly, relocation, and runtime proof
    experiment_evidence.json      machine-readable round-trip and negative control evidence
  T2-ASM-02/
    README.md                     T2-ASM-02 workstream record and full module proof summary
    experiment_evidence.md        detailed toolchain, full module assembly, and runtime proof
    experiment_evidence.json      machine-readable round-trip, runtime, and 28 negative controls evidence
  T2-ASM-03/
    README.md                     T2-ASM-03 workstream record and TH2.LOW proof summary
    experiment_evidence.md        detailed toolchain, TH2.LOW assembly, and runtime proof
    experiment_evidence.json      machine-readable round-trip, occurrence runtime, and negative controls evidence
  T2-ASM-04/
    README.md                     T2-ASM-04 workstream record and executable inventory summary
    experiment_evidence.md        detailed disc census, processor ownership, and SET07 proof
    experiment_evidence.json      machine-readable inventory, co-processor, and round-trip evidence
  T2-D17-native-scaling/
    README.md                     T2-D17-02 workstream record and scaling pipeline summary
    batch_codegen_evidence.md     detailed 3,302-block census and 270-block batch codegen evidence
    batch_codegen_evidence.json   machine-readable census, compiler, and shard telemetry
    block_census_summary.json     8-state census breakdown across 0TH2.BIN and TH2.LOW
  T2-ASM-CARVER/
    README.md                     T2-ASM-CARVER workstream record and architecture summary
    interval_db_summary.json      audited module and aggregate interval database metrics
    carver_passes.json            fixed-point pass-by-pass convergence telemetry
    unknown_gap_report.json       exhaustive audit of residual UNKNOWN gaps and campaigns
    provenance_graph_summary.json Provenance DAG node and edge topology metrics
    carver_evidence.md            comprehensive experiment evidence and denominator re-audit
  T2-GFX-01/
    README.md                     workstream record and artifact inventory
    input_revisions.json          disc revision metadata and SHA-256 hashes
    rus_usa_file_diff.tsv         file-by-file comparison between RUS and USA
    rus_usa_changed_ranges.json   detailed byte offset ranges for changed files
    sprite_archive_verification.json container verification across all 10 packages
    vram_provenance.json          VDP1/VDP2/CRAM hardware mapping evidence
    graphics_candidates.json      scored candidate graphics ranges
    extracted_images_manifest.json exported PNG dimensions, palettes, and provenance
    asset_census.json             audited resource breakdown and classification metrics
  T2-GFX-01.5/
    README.md                     workstream record and dynamic provenance architecture
    sprite_provenance.json        236 runtime sprite to VDP1/DMA/disc mappings
    sprite_records.json           catalog of 332 recovered 14-byte sprite descriptor records
    animation_map.json            43 animation sequences with 6,510 ordered frame records
    vdp1_trace_summary.json       multi-scene trace summary and 460 SCU DMA transfers
    coverage_metrics.json         audited metrics for sprite, animation, and scene coverage
  T2-GFX-02/
    README.md                     workstream record and asset recovery architecture
    chr_blocks.json               physical block partition of CHR.BIN (11 compressed + 1 font)
    chr_decompressor_map.json     reverse-engineered sub_4108 control-flow, decision tree and callsites
    chr_decompression_traces.json live dynamic decompression traces across boot, title, and scenes
    map_room_layouts.json         45 room packages decompressed to 49,152 bytes with VDP2 geometry
    map_interval_ownership.json   exhaustive whole-file interval partition of MAP.BIN (107 intervals)
    map_runtime_provenance.json   dynamic VDP2 pattern and map buffer allocation evidence
    ed_bin_metadata.json          ending sequence RGB555 palette and 8x 320x240 frame table
    graphics_unknown_intervals.json catalog of unresolved intervals across resource files
    byte_ownership.json           whole-file byte ownership classifications across all resource files
    asset_census_v3.json          audited resource breakdown, UNKNOWN reduction, and completeness metrics
    graphics_database.json        unified central index of all recovered graphics assets
  T2-MAP-01/
    map_unknown_intervals.json    17 frozen metadata intervals totaling 708,608 bytes
    map_metadata_structure_candidates.json 34 compressed sub-stream candidate decompositions
    map_metadata_runtime_provenance.json disc -> RAM -> consumer routine provenance traces
    room_bounds.json              104 room headers with camera boundaries and scroll deadzones
    entity_spawn_tables.json      1,277 entity spawn records across 104 rooms
    room_adjacency.json           527 exit and warp transitions connecting rooms
    trigger_tables.json           79 trigger volume bounding boxes and conditions
    map_event_references.json     79 event script dispatcher links (0x0601CA56)
    scu_dsp_map_program.json      128-instruction SCU DSP microcode specification for VDP2 RBG0
    collision_model.json          48KB collision heightfield and passability matrix model
    world_graph.json              complete topological graph of rooms, edges, and triggers
    map_byte_ownership_v2.json    100% whole-file interval ownership (UNKNOWN bytes: 0)
  T2-ASM-06/
    indirect_sites.json           complete inventory of 2,233 indirect sites with closed opcode accounting
    indirect_site_classes.json    structural classification across all 2,233 sites
    register_provenance.json      architectural register provenance records (1,242 resolved targets)
    jump_tables.json              46 indexed jump tables with proven bounds and 0 data overlaps
    call_graph.json               3,019 nodes and 5,271 call edges
    function_boundaries.json      3,019 function definitions with caller/callee domains
    indirect_resolution_scorecard.json master scorecard (1,378 resolved, 855 unresolved)
    indirect_dynamic_targets.json dynamic trace execution correlation across all 2,233 sites
    cfg_closure.json              CFG closure telemetry (-645 residual unknown gaps, +361 confirmed code segments)
  T2-ASM-07/
    struct_indirect_sites.json    complete inventory of 855 unresolved sites with base registers and displacements
    object_types.json             taxonomy of 6 object archetypes across High RAM, Low RAM, and system vectors
    struct_field_inventory.json   matrix of 15 struct callback fields (+0x00..+0x28) with semantic roles
    callback_tables.json          808 static function pointer tables (constant literal arrays >= 4 entries)
    state_machine_callbacks.json  10 finite proven callback domains across 427 static field writers
    struct_callback_scorecard.json master scorecard (1,686 resolved, 547 unresolved; 97.30% call/jump resolution)
    cfg_closure.json              CFG closure telemetry (+114 confirmed code segments, 546 injected targets)


asm/                              assembly reconstruction layout (ADR D-015)
  schema/
    module_manifest.schema.json   formal schema for assembly recovery module manifests
  generated/
    bb_06004000.s                 mechanically emitted SH-2 assembly specimen
  linker/
    bb_06004000.ld                linker script for bb_06004000 at VMA 0x06004000
    0TH2.ld                       linker script for full 0TH2.BIN module at VMA 0x06004000
    TH2_LOW.ld                    linker script for full TH2.LOW module at VMA 0x002DA000
    SET07.ld                      linker script for full SET07.BIN overlay at VMA 0x060D8000
  manifests/
    bb_06004000.json              provenance manifest for bb_06004000 slice
    0TH2.BIN.json                 provenance manifest for 0TH2.BIN module container
    TH2.LOW.json                  provenance manifest for TH2.LOW module container
    SET07.BIN.json                provenance manifest for SET07.BIN overlay container
    BGM.BIN.json                  provenance manifest for BGM.BIN sound driver container


external/
  README.md                       rules for private user-supplied inputs
```

## Rule

Directories are created only when they gain a real tracked artifact. Do not add empty placeholder trees merely to make the repository look complete.

Governance documents are not optional decoration: when their owned state changes, update the corresponding file in the same conceptual task/commit whenever practical.
