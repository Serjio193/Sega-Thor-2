#include "thor/sh2/sh2_executor.hpp"
#include "test_framework.hpp"

#include <iostream>

using namespace thor::sh2;

static void test_sign_extension_mov_w() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    mem.write16(0x06001000, 0x8000);
    mem.write16(0x06001002, 0xFFFF);
    mem.write16(0x06001004, 0x1234);

    state.r[1] = 0x06001000;
    const Sh2Instruction ins1 = decode_sh2(0x6011, 0x06000000); // MOV.W @R1, R0
    THOR_ASSERT(execute_sh2_instruction(ins1, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[0] == 0xFFFF8000);

    state.r[1] = 0x06001002;
    THOR_ASSERT(execute_sh2_instruction(ins1, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[0] == 0xFFFFFFFF);

    state.r[1] = 0x06001004;
    THOR_ASSERT(execute_sh2_instruction(ins1, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[0] == 0x00001234);
}

static void test_register_copy_mov_reg() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    state.r[0] = 0x06002EDC;
    state.r[15] = 0x00000000;
    const Sh2Instruction ins = decode_sh2(0x6F03, 0x06000000); // MOV R0, R15
    THOR_ASSERT(execute_sh2_instruction(ins, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[15] == 0x06002EDC);
    THOR_ASSERT(state.r[0] == 0x06002EDC);
}

static void test_pc_relative_alignment_mov_l() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    mem.write32(0x06004064, 0x11223344);
    mem.write32(0x06004060, 0x55667788);

    state.pc = 0x06004004;
    const Sh2Instruction ins_aligned = decode_sh2(0xD417, state.pc);
    THOR_ASSERT(execute_sh2_instruction(ins_aligned, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[4] == 0x11223344);

    state.pc = 0x06004002;
    const Sh2Instruction ins_unaligned = decode_sh2(0xD417, state.pc);
    THOR_ASSERT(execute_sh2_instruction(ins_unaligned, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[4] == 0x55667788);
}

static void test_writeback_ordering_same_register() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    mem.write32(0x06081C10, 0x060917DC);
    state.r[4] = 0x06081C10;
    const Sh2Instruction ins = decode_sh2(0x6442, 0x06000000); // MOV.L @R4, R4
    THOR_ASSERT(execute_sh2_instruction(ins, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.r[4] == 0x060917DC);
}

static void test_nop_semantics() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    state.r[0] = 0x12345678;
    state.r[15] = 0x06002EDC;
    state.pc = 0x0600400A;
    state.set_t(true);
    state.pr = 0x06001111;
    state.vbr = 0x06000000;

    const Sh2Instruction ins = decode_sh2(0x0009, state.pc);
    THOR_ASSERT(execute_sh2_instruction(ins, state, mem) == ExecutionResult::SUCCESS);

    THOR_ASSERT(state.pc == 0x0600400C);
    THOR_ASSERT(state.r[0] == 0x12345678);
    THOR_ASSERT(state.r[15] == 0x06002EDC);
    THOR_ASSERT(state.get_t() == true);
    THOR_ASSERT(state.pr == 0x06001111);
    THOR_ASSERT(state.vbr == 0x06000000);
    THOR_ASSERT(mem.log().empty());
}

static void test_bra_synthetic_semantics() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    // 1. Unconditional delayed branch + delay slot NOP:
    // 0x06004008: BRA 0x06004012 (0xA003)
    // 0x0600400A: NOP           (0x0009)
    mem.write16(0x06004008, 0xA003);
    mem.write16(0x0600400A, 0x0009);

    state.pc = 0x06004008;
    state.set_t(true);
    state.clear_delayed_branch();

    // Step 1: execute BRA
    const StepResult step1 = step_sh2(state, mem);
    THOR_ASSERT(step1.status == ExecutionResult::SUCCESS);
    THOR_ASSERT(step1.pre_pc == 0x06004008);
    THOR_ASSERT(step1.post_pc == 0x0600400A);
    THOR_ASSERT(state.pc == 0x0600400A);
    THOR_ASSERT(state.delayed_pc == 0x06004012);
    THOR_ASSERT(state.get_t() == true); // SR/T unchanged

    // Step 2: execute delay slot NOP
    const StepResult step2 = step_sh2(state, mem);
    THOR_ASSERT(step2.status == ExecutionResult::SUCCESS);
    THOR_ASSERT(step2.pre_pc == 0x0600400A);
    THOR_ASSERT(step2.post_pc == 0x06004012);
    THOR_ASSERT(state.pc == 0x06004012);
    THOR_ASSERT(!state.has_delayed_branch()); // Delayed PC cleared
    THOR_ASSERT(state.get_t() == true);

    // 2. Delay slot with register write:
    // 0x06001000: BRA 0x06001006 (disp = 0x001 -> target 0x06001000 + 4 + 2 = 0x06001006)
    // 0x06001002: MOV R0, R15   (0x6F03)
    mem.write16(0x06001000, 0xA001);
    mem.write16(0x06001002, 0x6F03);

    state.pc = 0x06001000;
    state.r[0] = 0xCAFEBABE;
    state.r[15] = 0x00000000;
    state.clear_delayed_branch();

    const StepResult d_step1 = step_sh2(state, mem);
    THOR_ASSERT(d_step1.status == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.pc == 0x06001002);
    THOR_ASSERT(state.delayed_pc == 0x06001006);
    THOR_ASSERT(state.r[15] == 0x00000000);

    const StepResult d_step2 = step_sh2(state, mem);
    THOR_ASSERT(d_step2.status == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.pc == 0x06001006);
    THOR_ASSERT(!state.has_delayed_branch());
    THOR_ASSERT(state.r[15] == 0xCAFEBABE); // Register write in delay slot took effect

    // 3. Illegal slot instruction detection (branch in delay slot):
    state.pc = 0x06001000;
    state.delayed_pc = 0x06001020; // In delay slot
    const Sh2Instruction bra_in_slot = decode_sh2(0xA003, state.pc);
    THOR_ASSERT(execute_sh2_instruction(bra_in_slot, state, mem) == ExecutionResult::ILLEGAL_SLOT_INSTRUCTION);
}

static void test_jsr_synthetic_semantics() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    // 1. Normal target JSR @R3 + delay slot NOP:
    // 0x06004286: JSR @R3 (0x430B)
    // 0x06004288: NOP     (0x0009)
    mem.write16(0x06004286, 0x430B);
    mem.write16(0x06004288, 0x0009);

    state.pc = 0x06004286;
    state.pr = 0x00000000;
    state.r[3] = 0x0600A0F8;
    state.clear_delayed_branch();
    mem.clear_log();

    // Step 1: execute JSR @R3
    const StepResult step1 = step_sh2(state, mem);
    THOR_ASSERT(step1.status == ExecutionResult::SUCCESS);
    THOR_ASSERT(step1.pre_pc == 0x06004286);
    THOR_ASSERT(step1.post_pc == 0x06004288);
    THOR_ASSERT(state.pc == 0x06004288); // In delay slot
    THOR_ASSERT(state.has_delayed_branch());
    THOR_ASSERT(state.delayed_pc == 0x0600A0F8);
    THOR_ASSERT(state.pr == 0x0600428A); // PR = PC + 4

    // Step 2: execute delay slot NOP
    const StepResult step2 = step_sh2(state, mem);
    THOR_ASSERT(step2.status == ExecutionResult::SUCCESS);
    THOR_ASSERT(step2.pre_pc == 0x06004288);
    THOR_ASSERT(step2.post_pc == 0x0600A0F8);
    THOR_ASSERT(state.pc == 0x0600A0F8); // Jumped to target
    THOR_ASSERT(!state.has_delayed_branch()); // Delayed PC retired
    THOR_ASSERT(state.pr == 0x0600428A); // PR preserved

    // 2. Alternate target (proves target is dynamic, not hardcoded):
    state.pc = 0x06004286;
    state.pr = 0x00000000;
    state.r[3] = 0x0600BEEF;
    state.clear_delayed_branch();

    THOR_ASSERT(step_sh2(state, mem).status == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.delayed_pc == 0x0600BEEF);
    THOR_ASSERT(state.pr == 0x0600428A);
    THOR_ASSERT(step_sh2(state, mem).status == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.pc == 0x0600BEEF);
    THOR_ASSERT(!state.has_delayed_branch());

    // 3. Delay slot modifies target register Rn (target must evaluate before delay slot):
    // 0x06001000: JSR @R3       (0x430B)
    // 0x06001002: MOV R0, R3    (0x6303)
    mem.write16(0x06001000, 0x430B);
    mem.write16(0x06001002, 0x6303);

    state.pc = 0x06001000;
    state.pr = 0x00000000;
    state.r[0] = 0xDEADBEEF;
    state.r[3] = 0x06005000; // Pre-delay target
    state.clear_delayed_branch();

    THOR_ASSERT(step_sh2(state, mem).status == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.pc == 0x06001002);
    THOR_ASSERT(state.delayed_pc == 0x06005000);
    THOR_ASSERT(state.r[3] == 0x06005000);

    THOR_ASSERT(step_sh2(state, mem).status == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.pc == 0x06005000); // Branched to pre-delay target
    THOR_ASSERT(state.r[3] == 0xDEADBEEF); // Delay slot mutation took effect
    THOR_ASSERT(!state.has_delayed_branch());

    // 4. Target 0x00000000 (verifies std::optional sentinel correctness):
    state.pc = 0x06004286;
    state.r[3] = 0x00000000;
    state.clear_delayed_branch();

    THOR_ASSERT(step_sh2(state, mem).status == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.has_delayed_branch());
    THOR_ASSERT(state.delayed_pc == 0x00000000);
    THOR_ASSERT(step_sh2(state, mem).status == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.pc == 0x00000000);
    THOR_ASSERT(!state.has_delayed_branch());

    // 5. PR overwrite:
    state.pc = 0x06004286;
    state.pr = 0x12345678; // Stale PR
    state.r[3] = 0x0600A0F8;
    state.clear_delayed_branch();

    THOR_ASSERT(step_sh2(state, mem).status == ExecutionResult::SUCCESS);
    THOR_ASSERT(state.pr == 0x0600428A); // Overwritten by JSR

    // 6. Illegal slot instruction detection (JSR in delay slot):
    state.pc = 0x06001000;
    state.delayed_pc = 0x06002000; // In delay slot
    const Sh2Instruction jsr_in_slot = decode_sh2(0x430B, state.pc);
    THOR_ASSERT(execute_sh2_instruction(jsr_in_slot, state, mem) == ExecutionResult::ILLEGAL_SLOT_INSTRUCTION);

    // 7. All 16 registers R0..R15:
    for (uint8_t reg = 0; reg < 16; ++reg) {
        const uint16_t op = static_cast<uint16_t>(0x400Bu | (static_cast<uint16_t>(reg) << 8));
        const uint32_t pc = 0x06002000 + (reg * 8u);
        const uint32_t target = 0x06020000 + (reg * 0x100u);
        mem.write16(pc, op);
        mem.write16(pc + 2, 0x0009); // NOP delay slot

        state.pc = pc;
        state.pr = 0;
        state.r[reg] = target;
        state.clear_delayed_branch();

        THOR_ASSERT(step_sh2(state, mem).status == ExecutionResult::SUCCESS);
        THOR_ASSERT(state.pr == pc + 4);
        THOR_ASSERT(state.delayed_pc == target);

        THOR_ASSERT(step_sh2(state, mem).status == ExecutionResult::SUCCESS);
        THOR_ASSERT(state.pc == target);
        THOR_ASSERT(!state.has_delayed_branch());
    }

    // 8. Zero memory access side-effects (JSR itself has no memory bus transactions):
    mem.clear_log();
    state.pc = 0x06004286;
    state.r[3] = 0x0600A0F8;
    state.clear_delayed_branch();
    const Sh2Instruction jsr_ins = decode_sh2(0x430B, state.pc);
    THOR_ASSERT(execute_sh2_instruction(jsr_ins, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(mem.log().empty());
}

static void test_register_isolation() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    for (size_t i = 0; i < 16; ++i) state.r[i] = static_cast<uint32_t>(0x1000 + i);
    state.pc = 0x06004000;
    state.pr = 0xAAAAAAAA;
    state.sr = 0x00000001;
    state.gbr = 0xBBBBBBBB;
    state.vbr = 0xCCCCCCCC;
    state.mach = 0xDDDDDDDD;
    state.macl = 0xEEEEEEEE;

    const Sh2Instruction ins = decode_sh2(0x6213, state.pc); // MOV R1, R2
    THOR_ASSERT(execute_sh2_instruction(ins, state, mem) == ExecutionResult::SUCCESS);

    THOR_ASSERT(state.r[2] == 0x1001);
    for (size_t i = 0; i < 16; ++i) {
        if (i != 2) THOR_ASSERT(state.r[i] == static_cast<uint32_t>(0x1000 + i));
    }
    THOR_ASSERT(state.pr == 0xAAAAAAAA);
    THOR_ASSERT(state.sr == 0x00000001);
    THOR_ASSERT(state.gbr == 0xBBBBBBBB);
    THOR_ASSERT(state.vbr == 0xCCCCCCCC);
    THOR_ASSERT(state.mach == 0xDDDDDDDD);
    THOR_ASSERT(state.macl == 0xEEEEEEEE);
}

static void test_ordered_memory_effects() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    mem.write32(0x06081C10, 0x11111111);
    mem.write32(0x06081C14, 0x22222222);
    mem.clear_log();

    state.r[4] = 0x06081C10;
    state.r[5] = 0x06081C14;

    const Sh2Instruction ins1 = decode_sh2(0x6442, 0x06000000); // MOV.L @R4, R4
    const Sh2Instruction ins2 = decode_sh2(0x6552, 0x06000002); // MOV.L @R5, R5

    THOR_ASSERT(execute_sh2_instruction(ins1, state, mem) == ExecutionResult::SUCCESS);
    THOR_ASSERT(execute_sh2_instruction(ins2, state, mem) == ExecutionResult::SUCCESS);

    const auto& log = mem.log();
    THOR_ASSERT(log.size() == 2);
    THOR_ASSERT(log[0].address == 0x06081C10 && log[0].value == 0x11111111);
    THOR_ASSERT(log[1].address == 0x06081C14 && log[1].value == 0x22222222);
}

int main() {
    std::cout << "[test_sh2_l0_semantics] Running sign extension tests (MOV.W)...\n";
    test_sign_extension_mov_w();
    std::cout << "[test_sh2_l0_semantics] Running register copy tests (MOV)...\n";
    test_register_copy_mov_reg();
    std::cout << "[test_sh2_l0_semantics] Running PC-relative alignment tests (MOV.L)...\n";
    test_pc_relative_alignment_mov_l();
    std::cout << "[test_sh2_l0_semantics] Running same-register writeback order tests...\n";
    test_writeback_ordering_same_register();
    std::cout << "[test_sh2_l0_semantics] Running NOP semantics tests...\n";
    test_nop_semantics();
    std::cout << "[test_sh2_l0_semantics] Running BRA synthetic semantics & delay slot tests...\n";
    test_bra_synthetic_semantics();
    std::cout << "[test_sh2_l0_semantics] Running JSR synthetic semantics & delay slot tests...\n";
    test_jsr_synthetic_semantics();
    std::cout << "[test_sh2_l0_semantics] Running register isolation tests...\n";
    test_register_isolation();
    std::cout << "[test_sh2_l0_semantics] Running ordered memory effects tests...\n";
    test_ordered_memory_effects();
    std::cout << "[test_sh2_l0_semantics] PASS: All L0 semantic tests green (0 divergences).\n";
    return 0;
}
