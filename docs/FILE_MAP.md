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
  RE_TOOLCHAIN_GUIDE.md           historical Saturn SDK/toolchain evidence rules
  RULES_TRANSFER_AUDIT.md         Sega-Thor -> Sega-Thor-2 governance parity audit

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
      shadow_checker.hpp          reusable shadow comparison framework declaration
      native_bridge.h             pure C ABI native dispatcher plugin interface
      native_dispatcher.hpp       reusable native dispatcher with shadow qualification
      mutation_harness.hpp        reusable mutation fault-injection harness declaration

src/
  sh2/
    sh2_decoder.cpp               target opcode decoding logic
    sh2_executor.cpp              target opcode execution semantics
    sh2_block.cpp                 basic block discovery and block execution
  recomp/
    block_identity.cpp            executable identity verification logic
    block_compiler.cpp            mechanical basic-block C++20 code generator
    shadow_checker.cpp            shadow comparison and differential outcome verification logic
    native_dispatcher.cpp         authoritative native dispatcher and C ABI export definitions
    mutation_harness.cpp          bounded mutation testing and restoration logic

tools/
  disc/
    census_saturn_cd.py           CUE/raw-sector/Saturn-header/ISO9660 census
  recomp/
    generate_sh2_block.cpp        build-time mechanical C++20 block generator CLI
    mutation_harness.py           live Mednafen IPC mutation and non-contamination harness
    saturnrecomp_adapter.py       external SaturnRecomp decoder probe adapter

tests/
  test_census_saturn_cd.py        synthetic tests for census parser
  sh2/
    test_framework.hpp            THOR_ASSERT macro
    reference_decode_manifest.hpp multi-reference decode vector manifest
    test_sh2_decoder.cpp          structured decode & Catherine/Mednafen cross-check
    test_sh2_l0_semantics.cpp     synthetic L0 semantic test suite
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
    test_m07_reference.py         SaturnRecomp reference manifest validation & negative control tests

workstreams/
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

external/
  README.md                       rules for private user-supplied inputs
```

## Rule

Directories are created only when they gain a real tracked artifact. Do not add empty placeholder trees merely to make the repository look complete.

Governance documents are not optional decoration: when their owned state changes, update the corresponding file in the same conceptual task/commit whenever practical.
