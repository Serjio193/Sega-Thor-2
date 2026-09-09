#include "thor/sh2/sh2_executor.hpp"
#include "test_framework.hpp"

#include <iostream>

using namespace thor::sh2;

static void test_mov_w_sign_extension() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    // Positive 16-bit value: 0x1234 -> 0x00001234
    mem.write16(0x00200000, 0x1234);
    state.r[1] = 0x00200000;
    state.r[6] = 0xAAAAAAAA;
    state.pc = 0x06004000;

    const Sh2Instruction ins1 = decode_sh2(0x6611, state.pc);
    const ExecutionResult res1 = execute_sh2_instruction(ins1, state, mem);
    THOR_ASSERT(res1 == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[6] == 0x00001234);
    THOR_ASSERT(state.r[1] == 0x00200000); // Source register untouched
    THOR_ASSERT(state.pc == 0x06004002);

    // Negative 16-bit value (bit 15 set): 0x8000 -> 0xFFFF8000
    mem.write16(0x00200002, 0x8000);
    state.r[1] = 0x00200002;
    state.r[6] = 0x00000000;
    state.pc = 0x06004000;

    const Sh2Instruction ins2 = decode_sh2(0x6611, state.pc);
    const ExecutionResult res2 = execute_sh2_instruction(ins2, state, mem);
    THOR_ASSERT(res2 == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[6] == 0xFFFF8000);

    // Negative 16-bit value: 0xFFFF -> 0xFFFFFFFF
    mem.write16(0x00200004, 0xFFFF);
    state.r[1] = 0x00200004;
    state.r[6] = 0x00000000;

    const Sh2Instruction ins3 = decode_sh2(0x6611, state.pc);
    const ExecutionResult res3 = execute_sh2_instruction(ins3, state, mem);
    THOR_ASSERT(res3 == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[6] == 0xFFFFFFFF);

    // Big-endian test: explicit bytes [0x12, 0x34] in memory
    mem.write8(0x00200010, 0x12);
    mem.write8(0x00200011, 0x34);
    state.r[1] = 0x00200010;
    state.r[6] = 0;

    const Sh2Instruction ins4 = decode_sh2(0x6611, state.pc);
    const ExecutionResult res4 = execute_sh2_instruction(ins4, state, mem);
    THOR_ASSERT(res4 == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[6] == 0x00001234);
}

static void test_mov_reg() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    // MOV R0, R15 with zero
    state.r[0] = 0x00000000;
    state.r[15] = 0xFFFFFFFF;
    state.pc = 0x06004002;
    const Sh2Instruction ins1 = decode_sh2(0x6F03, state.pc);
    THOR_ASSERT(execute_sh2_instruction(ins1, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[15] == 0x00000000);
    THOR_ASSERT(state.r[0] == 0x00000000);
    THOR_ASSERT(state.pc == 0x06004004);

    // MOV R0, R15 with all-ones
    state.r[0] = 0xFFFFFFFF;
    state.r[15] = 0x00000000;
    THOR_ASSERT(execute_sh2_instruction(ins1, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[15] == 0xFFFFFFFF);
    THOR_ASSERT(state.r[0] == 0xFFFFFFFF);

    // MOV R0, R15 with arbitrary target stack pointer
    state.r[0] = 0x06002EDC;
    state.r[15] = 0x06001000;
    THOR_ASSERT(execute_sh2_instruction(ins1, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[15] == 0x06002EDC);
    THOR_ASSERT(state.r[0] == 0x06002EDC);
}

static void test_mov_l_pc_rel() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    // Address 0x06004064 contains 0x06081C10
    mem.write32(0x06004064, 0x06081C10);

    // PC = 0x06004004, opcode 0xD417 -> disp = 0x17 (92 bytes -> 0x06004064)
    state.pc = 0x06004004;
    state.r[4] = 0x00000000;

    const Sh2Instruction ins = decode_sh2(0xD417, state.pc);
    THOR_ASSERT(execute_sh2_instruction(ins, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[4] == 0x06081C10);
    THOR_ASSERT(state.pc == 0x06004006);

    // Test big-endian byte order: [0x11, 0x22, 0x33, 0x44]
    mem.write8(0x06004008, 0x11);
    mem.write8(0x06004009, 0x22);
    mem.write8(0x0600400A, 0x33);
    mem.write8(0x0600400B, 0x44);
    state.pc = 0x06004004;
    const Sh2Instruction ins_disp0 = decode_sh2(0xD400, state.pc); // disp=0 -> ea = 0x06004008
    THOR_ASSERT(execute_sh2_instruction(ins_disp0, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[4] == 0x11223344);
}

static void test_mov_l_read_mem_same_register() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    // Critical edge case: Rm == Rn (0x6442: MOV.L @R4, R4)
    // Source address must be read before destination writeback!
    mem.write32(0x06081C10, 0x060917DC);
    state.r[4] = 0x06081C10;
    state.pc = 0x06004006;

    const Sh2Instruction ins = decode_sh2(0x6442, state.pc);
    THOR_ASSERT(execute_sh2_instruction(ins, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[4] == 0x060917DC);
    THOR_ASSERT(state.pc == 0x06004008);
}

static void test_unrelated_state_preservation() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    // Fill all registers with non-zero sentinel values
    for (size_t i = 0; i < 16; ++i) {
        state.r[i] = static_cast<uint32_t>(0x10000000u + i * 0x11111111u);
    }
    state.pr = 0x12345678;
    state.sr = 0x000000F1; // T = 1
    state.gbr = 0x23456789;
    state.vbr = 0x06000000;
    state.mach = 0x3456789A;
    state.macl = 0x456789AB;
    state.pc = 0x06004000;

    // Memory for MOV.W @R1, R6
    state.r[1] = 0x00200000;
    mem.write16(0x00200000, 0x5555);

    const Sh2Instruction ins = decode_sh2(0x6611, state.pc);
    THOR_ASSERT(execute_sh2_instruction(ins, state, mem) == ExecutionResult::SUCCESS);

    // Only R6 and PC should have changed:
    THOR_ASSERT(state.r[6] == 0x00005555);
    THOR_ASSERT(state.pc == 0x06004002);

    // All other registers must be preserved:
    THOR_ASSERT(state.r[0] == 0x10000000u);
    THOR_ASSERT(state.r[1] == 0x00200000u);
    for (size_t i = 2; i < 16; ++i) {
        if (i == 6) continue;
        THOR_ASSERT(state.r[i] == static_cast<uint32_t>(0x10000000u + i * 0x11111111u));
    }
    THOR_ASSERT(state.pr == 0x12345678);
    THOR_ASSERT(state.sr == 0x000000F1);
    THOR_ASSERT(state.get_t() == true);
    THOR_ASSERT(state.gbr == 0x23456789);
    THOR_ASSERT(state.vbr == 0x06000000);
    THOR_ASSERT(state.mach == 0x3456789A);
    THOR_ASSERT(state.macl == 0x456789AB);
}

static void test_ordered_memory_effects() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    mem.write16(0x00200000, 0x1234);
    mem.write32(0x00200004, 0x56789ABC);
    mem.clear_log(); // Clear setup writes

    state.r[1] = 0x00200000;
    state.r[2] = 0x00200004;
    state.pc = 0x06004000;

    // Instruction 1: MOV.W @R1, R6
    const Sh2Instruction ins1 = decode_sh2(0x6611, state.pc);
    THOR_ASSERT(execute_sh2_instruction(ins1, state, mem) == ExecutionResult::SUCCESS);

    // Instruction 2: MOV.L @R2, R3
    const Sh2Instruction ins2 = decode_sh2(0x6322, state.pc); // 0x6322: MOV.L @R2, R3
    THOR_ASSERT(execute_sh2_instruction(ins2, state, mem) == ExecutionResult::SUCCESS);

    const auto& log = mem.log();
    THOR_ASSERT(log.size() == 2);
    THOR_ASSERT(log[0].kind == MemoryAccessKind::READ);
    THOR_ASSERT(log[0].address == 0x00200000);
    THOR_ASSERT(log[0].value == 0x1234);
    THOR_ASSERT(log[0].size_bytes == 2);

    THOR_ASSERT(log[1].kind == MemoryAccessKind::READ);
    THOR_ASSERT(log[1].address == 0x00200004);
    THOR_ASSERT(log[1].value == 0x56789ABC);
    THOR_ASSERT(log[1].size_bytes == 4);
}

int main() {
    std::cout << "[test_sh2_l0_semantics] Running MOV.W sign extension tests...\n";
    test_mov_w_sign_extension();
    std::cout << "[test_sh2_l0_semantics] Running MOV Rm, Rn tests...\n";
    test_mov_reg();
    std::cout << "[test_sh2_l0_semantics] Running MOV.L PC-relative tests...\n";
    test_mov_l_pc_rel();
    std::cout << "[test_sh2_l0_semantics] Running MOV.L Rm, Rn same-register tests...\n";
    test_mov_l_read_mem_same_register();
    std::cout << "[test_sh2_l0_semantics] Running unrelated state preservation tests...\n";
    test_unrelated_state_preservation();
    std::cout << "[test_sh2_l0_semantics] Running ordered memory effects tests...\n";
    test_ordered_memory_effects();
    std::cout << "[test_sh2_l0_semantics] PASS: All L0 semantic tests green.\n";
    return 0;
}
