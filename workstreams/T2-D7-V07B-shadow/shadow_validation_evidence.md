# Shadow Validation Evidence — V-07B (`bb_06004000`)

Status:
- **`V-07B: PASS (0 positive divergences, 100% negative fault detection, complete pre-state isolation)`**
- **`D7: BOUNDED_PROOF for bb_06004000`**
- **`D8: PROPOSED`** (Do NOT start or claim native promotion)

---

## 1. Architecture & Reusability Contract

The reusable framework `thor::recomp::ShadowChecker` (`include/thor/recomp/shadow_checker.hpp`, `src/recomp/shadow_checker.cpp`) provides:

1. **Deterministic Pre-State Cloning**:
   `ShadowChecker::run_and_compare` accepts a `const BlockPreState& immutable_pre_state`, cloning two physically distinct CPU states and sparse flat memory maps (`oracle_cpu`/`oracle_mem` and `candidate_cpu`/`candidate_mem`).
2. **Strict Anti-Aliasing Guard**:
   Enforces pointer inequality:
   `&oracle_mem != &candidate_mem && &oracle_cpu != &candidate_cpu && &oracle_mem != &immutable_pre_state.memory && &oracle_cpu != &immutable_pre_state.cpu_state`.
   Fails closed with `ShadowStatus::EXECUTION_ERROR` if mutable state is shared.
3. **Fail-Closed Eligibility Check**:
   Invokes `check_block_eligibility(proven_identity, candidate_identity, pre_state.memory)` before any candidate execution. Rejects mismatched revision, module, CPU, range, or invalid bytes with `ShadowStatus::INELIGIBLE`.
4. **Authoritative Oracle Execution**:
   Executes verified basic block interpreter `execute_basic_block(block, oracle_cpu, oracle_mem)` to obtain authoritative post-state and memory log.
5. **Candidate Execution**:
   Executes candidate lambda/function pointer `candidate_fn(candidate_cpu, candidate_mem)`.
6. **Exhaustive Outcome Comparator**:
   `ShadowChecker::compare_outcomes` validates:
   - Registers `R0` through `R15`.
   - Program counter `PC`.
   - Status register `SR`.
   - Special/control registers `PR`, `GBR`, `VBR`, `MACH`, `MACL`.
   - Ordered memory access log: count of accesses, access kind (`READ`/`WRITE`), destination address, access width (`size_bytes`), value read/written, and access ordering.
   - Bounded event safety metadata (`mmio_accessed`, `irq_accepted`, `scu_dma_crossing`, `slave_sh2_active`, `delay_slot_atomic`).

---

## 2. Positive Shadow Validation (4 Vectors, 0 Divergences)

Evaluated via `test_shadow_positive.cpp` (`tests/recomp/test_shadow_positive.cpp`):

### 2.1 Synthetic Vector A (Arbitrary Non-Zero Values)
- Pre-State: `R0=0x06002000`, `R1=0x06004000`, `R4=0x11112222`, `R15=0x06001000`, `SR=1`.
- Post-State: `R6=0x00001234`, `R15=0x06002000`, `R4=0xDEADBEEF`, `PC=0x06004012`.
- Result: **0 divergences, Status: MATCH**.

### 2.2 Synthetic Vector B (Sign-Extension Boundary)
- Pre-State: Target 16-bit word at `R1` has high bit set (`0x8001`). Memory pool contains `0x80000000`.
- Post-State: `R6=0xFFFF8001` (sign-extended to 32 bits), `R4=0x80000000`, `PC=0x06004012`.
- Result: **0 divergences, Status: MATCH**.

### 2.3 Synthetic Vector C (Zero Boundary & Clean SR)
- Pre-State: `R0=0x0`, `R1=0x06004000`, `R4=0x0`, `R15=0x0`, `SR=0`.
- Post-State: `R6=0x00000000`, `R15=0x00000000`, `R4=0x00000000`, `PC=0x06004012`.
- Result: **0 divergences, Status: MATCH**.

### 2.4 Real Thor 2 Mednafen Cold-Boot Replay
- Pre-State: Authoritative entry state captured from Mednafen cold boot (`R0=0x06002EDC`, `R1=0x06004000`, `R4=0x00002650`, `R15=0x06001000`, `PC=0x06004000`, `SR=1`, `VBR=0x06000000`).
- Differential vs Oracle:
  - `R0`: `0x06002EDC` (MATCH)
  - `R1`: `0x06004000` (MATCH)
  - `R4`: `0x060917DC` (MATCH)
  - `R6`: `0x00006611` (MATCH)
  - `R15`: `0x06002EDC` (MATCH)
  - `PC`: `0x06004012` (MATCH)
  - `SR`: `0x00000001` (MATCH)
  - `VBR`: `0x06000000` (MATCH)
  - Memory read log: exactly 3 ordered reads (`[READ 0x06004000, 2, 0x6611]`, `[READ 0x06004064, 4, 0x06081C10]`, `[READ 0x06081C10, 4, 0x060917DC]`).
  - Memory write log: exactly 0 writes.
- Result: **0 divergences, Status: MATCH**.

---

## 3. Negative Fault Detection Matrix (24/24 Detected, 100%)

Evaluated via `test_shadow_negative.cpp` (`tests/recomp/test_shadow_negative.cpp`):

| Fault Category | Injected Fault | Expected Divergence Category | Detection Result |
|---|---|---|---|
| Register Fault | `R0 = 0xDEAD0000` | `REGISTER` | **DETECTED** |
| Register Fault | `R4 = 0xDEAD0004` | `REGISTER` | **DETECTED** |
| Register Fault | `R6 = 0xDEAD0006` | `REGISTER` | **DETECTED** |
| Register Fault | `R15 = 0xDEAD000F` | `REGISTER` | **DETECTED** |
| Register Fault | `PC = 0x06004008` | `PROGRAM_COUNTER` | **DETECTED** |
| Register Fault | `SR = 0x00000002` | `STATUS_REGISTER` | **DETECTED** |
| Control Register | `PR = 0x06001234` | `CONTROL_REGISTER` | **DETECTED** |
| Control Register | `GBR = 0x06005678` | `CONTROL_REGISTER` | **DETECTED** |
| Control Register | `MACH = 0x00000001` | `CONTROL_REGISTER` | **DETECTED** |
| Control Register | `MACL = 0x00000002` | `CONTROL_REGISTER` | **DETECTED** |
| Memory Write | Candidate omitted write | `MEMORY_EFFECT_COUNT` | **DETECTED** |
| Memory Write | Candidate added extra write | `MEMORY_EFFECT_COUNT` | **DETECTED** |
| Memory Write | Wrong write address (`0x06080004` vs `0x06080000`) | `MEMORY_EFFECT_ADDRESS` | **DETECTED** |
| Memory Write | Wrong write width (2-byte vs 4-byte) | `MEMORY_EFFECT_SIZE` | **DETECTED** |
| Memory Write | Corrupted write value (`0xDEADBEEF` vs `0x12345678`) | `MEMORY_EFFECT_VALUE` | **DETECTED** |
| Memory Order | Reversed order of 2 writes | `MEMORY_EFFECT_ADDRESS` / sequence | **DETECTED** |
| Event Safety | `mmio_accessed = true` | `EVENT_SAFETY_METADATA` | **DETECTED** |
| Event Safety | `irq_accepted = true` | `EVENT_SAFETY_METADATA` | **DETECTED** |
| Event Safety | `scu_dma_crossing = true` | `EVENT_SAFETY_METADATA` | **DETECTED** |
| Event Safety | `slave_sh2_active = true` | `EVENT_SAFETY_METADATA` | **DETECTED** |
| Event Safety | `delay_slot_atomic = false` | `EVENT_SAFETY_METADATA` | **DETECTED** |
| Eligibility | Module name mismatch (`SOMETHING_ELSE.BIN`) | `INELIGIBLE` (`MODULE_MISMATCH`) | **DETECTED** |
| Eligibility | Unproven provenance | `INELIGIBLE` (`PROVENANCE_NOT_PROVEN`) | **DETECTED** |
| Eligibility | Byte modification at runtime (`0x66` -> `0x09`) | `INELIGIBLE` (`CONTENT_BYTE_MISMATCH`) | **DETECTED** |

**Total Negative Controls: 24. Detected: 24 (100.0%). False Passes: 0.**

---

## 4. Pre-State Isolation & Anti-Aliasing Proof

Evaluated via `test_shadow_isolation.cpp` (`tests/recomp/test_shadow_isolation.cpp`):

1. **Candidate Mutation Non-Contamination**:
   An intentionally aggressive candidate performing illegal writes to `R0`, `R1`, `PC`, and memory addresses `0x06085000`, `0x06090000` is executed via `run_and_compare`.
   - Result: `res.status == ShadowStatus::DIVERGENCE`.
   - `pre_state.cpu_state` remains completely unmodified (`orig_r0` preserved).
   - `pre_state.memory` remains completely unmodified (`peek8(0x06085000)` preserved, `0x06090000 == 0`).
   - `pre_state.memory.log()` is strictly empty (never contaminated).
2. **Oracle Non-Contamination of Candidate Pre-State**:
   Oracle executes through standard interpreter prior to candidate execution. Candidate inspects its input arguments `state` and `mem` at entry and asserts that they match the pristine initial pre-state.
3. **Anti-Aliasing Validation**:
   Inspects memory and CPU object addresses passed into candidate:
   - `&candidate_mem != &pre_state.memory`
   - `&candidate_cpu != &pre_state.cpu_state`
   - `&candidate_mem != &oracle_mem`
   - `&candidate_cpu != &oracle_cpu`

---

## 5. Conclusion & Policy Compliance

- Zero positive divergences observed across 4 vectors.
- 100% negative fault detection across 24 injection controls.
- Full pre-state storage isolation proven.
- Framework is reusable across any block descriptor and callable candidate.
- Native promotion status remains strictly `PROPOSED` (D8 / V-07C unstarted).
