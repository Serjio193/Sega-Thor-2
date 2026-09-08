# File map

Current repository topology and ownership.

```text
README.md                         project entry point
AGENTS.md                         mandatory working rules
.gitignore                        prevents commercial/private artifacts entering Git

docs/
  PROJECT_VISION.md               end goal and non-goals
  PROJECT_STATE.md                current milestone and verified state
  ARCHITECTURE.md                 current architectural hypothesis
  ROADMAP.md                      milestone sequence
  WORKLOG.md                      chronological work record
  DECISIONS.md                    accepted/working project decisions
  REVERSE_ENGINEERING.md          evidence index and RE anchors
  FILE_MAP.md                     this file
  PIPELINE_VALIDATION_PLAN.md     authoritative external-method experiment queue

config/
  revisions/                      legal-safe revision identities/manifests/hashes
  modules/                        future module/segment metadata
  experiments/                    future bounded experiment configs

workstreams/
  T2-M0-disc-census/              only active workstream
  experiments/                    later method-validation workstreams

src/                              created only when a proven implementation slice exists
tools/                            legal-safe analysis/verification tooling
tests/                            deterministic tests and regression vectors
external/                         documentation for required user-supplied/private inputs
```

## Rule

Directories are created when they gain a real tracked artifact. Do not add empty placeholder trees merely to make the repository look complete.
