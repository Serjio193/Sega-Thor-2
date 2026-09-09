# M-07 — SaturnRecomp SH-2 Reference Corpus & Cross-Check

## 1. Overview & Objectives

Under **ADR D-012**, this workstream evaluates **M-07 (SaturnRecomp)** as part of the post-D8 second-pass external method review.

The primary objective is to evaluate whether SaturnRecomp's SH-2 decoder, execution semantics, and recompilation patterns can accelerate our reverse engineering and verification pipeline, while strictly maintaining project boundaries and legal repository hygiene.

## 2. Pinned External Repository & Provenance

- **Repository**: `https://github.com/sonsegajp/SaturnRecomp.git`
- **Pinned Commit**: `26c9715e5493054b8a205aa31d73d8f125fdd8f5`
- **Audit Date**: 2026-09-10
- **Licensing Constraint**: The upstream repository does not contain an open-source license grant. Consequently, **zero foreign source files are vendored or checked into Sega-Thor-2**. Only derived, legal-safe facts (opcode patterns, operand shapes, and behavioral contracts) are recorded in `reference_vectors.json`.

## 3. Structural Audit: M-07A vs M-07B

An audit of the pinned commit reveals a distinct split in capabilities:

1. **M-07A (SH-2 Decoder & Semantic Execution Corpus)**: **PRESENT & VERIFIED**
   - Core decoder located at `external/sh2-recomp-core/common/sh2_isa.h` and `sh2_decoder.c`.
   - Structured `sh2_insn` representation covers opcode identification, branch/delay flags, register operand shapes, memory load/store attributes, displacement, and immediate scaling.
   - Comprehensive execution semantic tests in `tests/sh2_semantics.c` (39/39 passing).
2. **M-07B (Public Ahead-of-Time Recompilation / C Code Generator)**: **NOT_PRESENT_AT_PIN**
   - `README.md` explicitly documents: *"The decoder and module-analysis foundation for ahead-of-time recompilation are present, but a complete public AOT emitter is not."*
   - Directory `recompiler/` contains disc header parsing, ISO extraction, and disassembly text formatting (`sh2_format`). No C code generation backend exists at this commit.

## 4. Epistemological Boundary: Reference != Authority

Even with 100% agreement across tested instructions:
- **Authority** remains:
  1. Official Hitachi SH7604 Hardware Manual / SH-1/SH-2 Programming Manual Rev. 4.0.
  2. Bounded Mednafen dynamic debug oracle for runtime validation.
- SaturnRecomp serves strictly as an **accelerator, cross-check reference, and secondary sanity check**.

## 5. Artifacts & Automation

- `reference_vectors.json`: Machine-readable reference manifest containing 6 `bb_06004000` overlap vectors, 14 future-expansion synthetic probe vectors, and 7 semantic edge case evaluations.
- `tools/recomp/saturnrecomp_adapter.py`: Out-of-tree probe adapter invoking the pinned external decoder.
- `tests/recomp/test_m07_reference.py`: Automated project-side test verifying manifest integrity, live cross-checks, and fail-closed negative controls.
