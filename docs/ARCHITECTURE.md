# Architecture

## Current architectural stance

The architecture is intentionally **not locked**. It evolves only through experiments in `docs/PIPELINE_VALIDATION_PLAN.md`.

The currently favored target shape is:

```text
Thor 2 disc revision & canonical extraction + hashes
        |
executable module/provenance database (0TH2.BIN, TH2.LOW, overlays)
        |
static discovery + dynamic oracle observation
        |
exact SH-2 decode + L0 instruction/memory semantics
        |
complete CODE/DATA/UNKNOWN ownership classification
        |
complete exact SH-2 assembly reconstruction (asm/ project tree)
        |
deterministic reassembly of all modules via validated toolchain
        |
rebuilt Saturn game replaces disc files & boots in clean Mednafen
        |
FULL_ASM_GAME_GATE (verified title, gameplay, & runtime parity)
        |
broad systematic ASM → C++ mechanical translation
        |
structural & semantic recovery with guest provenance
        |
proof-gated native subsystem replacements
        |
progressive standalone native runtime
```

### ASM-First Architecture Rule (ADR D-015)

Per ADR D-015, the project enforces an **ASM-FIRST recovery strategy**:
1. Broad C++ mechanical recompilation is **FROZEN** until the entire game binary is completely reconstructed into reassemblable assembly and passes the `FULL_ASM_GAME_GATE`.
2. Existing C++ blocks (`bb_06004000` and `bb_06004280`) are retained strictly as **bounded technology/proof specimens** verifying decoder, codegen, shadow verification, and native override capabilities.
3. No further broad C++ translation or unsupervised candidate harvesting (M-03) may occur until rebuilt Saturn binaries demonstrate cold boot and gameplay parity in Mednafen.

## Design principles

### Mechanical before semantic

Correct instruction-level/mechanical translation does not require knowing what a game function means. Therefore correctness and semantics are separate axes:

- correctness axis: original execution -> interpreter/oracle -> mechanical translation -> native replacement;
- abstraction axis: instruction -> block -> function -> structure -> subsystem -> game concept.

### Basic blocks first

Initial translation works on executed basic blocks. Function boundaries are useful annotations, not a prerequisite for correctness.

### Explicit guest state first

Early generated C++ should preserve explicit SH-2 architectural state and guest memory access rather than prematurely inventing native types.

### Fail closed

Unknown/unsupported flow, timing-sensitive device access, uncertain executable generation, or unresolved indirect control flow stays on the oracle/fallback path.

### Deterministic scheduler over host threads

If dual-SH2 behavior is required, first model it as deterministic virtual execution. Do not map Master and Slave directly to uncontrolled host threads.

### Preserve hardware semantics until proven replaceable

VDP1/VDP2, SCU, M68K/SCSP, CD, and SMPC begin as compatibility/runtime domains. Native replacements are optional later experiments, not assumptions.

## Storage architecture

Public GitHub contains legal-safe project state. Private laboratory artifacts stay external and are referenced by hashes/logical identifiers only.
