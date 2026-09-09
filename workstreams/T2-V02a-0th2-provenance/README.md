# T2-V02a — 0TH2.BIN Executable Provenance

Status: **PASS (V02A_DIRECT_PROVENANCE_PROVEN)**
Capability: **D2 — Executable Module Provenance (BOUNDED_PROOF for 0TH2.BIN)**
Method Adoption: **ADOPT_PARTIAL (Daytona Provenance Methodology, ADR D-011)**

## 1. Overview

This workstream establishes the runtime executable provenance of Thor 2's primary disc binary `0TH2.BIN` on the Sega Saturn architecture.

Using the pinned Mednafen debug dynamic oracle and `MednafenBot` IPC harness, this experiment proved that `0TH2.BIN` is loaded directly from the disc into High Work RAM at `0x06004000` without byte transformation, and that the Master SH-2 CPU executes code directly from this mapping.

---

## 2. Provenance Chain Summary

```
Disc Image (ISO9660 LBA 24..285, 262 sectors, 535,552 bytes)
  │ SHA-256: c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64
  ▼ [PROVEN: cdb.log shows FAD 0x0000AE..0x0001B3 transfer]
CD Block Sector Buffer
  ▼ [PROVEN: mem.log shows BIOS Master SH-2 CPU transfer loop at PC 0x00002368]
High Work RAM Destination: 0x06004000 .. 0x06086BFF (0x82C00 bytes)
  │ Live RAM Snapshot SHA-256: c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64
  │ Byte comparison vs disc: 0 differing bytes (100% exact match across 535,552 bytes)
  ▼ [PROVEN: Breakpoint 0x06004000 hit at cycle 305462360; steps 1–3 executed]
Master SH-2 Runtime Execution
```

---

## 3. Workstream Deliverables

- `provenance_evidence.md`: detailed factual report covering disc identity, pre-entry RAM snapshots (Run A and Run B), CD Block FAD trace, CPU transfer mechanism, and execution evidence.
- Full verification logs and non-copyrighted summaries.

---

## 4. Next Action

Review V-02a evidence before authorizing **V-02b — TH2.LOW Executable Provenance**.
