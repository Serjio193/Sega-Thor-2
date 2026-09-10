#include "thor/sh2/sh2_executor.hpp"
#include "test_framework.hpp"

#include <iostream>

using namespace thor::sh2;

static void test_extended_alu_and_imm() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    // MOV_IMM: 0xE1FE -> mov #-2, r1
    const auto ins_mov_imm = decode_sh2(0xE1FE, 0x06001000);
    THOR_ASSERT(execute_sh2_instruction(ins_mov_imm, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[1] == 0xFFFFFFFE);

    // ADD_IMM: 0x7105 -> add #5, r1
    const auto ins_add_imm = decode_sh2(0x7105, 0x06001002);
    THOR_ASSERT(execute_sh2_instruction(ins_add_imm, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[1] == 3);

    // ADD_REG: 0x312C -> add r2, r1
    state.r[2] = 10;
    const auto ins_add_reg = decode_sh2(0x312C, 0x06001004);
    THOR_ASSERT(execute_sh2_instruction(ins_add_reg, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[1] == 13);

    // SUB_REG: 0x3128 -> sub r2, r1
    const auto ins_sub_reg = decode_sh2(0x3128, 0x06001006);
    THOR_ASSERT(execute_sh2_instruction(ins_sub_reg, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[1] == 3);
}

static void test_extended_shifts_and_flags() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    // SETT / CLRT
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x0018, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.get_t() == true);
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x0008, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.get_t() == false);

    // SHLL: r1 = 0x80000001 -> r1 = 0x00000002, T = 1
    state.r[1] = 0x80000001;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x4100, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[1] == 0x00000002);
    THOR_ASSERT(state.get_t() == true);

    // SHLR: r1 = 0x00000003 -> r1 = 0x00000001, T = 1
    state.r[1] = 0x00000003;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x4101, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[1] == 0x00000001);
    THOR_ASSERT(state.get_t() == true);

    // SHLL2: r1 = 4 -> r1 = 16
    state.r[1] = 4;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x4108, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[1] == 16);

    // SHLR2: r1 = 16 -> r1 = 4
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x4109, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[1] == 4);

    // CLRMAC: mach = 0x1234, macl = 0x5678 -> 0
    state.mach = 0x1234;
    state.macl = 0x5678;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x0028, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.mach == 0 && state.macl == 0);
}

static void test_extended_comparisons_and_branches() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    // TST_REG: r1 & r2
    state.r[1] = 0x0F;
    state.r[2] = 0xF0;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x2128, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.get_t() == true); // result is 0 -> T = 1

    state.r[2] = 0xFF;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x2128, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.get_t() == false); // result != 0 -> T = 0

    // CMP_EQ_IMM: r0 == imm
    state.r[0] = 42;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x882A, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.get_t() == true);

    // CMP_EQ_REG: r1 == r2
    state.r[1] = 100;
    state.r[2] = 100;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x3120, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.get_t() == true);

    // BT / BF
    state.pc = 0x06001000;
    state.set_t(true);
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x8904, 0x06001000), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.pc == 0x0600100C);

    state.pc = 0x06001000;
    state.set_t(false);
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x8B04, 0x06001000), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.pc == 0x0600100C);
}

static void test_extended_memory_and_stack() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    // STS.L PR, @-R15
    state.r[15] = 0x06002000;
    state.pr = 0x06009999;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x4F22, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[15] == 0x06001FFC);
    THOR_ASSERT(mem.read32(0x06001FFC) == 0x06009999);

    // LDS.L @R15+, PR
    state.pr = 0;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x4F26, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[15] == 0x06002000);
    THOR_ASSERT(state.pr == 0x06009999);

    // MOV.L READ POSTINC: 0x6126 -> mov.l @r2+, r1
    state.r[2] = 0x06001000;
    mem.write32(0x06001000, 0xAABBCCDD);
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x6126, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[1] == 0xAABBCCDD);
    THOR_ASSERT(state.r[2] == 0x06001004);

    // MOV_B READ / WRITE
    state.r[1] = 0x06001000;
    state.r[2] = 0x7E;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x2120, 0), state, mem) == ExecutionResult::SUCCESS); // mov.b r2, @r1
    THOR_ASSERT(mem.read8(0x06001000) == 0x7E);

    state.r[3] = 0;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x6310, 0), state, mem) == ExecutionResult::SUCCESS); // mov.b @r1, r3
    THOR_ASSERT(state.r[3] == 0x7E);
}

static void test_extended_batch2_semantics() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    // SHAR
    state.r[1] = 0x80000003; // negative, odd
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x4121, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[1] == 0xC0000001); // sign maintained
    THOR_ASSERT(state.get_t() == true); // LSB was 1

    // EXTU.B, EXTU.W, EXTS.B, EXTS.W
    state.r[2] = 0x123480FF;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x612C, 0), state, mem) == ExecutionResult::SUCCESS); // extu.b r2, r1
    THOR_ASSERT(state.r[1] == 0x000000FF);

    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x612D, 0), state, mem) == ExecutionResult::SUCCESS); // extu.w r2, r1
    THOR_ASSERT(state.r[1] == 0x000080FF);

    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x612E, 0), state, mem) == ExecutionResult::SUCCESS); // exts.b r2, r1
    THOR_ASSERT(state.r[1] == 0xFFFFFFFF);

    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x612F, 0), state, mem) == ExecutionResult::SUCCESS); // exts.w r2, r1
    THOR_ASSERT(state.r[1] == 0xFFFF80FF);

    // CMP/PZ, CMP/PL
    state.r[1] = 0;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x4111, 0), state, mem) == ExecutionResult::SUCCESS); // cmp/pz r1 (0 >= 0)
    THOR_ASSERT(state.get_t() == true);
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x4115, 0), state, mem) == ExecutionResult::SUCCESS); // cmp/pl r1 (0 > 0)
    THOR_ASSERT(state.get_t() == false);

    // MOV.W @Rm+, Rn
    state.r[2] = 0x06001000;
    mem.write16(0x06001000, 0x8001);
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x6125, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[1] == 0xFFFF8001); // sign-extended
    THOR_ASSERT(state.r[2] == 0x06001002);

    // AND, OR
    state.r[1] = 0x0F0F;
    state.r[2] = 0xFF00;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x2129, 0), state, mem) == ExecutionResult::SUCCESS); // and r2, r1
    THOR_ASSERT(state.r[1] == 0x0F00);
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x212B, 0), state, mem) == ExecutionResult::SUCCESS); // or r2, r1
    THOR_ASSERT(state.r[1] == 0xFF00);

    // CMP/HS, CMP/GE, CMP/HI, CMP/GT
    state.r[1] = 0xFFFFFFFF; // unsigned high, signed -1
    state.r[2] = 1;          // unsigned 1, signed +1
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x3122, 0), state, mem) == ExecutionResult::SUCCESS); // cmp/hs r2, r1 (unsigned r1 >= r2)
    THOR_ASSERT(state.get_t() == true);
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x3123, 0), state, mem) == ExecutionResult::SUCCESS); // cmp/ge r2, r1 (signed r1 >= r2)
    THOR_ASSERT(state.get_t() == false);

    // BT_S / BF_S
    state.pc = 0x06001000;
    state.set_t(true);
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x8D04, 0x06001000), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.pc == 0x0600100C);

    state.pc = 0x06001000;
    state.set_t(false);
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x8F04, 0x06001000), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.pc == 0x0600100C);
}

void test_extended_batch3_semantics() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    // ROTCL
    state.r[1] = 0x80000000u;
    state.set_t(true);
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x4124, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[1] == 1u);
    THOR_ASSERT(state.get_t() == true); // MSB was 1

    // DT
    state.r[1] = 1;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x4110, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[1] == 0);
    THOR_ASSERT(state.get_t() == true);

    // MOVT
    state.set_t(true);
    state.r[1] = 0x1234;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x0129, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[1] == 1);

    // AND #imm, R0
    state.r[0] = 0x123F;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0xC90F, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[0] == 0x0F);

    // TST #imm, R0
    state.r[0] = 0x02;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0xC801, 0), state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.get_t() == true); // 0x02 & 0x01 == 0

    // Indexed moves: @(R0, Rm) / @(R0, Rn)
    mem.write32(0x06002004, 0xAABBCCDD);
    state.r[0] = 4;
    state.r[1] = 0x06002000;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x021E, 0), state, mem) == ExecutionResult::SUCCESS); // mov.l @(r0, r1), r2
    THOR_ASSERT(state.r[2] == 0xAABBCCDD);

    // Shifts: SHLL8, SHLL16, SHLR8, SHLR16
    state.r[1] = 0x12;
    THOR_ASSERT(execute_sh2_instruction(decode_sh2(0x4118, 0), state, mem) == ExecutionResult::SUCCESS); // shll8 r1
    THOR_ASSERT(state.r[1] == 0x1200);
}

int main() {
    std::cout << "[test_sh2_l0_extended] Testing extended SH-2 L0 execution semantics...\n";
    test_extended_alu_and_imm();
    test_extended_shifts_and_flags();
    test_extended_comparisons_and_branches();
    test_extended_memory_and_stack();
    test_extended_batch2_semantics();
    test_extended_batch3_semantics();
    std::cout << "[test_sh2_l0_extended] PASS: All extended L0 checks green.\n";
    return 0;
}
