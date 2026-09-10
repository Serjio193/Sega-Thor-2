#include "thor/sh2/sh2_decoder.hpp"
#include "reference_decode_manifest.hpp"
#include "test_framework.hpp"

#include <iostream>

using namespace thor::sh2;

static void test_manifest_crosscheck() {
    const auto& manifest = get_reference_decode_manifest();
    for (const auto& vec : manifest) {
        const Sh2Instruction ins = decode_sh2(vec.raw_opcode, vec.pc);

        THOR_ASSERT(ins.is_valid());
        THOR_ASSERT(ins.id == vec.expected_id);
        THOR_ASSERT(ins.rn == vec.expected_rn);
        THOR_ASSERT(ins.rm == vec.expected_rm);
        THOR_ASSERT(ins.disp == vec.expected_disp);
        THOR_ASSERT(ins.flow == vec.expected_flow);
        THOR_ASSERT(ins.has_delay_slot == vec.expected_has_delay_slot);
        THOR_ASSERT(ins.mem_access == vec.expected_mem_access);

        if (vec.expected_target != 0) {
            THOR_ASSERT(ins.compute_branch_target() == vec.expected_target);
        }

        if (vec.expected_ea != 0) {
            uint32_t base_reg = (vec.expected_id == OpcodeId::MOV_W_READ_MEM) ? 0x06004000 : 0x06081C10;
            THOR_ASSERT(ins.compute_effective_address(base_reg) == vec.expected_ea);
        }
    }
}

static void test_bra_displacement_edge_cases() {
    const uint32_t pc = 0x06002000;

    // disp = 0 -> PC + 4
    {
        const Sh2Instruction ins = decode_sh2(0xA000, pc);
        THOR_ASSERT(ins.id == OpcodeId::BRA);
        THOR_ASSERT(ins.has_delay_slot);
        THOR_ASSERT(ins.compute_branch_target() == pc + 4);
    }

    // disp = +1 -> PC + 4 + 2 = PC + 6
    {
        const Sh2Instruction ins = decode_sh2(0xA001, pc);
        THOR_ASSERT(ins.compute_branch_target() == pc + 6);
    }

    // disp = +3 -> PC + 4 + 6 = PC + 10 (as in 0TH2.BIN startup: 0x06004008 -> 0x06004012)
    {
        const Sh2Instruction ins = decode_sh2(0xA003, 0x06004008);
        THOR_ASSERT(ins.compute_branch_target() == 0x06004012);
    }

    // Max positive displacement (+2047): 0xA7FF -> PC + 4 + (2047 * 2) = PC + 4098
    {
        const Sh2Instruction ins = decode_sh2(0xA7FF, pc);
        THOR_ASSERT(ins.compute_branch_target() == pc + 4098);
    }

    // Backward self-loop (disp = -2): 0xAFFE -> PC + 4 + (-2 * 2) = PC
    {
        const Sh2Instruction ins = decode_sh2(0xAFFE, pc);
        THOR_ASSERT(ins.compute_branch_target() == pc);
    }

    // Delay-slot loop (disp = -1): 0xAFFF -> PC + 4 + (-1 * 2) = PC + 2
    {
        const Sh2Instruction ins = decode_sh2(0xAFFF, pc);
        THOR_ASSERT(ins.compute_branch_target() == pc + 2);
    }

    // Max negative displacement (-2048): 0xA800 -> PC + 4 + (-2048 * 2) = PC - 4092
    {
        const Sh2Instruction ins = decode_sh2(0xA800, pc);
        THOR_ASSERT(ins.compute_branch_target() == pc - 4092);
    }
}

static void test_pc_relative_ea_rules() {
    // Aligned PC: 0x06004004
    const Sh2Instruction aligned_ins = decode_sh2(0xD417, 0x06004004);
    THOR_ASSERT(aligned_ins.compute_effective_address() == 0x06004064);

    // Unaligned PC: 0x06004002 -> ((0x06004002 & ~3) + 4) + 0x5C = 0x06004004 + 0x5C = 0x06004060
    const Sh2Instruction unaligned_ins = decode_sh2(0xD417, 0x06004002);
    THOR_ASSERT(unaligned_ins.compute_effective_address() == 0x06004060);
}

static void test_jsr_decoding_all_registers() {
    for (uint8_t reg = 0; reg < 16; ++reg) {
        const uint16_t op = static_cast<uint16_t>(0x400Bu | (static_cast<uint16_t>(reg) << 8));
        const uint32_t pc = 0x06004280 + (reg * 2u);
        const Sh2Instruction ins = decode_sh2(op, pc);

        THOR_ASSERT(ins.is_valid());
        THOR_ASSERT(ins.id == OpcodeId::JSR);
        THOR_ASSERT(ins.rn == reg);
        THOR_ASSERT(ins.rm == 0);
        THOR_ASSERT(ins.disp == 0);
        THOR_ASSERT(ins.flow == ControlFlowType::CALL);
        THOR_ASSERT(ins.has_delay_slot == true);
        THOR_ASSERT(ins.mem_access == MemoryAccessType::NONE);

        std::string expected_mn = "jsr @r" + std::to_string(reg);
        THOR_ASSERT(ins.mnemonic() == expected_mn);
    }
}

static void test_mov_l_write_predec_decoding() {
    const Sh2Instruction ins = decode_sh2(0x2FE6, 0x002E9910);
    THOR_ASSERT(ins.is_valid());
    THOR_ASSERT(ins.id == OpcodeId::MOV_L_WRITE_PREDEC);
    THOR_ASSERT(ins.rn == 15);
    THOR_ASSERT(ins.rm == 14);
    THOR_ASSERT(ins.flow == ControlFlowType::SEQUENTIAL);
    THOR_ASSERT(ins.has_delay_slot == false);
    THOR_ASSERT(ins.mem_access == MemoryAccessType::WRITE_U32);
    THOR_ASSERT(ins.mnemonic() == "mov.l r14, @-r15");
}

static void test_rts_decoding() {
    const Sh2Instruction ins = decode_sh2(0x000B, 0x06004720);
    THOR_ASSERT(ins.is_valid());
    THOR_ASSERT(ins.id == OpcodeId::RTS);
    THOR_ASSERT(ins.flow == ControlFlowType::RETURN);
    THOR_ASSERT(ins.has_delay_slot == true);
    THOR_ASSERT(ins.mem_access == MemoryAccessType::NONE);
    THOR_ASSERT(ins.mnemonic() == "rts");
}

static void test_unsupported_opcodes_fail_closed() {
    const uint16_t unmodeled[] = {
        0x0000, 0x0001, 0x2FE5, 0x4000, 0x400A, 0x400C, 0x7001,
        0x8900, 0xB000, 0xC000, 0xE000, 0xFFFF
    };
    for (uint16_t op : unmodeled) {
        const Sh2Instruction ins = decode_sh2(op, 0x06004000);
        THOR_ASSERT(!ins.is_valid());
        THOR_ASSERT(ins.id == OpcodeId::UNKNOWN);
        THOR_ASSERT(ins.flow == ControlFlowType::ILLEGAL);
        THOR_ASSERT(ins.mem_access == MemoryAccessType::NONE);
    }
}

int main() {
    std::cout << "[test_sh2_decoder] Running manifest cross-check (Hitachi, Mednafen, Catherine)...\n";
    test_manifest_crosscheck();
    std::cout << "[test_sh2_decoder] Running BRA displacement edge cases...\n";
    test_bra_displacement_edge_cases();
    std::cout << "[test_sh2_decoder] Running JSR all-register decoding tests...\n";
    test_jsr_decoding_all_registers();
    std::cout << "[test_sh2_decoder] Running PC-relative EA rules...\n";
    test_pc_relative_ea_rules();
    std::cout << "[test_sh2_decoder] Running MOV.L Rm, @-Rn decoding tests...\n";
    test_mov_l_write_predec_decoding();
    std::cout << "[test_sh2_decoder] Running RTS decoding tests...\n";
    test_rts_decoding();
    std::cout << "[test_sh2_decoder] Running fail-closed unsupported opcode tests...\n";
    test_unsupported_opcodes_fail_closed();

    std::cout << "[test_sh2_decoder] PASS: All decode checks green (0 disagreements).\n";
    return 0;
}
