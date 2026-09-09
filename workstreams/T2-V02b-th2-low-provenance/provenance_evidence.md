# V-02b — TH2.LOW Executable Provenance Evidence

Status: **PASS (V02B_DIRECT_PROVENANCE_PROVEN)**
Capability: **D2 — Executable Module Provenance (BOUNDED_PROOF for 0TH2.BIN and TH2.LOW)**
Target: Disc file `TH2.LOW` runtime extent and execution mapping
Target Revision: `thor2_ntsc_patched_fe11d2fb`

## 1. Canonical Disc Extent & Identity

- **File Path on Disc:** `TH2.LOW` (ISO9660 root directory)
- **Logical Extent (LBA):** 52,123
- **Logical File Size:** 149,504 bytes (`0x24800`)
- **Logical Sector Count:** 73 sectors (`149504 / 2048 = 73`, LBA 52123 to 52195 inclusive)
- **Disc File SHA-256:** `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224`
- **Saturn CD Block FAD Addressing:**
  Saturn CD Block addressing maps $\text{FAD} = \text{LBA} + 150$.
  - Candidate Start FAD: $52123 + 150 = 52273 = \text{0x0000CC31}$
  - Candidate End FAD: $52195 + 150 = 52345 = \text{0x0000CC79}$
  - Following file (`TH2_ABST.TXT`, LBA 52196): $\text{FAD} = 52196 + 150 = 52346 = \text{0x0000CC7A}$

---

## 2. Dynamic Call-Site Proof in `0TH2.BIN`

Immediately before the candidate indirect call at `0x06004286` in `0TH2.BIN`, CPU register state was captured:

- **CPU Identity:** `MASTER_SH2`
- **Hook Address:** `0x0600428A` (arrived at step 4 immediately before branch execution)
- **R3 (Target Routine):** `0x0600A0F8`
- **R4 (Filename Argument):** `0x06081C20`
- **String at R4:** Memory read from `0x06081C20` dynamically confirmed NUL-terminated ASCII string: `"TH2.LOW"`
- **R5 (Destination Base):** `0x002DA000`
- **Return Address (`PR`):** `0x0600428A`
- **Call-Site Result:** Dynamic argument state matches static hypothesis 100% with zero contradiction across Run A and Run B.

---

## 3. Pre/Post Live RAM Snapshots

Candidate destination range `0x002DA000..0x002FE7FF` (`0x24800` / 149,504 bytes) was dumped before the call and immediately after the routine returned to `0x0600428A`.

### 3.1 Run A (Independent Cold Boot)
- **Pre-Load RAM SHA-256:** `71ba98cb5315c867d5670e7d214b2369d52235d1182658413d3890cfb982be6e` (unpopulated/initial state; differs from disc file)
- **Post-Load RAM SHA-256:** `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224`
- **Comparison vs Disc `TH2.LOW`:** **FULL_EXACT_MATCH** (0 differing bytes across all 149,504 bytes)

### 3.2 Run B (Independent Cold Boot)
- **Pre-Load RAM SHA-256:** `71ba98cb5315c867d5670e7d214b2369d52235d1182658413d3890cfb982be6e`
- **Post-Load RAM SHA-256:** `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224`
- **Comparison vs Disc `TH2.LOW`:** **FULL_EXACT_MATCH** (0 differing bytes)
- **Comparison Run A vs Run B:** **100% IDENTICAL**

---

## 4. CD Block & Memory-Transfer Evidence

### 4.1 CD Block Trace (`cdb.log`)
- **Command:** `CMD Play; Start=0x80cc31, End=0x800049, Mode=0x00`
- **Start FAD:** `0x00CC31` (exactly matches derived FAD for LBA 52123)
- **Sector Count:** `0x49` = 73 sectors (exactly matches `TH2.LOW` sector length)
- **Drive Status:** Reads concluded at FAD `0x00CC7A` (`PAUSE`), proving exact bounds matching `TH2.LOW`.

### 4.2 SCU DMA Trace (`dma.log`)
- Exactly 0 SCU DMA transfers targeted Low Work RAM (`0x002DA000..0x002FE7FF`).

### 4.3 Memory Profile Trace (`mem.log`)
- Exactly 37,376 32-bit writes ($37376 \times 4 = 149,504$ bytes) were recorded to destination `0x002DA000..0x002FE7FC`.
- All writes were executed by Master SH-2 CPU at PC `0x0607DF08` inside the CD transfer loop:
  `pc=0x0607DF08 addr=0x002DA000 val=0x1DF0317 sz=4 chain=0x0607DEDC<-0x0607DF7A<-0x0607DAD6<-0x0607D9E0<-0x06079484<-0x06078B42<-0x060787A4<-0x060786FA<-0x0600A0F8<-0x06004254<-0x06002D88`
- **Transfer Mechanism:** **`DIRECT_CPU_COPY_OBSERVED`**.

### 4.4 Routine Return State
- On return to `0x0600428A` (hook `0x0600428C`):
  - `R0 = 0x00024800` (length of transferred payload returned in `R0`)
  - `R14 = 0x00024800`
  - `PR = 0x0600428A`

---

## 5. Execution Confirmation

Following module transfer, execution inside `TH2.LOW` was dynamically observed:

- **Target CPU:** `MASTER_SH2`
- **Breakpoint Hit:** Requested `0x002E9910`, hook PC `0x002E9912` (via `pc - 2` delayed branch fallback)
- **Execution Cycle:** `387,459,915` (identical across Run A and Run B)
- **Module Offset:** $0x002E9910 - 0x002DA000 = \text{0xF910}$
- **Caller Chain:** Called from `0x060042E0` in `0TH2.BIN` (`JSR @R2`, `R2=0x002E9910`, return address in `PR=0x060042E4`)
- **Instruction Semantics:** Step 1 executed instruction `0x2FE6` (`MOV.L R14, @-R15`) at `0x002E9910`, advancing PC to `0x002E9914` and decrementing SP from `0x06002EDC` to `0x06002ED8`
- **Execution Status:** Address range `0x002E9910..0x002E9914` is **`CONFIRMED_CODE / EXECUTED`**; the remaining extent `0x002DA000..0x002FE7FF` is **`MAPPED (BYTE_EXACT)`**.
- **Byte Classification Scope:** Only dynamically observed instructions (`0x002E9910..0x002E9914`) are classified as `CONFIRMED_CODE / EXECUTED`. The unexecuted remainder of the mapped extent retains its prior `PROBABLE_CODE / HIGH` classification; complete code/data/unknown ownership remains queued for D4.

---

## 6. Complete Provenance Chain

| Stage / Link | Evidence | Status |
|---|---|---|
| Disc Extent | ISO9660 LBA 52123..52195, 73 sectors, SHA-256 `78139689...` | **PROVEN** |
| Call Site | `0TH2.BIN` PC `0x06004286`: `R4 -> "TH2.LOW"`, `R5=0x002DA000`, `R3=0x0600A0F8` | **PROVEN** |
| Disc Reading | CD Block `Play` FAD `0x00CC31..0x00CC79` (73 sectors) | **PROVEN** |
| Memory Transfer | Master SH-2 CPU copy loop at PC `0x0607DF08` to `0x002DA000..0x002FE7FF` | **PROVEN** |
| Runtime Mapping | Post-load live RAM dump matches disc byte-for-byte (`FULL_EXACT_MATCH`) | **PROVEN** |
| Execution | Master SH-2 executed instructions at `0x002E9910..0x002E9914` (offset `0xF910`, cycle `387459915`) | **PROVEN** |

---

## 7. Verdict & Decision

- **Experiment Result:** **`V02B_DIRECT_PROVENANCE_PROVEN`** (CASE A fully satisfied).
- **Capability State:** **`D2 — BOUNDED_PROOF for 0TH2.BIN and TH2.LOW`**.
- Both primary executable modules of Thor 2 now possess verified runtime provenance, exact destination bounds, full byte identity, transfer actor classification, and execution confirmation.
