# File map

Current repository topology and ownership.

```text
README.md                         project entry point
AGENTS.md                         mandatory working rules
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
  PIPELINE_VALIDATION_PLAN.md     authoritative method experiment queue

config/
  revisions/
    README.md                     revision schema rules
    thor2_ntsc_patched_fe11d2fb.yaml
                                  confirmed legal-safe substrate identity

tools/
  disc/
    census_saturn_cd.py           CUE/raw-sector/Saturn-header/ISO9660 census

tests/
  test_census_saturn_cd.py        synthetic tests for census parser

workstreams/
  T2-M0-disc-census/
    README.md                     completed M0 proof
    disc_manifest.tsv             all 33 ISO logical files: LBA/size/SHA-256
    executable_candidates.tsv     confidence-scored executable census
    static_load_evidence.md       TH2.LOW static mapping evidence

external/
  README.md                       rules for private user-supplied inputs
```

## Rule

Directories are created only when they gain a real tracked artifact. Do not add empty placeholder trees merely to make the repository look complete.
