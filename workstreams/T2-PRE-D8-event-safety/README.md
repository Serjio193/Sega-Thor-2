# Workstream T2-PRE-D8 — Minimum Event Safety Proof

Status: **PASS (`PRE_D8_MINIMUM_EVENT_SAFETY_PASS` for `bb_06004000` bounded execution only)**  
Target: Thor 2 Master SH-2 Startup Basic Block `bb_06004000` (`0x06004000..0x0600400A`, exit `0x06004012`)  
Substrate: Canonical patched NTSC disc (`fe11d2fb...`), Retail BIOS (`96e106f7...`)  
Oracle: Pinned Mednafen debug fork (`1554266...`, binary `861f03f3...`)

---

## 1. Objective

Before any mechanical or native block translation can be treated as an atomic state transition, the execution window of the candidate block must be proven free of unmodeled asynchronous or peripheral event boundaries:
- no MMIO accesses requiring peripheral synchronization;
- no accepted IRQ boundaries interrupting block atomicity;
- no SCU DMA event crossing the block window;
- no Slave SH-2 activity capable of mutating observable state;
- strict compliance of delayed branch and delay-slot semantics with architectural SH-2 specifications.

---

## 2. Verdict & Evidence Summary

`PRE_D8_MINIMUM_EVENT_SAFETY_PASS` is confirmed across two independent cold boots (Run A and Run B):
1. **MMIO Isolation**: All 6 instructions and their operands access only High Work RAM (`0x06000000..0x060FFFFF`). Zero MMIO bus transactions occur.
2. **Interrupt Invariance**: SR interrupt mask remains `I3..I0 = 0`, zero interrupt handlers or vector table fetches occur, and SH-2 architectural rules forbid interrupt acceptance in delay slots.
3. **SCU DMA Absence**: DMA tracing confirms zero DMA transfers during the entire startup execution window (`cycle=305462360..305462388`).
4. **Slave SH-2 Inactivity**: Slave SH-2 is observed disabled (`active=0`, `last_PC=00000000`).
5. **Cycle Window**: Bounded basic block duration spans exactly 27 master cycles (`305,462,360` to `305,462,387`), retiring atomically to exit `0x06004012` (subsequent instruction boundary at `305,462,388` delta 28; earlier mention of 18 was an arithmetic/typographical error for 28).

Detailed trace tables and logs are recorded in [event_safety_evidence.md](event_safety_evidence.md).
