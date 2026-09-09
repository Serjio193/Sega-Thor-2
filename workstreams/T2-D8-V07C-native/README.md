# Workstream Record: T2-D8-V07C-native

- Milestone: `D8 — First Native Promotion Proof`
- Verification Gate: `V-07C — Authoritative Native Override Proof`
- Target Block: `bb_06004000` (`0x06004000..0x0600400A`, 12 bytes, exit `0x06004012`)
- CPU: `MASTER_SH2`
- Module: `0TH2.BIN` (High Work RAM base `0x06004000`)
- Status: `PASS` (D8: BOUNDED_PROOF for bb_06004000; V-07C: PASS)

## Objectives
1. Implement reusable production native dispatcher (`NativeDispatcher`) with pre-execution eligibility guarding, shadow verification qualification (`ShadowChecker`), and C ABI plugin interface (`thor_native_plugin`).
2. Integrate native dispatch into pinned Mednafen debug oracle via C ABI dynamic plugin bridge and hook at `0x06004000`.
3. Reconcile historical timing documentation ("18 cycles" typo corrected to exact 28-cycle window `305462360..305462388`).
4. Execute authoritative native override on cold boot (`Run A`), verify bit-identical cold-boot reproduction (`Run B`), baseline interpreter (`Run C`), shadow verify mode (`Run D`), and byte corruption fallback negative control (`Run E`).
5. Prove live interpreter retired 0 instructions in replaced block (`retirements_in_interval = 0`).
6. Prove continuation through BSS clear and data copy to `0x06004280` matching interpreter baseline across all 23 registers with zero divergence.
7. Prove 100% fail-closed fallback under memory corruption without partial native register commits.
