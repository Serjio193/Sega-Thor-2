# T2-ASM-CARVER — Thor Saturn Recovery Carver

## 1. Mission & Architectural Overview

Task `T2-ASM-CARVER-01` establishes the **Thor Saturn Recovery Carver**, an evidence-driven discovery engine designed to systematically audit all residual `UNKNOWN` ranges across Saturn executable modules. Inspired by deep forensic file-carving, the Carver operates under strict legal-safe hygiene, discovering candidate structures without inventing behavior.

The Carver **finds candidates**; the existing Thor proof pipeline **decides truth**.

In accordance with user instructions, all broad native C++ translation scaling (D17, D18) is **FROZEN** under the mandatory ASM-first architecture. The denominator of executable code has been audited to eliminate artificial coverage inflation.

---

## 2. Core Architectural Subsystems

### 2.1 Central Interval Database (`tools/carver/interval_db.py`)
- Canonical non-overlapping interval partition covering 100% of every module (`0..module_size`).
- Tracks per-interval metadata:
  - `module`, `generation`, `cpu`, `offset_start`, `offset_end_exclusive`, `runtime_start`, `runtime_end_exclusive`
  - `classification`: `CONFIRMED_CODE`, `DATA`, `UNKNOWN`, `PADDING`
  - `subclass`: `LITERAL_POOL`, `POINTER_TABLE`, `MMIO_POINTER`, `STRING_TABLE`, `ALIGNMENT_PADDING`, etc.
  - `representation`: `MNEMONIC_PROVEN`, `RAW_CODE_PENDING`, `RAW_DATA`, `RAW_UNKNOWN`
  - `evidence_refs`, `conflicts`, `parent_provenance`, `consumer_refs`, `discovered_by`, `discovery_pass`
- Enforces the **Execution Conflict Rule (Rule 4)**:
  - Any byte retired by a CPU dynamically cannot remain `DATA` or `UNKNOWN`; it is promoted to `CONFIRMED_CODE`.
  - Proven `DATA` cannot be silently decoded as code; conflicts fail closed.

### 2.2 Saturn Detector Registry (`tools/carver/detector_registry.py`, `detectors_code.py`, `detectors_data.py`)
- Prioritized detector dispatch:
  1. `EXECUTED_PC_DETECTOR`: Dynamic CPU retirement extraction from CDL execution traces.
  2. `DIRECT_BRANCH_TARGET_DETECTOR`: SH-2 BRA, BSR, BT, BF, BTS, BFS target resolution.
  3. `CALL_TARGET_DETECTOR`: Function call target resolution.
  4. `LITERAL_POOL_DETECTOR`: PC-relative literal pool references (MOV.W, MOV.L, MOVA).
  5. `POINTER_TABLE_DETECTOR`: Dense 32-bit big-endian Saturn RAM pointer arrays.
  6. `MMIO_POINTER_DETECTOR`: Hardware MMIO target pointers (VDP1/2, SCU, SCSP, SMPC).
  7. `STRING_DETECTOR`: Formatted ASCII string table sequences.
  8. `PADDING_DETECTOR`: Continuous zero/FF alignment padding runs.
- Rule 2: Heuristic detectors never directly promote truth.

### 2.3 R-Studio Style RAM → Disc Signature Carver (`tools/carver/ram_disc_carver.py`)
- Scans unresolved runtime RAM ranges against all 33 ISO9660 files on disc.
- Performs bounded signature matching, progressive window expansion, and correlation with CD read (CDB) and DMA traces.

### 2.4 Provenance DAG & Graph Expansion Engine (`tools/carver/provenance_dag.py`)
- Tracks lineage for all discovered objects.
- Enforces **Rule 5**: Only `CONFIRMED` nodes may generate authoritative child candidates, preventing false-positive cascades.

### 2.5 Gap Reporter & Campaign Prioritization (`tools/carver/gap_reporter.py`)
- Audits residual UNKNOWN gaps, evaluating neighbors, reference density, and CDL activity.
- Prioritizes by: P1 Execution > P2 Provenance > P3 Control-Flow > P4 Data Consumer > P5 Heuristics.

---

## 3. Carver Fixed-Point Convergence Results

The carver pipeline ran to fixed-point convergence in **3 deterministic passes**:

| Pass | Candidates Evaluated | Bytes Promoted | Conflicts Detected | State |
|---|---|---|---|---|
| **Pass 1** | 11,362 | 166,141 | 0 | EXPANDING |
| **Pass 2** | 268 | 698 | 0 | CONVERGING |
| **Pass 3** | 214 | 0 | 0 | **FIXED POINT REACHED** |

### Verified Substrate Metrics

| Metric | Pre-Carver (Baseline) | Post-Carver (Audited) | Delta |
|---|---|---|---|
| **Total Binary Bytes** | 1,457,152 | 1,457,152 | 0 |
| **Confirmed Code Bytes** | 57,266 | 60,108 | **+2,842** |
| **Mnemonic Proven Bytes** | 55,342 | 55,342 | 0 |
| **Raw Code Pending Decode** | 1,924 | 4,766 | +2,842 |
| **Classified Data Bytes** | 0 | 81,435 | **+81,435** |
| **Classified Padding Bytes**| 0 | 82,562 | **+82,562** |
| **Residual UNKNOWN Bytes** | 1,399,886 | 1,233,047 | **-166,839** |
| **Aggregate Mnemonic Coverage** | 96.64% (inflated) | **92.07% (audited)** | Honest adjustment |
| **Execution Hits in UNKNOWN** | Many | **0 (P1_EXECUTION = 0)** | Zero residual hits |
| **Execution Conflicts** | 0 | **0** | Fail-closed integrity |
