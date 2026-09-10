# T2-D9 — Indirect Control-Flow Handling

Status: **BOUNDED_PROOF for bb_06004280 (Authoritative Native Indirect Override Proven)**
Capability: **D9 — Indirect Control-Flow Handling**
Baseline Commit: `b2a326852dd1f3d01596310d6dc25fc5b10d2109`

---

## 1. Capability Mission

Establish the runtime dispatch and control-flow continuation mechanism for basic blocks containing indirect jumps, calls, or computed branches on Sega Saturn SH-2 architecture.

Canonical definition per `docs/DEVELOPMENT_PLAN.md`:
> Strategy for blocks containing indirect jumps, calls, or computed branches. Required bounded deliverable: runtime dispatch mechanism OR evidence-based target resolution for at least one indirect-flow block. UNKNOWN targets remain on interpreter/fallback.

---

## 2. Workstream Artifacts

- `candidate_06004280.md`: First candidate block qualification record (`bb_06004280`), exact bytes, disassembly, oracle trace, and ownership classification.
- `docs/D9_INDIRECT_CONTROL_FLOW_PLAN.md`: Complete architectural design, exit representation, memory snapshot generalization, timing contract, negative control matrix, and sub-gate roadmap.
- `d9_2_d8_live_regression.md`: Live D8 production regression under pinned Mednafen debug oracle.
- `d9_4_native_indirect_evidence.md`: Authoritative live execution, timing parity, and multi-mode telemetry evidence.
- `d9_4_native_indirect_evidence.json`: Raw JSON telemetry from live Mednafen runs across all 4 modes.
- `tests/recomp/test_d9_plan.py`: Automated plan integrity validator with fail-closed negative controls.

---

## 3. First Bounded Candidate Summary

- **Block ID:** `bb_06004280`
- **Range:** `0x06004280 .. 0x06004288` (10 bytes, 5 instructions)
- **Module:** `0TH2.BIN` (Master SH-2)
- **Indirect Instruction:** `0x430B` (`JSR @R3`) at `0x06004286`
- **Delay Slot:** `0x0009` (`NOP`) at `0x06004288`
- **SHA-256 (Candidate Bytes Only):** `8879cbe14f58a5fbc4eb9545e1cc41b3593e306cab114769a94f814a18bcb770`
- **Observed Cold-Boot Target:** `0x0600A0F8`
- **Observed Return Address (`PR`):** `0x0600428A`
- **Execution Evidence:** Cold boot Hit 2 at frame 701 (debugger 0-indexed count, 702nd presentation frame), cycle `316309168` in Mednafen debug oracle; target `0x0600A0F8` reached at cycle `316309189` (21 cycles duration; 19 cycles to delay-slot entry).

---

## 4. Sub-Gate Progression

1. **`D9.P0` — Architecture & Candidate Qualification** [DONE / PASS]
2. **`D9.1` — Candidate Opcode L0 Semantics & Block Qualification** [DONE / PASS]
3. **`D9.2` — Generic Dynamic-Exit & Memory-Descriptor Representation** [DONE / PASS]
4. **`D9.3` — Isolated Shadow Proof for `bb_06004280`** [DONE / PASS]
5. **`D9.4` — Authoritative Native Indirect Override & Dynamic Continuation** [DONE / PASS (repaired under T2-D9.4.1)]
6. **`M-03` — Bounded SaturnAutoRE Candidate Harvester Re-Entry** [READY_FOR_BOUNDED_TEST / DEFERRED_BY_ASM_FIRST_ARCHITECTURE]
7. **`D9.5` — Multi-Target / Secondary Indirect Expansion** [FROZEN / DEFERRED_UNTIL_FULL_ASM_GAME_GATE]

*Architectural Note (ADR D-015):* D9 has reached bounded proof for specimen `bb_06004280`. Per ADR D-015, broad C++ mechanical recompilation is frozen until the entire game passes `FULL_ASM_GAME_GATE`. Bounded specimens are retained; broad expansion is deferred.
