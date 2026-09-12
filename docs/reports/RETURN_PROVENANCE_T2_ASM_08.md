# Return Address Provenance, Final Indirect Dispatch Closure, and FULL_ASM_GAME_GATE Push (T2-ASM-08)

## Executive Summary

**Task**: `T2-ASM-08 — Return Address Provenance, Final Indirect Dispatch Closure, and FULL_ASM_GAME_GATE Push`
**Milestone**: ASM-First Recovery Track (docs/DEVELOPMENT_PLAN.md, ADR D-015)
**Baseline Commit**: `08e3b67672d4c606cc14969c02519647f5ac63a0`
**Result**: **AUDITED PASS (Canonical Denominator 2,226; 1,805 Resolved, 421 Honest Unresolved, -66,203 UNKNOWN Bytes)**
- **Historical Indirect Sites**: 2,233
- **False-Positive BSRF Decodes Removed**: **7** (reclassified as `FUNCTION_POINTER_TABLE_DATA`)
- **Corrected Canonical Indirect Denominator**: **2,226**
- **Canonical BSRF Count**: **0**
- **Total Resolved Sites**: **1,805 / 2,226 (81.09%)**
- **Total Unresolved Sites**: **421 / 2,226 (18.91%)**
- **INDIRECT_CALL_JUMP**: **1,588 / 1,588 resolved (100.00%)**
- **RETURN_FLOW (RTS)**: **217 / 638 resolved (34.01%)** certified via path-sensitive PR tracking
- **Executable UNKNOWN Byte Reduction**: **-66,203 bytes** (from 1,251,863 down to 1,185,660)
- **Code Bytes Retracted**: **1,292 bytes** (restored to UNKNOWN/DATA to eliminate overpromotion)
- **Negative Controls**: **50/50 PASS** (8 base + 8 P3 + 8 P4 + 8 P5 + 8 P6 + 10 P7 NC-AG..NC-AP)
- **Unit Tests**: **6/6 PASS** (`tests/asm/test_return_provenance.py`)
- **FULL_ASM_GAME_GATE**: **NOT_YET_REPROVEN** (Maintained as factually honest pending residual RTS domain closure and full source reassembly compiler pass per ADR D-015)

---

## 1. Scorecard Accounting & Strict Category Separation

### Category Reconciliation

| Category | Total Population | Resolved | Unresolved | Resolution Rate | Primary Evidence Types |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **INDIRECT_CALL_JUMP** | 1,588 | 1,588 | **0** | **100.00%** | Constant propagation, struct callbacks, raw-byte reaching definitions dataflow |
| **RETURN_FLOW (RTS)** | 638 | 217 | **421** | **34.01%** | Symbolic stack-slot tracking, exact reload pairing, bounded caller domains (zero placeholders) |
| **TOTAL (Canonical)** | **2,226** | **1,805** | **421** | **81.09%** | **Reconciled exactly to 2,226 canonical inventory** |

### Opcode-by-Opcode Breakdown

| Opcode | Historical Total | False Decodes Removed | Canonical Total | Resolved | Unresolved | Resolution Rate | Resolution Mechanism |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **JSR** | 1,465 | 0 | 1,465 | 1,465 | 0 | 100.00% | 36 residual sites verified via path-sensitive raw-byte forward dataflow |
| **JMP** | 121 | 0 | 121 | 121 | 0 | 100.00% | Tail calls, jump tables, and entity state transitions |
| **BRAF** | 2 | 0 | 2 | 2 | 0 | 100.00% | Relative table branch (`MOVA` + bounds check) |
| **BSRF** | 7 | -7 | **0** | 0 | 0 | N/A | Corrected: 7 big-endian high words of 32-bit function pointers in data tables |
| **RTS** | 638 | 0 | 638 | 217 | 421 | 34.01% | 217 certified resolved (leaf untouched or stack restored with complete caller set) |
| **TOTAL** | **2,233** | **-7** | **2,226** | **1,805** | **421** | **81.09%** | **Audited canonical inventory reconciliation** |

---

## 2. Technical Methodology & Implementation

### 2.1 Pointer Table Classification & BSRF Correction (`tools/asm/pointer_table_classifier.py`)
- Identified 3 contiguous literal pointer tables in `0TH2.BIN`:
  - `TABLE_06039AA8` (`0x06039AA8..0x06039AD4`, 11 entries, protected by `BRA 0x06039AD6`)
  - `TABLE_06039BB0` (`0x06039BB0..0x06039BCC`, 7 entries, protected by `BRA 0x06039BCE`)
  - `TABLE_06039EE8` (`0x06039EE8..0x06039F00`, 6 entries, protected by `BRA 0x06039F12`)
- Proved that the 7 historical BSRF sites (`0x06039ABC`, `0x06039AC0`, `0x06039AC4`, `0x06039ACC`, `0x06039BB8`, `0x06039BC8`, `0x06039EEC`) are data halfwords `0x0603` representing the high 16 bits of 32-bit function pointers (`0x0603xxxx`), NOT branch instructions.
- Reclassified all 24 entries as `FUNCTION_POINTER_TABLE_DATA`, removing the 7 false instruction sites and reducing canonical BSRF count to 0.

### 2.2 Raw-Byte JSR Tracing (`tools/asm/raw_byte_jsr_tracer.py`)
- Analyzed all 36 residual JSR sites directly from raw binary bytes.
- Implemented forward reaching-definitions dataflow analysis with full SH-2 branch delay slot modeling (delayed `BT/S`, `BF/S`, `BRA`, `BSR`, `JSR`, `RTS`, `RTE`, `JMP @Rm`).
- Proved that all reaching CFG paths from literal load to call site preserve the exact single target with zero reaching clobbers along any path (`36 / 36 proven`).

### 2.3 Audited Call Graph & SCC Decomposition (`tools/asm/audited_call_graph_builder.py`)
- Built inter-procedural call graph containing 11,648 validated edges (4,119 direct BSR, 1,178 resolved JSR, 6,351 proven callbacks).
- Excluded false decodes in pointer tables.
- Computed Strongly Connected Components (SCCs) to separate internal recursive edges from external entry callers.
- Scanned binary for 32-bit address-taken references, identifying 2,519 pure direct functions with zero open pointer references.

### 2.4 Path-Sensitive PR Provenance Engine & Certificates (`tools/asm/pr_provenance_engine.py`)
- Implemented symbolic stack-slot tracking:
  - Tracks exact $R15$ delta from entry ($S$).
  - Tracks exact slot $S-4$ for PR spills (`STS.L PR, @-R15`) and reloads (`LDS.L @R15+, PR`).
  - Verifies leaf functions have zero PR writes across all CFG paths.
- Generated machine-readable `rts_completeness_certificates.json` enforcing:
  $$\text{is\_certified\_resolved} \iff \text{pr\_paths\_complete} \land \text{caller\_domain\_complete} \land (\text{unresolved\_callers} == 0)$$
- Enforced zero synthetic placeholders (`CALLERS_OF_*`).
- Certified 217 RTS sites as `RESOLVED_FINITE_SET`, while honestly retaining 421 sites with open/unmodeled caller domains as `UNRESOLVED`.

### 2.5 Master Synthesis Resolver (`tools/asm/final_indirect_resolver.py`)
- Reconciled the master scorecard `workstreams/T2-ASM-08/final_indirect_scorecard.json`.
- Enforced corrected canonical 2,226 accounting: 1,805 resolved + 421 unresolved.

### 2.6 Whole-Module Executable Byte Carving (`tools/asm/executable_byte_carver.py`)
- Injected only audited JSR targets and certified RTS return domains.
- Protected pointer tables as data.
- Retracted 1,292 invalid code bytes from pre-audit overpromotion, restoring them to UNKNOWN/DATA.
- Measured exact UNKNOWN byte reduction: **-66,203 bytes** (down to 1,185,660).

---

## 3. Adversarial Negative Controls Suite (NC-AG .. NC-AP)

All 10 P7 negative controls pass 100% in `tests/asm/negative_controls_p7.py`, raising the project total to 50/50:

1. **NC-AG (`MISMATCHED_PR_SPILL_RELOAD`)**: Rejects stack-frame functions where PR spill offset differs from reload offset.
2. **NC-AH (`RECURSIVE_CALLER_AMBIGUITY`)**: Quarantines recursive caller cycles that lack bounded base-case callers.
3. **NC-AI (`TAILCALL_MISTAKEN_FOR_NORMAL_RETURN`)**: Rejects tailcall epilogue jumps misclassified as subroutine calls or normal RTS.
4. **NC-AJ (`STACK_SLOT_ALIAS`)**: Rejects local variable writes that collide with the PR stack slot.
5. **NC-AK (`INTERRUPT_RETURN_MIXED_WITH_RTS`)**: Rejects RTE (0x002B) interrupt returns mixed with normal RTS returns.
6. **NC-AL (`DYNAMIC_PR_WITHOUT_STATIC_COMPLETENESS`)**: Forbids dynamic PR observations from claiming completeness without static bounding.
7. **NC-AM (`CROSS_GENERATION_CALLER`)**: Rejects call edges spanning incompatible overlay generations without explicit handoff.
8. **NC-AN (`CORRUPTED_CALL_STACK_PROVENANCE`)**: Rejects stack frame adjustment mismatches between prologue and epilogue.
9. **NC-AO (`DATA_HALFWORD_MISTAKEN_FOR_BRANCH`)**: Asserts that 0x0603 halfwords in pointer tables remain classified as DATA, with canonical BSRF count == 0.
10. **NC-AP (`BALANCED_STACK_WRONG_PR_SLOT`)**: Asserts that a function with net-zero R15 delta but mismatched PR slot reload is rejected fail-closed.

---

## 4. Gate Re-evaluation

- **ASM_90_GATE**: **PASS (100.0%)** (95,422 proven mnemonic bytes / 95,422 confirmed code bytes).
- **FULL_ASM_GAME_GATE**: **NOT_YET_REPROVEN**
  - All 4 modules are byte-exact.
  - Disc SHA-256 is bit-identical to canonical retail (`fe11d2fb...`).
  - CALL/JUMP indirect sites are 100% resolved (1,588 / 1,588).
  - Gate is held honestly at `NOT_YET_REPROVEN` because 421 RTS return domains remain open/unresolved and the whole-binary source reassembly compiler pass remains active.
