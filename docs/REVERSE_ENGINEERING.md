# Reverse engineering record

## Confirmed substrate: `thor2_ntsc_patched_fe11d2fb`

T2-M0 reproducibility gate: **PASS**.

Two independent executions of `tools/disc/census_saturn_cd.py` produced identical `disc_manifest.tsv` and summary outputs from the same private input image.

### Disc identity

| Item | Value | Status |
|---|---|---|
| Image SHA-256 | `fe11d2fbda58d63300ef2265c555ce05bddf14d69fb7b73fc409e25c0ef6c0a8` | CONFIRMED |
| CUE SHA-256 | `afc0b101bbb493adbd43fd44ffd76959484d67cf0b566137dd145f1c68d411e0` | CONFIRMED |
| Format | `MODE1/2352` | CONFIRMED |
| Raw sectors | 52,224 | CONFIRMED |
| Volume ID | `THE STORY OF THOR 2` | CONFIRMED |
| Files | 33 | CONFIRMED |
| Product code | `MK-81302` | CONFIRMED |
| Version | `V1.000` | CONFIRMED |
| Header date | `19960618` | CONFIRMED |
| Header title | `THE STORY OF      THOR 2 (patched for NTSC)` | CONFIRMED |
| First-read address | `0x06004000` | CONFIRMED header field |

Full per-file identity is in `workstreams/T2-M0-disc-census/disc_manifest.tsv`.

## Executable module `0TH2.BIN`

Module status: `EXECUTABLE_MODULE / RUNTIME_MAPPING_EXACT / FULL_EXACT_MATCH / DIRECT_PROVENANCE_PROVEN` (V-02a proven direct runtime mapping; ADR D-011).
Byte classification: `CONFIRMED_CODE / EXECUTED` for dynamically observed instructions at `0x06004000..0x06004008`; unexecuted remainder `0x06004008..0x06086BFF` remains `PROBABLE_CODE / HIGH` (mapped byte-exact to disc; complete code/data/unknown ownership queued for D4).

- SHA-256: `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64`
- Disc extent: ISO9660 LBA 24..285 (262 sectors, 535,552 bytes / `0x82C00`)
- CD Block FAD: `0x0000AE` .. `0x0001B3` (LBA + 150)
- Runtime load base: `0x06004000`
- Runtime load end: `0x06086BFF`
- Transfer mechanism: `DIRECT_CPU_COPY_OBSERVED` (BIOS Master SH-2 copy loop at PC `0x00002368`, zero SCU DMA to High Work RAM)
- Pre-entry live RAM hash: `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64` (0 differing bytes vs disc, `FULL_EXACT_MATCH` across Run A and Run B)
- Execution: Master SH-2 entry breakpoint hit at cycle `305462360`; initial instructions executed at `0x06004000..0x06004008`

Evidence:

- Saturn header first-read address is `0x06004000`;
- it is the first ISO9660 file record;
- **Dynamic proof (V-01-core / V-01-automation)**: Master SH-2 hit breakpoint on candidate entry `0x06004000` from BIOS (`ret=0x06002244`) at frame 680, cycle `305462360` (debugger hook PC `0x06004002` via `pc - 2` fallback). Startup sequence: Step 2 retires `0x6611` (`MOV.W @R1, R6`, setting R6=`0x6611`); Step 3 retires `0x6F03` (`MOV R0, R15`, switching SP from header default `0x06001000` to target `0x06002EDC`); Step 4 retires `0xD417` (`MOV.L @(0x5C, PC), R4`, loading pointer `0x06081C10`); Step 5 executes `0x6442` (`MOV.L @R4, R4`), dynamically triggering `read_watchpoint 06081C10` with value `0x060917DC` (BSS start pointer); Step 6 completes R4 writeback to `0x060917DC`.
- **Dynamic provenance proof (V-02a)**: Proved direct byte identity between disc file and live pre-execution RAM at `0x06004000..0x06086BFF` across two independent cold boots (`FULL_EXACT_MATCH`). CD Block trace `cdb.log` proved 262-sector transfer (`Get and Delete Sector Data`) across FAD `0x0000AE..0x0001B3` terminating with `End Data Transfer`. Traces `dma.log` and `mem.log` proved zero SCU DMA to High Work RAM and transfer via BIOS Master SH-2 CPU copy loop at PC `0x00002368` (`MOV.B @R0, R1` / `MOV.B R1, @R7`).

Next proof: exact SH-2 decode / L0 semantics (D3).

## Executable module `TH2.LOW`

Module status: `EXECUTABLE_MODULE / RUNTIME_MAPPING_EXACT / FULL_EXACT_MATCH / DIRECT_PROVENANCE_PROVEN` (V-02b proven direct runtime mapping).
Byte classification: `CONFIRMED_CODE / EXECUTED` for dynamically observed instructions at `0x002E9910..0x002E9914`; unexecuted remainder `0x002DA000..0x002FE7FF` remains `PROBABLE_CODE / HIGH` (mapped byte-exact to disc; complete code/data/unknown ownership queued for D4).

- SHA-256: `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224`
- Disc extent: ISO9660 LBA 52123..52195 (73 sectors, 149,504 bytes / `0x24800`)
- CD Block FAD: `0x00CC31` .. `0x00CC79` (LBA + 150)
- Runtime load base: `0x002DA000`
- Runtime load end: `0x002FE7FF`
- Transfer mechanism: `DIRECT_CPU_COPY_OBSERVED` (Master SH-2 CPU write loop at PC `0x0607DF08`, zero SCU DMA to Low Work RAM)
- Pre-load live RAM hash: `71ba98cb5315c867d5670e7d214b2369d52235d1182658413d3890cfb982be6e`
- Post-load live RAM hash: `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224` (0 differing bytes vs disc, `FULL_EXACT_MATCH` across Run A and Run B)
- Execution: Master SH-2 breakpoint at `0x002E9910` hit at cycle `387459915` (called from `0x060042E0`, `PR=0x060042E4`), executed `0x2FE6` (`MOV.L R14, @-R15`) advancing to `0x002E9914`.

Evidence:
- **Static evidence**: recorded in `workstreams/T2-M0-disc-census/static_load_evidence.md`. Call-site in `0TH2.BIN` at `0x06004280..0x06004286` prepares `R4 -> "TH2.LOW"` (`0x06081C20`), `R5 = 0x002DA000`, and `JSR @R3` (`R3 = 0x0600A0F8`).
- **Dynamic call-site proof (V-02b)**: CPU state confirmed before call: `R3 = 0x0600A0F8`, `R4 = 0x06081C20` (memory read dynamically confirmed ASCII `"TH2.LOW"`), `R5 = 0x002DA000`, `PR = 0x0600428A`.
- **Dynamic transfer & mapping proof (V-02b)**: CD Block trace `cdb.log` recorded 73-sector read (`CMD Play; Start=0x80cc31, End=0x800049`) across FAD `0x00CC31..0x00CC79`. Memory trace `mem.log` recorded 37,376 32-bit writes ($37376 \times 4 = 149,504$ bytes) into `0x002DA000..0x002FE7FF` by Master SH-2 at PC `0x0607DF08`. SCU DMA trace recorded zero DMA to Low Work RAM. Live RAM snapshot post-transfer matches disc file byte-for-byte (`FULL_EXACT_MATCH`, 0 differing bytes).
- **Dynamic execution proof (V-02b)**: Called from `0x060042E0` (`PR=0x060042E4`), Master SH-2 executed instruction at `0x002E9910` (offset `0xF910`, cycle `387459915`), retiring `MOV.L R14, @-R15` (`0x2FE6`) and advancing PC to `0x002E9914`.

Next proof: D3 opcode corpus expansion / D4 code/data ownership.

## Executed startup opcode slice (`0x06004000..0x06004008`)

Slice status: `DECODE_VERIFIED` / `INSTRUCTION_SEMANTICS_VERIFIED` / `MEMORY_SEMANTICS_VERIFIED` (T2-D3.1).
Decoder: `thor::sh2::decode_sh2` (fail-closed C++20 implementation; V-06 cross-check passed with 0 disagreements).
Executor: `thor::sh2::execute_sh2_instruction` / `thor::sh2::step_sh2` (L0 semantic test suite and real Thor 2 startup vector passed with 0 divergences).

- `0x06004000`: `0x6611` — `MOV.W @R1, R6` (reads 16-bit word from `R1=0x06004000`, sign-extends to 32 bits into `R6=0x00006611`, advances PC to `0x06004002`).
- `0x06004002`: `0x6F03` — `MOV R0, R15` (copies stack pointer `R0=0x06002EDC` into `R15`, advances PC to `0x06004004`).
- `0x06004004`: `0xD417` — `MOV.L @(0x5C, PC), R4` (reads 32-bit word from `((PC & ~3) + 4) + 0x5C = 0x06004064` containing `0x06081C10` into `R4`, advances PC to `0x06004006`).
- `0x06004006`: `0x6442` — `MOV.L @R4, R4` (reads 32-bit word from `R4=0x06081C10` containing `0x060917DC` before writeback to `R4`, advances PC to `0x06004008`).

## Public-research address anchors queued for revision validation

Prior public Thor 2 research has reported:

- `0x06009CC4` — debug-related routine;
- `0x002E55A4` — Low Work RAM code;
- `0x002E8A38` — Low Work RAM code.

For the confirmed current substrate:

- `0x002E55A4` is consistent with `TH2.LOW + 0xB5A4`;
- `0x002E8A38` is consistent with `TH2.LOW + 0xEA38`;
- both current-revision offsets contain SH-2-like instruction streams.

These public labels/semantics remain revision hints until independently behavior-verified.

## Record template

For each new finding record:

```text
ID:
STATUS:
REVISION/HASH:
DISC FILE:
FILE RANGE:
RUNTIME RANGE:
CPU:
MODULE/GENERATION:
STATIC EVIDENCE:
DYNAMIC EVIDENCE:
READS/WRITES:
CONTROL FLOW:
HARDWARE INTERACTION:
HYPOTHESIS:
CONFIDENCE:
VERIFICATION:
NEGATIVE EVIDENCE:
NEXT ACTION:
```
