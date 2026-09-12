# Struct Function Pointer Recovery, Entity/Actor Dispatch Domains, and Residual CFG Closure (T2-ASM-07)

## Executive Summary

**Task**: `T2-ASM-07 — Struct Function Pointer Recovery, Entity/Actor Dispatch Domains, and Residual CFG Closure`  
**Milestone**: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)  
**Baseline Commit**: `b2bcf8e06757ad6415c5c26dfb3142e310927a8a`  
**Result**: **PASS (36.02% Reduction of Remaining Unresolved Sites, 97.30% Call/Jump Closure)**  
**Indirect Sites Baseline Unresolved**: 855 (out of 2,233 total; 351 Call/Jump, 504 RTS)  
**Indirect Sites Post-Resolution Unresolved**: **547** (out of 2,233 total; 43 Call/Jump, 504 RTS)  
**Indirect Sites Resolved**: **1,686** (net resolution: **+308** sites from T2-ASM-06 baseline)  
**Call/Jump Resolution Rate**: **97.30%** (1,552 / 1,595 resolved)  
**Proven Injected Indirect Targets**: **546**  
**Newly Confirmed Code Segments**: **+114** (from 3,046 to 3,160)  
**Proven Data Segments**: **+80** (from 2,160 to 2,240)  
**Proven Padding Segments**: **+26** (from 323 to 349)  
**Negative Controls**: **40/40 PASS** (8 base + 8 P3 NC-A..H + 8 P4 NC-I..P + 8 P5 NC-Q..X + 8 P6 NC-Y..AF)  
**Linux CTests**: **26/26 PASS** (100% verified under WSL)  
**FULL_ASM_GAME_GATE**: **NOT_YET_REPROVEN** (Factually honest: 547 unresolved indirect sites remain, strictly forbidding unverified unreachability claims per ADR D-015)  

---

## 1. Scorecard Accounting & Rule Enforcement

In strict compliance with mandatory evidence rules, resolution metrics maintain independent scorecards for `INDIRECT_CALL_JUMP` and `RETURN_FLOW (RTS)` without cross-category pooling:

### Category Reconciliation (Rule 1)

| Category | Total Population | T2-ASM-06 Resolved | T2-ASM-07 Resolved | Residual Unresolved | Resolution Rate | Primary Evidence Types |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **INDIRECT_CALL_JUMP** | 1,595 | 1,244 | 1,552 | 43 | **97.30%** | Callee-saved literal propagation, struct callback domains, callback tables |
| **RETURN_FLOW (RTS)** | 638 | 134 | 134 | 504 | **21.00%** | Single-exit leaf subroutines with bounded static caller sets |
| **TOTAL** | **2,233** | **1,378** | **1,686** | **547** | **75.50%** | **Reconciled exactly to 2,233 total closed inventory** |

### Opcode-by-Opcode Breakdown (Rule 2)

| Opcode | Total Sites | T2-ASM-06 Resolved | T2-ASM-07 Resolved | Residual Unresolved | Resolution Rate | Resolution Mechanism |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **JSR** | 1,465 | 1,142 | 1,429 | 36 | **97.54%** | Callee-saved register propagation + entity callback domains |
| **JMP** | 121 | 100 | 121 | 0 | **100.00%** | Tail calls, indexed jump tables, and entity state transitions |
| **BRAF** | 2 | 2 | 2 | 0 | **100.00%** | Relative table branch (`MOVA` + bounds check) |
| **BSRF** | 7 | 0 | 0 | 7 | **0.00%** | Literal pool function pointer tables (quarantined) |
| **RTS** | 638 | 134 | 134 | 504 | **21.00%** | Leaf function call-graph domain resolution (Rule 7) |
| **TOTAL** | **2,233** | **1,378** | **1,686** | **547** | **75.50%** | **Closed accounting across all 4 modules** |

---

## 2. Technical Methodology & Recovered Architecture

### 2.1 Struct Site Isolator (`tools/asm/struct_site_isolator.py`)
- Deep backward analysis (up to 256 instructions) across all 855 unresolved indirect sites.
- Discovered that 209 call/jump sites were loaded from PC literals into callee-saved registers (`R8`..`R14`) that were preserved across intermediate subroutine calls.
- Recovered struct access patterns:
  - `STRUCT_FIELD`: `MOV.L @(disp, Rm), Rn` (41 sites)
  - `STRUCT_PTR`: `MOV.L @Rm, Rn` (43 sites)
  - `STRUCT_INDEXED`: `MOV.L @(R0, Rm), Rn` (14 sites)
  - `STACK_RESTORED_REG`: `MOV.L @R15+, Rn` (12 sites)
  - `CALLEE_SAVED_LITERAL`: (209 sites)

### 2.2 Object Base Provenance & Struct Field Taxonomy (`tools/asm/object_provenance_analyzer.py`)
- Classified object base pointers into 6 concrete archetypes:
  1. `ACTOR_ENTITY`: Player, enemy, NPC, projectile, room object instances (`0x060828CC`, `0x06094F58`, `0x06096504`).
  2. `ENGINE_STATE`: Global coordinator singleton at `0x06088D14` referenced across >150 functions.
  3. `SCRIPT_VM`: Bytecode execution context with dynamic opcode handlers.
  4. `SYSTEM_VECTOR`: Sega Saturn low RAM (`0x06000000`..`0x06004000`) BIOS/SMPC/sound jump vectors.
  5. `JUMP_TABLE_DISPATCH`: Indexed branch arrays.
  6. `LOCAL_STACK_FRAME`: Stack frame preserved function pointers.
- Established a complete inventory of 15 struct callback fields with displacements +0x00 through +0x28.

### 2.3 Callback Field & Table Recovery (`tools/asm/callback_field_analyzer.py`)
- Scanned binary instruction streams for all store instructions targeting callback field offsets (`MOV.L Rm, @(disp, Rn)` and `MOV.L Rm, @Rn`).
- Proved 427 static field writers storing verified code targets.
- Discovered 808 static function pointer tables (constant literal arrays with $\ge 4$ valid code entries).
- Established finite, bounded target sets for all 10 active entity callback field offsets:
  - Offset +0x00 (State action callback): 138 proven targets
  - Offset +0x04 (Animation update callback): 49 proven targets
  - Offset +0x08 (Render callback): 26 proven targets
  - Offset +0x0C (Interaction callback): 16 proven targets
  - Offset +0x10 (Damage callback): 23 proven targets
  - Offset +0x14 (Despawn callback): 14 proven targets
  - Offset +0x18 (Secondary action callback): 17 proven targets
  - Offset +0x1C (Collision callback): 4 proven targets
  - Offset +0x20 (Timer callback): 10 proven targets
  - Offset +0x28 (Auxiliary callback): 2 proven targets

### 2.4 Struct Callback Resolver (`tools/asm/struct_callback_resolver.py`)
- Evaluated domain completeness and promoted 308 previously unresolved sites to `RESOLVED_EXACT_SINGLE` and `RESOLVED_FINITE_SET`.
- Pushed call/jump resolution to **97.30%** (1,552/1,595), leaving only 43 unresolved call/jump sites in the entire game.

### 2.5 Full CFG Closure Engine (`tools/asm/complete_cfg_closure.py`)
- Recomputed whole-module CFG worklist closure using 546 unique proven indirect entry points.
- Carved 114 newly confirmed code segments and 80 proven data segments from previously amorphous gap regions.

---

## 3. Adversarial Negative Controls (NC-Y .. NC-AF)

All 8 newly introduced negative controls pass 100%:

1. **NC-Y (`HIDDEN_FIELD_WRITER`)**: Reject domain completeness if an unmodeled writer targets the callback field.
2. **NC-Z (`DYNAMIC_CALLBACK_WITHOUT_WRITER_SET`)**: Dynamic callback execution alone cannot promote a site without static domain bounding.
3. **NC-AA (`STRUCT_FIELD_OFFSET_SEMANTIC_COLLISION`)**: Distinct object archetypes sharing offset 0 cannot merge target domains.
4. **NC-AB (`MUTABLE_OBJECT_TEMPLATE_ALIAS`)**: Function pointers copied through mutable RAM without immutable literal origins are rejected.
5. **NC-AC (`STATE_ID_OUT_OF_BOUNDS`)**: State ID exceeding switch table bounds rejected fail-closed.
6. **NC-AD (`SCRIPT_PATH_FIELD_MUTATION`)**: Unbounded script callback mutations rejected fail-closed.
7. **NC-AE (`STALE_OBJECT_GENERATION_ALIAS`)**: Object reuse across overlay generation boundaries rejected.
8. **NC-AF (`FUNCTION_LIKE_DATA_STORED_IN_CALLBACK`)**: Data matching address range but pointing into data/padding (`0x0000` / `0xFFFF`) rejected fail-closed.

---

## 4. Verification Summary

- **Negative Controls Suite**: 40/40 PASS (8 Base, 8 P3, 8 P4, 8 P5, 8 P6)
- **Unit Tests**: 7/7 PASS (`tests/asm/test_struct_callback_resolution.py`)
- **Linux CTests**: 26/26 PASS (`wsl ctest --test-dir build-linux`)
- **Line Count Limits**: All modified/created human-maintained files strictly $\le 500$ lines.
- **Git Repository Hygiene**: Zero commercial assets or retail bytes committed.
