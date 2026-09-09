# V-02a — 0TH2.BIN Executable Provenance Evidence

Status: **PASS (V02A_DIRECT_PROVENANCE_PROVEN)**
Capability: **D2 — Executable Module Provenance (BOUNDED_PROOF for 0TH2.BIN)**
Target: Disc file `0TH2.BIN` runtime extent and execution mapping
Target Revision: `thor2_ntsc_patched_fe11d2fb`

## 1. Canonical Disc Extent & Identity

- **File Path on Disc:** `0TH2.BIN` (first file record in ISO9660 root directory)
- **Logical Extent (LBA):** 24
- **Logical File Size:** 535,552 bytes (`0x82C00`)
- **Logical Sector Count:** 262 sectors (`535552 / 2048 = 261.5` $\rightarrow$ 262 sectors, LBA 24 to 285 inclusive)
- **Disc File SHA-256:** `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64`
- **Saturn CD Block FAD Addressing:**
  Saturn CD Block addressing maps $\text{FAD} = \text{LBA} + 150$.
  - Start FAD: $24 + 150 = 174 = \text{0x0000AE}$
  - End FAD: $285 + 150 = 435 = \text{0x0001B3}$
  - Following file (`ARELE.BIN`, LBA 286): $\text{FAD} = 286 + 150 = 436 = \text{0x0001B4}$

---

## 2. Pre-Entry Live RAM Snapshots

Immediately upon hitting the entry breakpoint at candidate base `0x06004000` (before the first game instruction retired), the full candidate extent `0x82C00` was dumped via `dump_mem_bin 06004000 82C00`.

### 2.1 Run A (Independent Cold Boot)
- **Runtime Environment:** `/mnt/c/Users/serji/.../scratch/provenance/run_a`
- **Dump Base Address:** `0x06004000`
- **Dump Size:** 535,552 bytes (`0x82C00`)
- **Dumped RAM SHA-256:** `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64`
- **Comparison vs Disc `0TH2.BIN`:** **FULL_EXACT_MATCH** (0 differing bytes across all 535,552 bytes)

### 2.2 Run B (Independent Cold Boot)
- **Runtime Environment:** `/mnt/c/Users/serji/.../scratch/provenance/run_b`
- **Dump Base Address:** `0x06004000`
- **Dump Size:** 535,552 bytes (`0x82C00`)
- **Dumped RAM SHA-256:** `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64`
- **Comparison vs Disc `0TH2.BIN`:** **FULL_EXACT_MATCH** (0 differing bytes)
- **Comparison Run A vs Run B:** **100% IDENTICAL**

---

## 3. Disc & CD Block Transfer Evidence

Inspection of `cdb.log` during the boot phase recorded the exact sequence of CD Block operations:
1. Drive phase transitioned from `STARTUP` to `PLAY`.
2. Commands `Get Sector Number` and `Get and Delete Sector Data` were executed for each individual sector from FAD `0x0000AE` (LBA 24) through FAD `0x0001B3` (LBA 285).
3. The sector transfer sequence terminated with `CMD End Data Transfer` at FAD `0x0001B3` (cycle `157276`).
4. Subsequent sector query at FAD `0x0001B4` entered `PAUSE` status, confirming exact bounds matching `0TH2.BIN`'s 262 sectors.

---

## 4. Memory Transfer Mechanism

Tracing SCU DMA (`dma_trace`) and memory write operations (`mem_profile 06004000 06086BFF`) established:
- **SCU DMA Activity:** Exactly 241 DMA Level 0 transfers occurred during the boot window. All 241 transfers targeted VDP2 VRAM (`0x05C00000..0x05C2FFFF`) for Saturn splash display. Zero SCU DMA transfers targeted High Work RAM (`0x06004000..0x06086BFF`).
- **CPU Write Activity:** High Work RAM writes were executed by the Master SH-2 executing from BIOS ROM (`mpr-17933.bin` in `0x00000000..0x0007FFFF`):
  - PC `0x000002B4` & `0x00002F0A`: Initial buffer zeroing and cleanup.
  - PC `0x00002368`: Tight copy loop (`MOV.B @R0, R1` / `MOV.B R1, @R7`) transferring sector bytes directly from the CD Block data register into High Work RAM (`0x06004000..0x06086BFF`).
- **Classification:** **`DIRECT_CPU_COPY_OBSERVED`**.

---

## 5. Execution Confirmation

- **Target CPU:** `MASTER_SH2`
- **Entry Breakpoint:** Requested `0x06004000`, hook PC `0x06004002` (via `pc - 2` delayed branch fallback from BIOS `ret=0x06002244`).
- **Master Cycle:** `305,462,360`
- **Execution Continuation:**
  - Step 1: PC `0x06004004` (pipeline advance)
  - Step 2: PC `0x06004006` (retires `0x6611` at `0x06004000`)
  - Step 3: PC `0x06004008` (retires `0x6F03` at `0x06004002`)
- **Range Status:** `0x06004000..0x06004008` **EXECUTED**; remainder of `0x06004000..0x06086BFF` **MAPPED (BYTE_EXACT)**.

---

## 6. Complete Provenance Chain

| Stage / Link | Evidence | Status |
|---|---|---|
| Disc Extent | ISO9660 LBA 24..285, 262 sectors, SHA-256 `c1cc4117...` | **PROVEN** |
| Disc Reading | CD Block `Get and Delete Sector Data` FAD `0x0000AE..0x0001B3` | **PROVEN** |
| Memory Transfer | BIOS Master SH-2 CPU copy loop (`PC=0x00002368`) to High Work RAM | **PROVEN** |
| Runtime Mapping | Pre-execution live RAM dump `0x06004000..0x06086BFF` matches disc byte-for-byte | **PROVEN** |
| Execution | Master SH-2 entry breakpoint hit and stepped inside mapped extent | **PROVEN** |

---

## 7. Verdict & Decision

- **Experiment Result:** **`V02A_DIRECT_PROVENANCE_PROVEN`** (CASE A fully satisfied).
- **Capability State:** **`D2 — BOUNDED_PROOF for 0TH2.BIN only`**.
- **Method Adoption:** **`ADOPT_PARTIAL`** (Daytona Provenance Methodology adopted for module mapping and pre-execution live byte comparison; ADR D-011).
