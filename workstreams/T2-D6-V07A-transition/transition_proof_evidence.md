# Transition Proof Evidence — V-07A (`bb_06004000`)

Status: **`V-07A: PASS (transition divergences = 0)`**

---

## 1. Mechanical Generation Contract

The mechanical compiler `thor::recomp::compile_block_to_cpp` consumes the decoded `Sh2BasicBlock` representation and emits deterministic C++20.

Strict constraints verified:
1. **No Interpreter Wrappers**: Generated block does not call `decode_sh2`, `execute_sh2_instruction`, `step_sh2`, or `execute_basic_block`.
2. **Link-Time Symbol Isolation**: The library `thor_generated_bb_06004000` does not link against `thor_sh2`. The test `test_generated_link_isolation` links exclusively against `thor_generated_bb_06004000` with 0 unresolved symbols.
3. **No Hardcoded Values**: Register inputs and memory read outputs are dynamically evaluated from `state.r` and `mem.read*()`.
4. **Mechanical Specialization**: Specializes instruction addresses, register indices, literal pool EA, and branch exit target `0x06004012`.
5. **Fail-Closed Policy**: Unsupported instructions or malformed blocks return `std::nullopt`.

---

## 2. Differential Transition Vectors

The compiled generated block `bb_06004000(state, mem)` was compared against the verified interpreter `execute_basic_block(block, state, mem)` using isolated pre-states.

### 2.1 Synthetic Vector A (Arbitrary Non-Zero Pattern)
- Pre-State: `R0=0x06002000`, `R1=0x06004000`, `R4=0x11112222`, `R15=0x06001000`, `PC=0x06004000`. Memory populated at `0x06004000` (`0x1234`), literal pool `0x06004064` (`0x06085000`), and target `0x06085000` (`0xDEADBEEF`).
- Result: **0 CPU divergences, 0 memory log divergences**.
- Post-State: `PC=0x06004012`, `R6=0x00001234`, `R15=0x06002000`, `R4=0xDEADBEEF`.

### 2.2 Synthetic Vector B (Sign-Extension Boundary)
- Pre-State: Memory at `0x06004000` has negative 16-bit word `0x8001`. Target memory at `0x06089000` has high-bit word `0x80000000`.
- Result: **0 CPU divergences, 0 memory log divergences**.
- Post-State: `R6=0xFFFF8001` (exact architectural sign-extension), `R4=0x80000000`, `PC=0x06004012`.

### 2.3 Real Thor 2 Mednafen Cold-Boot Replay
- Pre-State: Captured entry state from Mednafen cold boot (`R0=0x06002EDC`, `R1=0x06004000`, `R4=0x00002650`, `R15=0x06001000`, `PC=0x06004000`, `SR=1`, `VBR=0x06000000`). Memory populated with retail binary bytes.
- Result vs Interpreter: **0 CPU divergences, 0 memory log divergences**.
- Result vs Accepted Mednafen Oracle:
  - `R0`: `0x06002EDC` (EXACT MATCH)
  - `R1`: `0x06004000` (EXACT MATCH)
  - `R4`: `0x060917DC` (EXACT MATCH)
  - `R6`: `0x00006611` (EXACT MATCH)
  - `R15`: `0x06002EDC` (EXACT MATCH)
  - `PC`: `0x06004012` (EXACT MATCH)
  - `SR`: `0x00000001` (EXACT MATCH)
  - `VBR`: `0x06000000` (EXACT MATCH)
  - Ordered Memory Reads: 3 reads matching sequence, addresses, and sizes.
  - Ordered Memory Writes: 0 writes.

---

## 3. Negative / Independence Controls

In `tests/recomp/test_v07a_transition.cpp`, the comparison harness was verified to fail when faults are injected:
1. Register Corruption (`R4 = 0xDEADBEEF`) -> `compare_cpu_and_memory` flags divergence.
2. PC Corruption (`PC = 0x0600400C`) -> `compare_cpu_and_memory` flags divergence.
3. Memory Log Corruption (injected unrecorded access) -> `compare_cpu_and_memory` flags divergence.

Conclusion: Generated transition divergences = **0**.
