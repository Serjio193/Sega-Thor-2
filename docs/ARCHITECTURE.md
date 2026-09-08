# Architecture

## Current architectural stance

The architecture is intentionally **not locked**. It evolves only through experiments in `docs/PIPELINE_VALIDATION_PLAN.md`.

The currently favored target shape is:

```text
Thor 2 disc revision
        |
canonical extraction + hashes
        |
module/provenance database
        |
static discovery + dynamic oracle
        |
exact SH-2 decode
        |
code/data/unknown ownership DB
        |
mechanical explicit-state C++ blocks
        |                 \
        |                  interpreter/oracle fallback
        +------ shadow differential ------+
        |
verified native blocks
        |
structural recovery
        |
semantic recovery
        |
proof-gated native subsystem replacements
        |
progressive standalone runtime
```

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
