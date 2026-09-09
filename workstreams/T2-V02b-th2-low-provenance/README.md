# T2-V02b — TH2.LOW Executable Provenance

Status: **PASS (V02B_DIRECT_PROVENANCE_PROVEN)**
Capability: **D2 — Executable Module Provenance (BOUNDED_PROOF for 0TH2.BIN and TH2.LOW)**

## 1. Overview

This workstream establishes the runtime executable provenance of Thor 2's secondary executable candidate `TH2.LOW` on the Sega Saturn architecture.

Using the pinned Mednafen debug dynamic oracle and `MednafenBot` IPC harness across two independent cold boots (Run A and Run B), this experiment proved:
1. Static call-site arguments in `0TH2.BIN` at `0x06004280..0x06004286` (`R4 -> "TH2.LOW"`, `R5 = 0x002DA000`, `R3 = 0x0600A0F8`, `JSR @R3`) are dynamically confirmed immediately before the call.
2. Disc file `TH2.LOW` (ISO9660 LBA 52123..52195, 73 sectors, 149,504 bytes) is read from CD Block sectors FAD `0x00CC31..0x00CC79`.
3. The routine at `0x0600A0F8` transfers the bytes directly into Low Work RAM at candidate destination `0x002DA000..0x002FE7FF` via Master SH-2 CPU writes from PC `0x0607DF08`, with zero SCU DMA transfers.
4. Pre-load live RAM at `0x002DA000` differed from the file; post-load live RAM matches extracted `TH2.LOW` byte-for-byte across all 149,504 bytes (`FULL_EXACT_MATCH`, 0 differing bytes, SHA-256 `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224`).
5. Master SH-2 runtime execution from within the mapped `TH2.LOW` extent was dynamically observed at `0x002E9910..0x002E9914` (module offset `0xF910`, cycle `387459915`).

---

## 2. Provenance Chain Summary

```
Disc Image (ISO9660 LBA 52123..52195, 73 sectors, 149,504 bytes)
  │ SHA-256: 781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224
  ▼ [PROVEN: cdb.log shows FAD 0x00CC31..0x00CC79 transfer]
CD Block Sector Buffer
  ▼ [PROVEN: mem.log shows Master SH-2 CPU write loop at PC 0x0607DF08]
Low Work RAM Destination: 0x002DA000 .. 0x002FE7FF (0x24800 bytes)
  │ Live RAM Snapshot SHA-256: 781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224
  │ Byte comparison vs disc: 0 differing bytes (100% exact match across 149,504 bytes)
  ▼ [PROVEN: Breakpoint at 0x002E9910 hit at cycle 387459915, called from 0x060042E0]
Master SH-2 Runtime Execution
```

---

## 3. Workstream Deliverables

- `provenance_evidence.md`: detailed factual evidence report covering disc extent, call-site argument confirmation, pre/post RAM snapshots, CD Block FAD trace, memory write profile, and execution observation.

---

## 4. Next Action

Review V-02b evidence before starting **D3 — Exact SH-2 Decode / L0 Semantics**.
