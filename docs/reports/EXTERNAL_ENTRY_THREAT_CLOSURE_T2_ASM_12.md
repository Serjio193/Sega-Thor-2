# Targeted UNKNOWN Caller-Threat Elimination, Region Ownership Proof, and External-Entry Closure Report (T2-ASM-12)

**Task**: `T2-ASM-12 — Targeted UNKNOWN Caller-Threat Elimination, Region Ownership Proof, and External-Entry Closure`  
**Date**: 2026-09-12  
**Baseline Commit**: `f7b9eabd5d0614fb8f4ef1f452e6709ba8c3c7a7`  
**Classification**: ASM-FIRST CONTROL-FLOW RECOVERY / THREAT ELIMINATION & EXTERNAL-ENTRY CLOSURE  

---

## 1. Executive Summary & Strategic Objective

Milestone `T2-ASM-12` continued the ASM-first proof track from the sound `T2-ASM-11` baseline (453 resolved RTS, 185 honest unresolved RTS) without metric forcing or unguided bulk byte carving.

The primary objective was the elimination of the 81 `UNRESOLVED_EXTERNAL_ENTRY` RTS blockers and secondary caller-domain blockers by establishing formal ownership proofs and reachability exclusions across two independent channels:
1. **Channel A (Executable-Source Threat)**: Proving that opaque UNKNOWN regions cannot execute as code and therefore cannot initiate calls into entry points.
2. **Channel B (Data-Target Threat)**: Proving that pointers located in data/literal pools cannot reach unanalyzed call sinks, bounding consumer chains to audited indirect jumps/calls.
3. **Channel C (Tailcall Entry Threat)**: Bounding upstream tailcall graphs to ensure no hidden entries inherit caller return addresses without an audited stack frame.
4. **Channel D (Root/Exception Entry Threat)**: Verifying hardware vector and reset roots.

### Key Verification Results
- **RTS Completeness V5 Resolution**: **510 / 638 resolved (79.94%)**, **128 honest unresolved (20.06%)**.
  - Net increase of **+57 certified resolved sites** (51 primary external entry resolutions + 6 secondary caller domain resolutions).
  - **INVALID_RESOLVED_CERTIFICATES == 0** across all 638 sites.
  - ZERO empty return domains; 100% of return continuations verified in `CONFIRMED_CODE`.
- **Calls and Jumps**: **1,588 / 1,588 (100.0%)** resolved.
- **Overall Indirect Resolution**: **2,098 / 2,226 (94.25%)**, **128 unresolved (5.75%)**.
- **Adversarial Negative Controls**: Expanded from 82 to **91 controls** (9 new P12 controls: NC-BW through NC-CE), passing 100%.
- **Caller Threat Frontier Decarving**:
  - Total SH-2 UNKNOWN bytes remain **498,392 bytes**.
  - Active UNKNOWN bytes on the caller threat frontier reduced from 498,392 bytes to **202 bytes** across 5 isolated intervals containing 6 candidate branch instructions.
  - **498,190 bytes** proven reachability-excluded from caller threat ingress.
- **Gate Status**:
  - `ASM_90_GATE`: **PASS** (100.00% mnemonic coverage across confirmed code).
  - `FULL_ASM_GAME_GATE`: Maintained honestly at **NOT_YET_REPROVEN** pending 128 residual RTS sites and 498,392 SH-2 UNKNOWN bytes.
- **Invariants Preserved**:
  - 4/4 module reassembly byte-exact (0 differing bytes).
  - Full-disc SHA-256 exact (`fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8`).
  - Mednafen 6-scenario suite: ZERO divergence.
  - 41/41 Linux CTests passing.

---

## 2. Threat Rebase Audit & The Dual-Channel Prover

### Threat Universe Rebase
The historical threat counts (148 reference sources, 2,810 entry-graph edges) were rebased directly against `module_byte_ownership_v3.json`:
- **Historical Reference Sources (99 unique addresses)**:
  - **100% (99/99)** reside in `DATA` (`DATA_LITERAL_POOL`).
  - Zero reference sources reside in `CODE` or `UNKNOWN`.
- **Entry-Graph Edges Originating in UNKNOWN (2,810 edges)**:
  - **2,801 edges**: Proven `DATA_HALFWORD_FALSE_DECODE` (literal pool and data table halfwords falsely decoded as `BSR` or branch instructions).
  - **9 edges across 6 branch sites in 4 functions**: Valid branch patterns (`VALID_EXECUTABLE_CANDIDATE`).

### Channel A & Channel B Proof Mechanics
1. **Channel B (Data Consumer Chains)**:
   - For all 99 literal pool addresses, consumer chains were traced through basic blocks:
   - 88 addresses feed audited indirect `JSR` call sites.
   - 4 addresses feed audited tailcall `JMP` sites.
   - 5 addresses are loaded for non-call purposes (arithmetic/store/overwritten).
   - 2 addresses have mixed call/non-call paths.
   - **0 open consumers**: Zero literal pool references remain unanalyzed.
2. **Channel A (Reachability Exclusion)**:
   - 35,435 UNKNOWN intervals (498,190 bytes) have no incoming code branch edges, are not reset/vector entries, and are not in any bounded jump table. Reachability exclusion certificates were formally issued for all 35,435 intervals.
   - The 6 candidate branch instructions reside in 5 unconfirmed intervals totaling 202 bytes (`0x0600F9FE..0x0600FA30`, `0x06010568..0x0601057E`, `0x06010CB4..0x06010CD2`, `0x06078C4A..0x06078CBC`, `0x0607E62A..0x0607E65C`). These 202 bytes are retained fail-closed on the active caller threat frontier.

---

## 3. Tailcall Domain Bounding & Fail-Closed Retention

Eight functions were identified with upstream tailcall ingress:
- `sub_0600406C`, `sub_0600DEDC`, `sub_0606DD04`, `sub_0606EC54`, `sub_0606EE8C`, `sub_060787A4`, `sub_06081898`, `sub_002E73FC`.

Detailed reverse engineering of the tailcall graph traced upstream caller inheritance:
- An upstream tailcall site `jmp @r3` at `0x0602F5C8` in leaf function `sub_0602F312` currently has 0 known callers.
- Because `sub_0602F312` has 0 confirmed callers, the PR state inherited across `jmp @r3` cannot be soundly bounded.
- In strict adherence to Rule 14 and the zero metric forcing contract, all 8 tailcall functions and their 24 RTS sites were retained **fail-closed** as `BLOCKED_TAILCALL_DOMAIN_INCOMPLETE`.

Four functions with candidate branch targets in UNKNOWN regions:
- `sub_06010094`, `sub_06010BC2`, `sub_06078690`, `sub_0607E6FE`.
- Their 6 RTS sites were retained **fail-closed** as `BLOCKED_UNKNOWN_BRANCH_THREAT`.

---

## 4. Summary of RTS Completeness V5

| Category | Baseline V4 (T2-ASM-11) | T2-ASM-12 (V5) | Delta | Classification / Status |
| :--- | :---: | :---: | :---: | :--- |
| **Certified Resolved** | **453** | **510** | **+57** | **Sound Return Domain Complete** |
| - *Exact Return* | 240 | 265 | +25 | Single unique return continuation |
| - *Finite Set* | 213 | 245 | +32 | Multi-caller bounded return domain |
| **Unresolved Sites** | **185** | **128** | **-57** | **Honest Fail-Closed Retention** |
| - *External Entry Threats* | 81 | 30 | -51 | 24 tailcall-blocked + 6 branch-threat |
| - *PR Path / Shared Epilogue* | 59 | 59 | 0 | Retained pending PR dataflow closure |
| - *Open Caller Domain* | 45 | 39 | -6 | 6 resolved; 39 retained fail-closed |
| **Total RTS Sites** | **638** | **638** | **0** | Exact total preserved |

### Independent Soundness Audit Results
- `total_sites_audited`: 638
- `resolved_sites_count`: 510
- `unresolved_sites_count`: 128
- `invalid_resolved_certificates_count`: 0
- `audit_passed`: true

---

## 5. Byte Ownership Partition V4 & Closed-World Control-Flow Theorems V3

### Byte Partition V4
- Total Binary Bytes: 1,457,152
- Confirmed Code Bytes: 156,694 (100% mnemonic coverage)
- Proven Data Bytes: 68,980
- Confirmed Padding Bytes: 59,324
- Total UNKNOWN Bytes: 1,172,154 (SH-2: 498,392 bytes)
  - **Reachability Excluded SH-2 UNKNOWN Bytes**: **498,190 bytes**
  - **Active Caller Threat Frontier Bytes**: **202 bytes** (5 intervals)

### Closed-World Control-Flow Theorems V3
- **Theorem 1 (Confirmed Code Exclusivity)**: `PROVEN`. All resolved indirect calls, jumps, and RTS sites resolve exclusively to targets within confirmed `CODE`.
- **Theorem 2 (Caller Threat Frontier Boundary)**: `PROVEN`. All possible external entry threats into confirmed functions are bounded to exactly 5 intervals (202 bytes) and 1 open upstream tailcall site (`0x0602F5C8`).
- **Theorem 3 (Total Binary Closed World)**: `HELD_OPEN_FAIL_CLOSED`. The total binary cannot be declared closed until the remaining 202 frontier bytes, 8 tailcall functions, 59 PR paths, and 39 caller domains are resolved.

---

## 6. Next Steps
1. Target the single upstream tailcall blocker at `0x0602F5C8` (`sub_0602F312`) to unblock the 8 tailcall functions (24 RTS sites).
2. Classify the 5 caller-frontier UNKNOWN intervals (202 bytes) to determine whether the 6 candidate branches are valid code or false decodes, unblocking the 4 branch-threat functions (6 RTS sites).
3. Discharge residual PR-path and caller-domain sites.
