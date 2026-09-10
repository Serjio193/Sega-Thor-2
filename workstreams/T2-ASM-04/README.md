# Workstream T2-ASM-04: Secondary Modules & Systematic Executable Inventory

## Objectives
- Conduct exhaustive disc census across all 33 Saturn CD-ROM files.
- Determine processor ownership for Master SH-2, Slave SH-2, and Motorola 68EC000.
- Establish formal module manifest and linker script for `SET07.BIN` (overlay).
- Establish formal module manifest for `BGM.BIN` (sound driver).
- Generate lossless assembly container for `SET07.BIN` and prove byte-exact reassembly.
- Expand `thor_sh2` instruction decoder for `MOV_L_WRITE_PREDEC` and `RTS`, promoting `TH2.LOW` confirmed code to `MNEMONIC_PROVEN`.
- Maintain test suite integrity across Windows MinGW and Linux WSL (24/24 CTests pass).

## Verification Artifacts
- Manifests:
  - `asm/manifests/SET07.BIN.json`
  - `asm/manifests/BGM.BIN.json`
  - `asm/manifests/TH2.LOW.json` (upgraded)
- Linker script: `asm/linker/SET07.ld`
- Integration test: `tests/asm/test_set07_asm.py`
- Machine-readable evidence: `workstreams/T2-ASM-04/experiment_evidence.json`
- Detailed evidence: `workstreams/T2-ASM-04/experiment_evidence.md`
