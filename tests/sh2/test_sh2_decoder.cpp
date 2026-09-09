#include "thor/sh2/sh2_decoder.hpp"
#include "test_framework.hpp"

#include <iostream>

using namespace thor::sh2;

static void test_target_opcodes_decode() {
    // 0x06004000: 0x6611 -> MOV.W @R1, R6
    {
        const Sh2Instruction ins = decode_sh2(0x6611, 0x06004000);
        THOR_ASSERT(ins.is_valid());
        THOR_ASSERT(ins.id == OpcodeId::MOV_W_READ_MEM);
        THOR_ASSERT(ins.rn == 6);
        THOR_ASSERT(ins.rm == 1);
        THOR_ASSERT(ins.length == 2);
        THOR_ASSERT(ins.flow == ControlFlowType::SEQUENTIAL);
        THOR_ASSERT(!ins.has_delay_slot);
        THOR_ASSERT(ins.mem_access == MemoryAccessType::READ_S16);
        THOR_ASSERT(ins.compute_effective_address(0x06004000) == 0x06004000);
        THOR_ASSERT(ins.mnemonic() == "mov.w @r1, r6");
    }

    // 0x06004002: 0x6F03 -> MOV R0, R15
    {
        const Sh2Instruction ins = decode_sh2(0x6F03, 0x06004002);
        THOR_ASSERT(ins.is_valid());
        THOR_ASSERT(ins.id == OpcodeId::MOV_REG);
        THOR_ASSERT(ins.rn == 15);
        THOR_ASSERT(ins.rm == 0);
        THOR_ASSERT(ins.length == 2);
        THOR_ASSERT(ins.flow == ControlFlowType::SEQUENTIAL);
        THOR_ASSERT(!ins.has_delay_slot);
        THOR_ASSERT(ins.mem_access == MemoryAccessType::NONE);
        THOR_ASSERT(ins.mnemonic() == "mov r0, r15");
    }

    // 0x06004004: 0xD417 -> MOV.L @(0x5C, PC), R4
    {
        const Sh2Instruction ins = decode_sh2(0xD417, 0x06004004);
        THOR_ASSERT(ins.is_valid());
        THOR_ASSERT(ins.id == OpcodeId::MOV_L_PC_REL);
        THOR_ASSERT(ins.rn == 4);
        THOR_ASSERT(ins.disp == 0x17);
        THOR_ASSERT(ins.length == 2);
        THOR_ASSERT(ins.flow == ControlFlowType::SEQUENTIAL);
        THOR_ASSERT(!ins.has_delay_slot);
        THOR_ASSERT(ins.mem_access == MemoryAccessType::READ_U32);
        // PC-relative calculation: ((0x06004004 & ~3) + 4) + (0x17 * 4) = 0x06004008 + 0x5C = 0x06004064
        THOR_ASSERT(ins.compute_effective_address() == 0x06004064);
        THOR_ASSERT(ins.mnemonic() == "mov.l @(0x5c, pc), r4");
    }

    // 0x06004006: 0x6442 -> MOV.L @R4, R4
    {
        const Sh2Instruction ins = decode_sh2(0x6442, 0x06004006);
        THOR_ASSERT(ins.is_valid());
        THOR_ASSERT(ins.id == OpcodeId::MOV_L_READ_MEM);
        THOR_ASSERT(ins.rn == 4);
        THOR_ASSERT(ins.rm == 4);
        THOR_ASSERT(ins.length == 2);
        THOR_ASSERT(ins.flow == ControlFlowType::SEQUENTIAL);
        THOR_ASSERT(!ins.has_delay_slot);
        THOR_ASSERT(ins.mem_access == MemoryAccessType::READ_U32);
        THOR_ASSERT(ins.compute_effective_address(0x06081C10) == 0x06081C10);
        THOR_ASSERT(ins.mnemonic() == "mov.l @r4, r4");
    }
}

static void test_pc_relative_ea_rules() {
    // Aligned PC: 0x06004004 -> ((0x06004004 & ~3) + 4) = 0x06004008
    const Sh2Instruction ins1 = decode_sh2(0xD400, 0x06004004);
    THOR_ASSERT(ins1.compute_effective_address() == 0x06004008);

    // Unaligned PC: 0x06004002 -> ((0x06004002 & ~3) + 4) = 0x06004000 + 4 = 0x06004004
    const Sh2Instruction ins2 = decode_sh2(0xD400, 0x06004002);
    THOR_ASSERT(ins2.compute_effective_address() == 0x06004004);

    // Unaligned PC: 0x06004006 -> ((0x06004006 & ~3) + 4) = 0x06004004 + 4 = 0x06004008
    const Sh2Instruction ins3 = decode_sh2(0xD400, 0x06004006);
    THOR_ASSERT(ins3.compute_effective_address() == 0x06004008);

    // Maximum displacement: disp = 0xFF (255) -> 255 * 4 = 1020 (0x3FC)
    const Sh2Instruction ins4 = decode_sh2(0xD0FF, 0x06004000);
    THOR_ASSERT(ins4.compute_effective_address() == 0x06004004 + 0x3FC);
}

static void test_unsupported_opcodes_fail_closed() {
    // Arbitrary unmodeled opcodes must fail closed as UNKNOWN
    const uint16_t unmodeled[] = {
        0x0000, 0x0009, 0x000B, 0x2FE6, 0x7001,
        0x8900, 0xA000, 0xB000, 0xC000, 0xE000, 0xFFFF
    };
    for (uint16_t op : unmodeled) {
        const Sh2Instruction ins = decode_sh2(op, 0x06004000);
        THOR_ASSERT(!ins.is_valid());
        THOR_ASSERT(ins.id == OpcodeId::UNKNOWN);
        THOR_ASSERT(ins.flow == ControlFlowType::ILLEGAL);
        THOR_ASSERT(ins.mem_access == MemoryAccessType::NONE);
    }
}

static void test_catherine_mednafen_crosscheck() {
    // V-06 Cross-check verification on the target subset:
    // Opcode 0x6611:
    //   - Catherine: MOVWL (mov.w @rm, rn), Rm=1, Rn=6, signed 16-bit read
    //   - Mednafen: MOV_W_REGINDIR_REG, Rm=1, Rn=6, WB_READ16 (sign-extended int16)
    //   - Hardware manual: MOV.W @Rm, Rn -> (Rm) -> Sign extension -> Rn
    const Sh2Instruction c1 = decode_sh2(0x6611, 0x06004000);
    THOR_ASSERT(c1.id == OpcodeId::MOV_W_READ_MEM && c1.rn == 6 && c1.rm == 1);

    // Opcode 0x6F03:
    //   - Catherine: MOV (mov rm, rn), Rm=0, Rn=15
    //   - Mednafen: MOV_REG_REG, Rm=0, Rn=15
    //   - Hardware manual: MOV Rm, Rn -> Rm -> Rn
    const Sh2Instruction c2 = decode_sh2(0x6F03, 0x06004002);
    THOR_ASSERT(c2.id == OpcodeId::MOV_REG && c2.rn == 15 && c2.rm == 0);

    // Opcode 0xD417:
    //   - Catherine: MOVLL4 (mov.l @(disp, pc), rn), disp=0x17, Rn=4
    //   - Mednafen: MOV_L_PCREL_REG, (PC & ~3) + (d << 2), Rn=4
    //   - Hardware manual: MOV.L @(disp, PC), Rn -> (disp * 4 + PC) -> Rn
    const Sh2Instruction c3 = decode_sh2(0xD417, 0x06004004);
    THOR_ASSERT(c3.id == OpcodeId::MOV_L_PC_REL && c3.rn == 4 && c3.disp == 0x17);

    // Opcode 0x6442:
    //   - Catherine: MOVLL (mov.l @rm, rn), Rm=4, Rn=4
    //   - Mednafen: MOV_L_REGINDIR_REG, Rm=4, Rn=4
    //   - Hardware manual: MOV.L @Rm, Rn -> (Rm) -> Rn
    const Sh2Instruction c4 = decode_sh2(0x6442, 0x06004006);
    THOR_ASSERT(c4.id == OpcodeId::MOV_L_READ_MEM && c4.rn == 4 && c4.rm == 4);
}

int main() {
    std::cout << "[test_sh2_decoder] Running target opcode decode tests...\n";
    test_target_opcodes_decode();
    std::cout << "[test_sh2_decoder] Running PC-relative EA tests...\n";
    test_pc_relative_ea_rules();
    std::cout << "[test_sh2_decoder] Running fail-closed unsupported opcode tests...\n";
    test_unsupported_opcodes_fail_closed();
    std::cout << "[test_sh2_decoder] Running Catherine / Mednafen cross-check tests...\n";
    test_catherine_mednafen_crosscheck();
    std::cout << "[test_sh2_decoder] PASS: All decode checks green (0 disagreements).\n";
    return 0;
}
