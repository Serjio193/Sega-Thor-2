# T2-D4-D5-block0 — First Complete Thor 2 Basic Block Proof

Status: **PASS (BOUNDED_PROOF)**
Milestone: **D3 / D4 / D5 — First Complete Basic Block**
Target: Startup basic block in `0TH2.BIN` at candidate entry `0x06004000`

## Objectives & Results

1. **Dynamic Block Discovery**: Traced execution under pinned Mednafen oracle from cold boot to the first architectural terminator:
   - Block entry: `0x06004000`
   - Block exit: `0x06004012`
   - Inclusive instruction range: `0x06004000..0x0600400A` (6 instructions, 12 bytes)
   - Terminator: `0xA003` (`BRA 0x06004012`) at `0x06004008`
   - Delay slot: `0x0009` (`NOP`) at `0x0600400A`
2. **D4 Code Ownership**:
   - `0x06004000..0x0600400B` (12 bytes) promoted to `CONFIRMED_CODE / EXECUTED`.
   - Remainder of mapped module extent (`0x0600400C..0x06086BFF`) retains conservative `PROBABLE_CODE / HIGH`.
3. **D5 Basic-Block CFG**:
   - Explicit CFG record documented in `block_06004000.md`.
   - Terminator `BRA` has direct taken exit `0x06004012` and no fallthrough exit (`fallthrough = nullopt`).
4. **Oracle Replay & Parity**:
   - Full 6-instruction block replayed against Mednafen pre-state and post-state.
   - Zero register divergences across all CPU registers (`R0..R15`, `PC`, `PR`, `SR/T`, `GBR`, `VBR`, `MACH`, `MACL`).
   - Zero memory effect divergences.

## Evidence Artifacts

- Block CFG Record: `block_06004000.md`
- Reference Decode Manifest: `../T2-D3-sh2-decode/reference_decode_manifest.json`
- Cross-Check Evidence: `../T2-D3-sh2-decode/decode_crosscheck_evidence.md`
- Unit Tests: `tests/sh2/test_sh2_block.cpp`, `tests/sh2/test_sh2_decoder.cpp`, `tests/sh2/test_sh2_l0_semantics.cpp`
