#include "thor/sh2/sh2_block.hpp"
#include "test_framework.hpp"

#include <iostream>

using namespace thor::sh2;

/// Sets up the complete 6-instruction Thor 2 startup basic block at 0x06004000.
static void setup_block0_memory(Sh2FlatMemory& mem) {
    // 0x06004000: 0x6611  MOV.W @R1, R6
    mem.write16(0x06004000, 0x6611);
    // 0x06004002: 0x6F03  MOV R0, R15
    mem.write16(0x06004002, 0x6F03);
    // 0x06004004: 0xD417  MOV.L @(0x5C, PC), R4
    mem.write16(0x06004004, 0xD417);
    // 0x06004006: 0x6442  MOV.L @R4, R4
    mem.write16(0x06004006, 0x6442);
    // 0x06004008: 0xA003  BRA 0x06004012 (terminator)
    mem.write16(0x06004008, 0xA003);
    // 0x0600400A: 0x0009  NOP (delay slot)
    mem.write16(0x0600400A, 0x0009);

    // Literal pool entry at 0x06004064:
    mem.write32(0x06004064, 0x06081C10);
    // Variable at 0x06081C10 (BSS pointer):
    mem.write32(0x06081C10, 0x060917DC);

    mem.clear_log();
}

static void test_block_discovery() {
    Sh2FlatMemory mem;
    setup_block0_memory(mem);

    const Sh2BasicBlock block = discover_basic_block(0x06004000, mem);

    THOR_ASSERT(block.start_address == 0x06004000);
    THOR_ASSERT(block.end_address == 0x0600400A);
    THOR_ASSERT(block.instruction_count == 6);
    THOR_ASSERT(block.byte_length == 12);
    THOR_ASSERT(block.module_id == "0TH2.BIN");
    THOR_ASSERT(block.cpu_id == "MASTER_SH2");

    // Terminator checks
    THOR_ASSERT(block.terminator.id == OpcodeId::BRA);
    THOR_ASSERT(block.terminator.pc == 0x06004008);
    THOR_ASSERT(block.terminator.flow == ControlFlowType::BRANCH);
    THOR_ASSERT(block.terminator.has_delay_slot == true);

    // Delay slot checks
    THOR_ASSERT(block.delay_slot.has_value());
    THOR_ASSERT(block.delay_slot->id == OpcodeId::NOP);
    THOR_ASSERT(block.delay_slot->pc == 0x0600400A);

    // Exits
    THOR_ASSERT(block.direct_exits.size() == 1);
    THOR_ASSERT(block.direct_exits[0] == 0x06004012);
    THOR_ASSERT(!block.fallthrough.has_value());
    THOR_ASSERT(block.dynamic_taken_exit.has_value());
    THOR_ASSERT(*block.dynamic_taken_exit == 0x06004012);

    // Byte intervals
    THOR_ASSERT(block.contains_pc(0x06004000));
    THOR_ASSERT(block.contains_pc(0x0600400A));
    THOR_ASSERT(block.contains_pc(0x0600400B));
    THOR_ASSERT(!block.contains_pc(0x0600400C));
}

static void test_block_execution_vs_mednafen_oracle() {
    Sh2FlatMemory mem;
    setup_block0_memory(mem);

    // 1. Initial architectural register state at Thor 2 entry (V-01-core Section 3.3):
    Sh2CpuState state_block;
    state_block.r[0] = 0x06002EDC;
    state_block.r[1] = 0x06004000;
    state_block.r[2] = 0x00000000;
    state_block.r[3] = 0x00002650;
    state_block.r[4] = 0x00002650;
    state_block.r[5] = 0x060002DC;
    state_block.r[6] = 0x00000000;
    state_block.r[7] = 0x06000D00;
    for (size_t i = 8; i <= 14; ++i) state_block.r[i] = 0x00000000;
    state_block.r[15] = 0x06001000;
    state_block.pc = 0x06004000;
    state_block.pr = 0x00000000;
    state_block.sr = 0x00000001; // T = 1
    state_block.gbr = 0x00000000;
    state_block.vbr = 0x06000000;
    state_block.mach = 0x00000000;
    state_block.macl = 0x00000000;
    state_block.delayed_pc = 0;

    Sh2CpuState state_step = state_block;

    // Method A: Execute via discover_basic_block + execute_basic_block
    const Sh2BasicBlock block = discover_basic_block(0x06004000, mem);
    const ExecutionResult res = execute_basic_block(block, state_block, mem);
    THOR_ASSERT(res == ExecutionResult::SUCCESS);

    // Method B: Step instruction-by-instruction for all 6 instructions
    Sh2FlatMemory mem_step;
    setup_block0_memory(mem_step);
    for (size_t s = 0; s < 6; ++s) {
        const StepResult step = step_sh2(state_step, mem_step);
        THOR_ASSERT(step.status == ExecutionResult::SUCCESS);
    }

    // Both methods must match identically
    THOR_ASSERT(state_block == state_step);

    // Compare with Mednafen oracle post-state at Step 6 (block retirement):
    // R0 = 0x06002EDC
    // R1 = 0x06004000
    // R4 = 0x060917DC
    // R6 = 0x00006611
    // R15 = 0x06002EDC
    // PC = 0x06004012 (branch target)
    // SR = 0x00000001 (T = 1)
    // PR = 0x00000000
    // VBR = 0x06000000
    THOR_ASSERT(state_block.r[0] == 0x06002EDC);
    THOR_ASSERT(state_block.r[1] == 0x06004000);
    THOR_ASSERT(state_block.r[4] == 0x060917DC);
    THOR_ASSERT(state_block.r[6] == 0x00006611);
    THOR_ASSERT(state_block.r[15] == 0x06002EDC);
    THOR_ASSERT(state_block.pc == 0x06004012);
    THOR_ASSERT(state_block.sr == 0x00000001);
    THOR_ASSERT(state_block.get_t() == true);
    THOR_ASSERT(state_block.pr == 0x00000000);
    THOR_ASSERT(state_block.gbr == 0x00000000);
    THOR_ASSERT(state_block.vbr == 0x06000000);
    THOR_ASSERT(state_block.mach == 0x00000000);
    THOR_ASSERT(state_block.macl == 0x00000000);
    THOR_ASSERT(state_block.delayed_pc == 0);

    // Validate memory effects
    const auto& log = mem.log();
    bool found_w16 = false;
    bool found_literal = false;
    bool found_bss = false;
    for (const auto& entry : log) {
        if (entry.address == 0x06004000 && entry.size_bytes == 2 && entry.value == 0x6611) found_w16 = true;
        if (entry.address == 0x06004064 && entry.size_bytes == 4 && entry.value == 0x06081C10) found_literal = true;
        if (entry.address == 0x06081C10 && entry.size_bytes == 4 && entry.value == 0x060917DC) found_bss = true;
    }
    THOR_ASSERT(found_w16);
    THOR_ASSERT(found_literal);
    THOR_ASSERT(found_bss);
}

int main() {
    std::cout << "[test_sh2_block] Running basic block discovery tests...\n";
    test_block_discovery();
    std::cout << "[test_sh2_block] Running basic block oracle replay vs Mednafen...\n";
    test_block_execution_vs_mednafen_oracle();
    std::cout << "[test_sh2_block] PASS: First Thor 2 basic block matches oracle identically (0 divergences).\n";
    return 0;
}
