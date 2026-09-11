# Current task

TASK: T2-D13-01 Implement Guest-Address & Native-Type Provenance Model (Milestone D13 / Gate V-09)
WHY: Moving toward native C++20 recovery requires typed data structures, but raw pointer conversions or ad-hoc host structures discard original Saturn VMA provenance and prevent differential verification. Gate V-09 establishes a strongly-typed `GuestAddress<T>`, `GuestPtr<T>`, and `GuestView` type system preserving original guest addresses (e.g. `0x06081C04..0x06081C18` BSS/Data init table), enforcing bounds/alignment fail-closed, and verifying 100% equivalence against flat memory.

CURRENT MILESTONE: Milestone D13 (docs/DEVELOPMENT_PLAN.md, Gate V-09 in docs/PIPELINE_VALIDATION_PLAN.md)
TASK STATUS: IN_PROGRESS
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
SLICE CONFIDENCE EVIDENCE: Saturn application startup descriptor table at `0x06081C04..0x06081C18` is proven by dynamic watchpoint traces (V-01, V-02a) and mechanical execution of `bb_06004000` (D8) to contain `_data_rom_start`, `_data_ram_start`, `_data_ram_end`, `_bss_start` (`0x060917DC`), and `_bss_end`.
ACCEPTANCE CRITERIA:
- [x] Define type-safe `GuestAddress<T>`, `GuestPtr<T>`, and provenance tags in `include/thor/provenance/guest_address.hpp`;
- [x] Define `GuestView` with big-endian reading/writing and range validation in `include/thor/provenance/guest_view.hpp`;
- [x] Define proven Saturn application init layout `SaturnStartupTable` with evidence-backed guest offsets in `include/thor/provenance/saturn_runtime_table.hpp`;
- [x] Implement comprehensive test suite `tests/provenance/test_guest_provenance.cpp` verifying type safety, VMA preservation, alignment enforcement, negative controls (out of bounds, misalignment, null), and differential equivalence vs `ISh2Memory`;
- [x] Register test in `CMakeLists.txt` and verify 100% pass across Windows MinGW and Linux WSL;
- [x] Update `docs/WORKLOG.md`, `docs/FILE_MAP.md`, `docs/PROJECT_STATE.md`, `docs/ROADMAP.md`, and `TASK.md`;
- [x] Ensure all modified/new files adhere strictly to the <= 500 lines limit;
- [x] Maintain legal repository hygiene (zero commercial bytes in git).

EVIDENCE AVAILABLE:
- Dynamic watchpoint and trace logs for `0x06081C04..0x06081C18`;
- Mechanical execution records of `bb_06004000` and `0x06004012` boot loop;
- Authoritative `thor::sh2::ISh2Memory` big-endian bus semantics.
KNOWN UNKNOWNS:
- Extended stage overlay data structure field mappings (reserved for D14 / stage loading).
ALLOWED SCOPE:
- Provenance type system (`include/thor/provenance/`), test suite (`tests/provenance/`), build scripts, and documentation.
OUT OF SCOPE:
- Premature abstraction of unproven game structures or speculative renaming.

## Last verified result

`V-09_GUEST_PROVENANCE_PASS`: Strongly typed `GuestAddress<T>`, `GuestPtr<T>`, `GuestView`, and `SaturnStartupTable` implemented; 100% test pass on Windows MinGW and Linux WSL (`test_guest_provenance`).

## Session checkpoint

CURRENT MILESTONE: Milestone D13 (Guest-Address/Type Provenance, Gate V-09)
CURRENT TASK: T2-D13-01 Implement Guest-Address & Native-Type Provenance Model
TASK STATUS: COMPLETE
MILESTONE UNDERSTANDING CONFIDENCE: 100%
CURRENT SLICE UNDERSTANDING CONFIDENCE: 100%
LAST VERIFIED RESULT: Gate V-09 satisfied with 5/5 sub-tests passing; dual-platform green.
FILES CHANGED: CMakeLists.txt, TASK.md, include/thor/provenance/guest_address.hpp, include/thor/provenance/guest_view.hpp, include/thor/provenance/saturn_runtime_table.hpp, tests/provenance/test_guest_provenance.cpp.
TESTS RUN: test_guest_provenance passing on Windows MinGW and Linux WSL; 37/37 unit tests passing on Windows & Linux WSL.
NEW KNOWLEDGE: Confirmed Saturn startup descriptor layout at 0x06081C04..0x06081C18; verified big-endian typed view with fail-closed bounds and alignment checking.
OPEN QUESTIONS: Resource decode/re-encode toolchain for stage overlays and sprites (D14).
EXACT NEXT ACTION: Update documentation (WORKLOG, FILE_MAP, PROJECT_STATE, ROADMAP), commit and push D13, then proceed to D14 / D17.
