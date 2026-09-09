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
      sh2_types.hpp               instruction types, opcode categories, effective address
      sh2_decoder.hpp             fail-closed SH-2 instruction decoder declaration
      sh2_state.hpp               architectural CPU state (R0..R15, PC, PR, SR/T, etc.)
      sh2_memory.hpp              big-endian memory interface and test harness
      sh2_executor.hpp            L0 instruction execution harness declaration

src/
  sh2/
    sh2_decoder.cpp               target opcode decoding logic
    sh2_executor.cpp              target opcode execution semantics

tools/
  disc/
    census_saturn_cd.py           CUE/raw-sector/Saturn-header/ISO9660 census

tests/
  test_census_saturn_cd.py        synthetic tests for census parser
  sh2/
    test_framework.hpp            THOR_ASSERT macro
    test_sh2_decoder.cpp          structured decode & Catherine/Mednafen cross-check
    test_sh2_l0_semantics.cpp     synthetic L0 semantic test suite
    test_sh2_oracle_vector.cpp    Thor 2 startup oracle vector validation

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
    README.md                     D3 target-subset decode & L0 summary
    decode_crosscheck_evidence.md multi-reference cross-check matrix and oracle parity

external/
  README.md                       rules for private user-supplied inputs
```

## Rule

Directories are created only when they gain a real tracked artifact. Do not add empty placeholder trees merely to make the repository look complete.

Governance documents are not optional decoration: when their owned state changes, update the corresponding file in the same conceptual task/commit whenever practical.
