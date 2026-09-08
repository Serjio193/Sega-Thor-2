# Sega-Thor-2

Evidence-driven reverse engineering and progressive recompilation research for **The Story of Thor 2 / The Legend of Oasis** on Sega Saturn.

This repository contains only legal-safe source, tooling, configuration, documentation, hashes/manifests, and derived metadata. Original commercial disc images, extracted retail binaries, save states, RAM dumps, and other copyrighted game data stay outside GitHub.

## Current status

**T2-M0 — Canonical Disc + Executable/Module Census: COMPLETE**

Confirmed substrate revision: `thor2_ntsc_patched_fe11d2fb`.

**Next queued experiment:** `T2-M1 — SaturnAutoRE dynamic-oracle validation` (`PROPOSED`).

No decompiler/recompiler architecture is considered final. External techniques are introduced one at a time, tested on a bounded Thor 2 slice, and retained only after evidence-backed validation.

## Start here

- `AGENTS.md` — mandatory project rules
- `docs/PROJECT_STATE.md` — current verified state
- `docs/PIPELINE_VALIDATION_PLAN.md` — sequential experiment plan
- `docs/REVERSE_ENGINEERING.md` — evidence index
- `workstreams/T2-M0-disc-census/README.md` — completed first workstream
- `tools/disc/census_saturn_cd.py` — reproducible legal-safe disc census tool
