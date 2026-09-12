# Context-Sensitive Shared-Epilogue Decomposition, Multi-Entry CFG Normalization, and Residual RTS Return-Domain Closure Report (T2-ASM-11)

**Task**: `T2-ASM-11 — Context-Sensitive Shared-Epilogue Decomposition, Multi-Entry CFG Normalization, and Residual RTS Return-Domain Closure`  
**Date**: 2026-09-12  
**Baseline Commit**: `2575529a047690eaa3f07702b5f19b86f08c9a1c`  
**Classification**: ASM-FIRST CONTROL-FLOW RECOVERY / EPILOGUE CLOSURE  

---

## 1. Executive Summary & Objective

Milestone `T2-ASM-11` was executed to advance the ASM-first proof track from the sound `T2-ASM-10.1` baseline (420 resolved RTS, 218 honest unresolved RTS) without metric-forcing or broad, unguided byte sweeps.

The milestone focused on three concrete, high-leverage bottlenecks:
1. **Context-Sensitive PR Dataflow Decomposition**: Decomposing shared epilogues across the 81 `UNRESOLVED_PR_PATH` sites by separating physical basic-block CFGs from logical entry contexts `(module, generation, pc, logical_entry, PR_generation, stack_frame_generation)`.
2. **Caller Return Domain Audit & False Call Edge Excision**: Auditing the 56 caller-blocked sites (including the 43 return edges revoked in T2-ASM-10.1). Our investigation proved that these 43 edges—and 2,288 total edges in the canonical entry graph—were `FALSE_CALL_EDGE` instances originating from literal pool 16-bit halfwords (e.g. `0xBA88` in `0x0609BA88`) falsely decoded as `BSR` call instructions.
3. **Function Boundary Normalization**: Resolving artificial function splits that separated function prologues (`sts.l pr, @-r15`) from their epilogues (`lds.l @r15+, pr; rts`), such as `0TH2.BIN_0x06008224` (originally assigned to pseudo-function `sub_0600812E`, normalized to prologue `0x06007C04`).

### Key Results
- **RTS V4 Certified Resolution**: **453 / 638 resolved (71.00%)**, **185 honest unresolved (29.00%)**.
  - Net increase of +33 soundly resolved sites (22 from PR path closure + 11 from caller domain recovery).
  - ZERO invalid resolved certificates (`INVALID_RESOLVED_CERTIFICATES == 0`).
  - ZERO empty return domains (`return_domain_count > 0` for all resolved sites).
  - ZERO return PCs in DATA or PADDING (`100% of return PCs strictly inside CONFIRMED_CODE`).
- **Calls and Jumps**: **1,588 / 1,588 (100.0%)** resolved.
- **Overall Indirect Resolution**: **2,041 / 2,226 (91.69%)**, **185 unresolved (8.31%)**.
- **Negative Controls**: Expanded from 74 to **82 controls** (8 new P11 controls: NC-BO through NC-BV), passing 100%.
- **Gate Status**:
  - `ASM_90_GATE`: **PASS** (91.69% >= 90.00%).
  - `FULL_ASM_GAME_GATE`: Maintained honestly at **NOT_YET_REPROVEN** (185 unresolved RTS sites and 498,392 SH-2 UNKNOWN bytes remain).
- **Invariants Preserved**:
  - 4/4 module reassembly byte-exact (0 differing bytes).
  - Full-disc SHA-256 exact (`fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8`).
  - Mednafen 6-scenario suite: ZERO divergence (exact register parity across all checkpoints).
  - 26/26 Linux CTests passing.

---

## 2. Root Cause Discovery: False Call Edges from Literal Pools

During the T2-ASM-10.1 audit, 36 certificates were demoted because their return PCs pointed into DATA literal pools. In T2-ASM-11, deep binary analysis identified the fundamental cause:
- In SH-2 machine code, the opcode format for `BSR label` is `1011 dddd dddd dddd` (`0xB...`).
- When literal pools contain 32-bit addresses (e.g. `0x0609BA88`), the lower 16-bit word is `0xBA88`.
- Historical naive disassemblers scanned the binary sequentially across data boundaries, encountered `0xBA88`, and decoded it as `BSR loc_0600714E`.
- Consequently, `0x06007C3A` was registered as a call site to `sub_0600714E`, and its return continuation was computed as `0x06007C3A + 4 = 0x06007C3E` (which lands directly on the next 32-bit literal pointer).

### Census of False Edges
Auditing all 14,656 edges in `canonical_entry_graph.json` against `module_byte_ownership_v3.json` revealed:
- **True Call/Branch Edges (source in CODE)**: **9,558**
- **False Call/Branch Edges (source in DATA)**: **2,288** (100% excised)
- **Unknown Threat Edges (source in UNKNOWN)**: **2,810** (retained as caller threats)

By excising the 2,288 false edges from DATA:
- Functions that previously had data return continuations (such as `0TH2.BIN_0x0600F752`, `0TH2.BIN_0x06010AC6`, `0TH2.BIN_0x06012E1C`) had their false caller edges stripped.
- All their remaining callers were verified to be in `CONFIRMED_CODE`, with 100% of return continuations in `CONFIRMED_CODE`, zero unknown caller threats, and complete caller domains.
- Functions whose *only* callers were false data decodes (e.g. `sub_0600714E`) were recognized as having no legitimate callers from code and were quarantined fail-closed as `UNRESOLVED_CALLER_DOMAIN`.

---

## 3. Context-Sensitive PR Dataflow & Epilogue Decomposition

### Engine Implementation
`tools/asm/context_sensitive_pr_engine.py` was built to construct a strict CODE-only CFG from `module_byte_ownership_v3.json` and trace backward from all 638 RTS sites to all reaching entry points.

Control transfer rules accurately model SH-2 delay slots:
- Unconditional delayed branches (`BRA`, `JMP`, `BRAF`) execute the delay slot at `pc + 2`, then transfer to target; delay slot does not fall through.
- Delayed conditional branches (`BT/S`, `BF/S`) branch to target or fall through to `pc + 4`.
- Delayed calls (`BSR`, `JSR`) execute delay slot at `pc + 2`, then return continuation is `pc + 4`.

### Census of the 81 Residual PR Sites
- **PROVEN_PR_STACK_SLOT**: **62 sites** trace backward to a single, unique `sts.l pr, @-r15` prologue, and exit through a matching `lds.l @r15+, pr` epilogue with balanced stack frame depth.
- **LEAF_UNTOUCHED_PR**: **17 sites** never modify PR along any reaching execution path (e.g., accessor helper `0TH2.BIN_0x0600467E` starting at `0x06004678`).
- **AMBIGUOUS_PR**: **2 sites** (`0TH2.BIN_0x060106A0` and `0TH2.BIN_0x0603A352`) have prologues located inside UNKNOWN regions (`0x06010568..0x0601057E` and `0x0603A2B0..0x0603A2BA`), correctly quarantined fail-closed.

---

## 4. Function Boundary Normalization

In historical Ghidra exports, internal branch labels or jump table targets caused functions to be artificially split into pseudo-functions (e.g., `sub_0600812E` starting at `0x0600812E`).
- Because `sub_0600812E` started mid-function, it had no `sts.l pr` prologue.
- Its epilogue at `0x06008216` (`lds.l @r15+, pr; rts`) appeared orphaned, leading prior tools to mark it `UNVERIFIED_PR`.
- CFG reachability analysis proved that `0x06008224` is strictly reached from prologue `0x06007C04` (`sts.l pr, @-r15`), with 731 reaching instructions and perfect stack depth balance (`add #-88, r15` at entry, `add #88, r15` at exit).
- Emitted `workstreams/T2-ASM-11/function_boundary_v4.json` normalizing artificial boundaries to verified prologues without altering binary bytes.

---

## 5. Summary of RTS V4 Resolution

| Category | Baseline (V3.1) | T2-ASM-11 (V4) | Delta | Reason |
| :--- | :---: | :---: | :---: | :--- |
| **Certified Resolved** | **420** | **453** | **+33** | 22 PR closures + 11 caller domain recoveries |
| - *Exact Return* | 229 | 240 | +11 | Single proven return continuation |
| - *Finite Set* | 191 | 213 | +22 | Multi-caller bounded finite domain |
| **Unresolved Sites** | **218** | **185** | **-33** | Honest fail-closed retention |
| - *External Entry in UNKNOWN* | 81 | 81 | 0 | Retained: caller threats from UNKNOWN bytes |
| - *PR Path / Shared Epilogue* | 81 | 59 | -22 | 22 resolved; 59 retained (threats/data callers) |
| - *Open Caller Domain* | 56 | 45 | -11 | 11 resolved; 45 retained (zero callers/threats) |
| **Total RTS Sites** | **638** | **638** | **0** | Exact total preserved |

### Soundness Audit Invariants
- `INVALID_RESOLVED_CERTIFICATES == 0`
- `EMPTY_RETURN_DOMAIN == 0`
- `RETURN_PC_IN_DATA == 0`
- `CALLER_COUNT_MISMATCH == 0`

---

## 6. Adversarial Negative Controls Suite P11

Suite `tests/asm/negative_controls_p11.py` introduces 8 new negative controls:
1. `NC-BO: SHARED_EPILOGUE_CONTEXT_COLLAPSE`: Rejects certifying a multi-entry shared epilogue by collapsing contexts without individual PR proof.
2. `NC-BP: ONE_CONTEXT_UNRESOLVED`: Asserts that if even one reaching context is ambiguous, the physical RTS must fail closed.
3. `NC-BQ: RETURN_PC_SHIFT_TO_NEAREST_CODE`: Rejects shifting data return continuation addresses to nearest code addresses.
4. `NC-BR: WRONG_DELAY_SLOT_RETURN_SEMANTICS`: Rejects calculating call return PC as `caller + 2` instead of `caller + 4`.
5. `NC-BS: TAILCALL_FRESH_PR_FALSE`: Rejects modeling tailcall jumps as creating fresh PR values.
6. `NC-BT: FRAME_GENERATION_ALIAS`: Rejects conflating frame generation IDs across distinct function scopes.
7. `NC-BU: FUNCTION_SPLIT_HIDES_ENTRY`: Asserts resolution of pseudo-function splits via boundary normalization.
8. `NC-BV: AGGREGATE_SITE_PASS_WITH_FAILED_CONTEXT`: Rejects certifying an RTS site when aggregate return domain is non-empty but one context failed contract.

**Total negative controls in repository: 82 / 82 PASS (100%)**.

---

## 7. Next Technical Action

With RTS V4 soundly certified at **453 / 638 resolved** (2,041 / 2,226 total indirect sites, 91.69%), the next milestone will target the remaining 185 unresolved RTS sites and the 498,392 SH-2 UNKNOWN bytes via guided, caller-threat-targeted boundary decarving.
