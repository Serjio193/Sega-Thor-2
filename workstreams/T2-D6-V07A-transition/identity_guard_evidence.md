# Executable Identity Guard Evidence — `bb_06004000`

Status: **`PRE_D8_EXECUTABLE_IDENTITY_GUARD: PASS` for `bb_06004000` only**

---

## 1. Identity Specification for `bb_06004000`

| Field | Bound Value | Rationale / Provenance |
|---|---|---|
| Revision ID | `thor2_ntsc_patched_fe11d2fb` | Proven canonical disc image hash in D0 |
| Module | `0TH2.BIN` | Proven runtime mapping to High Work RAM in V-02a |
| Module Provenance | `PROVEN` (`DIRECT_PROVENANCE_PROVEN`) | Direct byte match against disc extent |
| CPU Target | `MASTER_SH2` | Master CPU execution confirmed |
| Start PC | `0x06004000` | Basic block entry address |
| End PC | `0x0600400A` | Basic block terminator delay slot address |
| Expected Bytes | `66 11 6F 03 D4 17 64 42 A0 03 00 09` | 12 retired bytes |
| Validity State | `VALID` | Must fail closed if `INVALIDATED` or `UNVERIFIED` |

---

## 2. Non-Contaminating Host Observation

Per project rules, identity verification must be a host-side non-architectural observation that does NOT contaminate the guest memory-effect log.

Implementation:
- `ISh2Memory::peek8(uint32_t addr)` reads guest RAM without recording to `MemoryLogEntry`.
- Verified in `test_executable_identity`: `mem.log().empty()` is `true` after complete block eligibility checks.

---

## 3. Negative Control Test Matrix

The reusable guard `check_block_eligibility` was evaluated against the following negative test suite in `tests/recomp/test_executable_identity.cpp`:

| Test Case | Injected Mutation | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| Baseline | Valid descriptor and memory | `ELIGIBLE` | `ELIGIBLE` | PASS |
| Wrong Revision | `revision_id = "thor2_pal_unverified"` | `REVISION_MISMATCH` | `REVISION_MISMATCH` | PASS |
| Wrong Module | `module_name = "TH2.LOW"` | `MODULE_MISMATCH` | `MODULE_MISMATCH` | PASS |
| Unproven Provenance | `module_provenance_proven = false` | `PROVENANCE_NOT_PROVEN` | `PROVENANCE_NOT_PROVEN` | PASS |
| Wrong CPU | `cpu = SLAVE_SH2` | `CPU_MISMATCH` | `CPU_MISMATCH` | PASS |
| Wrong Address Range | `start_pc = 0x06004002` | `ADDRESS_RANGE_MISMATCH` | `ADDRESS_RANGE_MISMATCH` | PASS |
| Byte 0 Inverted | Byte at `0x06004000` flipped | `CONTENT_BYTE_MISMATCH` | `CONTENT_BYTE_MISMATCH` | PASS |
| Byte 1..11 Inverted | Each byte mutated individually | `CONTENT_BYTE_MISMATCH` | `CONTENT_BYTE_MISMATCH` | PASS |
| Invalid State (1) | `validity = INVALIDATED` | `INVALID_STATE` | `INVALID_STATE` | PASS |
| Invalid State (2) | `validity = UNVERIFIED` | `INVALID_STATE` | `INVALID_STATE` | PASS |

All negative tests fail closed as required.
