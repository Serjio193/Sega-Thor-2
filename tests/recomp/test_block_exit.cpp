#include "thor/recomp/block_exit.hpp"
#include "thor/sh2/sh2_block.hpp"
#include "thor/sh2/sh2_memory.hpp"
#include "thor/sh2/sh2_state.hpp"
#include "tests/sh2/test_framework.hpp"

#include <iostream>

using namespace thor::recomp;
using namespace thor::sh2;

static Sh2BasicBlock make_bb0() {
    Sh2FlatMemory mem;
    // 0x06004000..0x0600400A bytes:
    // 66 11 (MOV.W @R1, R6)
    // 6F 03 (MOV R0, R15)
    // D4 17 (MOV.L @(0x5c, PC), R4)
    // 64 42 (MOV.L @R4, R4)
    // A0 03 (BRA 0x06004012)
    // 00 09 (NOP)
    const uint8_t bytes[] = {
        0x66, 0x11, 0x6F, 0x03, 0xD4, 0x17, 0x64, 0x42, 0xA0, 0x03, 0x00, 0x09
    };
    for (size_t i = 0; i < sizeof(bytes); ++i) {
        mem.write8(0x06004000u + static_cast<uint32_t>(i), bytes[i]);
    }
    return discover_basic_block(0x06004000u, mem);
}

static Sh2BasicBlock make_cand_block() {
    Sh2FlatMemory mem;
    // 0x06004280..0x06004288:
    // D5 36 (MOV.L @(0xd8, PC), R5)
    // D4 37 (MOV.L @(0xdc, PC), R4)
    // D3 37 (MOV.L @(0xdc, PC), R3)
    // 43 0B (JSR @R3)
    // 00 09 (NOP)
    const uint8_t bytes[] = {
        0xD5, 0x36, 0xD4, 0x37, 0xD3, 0x37, 0x43, 0x0B, 0x00, 0x09
    };
    for (size_t i = 0; i < sizeof(bytes); ++i) {
        mem.write8(0x06004280u + static_cast<uint32_t>(i), bytes[i]);
    }
    return discover_basic_block(0x06004280u, mem);
}

static void test_static_exit_derivation_bb0() {
    Sh2BasicBlock bb0 = make_bb0();
    auto opt_desc = derive_block_exit_descriptor(bb0);
    THOR_ASSERT(opt_desc.has_value());

    const BlockExitDescriptor& desc = *opt_desc;
    THOR_ASSERT(desc.kind == BlockExitKind::DIRECT);
    THOR_ASSERT(desc.terminator_pc == 0x06004008u);
    THOR_ASSERT(desc.has_delay_slot == true);
    THOR_ASSERT(desc.static_target_pc.has_value());
    THOR_ASSERT(*desc.static_target_pc == 0x06004012u);
    THOR_ASSERT(!desc.fallthrough_pc.has_value());
    THOR_ASSERT(desc.writes_pr == false);
    std::cout << "  [OK] test_static_exit_derivation_bb0\n";
}

static void test_static_exit_derivation_candidate() {
    Sh2BasicBlock cand = make_cand_block();
    auto opt_desc = derive_block_exit_descriptor(cand);
    THOR_ASSERT(opt_desc.has_value());

    const BlockExitDescriptor& desc = *opt_desc;
    THOR_ASSERT(desc.kind == BlockExitKind::INDIRECT_CALL);
    THOR_ASSERT(desc.terminator_pc == 0x06004286u);
    THOR_ASSERT(desc.has_delay_slot == true);
    // Anti-hardcoding invariant: static descriptor MUST NOT contain static_target_pc
    THOR_ASSERT(!desc.static_target_pc.has_value());
    THOR_ASSERT(!desc.fallthrough_pc.has_value());
    THOR_ASSERT(desc.writes_pr == true);
    std::cout << "  [OK] test_static_exit_derivation_candidate\n";
}

static void test_runtime_exit_resolution_synthetic_controls() {
    Sh2BasicBlock cand = make_cand_block();
    auto opt_desc = derive_block_exit_descriptor(cand);
    THOR_ASSERT(opt_desc.has_value());
    const BlockExitDescriptor& desc = *opt_desc;

    // Control A: JSR result target = 0x0600A0F8, PR = 0x0600428A
    {
        Sh2CpuState post_state{};
        post_state.pc = 0x0600A0F8u;
        post_state.pr = 0x0600428Au;
        auto res = resolve_block_exit(desc, post_state);
        THOR_ASSERT(res.has_value());
        THOR_ASSERT(res->kind == BlockExitKind::INDIRECT_CALL);
        THOR_ASSERT(res->target_pc == 0x0600A0F8u);
        THOR_ASSERT(res->pr_value.has_value() && *res->pr_value == 0x0600428Au);
        THOR_ASSERT(res->delay_slot_completed == true);
    }

    // Control B: Alternate target = 0x0600BEEF
    {
        Sh2CpuState post_state{};
        post_state.pc = 0x0600BEEFu;
        post_state.pr = 0x0600428Au;
        auto res = resolve_block_exit(desc, post_state);
        THOR_ASSERT(res.has_value());
        THOR_ASSERT(res->target_pc == 0x0600BEEFu);
    }

    // Control C: Target = 0x00000000 (valid zero vector)
    {
        Sh2CpuState post_state{};
        post_state.pc = 0x00000000u;
        post_state.pr = 0x0600428Au;
        auto res = resolve_block_exit(desc, post_state);
        THOR_ASSERT(res.has_value());
        THOR_ASSERT(res->target_pc == 0x00000000u);
    }

    // Control D: Hardcoded target detector (mock hardcoding 0x0600A0F8 must fail when target is 0x0600BEEF)
    {
        auto mock_hardcoded_resolver = [](const Sh2CpuState&) -> uint32_t {
            return 0x0600A0F8u;
        };
        Sh2CpuState state_beef{};
        state_beef.pc = 0x0600BEEFu;
        auto res = resolve_block_exit(desc, state_beef);
        THOR_ASSERT(res.has_value());
        THOR_ASSERT(mock_hardcoded_resolver(state_beef) != res->target_pc);
    }

    // Control E: Direct BRA post-PC differing from static target must fail validation
    {
        Sh2BasicBlock bb0 = make_bb0();
        auto opt_bb0_desc = derive_block_exit_descriptor(bb0);
        THOR_ASSERT(opt_bb0_desc.has_value());

        // Normal: post_state.pc == 0x06004012
        Sh2CpuState valid_state{};
        valid_state.pc = 0x06004012u;
        auto res_valid = resolve_block_exit(*opt_bb0_desc, valid_state);
        THOR_ASSERT(res_valid.has_value());
        THOR_ASSERT(res_valid->target_pc == 0x06004012u);

        // Mismatched: post_state.pc == 0x06004020
        Sh2CpuState diverged_state{};
        diverged_state.pc = 0x06004020u;
        auto res_diverged = resolve_block_exit(*opt_bb0_desc, diverged_state);
        THOR_ASSERT(!res_diverged.has_value()); // Must fail closed!
    }

    std::cout << "  [OK] test_runtime_exit_resolution_synthetic_controls\n";
}

static void test_exit_descriptor_negative_controls() {
    // 1. Empty block fails closed
    Sh2BasicBlock empty_block{};
    THOR_ASSERT(!derive_block_exit_descriptor(empty_block).has_value());

    // 2. Inconsistent delay slot (terminator has delay slot, but delay_slot is nullopt)
    Sh2BasicBlock inc_block = make_cand_block();
    inc_block.delay_slot = std::nullopt;
    THOR_ASSERT(!derive_block_exit_descriptor(inc_block).has_value());

    // 3. Inconsistent delay slot (terminator lacks delay slot, but delay_slot has value)
    Sh2BasicBlock inc_block2 = make_cand_block();
    inc_block2.terminator.has_delay_slot = false;
    THOR_ASSERT(!derive_block_exit_descriptor(inc_block2).has_value());

    // 4. JSR with illegal static direct exit
    Sh2BasicBlock bad_jsr = make_cand_block();
    bad_jsr.direct_exits.push_back(0x0600A0F8u);
    THOR_ASSERT(!derive_block_exit_descriptor(bad_jsr).has_value());

    // 5. Unknown opcode terminator fails closed
    Sh2BasicBlock bad_term = make_cand_block();
    bad_term.terminator.id = OpcodeId::UNKNOWN;
    THOR_ASSERT(!derive_block_exit_descriptor(bad_term).has_value());

    // 6. Direct exit descriptor without static target fails resolution
    BlockExitDescriptor bad_desc{};
    bad_desc.kind = BlockExitKind::DIRECT;
    bad_desc.static_target_pc = std::nullopt; // Direct without static target
    Sh2CpuState s{};
    s.pc = 0x06004012u;
    THOR_ASSERT(!resolve_block_exit(bad_desc, s).has_value());

    // 7. JSR exit descriptor with illegally populated static target fails resolution
    BlockExitDescriptor bad_jsr_desc{};
    bad_jsr_desc.kind = BlockExitKind::INDIRECT_CALL;
    bad_jsr_desc.writes_pr = true;
    bad_jsr_desc.static_target_pc = 0x0600A0F8u; // JSR cannot have static target
    THOR_ASSERT(!resolve_block_exit(bad_jsr_desc, s).has_value());

    // 8. INDIRECT_CALL post-state still has delayed_pc (unretired delayed transfer) -> FAIL CLOSED
    Sh2BasicBlock cand = make_cand_block();
    auto opt_cand_desc = derive_block_exit_descriptor(cand);
    THOR_ASSERT(opt_cand_desc.has_value());
    Sh2CpuState unretired_indirect_state{};
    unretired_indirect_state.pc = 0x0600A0F8u;
    unretired_indirect_state.pr = 0x0600428Au;
    unretired_indirect_state.delayed_pc = 0x0600A0F8u; // Still pending!
    THOR_ASSERT(!resolve_block_exit(*opt_cand_desc, unretired_indirect_state).has_value());

    // 9. DIRECT post-state still has delayed_pc (unretired delayed transfer) -> FAIL CLOSED
    Sh2BasicBlock bb0 = make_bb0();
    auto opt_bb0_desc = derive_block_exit_descriptor(bb0);
    THOR_ASSERT(opt_bb0_desc.has_value());
    Sh2CpuState unretired_direct_state{};
    unretired_direct_state.pc = 0x06004012u;
    unretired_direct_state.delayed_pc = 0x06004012u; // Still pending!
    THOR_ASSERT(!resolve_block_exit(*opt_bb0_desc, unretired_direct_state).has_value());

    // 10. INDIRECT_CALL descriptor with writes_pr=false -> FAIL CLOSED
    BlockExitDescriptor no_pr_jsr = *opt_cand_desc;
    no_pr_jsr.writes_pr = false;
    Sh2CpuState valid_state{};
    valid_state.pc = 0x0600A0F8u;
    valid_state.pr = 0x0600428Au;
    THOR_ASSERT(!resolve_block_exit(no_pr_jsr, valid_state).has_value());

    // 11. INDIRECT_CALL descriptor with malformed fallthrough -> FAIL CLOSED
    BlockExitDescriptor fall_jsr = *opt_cand_desc;
    fall_jsr.fallthrough_pc = 0x0600428Au;
    THOR_ASSERT(!resolve_block_exit(fall_jsr, valid_state).has_value());

    // 12. DIRECT descriptor with writes_pr=true -> FAIL CLOSED
    BlockExitDescriptor pr_direct = *opt_bb0_desc;
    pr_direct.writes_pr = true;
    Sh2CpuState valid_dir_state{};
    valid_dir_state.pc = 0x06004012u;
    THOR_ASSERT(!resolve_block_exit(pr_direct, valid_dir_state).has_value());

    std::cout << "  [OK] test_exit_descriptor_negative_controls\n";
}

int main() {
    std::cout << "=== D9.2 Block Exit Descriptor & Resolution Unit Tests ===\n";
    test_static_exit_derivation_bb0();
    test_static_exit_derivation_candidate();
    test_runtime_exit_resolution_synthetic_controls();
    test_exit_descriptor_negative_controls();
    std::cout << "ALL BLOCK EXIT TESTS PASSED.\n";
    return 0;
}
