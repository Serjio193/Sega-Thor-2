# D9 Candidate Record — Startup Indirect Call Block `bb_06004280`

Status: **QUALIFIED_CANDIDATE (READY_FOR_BOUNDED_TEST)**  
Capability: **D9 — Indirect Control-Flow Handling**  
Target Revision: `thor2_ntsc_patched_fe11d2fb` (`The_Story_of_Thor_2_[RUS]_(NTSC).bin`)  
Module: `0TH2.BIN` (High Work RAM `0x06004000..0x06086BFF`)  
Target CPU: `MASTER_SH2`  

---

## 1. Candidate Block Boundaries & Identification

- **Start Address:** `0x06004280`
- **End Address:** `0x06004288` (Address of delay-slot instruction `NOP`)
- **Instruction Count:** 5 instructions (10 bytes)
- **Byte Extent:** `0x06004280 .. 0x06004289` inclusive (offset `+0x000280 .. +0x000289` in `0TH2.BIN`)
- **Exact Raw Bytes (Hex):** `D5 36 D4 37 D3 37 43 0B 00 09`
- **SHA-256 (Candidate Block Bytes Only):**  
  `8879cbe14f58a5fbc4eb9545e1cc41b3593e306cab114769a94f814a18bcb770`

---

## 2. Disassembly & Instruction Profile

| Address | Offset | Opcode | Mnemonic | Operands / Effective Address | Classification |
|---|---|---|---|---|---|
| `0x06004280` | `+0x0280` | `0xD536` | `MOV.L @(disp,PC), R5` | `disp=0x36`, EA=`0x0600435C`, Val=`0x002DA000` | `ALREADY_D3_L0_PROVEN` |
| `0x06004282` | `+0x0282` | `0xD437` | `MOV.L @(disp,PC), R4` | `disp=0x37`, EA=`0x06004360`, Val=`0x06081C20` ("TH2.LOW") | `ALREADY_D3_L0_PROVEN` |
| `0x06004284` | `+0x0284` | `0xD337` | `MOV.L @(disp,PC), R3` | `disp=0x37`, EA=`0x06004364`, Val=`0x0600A0F8` | `ALREADY_D3_L0_PROVEN` |
| `0x06004286` | `+0x0286` | `0x430B` | `JSR @R3` | Target=`R3`, Return=`PR` (`0x0600428A`) | `NEEDS_D3_L0_PROOF` |
| `0x06004288` | `+0x0288` | `0x0009` | `NOP` | Delay slot for `JSR @R3` | `ALREADY_D3_L0_PROVEN` |

---

## 3. Dynamic Execution & Oracle Trace (Cold Boot)

Verified via pinned Mednafen debug oracle (`AJBats/mednafen-saturn-debug` commit `155426661b7ac3152e2c93a98da60ac33002b908`):

### 3.1 Entry State (`0x06004280`)
- **Arrival Condition:** Cold boot Hit 2 at frame 701 (debugger 0-indexed frame count, corresponding to 702nd presentation frame), master cycle `316309168`.
  *(Note: Hit 1 at frame 682, cycle 307090585, is return-address setup from `0x0600427C` (`BSR 0x0600447C`); Hit 2 is actual execution entry following `RTS` return from `0x0600447C`).*
  *(Frame Note: Frame numbering is a presentation counting convention and is not part of the deterministic architectural contract; deterministic equivalence is proven by cycle count `316309168`, PC, register state, and memory).*
- **Entry Registers:**
  ```text
  R0=00000023 R1=06093B14 R2=00000028 R3=06094F28 R4=00000000 R5=06094B68
  R6=00000BC5 R7=00000008 R8=00000000 R9=00000000 R10=00000000 R11=06096523
  R12=06088708 R13=00000001 R14=00000002 R15=06002ED8 PC=06004280 SR=00000001
  PR=06004280 GBR=00000000 VBR=06000000 MACH=00000000 MACL=00000000 cycle=316309168
  ```

### 3.2 Step-by-Step Retirement & Timestamp Progression
- **Step 1 (`0x06004280`: `MOV.L @(0xD8,PC), R5`)**:
  - `R5` updated to `0x002DA000` (destination address for `TH2.LOW` in Low Work RAM).
  - `PC` advances to `0x06004282`.
  - Timestamp: `316309168` $\rightarrow$ `316309169` (+1 cycle).
- **Step 2 (`0x06004282`: `MOV.L @(0xDC,PC), R4`)**:
  - `R4` updated to `0x06081C20` (pointer to ASCII string `"TH2.LOW"`).
  - `PC` advances to `0x06004284`.
  - Timestamp: `316309169` $\rightarrow$ `316309171` (+2 cycles).
- **Step 3 (`0x06004284`: `MOV.L @(0xDC,PC), R3`)**:
  - `R3` updated to `0x0600A0F8` (entry address of disc streaming / loading routine).
  - `PC` advances to `0x06004286`.
  - Timestamp: `316309171` $\rightarrow$ `316309172` (+1 cycle).
- **Step 4 (`0x06004286`: `JSR @R3`)**:
  - Target register evaluated: `R3 = 0x0600A0F8`.
  - Procedure Register updated: `PR = PC + 4 = 0x06004286 + 4 = 0x0600428A`.
  - Pipeline branches to delay slot at `0x06004288`.
  - Timestamp: `316309172` $\rightarrow$ `316309187` (+15 cycles: branch target fetch & pipeline refill).
- **Step 5 (`0x06004288`: `NOP`, delay slot)**:
  - Delay slot retired.
  - Architectural branch taken to `0x0600A0F8`.
  - Timestamp: `316309187` $\rightarrow$ `316309189` (+2 cycles: execution begins at target `0x0600A0F8`).

### 3.3 Exit State (`0x0600A0F8`)
- **Exit PC:** `0x0600A0F8`
- **Return Address (`PR`):** `0x0600428A`
- **Callstack:** `0x06004286 -> 0x0600A0F8 (ret=0x0600428A)`
- **Duration of Candidate Block:** 21 cycles (`316309189 - 316309168 = 21`)
- **Timing Breakdown & Reconciliation:**
  - `BLOCK_ENTRY_CYCLE = 316309168` (master cycle at initial instruction fetch `0x06004280`)
  - `DELAY_SLOT_ENTRY_CYCLE = 316309187` (+19 cycles relative to entry; delay slot `0x06004288` entered following branch pipeline refill)
  - `BLOCK_EXIT_TARGET_ENTRY_CYCLE = 316309189` (+21 cycles relative to entry; execution begins at target `0x0600A0F8`)
  - *Reconciliation:* The preliminary 19-cycle count was measured upon entry into the delay slot instruction. With atomic delay-slot execution completed (+2 cycles for `NOP`), total block duration to target entry is exactly 21 cycles.

---

## 4. Memory & Hardware Interactions

- **Memory Reads:**
  - `0x0600435C`: 4 bytes, value `0x002DA000` (literal pool)
  - `0x06004360`: 4 bytes, value `0x06081C20` (literal pool)
  - `0x06004364`: 4 bytes, value `0x0600A0F8` (literal pool)
- **Memory Writes:** Exactly 0 writes.
- **MMIO Accesses:** 0.
- **SCU DMA / Inter-CPU Signaling:** None.
- **Atomic Delay Slot:** Yes (`NOP` at `0x06004288` executed atomically before control transfer).

---

## 5. Code Ownership Classification

Per `AGENTS.md` and ADR D-011 / D-012 rules:
- **Provenance:** `0TH2.BIN` is proven byte-for-byte in RAM under ADR D-011 (`V-02a`).
- **Static Candidate:** `bb_06004280` is statically bounded as 5 instructions ending in `JSR @R3` + delay slot.
- **Dynamic Observation:** Stepping trace proves 100% of the candidate block executes at cold boot Hit 2 (debugger reported frame 701, corresponding to 702nd presentation frame; master cycle 316309168).
- **Classification Status:**
  - **D3 (Instruction Semantics):** `BOUNDED_PROOF` — all 5 instructions (`MOV.L`, `JSR @Rn`, `NOP`) have full verified L0 semantics and 0 oracle disagreements.
  - **D4 (Static Disassembly):** `BOUNDED_PROOF` — address range `0x06004280..0x06004289` (10 bytes) is promoted to `CONFIRMED_CODE / EXECUTED`.
  - **D5 (CFG Structure):** `BOUNDED_PROOF` — `bb_06004280` is recovered as an indirect call block with empty direct exits, nullopt fallthrough, and dynamic runtime target.
  - **D9 (Indirect Dispatch):** Sub-gate `D9.1` is `PASS`. Milestone D9 remains `READY_FOR_BOUNDED_TEST` until generic dispatch, shadow proof, and native override gates complete.
- **Candidate SHA-256:** `8879cbe14f58a5fbc4eb9545e1cc41b3593e306cab114769a94f814a18bcb770`
