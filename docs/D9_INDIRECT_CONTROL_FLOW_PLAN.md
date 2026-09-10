# D9 — Indirect Control-Flow Handling Architectural Plan & First Candidate Specification

Status: **READY_FOR_BOUNDED_TEST**  
Capability: **D9 — Indirect Control-Flow Handling**  
Baseline Commit: `b2a326852dd1f3d01596310d6dc25fc5b10d2109`  
Authoritative Reference: `docs/DEVELOPMENT_PLAN.md`, `AGENTS.md`, ADR D-006, D-009, D-011, D-012, D-014  

---

## 1. Executive Summary & Canonical Capability Definition

Capability **D9** is defined in `docs/DEVELOPMENT_PLAN.md` as:
> **Indirect Control-Flow Handling**  
> Strategy for blocks containing indirect jumps, calls, or computed branches.  
> Required bounded deliverable: runtime dispatch mechanism OR evidence-based target resolution for at least one indirect-flow block.  
> UNKNOWN targets remain on interpreter/fallback.

This document establishes the architectural foundation, execution contracts, memory snapshot generalization, and verification matrix for indirect control flow in Sega-Thor-2. It qualifies the first indirect-flow candidate block (`bb_06004280`), defines the pre-D9 prerequisite chain, establishes the unknown target fail-closed policy, and schedules the exact re-entry trigger for discovery method M-03.

---

## 2. Audit of Current Single-Block Architecture (D8 $\rightarrow$ D9 Delta)

An audit of the D8 production implementation (`include/thor/recomp/native_dispatcher.hpp`, `src/recomp/native_dispatcher.cpp`, `include/thor/recomp/shadow_checker.hpp`, `include/thor/sh2/sh2_block.hpp`, `src/recomp/block_compiler.cpp`) identifies ten foundational assumptions:

| # | Current Single-Block Implementation Fact | Architectural Classification | D9 Generalization Requirement |
|---|---|---|---|
| 1 | `RegisteredNativeBlock` contains a static `target_pc` field (`0x06004012`). | `VALID_D8_SPECIALIZATION` | **`MUST_GENERALIZE_FOR_D9`**: Exit target must be computed dynamically from post-execution architectural CPU state. |
| 2 | `RegisteredNativeBlock` contains a single fixed `cycle_cost` (`27u`). | `VALID_D8_SPECIALIZATION` | **`MUST_GENERALIZE_FOR_D9`**: Timing must account for instruction cost, cache line fills, SDRAM wait states, and pipeline refill. |
| 3 | `NativeDispatcher::dispatch_step` returns `out_target_pc = block.target_pc` from registration metadata. | `MUST_GENERALIZE_FOR_D9` | **`MUST_GENERALIZE_FOR_D9`**: Dispatcher must assign `out_target_pc = live_cpu.pc` directly from the executed candidate post-state. |
| 4 | `NativeDispatcher::dispatch_step` hardcodes literal address `0x06004064` and `live_regs.r[1]` in pre-state memory setup. | `VALID_D8_SPECIALIZATION` | **`MUST_GENERALIZE_FOR_D9`**: Memory dependencies must be declaratively specified via generator descriptors or handled via a copy-on-read facade. |
| 5 | `Sh2BasicBlock` only recognizes `OpcodeId::BRA` for branch target calculation (`compute_branch_target()`). | `MUST_GENERALIZE_FOR_D9` | **`MUST_GENERALIZE_FOR_D9`**: Basic block model must support `JSR`, `BSR`, `JMP`, `RTS`, `BT`, `BF`. |
| 6 | Block identity and registry is keyed only for single block `0x06004000`. | `VALID_D8_SPECIALIZATION` | **`MUST_GENERALIZE_FOR_D9`**: Registry map must support multiple disjoint blocks keyed by start PC with individual descriptors. |
| 7 | No general representation exists for an indirect exit whose runtime target is produced by guest register computation. | `MUST_GENERALIZE_FOR_D9` | **`MUST_GENERALIZE_FOR_D9`**: Introduce `BlockExitDescriptor` distinguishing direct, indirect call, indirect jump, and return. |
| 8 | No native-to-interpreter dynamic-target continuation contract is explicitly proven. | `MUST_GENERALIZE_FOR_D9` | **`MUST_GENERALIZE_FOR_D9`**: Define contract where native block commits state and cleanly resumes original interpreter at `out_target_pc`. |
| 9 | No multi-block chaining policy exists. | `VALID_D8_SPECIALIZATION` | Retain for D9: first bounded proof does **not** require native-to-native chaining; target execution resumes on interpreter. |
| 10 | Event/timing qualification is block-specific. | `VALID_D8_SPECIALIZATION` | **`MUST_GENERALIZE_FOR_D9`**: Bounded event metadata and cycle checks must be parameterized per registered block descriptor. |

---

## 3. First Bounded Candidate: Startup Indirect Call Block `bb_06004280`

### 3.1 Candidate Profile
- **Address Range:** `0x06004280 .. 0x06004288` (last instruction is delay slot at `0x06004288`)
- **Byte Length:** 10 bytes (5 16-bit instructions)
- **Module & CPU:** `0TH2.BIN` (offset `+0x000280`), `MASTER_SH2`
- **Candidate Bytes (Hex):** `D5 36 D4 37 D3 37 43 0B 00 09`
- **SHA-256 (Candidate Block Bytes Only):**  
  `8879cbe14f58a5fbc4eb9545e1cc41b3593e306cab114769a94f814a18bcb770`

### 3.2 Disassembly & Semantics
1. `0x06004280`: `D5 36` — `MOV.L @(0xD8, PC), R5`  
   Effective Address: `((0x06004280 & ~3) + 4) + (0x36 * 4) = 0x0600435C`. Reads `0x002DA000` into `R5` (destination buffer for `TH2.LOW` in Low Work RAM).
2. `0x06004282`: `D4 37` — `MOV.L @(0xDC, PC), R4`  
   Effective Address: `((0x06004282 & ~3) + 4) + (0x37 * 4) = 0x06004360`. Reads `0x06081C20` into `R4` (pointer to ASCII string `"TH2.LOW"`).
3. `0x06004284`: `D3 37` — `MOV.L @(0xDC, PC), R3`  
   Effective Address: `((0x06004284 & ~3) + 4) + (0x37 * 4) = 0x06004364`. Reads `0x0600A0F8` into `R3` (entry address of disc streaming / loading routine).
4. `0x06004286`: `43 0B` — `JSR @R3`  
   Indirect subroutine call. Evaluates branch target from `R3` (`0x0600A0F8`), stores return address in Procedure Register (`PR = PC + 4 = 0x0600428A`), and branches after the delay slot.
5. `0x06004288`: `00 09` — `NOP`  
   Delay slot instruction. Executes atomically before control transfers to `0x0600A0F8`.

### 3.3 Dynamic Oracle Trace (Mednafen Debug Fork `155426661b7ac3152e2c93a98da60ac33002b908`)
- **Cold Boot Arrival:** Hit 2 at frame `702`, master cycle `316309168` (following `RTS` return from previous initialization subroutine `0x0600447C`).
- **Retirement Progression:**
  - `0x06004280`: `R5 = 0x002DA000`, cycle `316309169` (+1 cycle)
  - `0x06004282`: `R4 = 0x06081C20`, cycle `316309171` (+2 cycles)
  - `0x06004284`: `R3 = 0x0600A0F8`, cycle `316309172` (+1 cycle)
  - `0x06004286`: `PR = 0x0600428A`, cycle `316309187` (+15 cycles target fetch & pipeline refill)
  - `0x06004288`: Delay slot `NOP` completes, target `0x0600A0F8` enters at cycle `316309189` (+2 cycles)
- **Timing Reconciliation:**
  - `BLOCK_ENTRY_CYCLE = 316309168` (master cycle at initial instruction fetch `0x06004280`)
  - `DELAY_SLOT_ENTRY_CYCLE = 316309187` (+19 cycles relative to entry; delay slot `0x06004288` entered following branch pipeline refill)
  - `BLOCK_EXIT_TARGET_ENTRY_CYCLE = 316309189` (+21 cycles relative to entry; execution begins at target `0x0600A0F8`)
  - `BLOCK_DURATION = 21 cycles` (`316309189 - 316309168 = 21`)
  - *Accounting Note:* The 19-cycle timestamp (`316309187`) was solely entry into the delay slot instruction. Full block completion and architectural target entry occurs after the 2-cycle delay slot retires at cycle `316309189`, giving an exact total duration of 21 cycles.
- **Exit State:** `PC = 0x0600A0F8`, `PR = 0x0600428A`, total block duration = 21 cycles (`316309189 - 316309168 = 21`).

---

## 4. Code Ownership Classification & Evidence Boundaries

Per `AGENTS.md` and ADR D-011 / D-012, code ownership must not bootstrap itself:
- **Module Provenance:** Disc file `0TH2.BIN` is proven byte-for-byte in RAM (`0x06004000..0x06086BFF`) via ADR D-011.
- **Static Candidate:** `bb_06004280` is statically bounded as 5 instructions ending in `JSR @R3` + delay slot.
- **Dynamic Evidence:** 100% of candidate instructions were observed executing during cold boot.
- **Ownership State:** Address range `0x06004280..0x06004288` is classified as **`QUALIFIED_CANDIDATE`**. It is **not** promoted to `CONFIRMED_CODE` or `BOUNDED_PROOF` until its own L0, shadow, and native gates pass.

---

## 5. Pre-D9 Prerequisite Chain

Before `bb_06004280` can be promoted to native execution, all instructions must satisfy the verification hierarchy:

| Opcode | Mnemonic | Status in Repo | Action Required |
|---|---|---|---|
| `0xD536` | `MOV.L @(disp,PC), R5` | `ALREADY_D3_L0_PROVEN` | None (covered by existing L0 vector suite) |
| `0xD437` | `MOV.L @(disp,PC), R4` | `ALREADY_D3_L0_PROVEN` | None |
| `0xD337` | `MOV.L @(disp,PC), R3` | `ALREADY_D3_L0_PROVEN` | None |
| `0x430B` | `JSR @R3` | `NEEDS_D3_L0_PROOF` | **Must implement SH-2 decoder & executor semantics, PR update, and L0 test vectors** (Satisfied in D9.1) |
| `0x0009` | `NOP` | `ALREADY_D3_L0_PROVEN` | None |

*Important:* Method M-07 (SaturnRecomp reference data) is an accelerator and cross-check only. It cannot substitute for independent D3 L0 proof in Sega-Thor-2.

### Exact Staged Sub-Gate Sequence
```text
D9.P0 — Architecture, Candidate Qualification & Plan (This Deliverable)
  │
  ▼
D9.1  — Opcode L0 Semantics (JSR @Rn, PR update, delay slot) & Block Model Extension
  │
  ▼
D9.2  — Generic Dynamic-Exit Representation & Declarative Memory Descriptors
  │
  ▼
D9.3  — Isolated Shadow Qualification for bb_06004280 (Zero-Divergence Proof)
  │
  ▼
D9.4  — Authoritative Native Indirect Override & Dynamic Continuation
  │
  ├──────────────────────────────────────────────────────┐
  ▼                                                      ▼
M-03  — Bounded SaturnAutoRE Harvester Re-Entry    D9.5 — Multi-Target / Secondary Indirect Expansion
```

---

## 6. D9 Dynamic Exit Model Design

### 6.1 Exit Classification (`BlockExitKind`)
```cpp
enum class BlockExitKind : uint8_t {
    DIRECT = 0,             // Unconditional static branch (BRA, BSR)
    CONDITIONAL,            // Conditional branch (BT, BF) with taken and fallthrough
    INDIRECT_JUMP,          // Dynamic jump (JMP @Rn)
    INDIRECT_CALL,          // Dynamic call (JSR @Rn), updates PR
    RETURN,                 // Return from subroutine (RTS), targets PR
    FALLBACK_UNSUPPORTED    // Unsupported instruction or abnormal condition
};
```

### 6.2 Exit Representation (`BlockExitDescriptor`)
```cpp
struct BlockExitDescriptor {
    BlockExitKind exit_kind = BlockExitKind::DIRECT;
    uint32_t target_pc = 0;                     // Computed from architectural post-state
    std::optional<uint32_t> fallthrough_pc;     // For conditional branches
    std::optional<uint32_t> pr_value;           // Procedure register value on exit
    bool has_delay_slot = false;
    bool delay_slot_completed = false;
    uint32_t cycle_cost = 0;
    BoundedEventMetadata event_safety{};
};
```

### 6.3 Critical Invariant
For any indirect block, the runtime target **must** be derived strictly from the guest post-state computation (`live_cpu.pc = live_cpu.r[instr.rn]`):
$$\text{Target}_{\text{runtime}} = \text{State}_{\text{post}}.\text{PC}$$
It **must never** be hardcoded from an observed trace constant (e.g. `0x0600A0F8`).

---

## 7. Execution Architecture: Native Indirect Source with Interpreter Continuation

The minimal defensible D9 architecture decouples source block translation from target block translation:

```text
[Live SH-2 PC = 0x06004280]
           │
           ▼
[NativeDispatcher::dispatch_step]
           │
     (Check Eligibility & Shadow Run)
           │
           ├─ Match ──► [Commit Native Post-State]
           │            - R5 = 0x002DA000
           │            - R4 = 0x06081C20
           │            - R3 = 0x0600A0F8
           │            - PR = 0x0600428A
           │            - out_target_pc = live_cpu.pc (0x0600A0F8)
           │            - out_cycles_advanced = 19
           │
           ▼
[Return true to Mednafen Native Bridge]
           │
           ▼
[Mednafen Interpreter Resumes at out_target_pc (0x0600A0F8)]
(Target block 0x0600A0F8 executes normally via interpreter)
```

**Proof Independence:** This architecture proves native indirect control flow without requiring:
- native translation of the target block (`0x0600A0F8`);
- exhaustive target-set recovery;
- jump-table enumeration;
- whole-game CFG recovery.

Native-to-native block chaining is an optional optimization deferred to D9.5.

---

## 8. Fail-Closed Unknown Target Policy

| Scenario | Condition | Dispatcher Action | Architectural Result |
|---|---|---|---|
| **A** | Source block ineligible (hash, rev, CPU mismatch) | Do not dispatch; return `false` | Interpreter executes source block from clean state. Zero partial native commit. |
| **B** | Source block shadow divergence | Abort native commit; return `false` | Interpreter executes source block from clean state. Zero partial native commit. |
| **C** | Source block matches; dynamic target is **not** native-registered | Commit verified source block; return `true` with `out_target_pc = computed_target` | Interpreter resumes cleanly at computed target. Parity preserved. |
| **D** | Malformed / impossible target (e.g. unaligned PC, odd address) | Follow SH-2 architectural semantics | Hardware triggers address error exception (VBR + vector). Host does not invent synthetic exception. |
| **E** | Registered target exists but its identity / event guard fails | Do not chain into target natively | Interpreter resumes execution at the target PC. |

---

## 9. Call Semantics Contract (`JSR @Rn`)

Per Hitachi SH-2 Architecture Manual:
1. **Target Evaluation:** Target address is read from `Rn` before delay slot execution. (Even if delay slot modifies `Rn`, the pre-delay-slot `Rn` value governs the branch destination).
2. **Procedure Register (`PR`):** `PR` is loaded with `PC + 4`, which is the address of the instruction immediately following the delay slot.
3. **Delay Slot Execution:** Exactly one instruction in the delay slot executes before control transfers.
4. **Illegal Slot Instructions:** Branch, jump, and return instructions (`BRA`, `BSR`, `JMP`, `JSR`, `RTS`, `RTE`, `TRAPA`) are prohibited in a delay slot and trigger an Illegal Slot Instruction exception.
5. **Event / Interrupt Atomicity:** Hardware mask prevents interrupts from being accepted between `JSR` and its delay slot. The two instructions execute as an atomic sequence.

---

## 10. Memory Snapshot Generalization Contract

Current D8 hardcoding of literal `0x06004064` and `live_regs.r[1]` in `NativeDispatcher` cannot scale. For D9, memory pre-state capture is generalized:

### 10.1 Evaluated Architecture Options
- **Option A (Generator-Produced Dependency Descriptors):** The block compiler inspects instructions during translation and emits an array of required memory address ranges (static literals and base registers).
- **Option B (Copy-on-Read Memory Facade):** An `ISh2Memory` wrapper intercepts all reads from live hardware memory during shadow execution, logs the access, and populates the shadow pre-state on demand. Writes are strictly buffered in an isolated delta layer.
- **Option C (Lazy Instrumented Snapshot):** Page-level memory protection.

### 10.2 Recommended Architecture
**Hybrid of Option A and Option B:**
- Static literals (e.g. `MOV.L @(disp,PC)`) are declared in the `BlockIdentityDescriptor::memory_dependencies`.
- Dynamic register-indirect reads are captured via a read-only hardware callback wrapper into `pre_state.memory` before candidate execution.
- *Isolation Invariant:* The candidate function executes strictly against an independently cloned `Sh2FlatMemory` buffer. Zero reads observe post-oracle mutations. MMIO addresses are prohibited and fail closed.

---

## 11. Timing, Cache, and Scheduler Contract

The D8 timing reconciliation proved that register equality is insufficient:
1. **Cache Controller Integration:** Native memory reads must route through the Saturn cache controller (`CPU[0].MRFP/MWFP`) to ensure cache lines are properly warmed, preventing artificial SDRAM wait states in subsequent code.
2. **Pipeline Refill Cost:** Indirect calls require pipeline refill cycles (+15 cycles in Mednafen).
3. **Cycle Accounting:**
   $$\text{Total Block Cycles} = \sum \text{Instruction Execution Cycles} + \text{Bus Wait Cycles} + \text{Branch Refill Cycles}$$
   For `bb_06004280`: $1 + 2 + 1 + 15 = 19\text{ cycles}$.
4. **Verification Requirement:** Schedular timestamp comparisons must show **zero cycle drift** at:
   - source block entry (`0x06004280`);
   - source block exit / target entry (`0x0600A0F8`);
   - downstream checkpoint (`0x060042E0`).

---

## 12. Target Observation Database Schema

To track dynamic targets without assuming exhaustive knowledge:
```json
{
  "schema_version": "1.0",
  "observations": [
    {
      "revision_id": "thor2_ntsc_patched_fe11d2fb",
      "cpu": "MASTER_SH2",
      "module_id": "0TH2.BIN",
      "source_pc": "0x06004286",
      "target_pc": "0x0600A0F8",
      "workload": "cold_boot",
      "hit_count": 1,
      "last_observed_cycle": 316309187
    }
  ]
}
```
*Rule:* An observed target is empirical evidence only. It does not establish target-set completeness, does not prove unobserved targets impossible, and does not authorize native execution of the target block.

---

## 13. Multi-Block Scope Boundaries

- **D9 Minimal Scope:** Indirect control flow handling (dynamic exit resolution + interpreter continuation).
- **Expanded D9 Scope:** Jump-table dispatch, dynamic subroutine return (`RTS`), multi-target registry.
- **D12 Structural Recovery Scope:** Function boundary recovery, procedural calling conventions, call graph reconstruction.
- **Interpreter Fallback:** All unregistered or unverified targets remain on the original interpreter.

---

## 14. M-03 Re-Entry Trigger Specification

ADR D-012 records method **M-03 (SaturnAutoRE Offline Candidate Harvester)** as `PREREQUISITE_BLOCKED_AT_D9`.

### 14.1 Exact Re-Entry Gate
The trigger for unblocking M-03 is the completion of **`D9.4` (Authoritative Native Indirect Override & Dynamic Continuation)**.

### 14.2 Operating Constraints for M-03
- **Role:** Discovery-only candidate harvester for indirect call-sites in `0TH2.BIN`.
- **Zero Autonomous Promotion:** M-03 output is treated as untrusted hypothesis data.
- **Mandatory Gates:** Every harvested candidate must independently pass D3 (L0 semantics), D4 (execution proof), D5 (block boundary proof), and D7 (isolated shadow verification).
- **No Private Binaries:** Output committed to repository is limited to text manifests and metadata.

---

## 15. Negative Control Matrix for Future D9 Implementation

| Test Case | Injected Fault / Vector | Expected Dispatcher Behavior | Commit Result | Fallback Point |
|---|---|---|---|---|
| **NC-01** | Source byte corrupted at `0x06004286` (`0x430B` $\rightarrow$ `0x0009`) | `check_block_eligibility` fails (`CONTENT_BYTE_MISMATCH`) | No commit (`partial=0`) | Interpreter executes source |
| **NC-02** | Wrong revision ID | `check_block_eligibility` fails (`REVISION_MISMATCH`) | No commit (`partial=0`) | Interpreter executes source |
| **NC-03** | Target CPU mismatch (`SLAVE_SH2`) | `check_block_eligibility` fails (`CPU_MISMATCH`) | No commit (`partial=0`) | Interpreter executes source |
| **NC-04** | Slave SH-2 active during dispatch | Event safety guard fails | No commit (`partial=0`) | Interpreter executes source |
| **NC-05** | SCU DMA active during dispatch | Event safety guard fails | No commit (`partial=0`) | Interpreter executes source |
| **NC-06** | IRQ pending during dispatch | Event safety guard fails | No commit (`partial=0`) | Interpreter executes source |
| **NC-07** | Synthetic target alteration (`R3 = 0x0600BEEF`) | Candidate outputs `PC = 0x0600BEEF` | Matches oracle | Resumes interpreter at `0x0600BEEF` |
| **NC-08** | Hardcoded target detector (Candidate emits `0x0600A0F8` when R3 modified) | Shadow checker catches `PROGRAM_COUNTER` divergence | No commit (`partial=0`) | Interpreter executes source |
| **NC-09** | Return address divergence (`PR` mutated in candidate) | Shadow checker catches `CONTROL_REGISTER` divergence | No commit (`partial=0`) | Interpreter executes source |
| **NC-10** | Delay slot mutation (delay slot writes invalid memory) | Shadow checker catches `MEMORY_EFFECT` divergence | No commit (`partial=0`) | Interpreter executes source |
| **NC-11** | Unregistered target PC | Dispatcher returns `out_target_pc`, target not in registry | Source committed | Resumes interpreter at target |
| **NC-12** | Target registered but ineligible | Dispatcher returns `out_target_pc`, target fails eligibility | Source committed | Resumes interpreter at target |
| **NC-13** | Cycle count mismatch | Timing verification fails | Gate fails | Debug/repair required |
| **NC-14** | Cache line cold drift | Continuation checkpoint fails cycle parity | Gate fails | Cache controller repair required |

---

## 16. First D9 Bounded Verification Contract

For promotion of `bb_06004280` under sub-gate `D9.4`:
1. **Differential Equivalence:**
   - Bit-identical match across all 23 CPU registers (`R0-R15`, `PC`, `SR`, `PR`, `GBR`, `VBR`, `MACH`, `MACL`).
   - Ordered memory reads match oracle byte-for-byte.
   - Dynamic target `out_target_pc == 0x0600A0F8`.
   - Return address `live_regs.pr == 0x0600428A`.
2. **Retirement Parity:**
   - In replaced interval `0x06004280..0x06004288`, original interpreter instruction retirements $= 0$.
   - Partial commit count $= 0$ on any failure.
3. **Continuation Parity:**
   - Original interpreter seamlessly resumes execution at `0x0600A0F8`.
   - Downstream checkpoint at `0x060042E0` matches pure-interpreter baseline with **0 cycles timing delta**.
4. **Reproducibility:**
   - Independent cold-boot runs (Run A and Run B) yield 100% identical results.

---

## 17. D9 Status Decision

Because the first indirect-flow candidate block `bb_06004280`:
- has exact bounded bytes and SHA-256 (`8879cbe14f58a5fbc4eb9545e1cc41b3593e306cab114769a94f814a18bcb770`);
- has verified dynamic cold-boot execution trace and exact timing (19 cycles);
- has exact identified basic block boundaries (5 instructions, 10 bytes);
- has an explicit prerequisite chain (`JSR @Rn` L0 semantics identified for D9.1);
- has a fully specified dynamic exit and continuation architecture;
- has an explicit fail-closed unknown target policy;
- has zero unresolved architectural blockers;

Capability status is formally declared:
$$\mathbf{D9 = READY\_FOR\_BOUNDED\_TEST}$$
*(Not marked BOUNDED_PROOF until D9.1..D9.4 pass).*
