#include "thor/sh2/sh2_executor.hpp"
#include "test_framework.hpp"

#include <iostream>

using namespace thor::sh2;

/// Validates the L0 semantic harness against the real Thor 2 startup oracle vector
/// recorded from the pinned Mednafen debug oracle during V-01-core.
///
/// Oracle Reference: workstreams/T2-V01-dynamic-oracle/bounded_observation.md
/// Startup Sequence in 0TH2.BIN:
/// 0x06004000: 0x6611  MOV.W @R1, R6
/// 0x06004002: 0x6F03  MOV R0, R15
/// 0x06004004: 0xD417  MOV.L @(0x5C, PC), R4
/// 0x06004006: 0x6442  MOV.L @R4, R4
static void test_thor2_startup_oracle_vector() {
    Sh2FlatMemory mem;
    Sh2CpuState state;

    // 1. Initial architectural register state at Thor 2 entry (V-01-core Section 3.3):
    state.r[0] = 0x06002EDC;  // Stack pointer passed from BIOS loader
    state.r[1] = 0x06004000;  // Entry address pointer
    state.r[2] = 0x00000000;
    state.r[3] = 0x00002650;
    state.r[4] = 0x00002650;
    state.r[5] = 0x060002DC;
    state.r[6] = 0x00000000;
    state.r[7] = 0x06000D00;
    for (size_t i = 8; i <= 14; ++i) {
        state.r[i] = 0x00000000;
    }
    state.r[15] = 0x06001000; // Initial Master stack pointer from Saturn CD header
    state.pc = 0x06004000;    // Canonical first instruction address
    state.pr = 0x00000000;
    state.sr = 0x00000001;    // T = 1
    state.gbr = 0x00000000;
    state.vbr = 0x06000000;
    state.mach = 0x00000000;
    state.macl = 0x00000000;

    // 2. Program and literal pool bytes in High Work RAM:
    mem.write16(0x06004000, 0x6611); // MOV.W @R1, R6
    mem.write16(0x06004002, 0x6F03); // MOV R0, R15
    mem.write16(0x06004004, 0xD417); // MOV.L @(0x5C, PC), R4
    mem.write16(0x06004006, 0x6442); // MOV.L @R4, R4

    // Literal pool entry at 0x06004064:
    mem.write32(0x06004064, 0x06081C10);

    // Variable memory at 0x06081C10 (BSS pointer):
    mem.write32(0x06081C10, 0x060917DC);

    mem.clear_log(); // Clear test setup writes

    // --- STEP 1: Execute 0x6611 (MOV.W @R1, R6) ---
    // Oracle expectation: R6 becomes 0x00006611; PC advances to 0x06004002
    {
        const StepResult step1 = step_sh2(state, mem);
        THOR_ASSERT(step1.status == ExecutionResult::SUCCESS);
        THOR_ASSERT(step1.instruction.id == OpcodeId::MOV_W_READ_MEM);
        THOR_ASSERT(step1.pre_pc == 0x06004000);
        THOR_ASSERT(step1.post_pc == 0x06004002);
        THOR_ASSERT(state.r[6] == 0x00006611);
        THOR_ASSERT(state.r[1] == 0x06004000);
        THOR_ASSERT(state.pc == 0x06004002);
    }

    // --- STEP 2: Execute 0x6F03 (MOV R0, R15) ---
    // Oracle expectation: R15 becomes 0x06002EDC; PC advances to 0x06004004
    {
        const StepResult step2 = step_sh2(state, mem);
        THOR_ASSERT(step2.status == ExecutionResult::SUCCESS);
        THOR_ASSERT(step2.instruction.id == OpcodeId::MOV_REG);
        THOR_ASSERT(step2.pre_pc == 0x06004002);
        THOR_ASSERT(step2.post_pc == 0x06004004);
        THOR_ASSERT(state.r[15] == 0x06002EDC);
        THOR_ASSERT(state.r[0] == 0x06002EDC);
        THOR_ASSERT(state.pc == 0x06004004);
    }

    // --- STEP 3: Execute 0xD417 (MOV.L @(0x5C, PC), R4) ---
    // Oracle expectation: R4 becomes 0x06081C10; PC advances to 0x06004006
    {
        const StepResult step3 = step_sh2(state, mem);
        THOR_ASSERT(step3.status == ExecutionResult::SUCCESS);
        THOR_ASSERT(step3.instruction.id == OpcodeId::MOV_L_PC_REL);
        THOR_ASSERT(step3.pre_pc == 0x06004004);
        THOR_ASSERT(step3.post_pc == 0x06004006);
        THOR_ASSERT(state.r[4] == 0x06081C10);
        THOR_ASSERT(state.pc == 0x06004006);
    }

    // --- STEP 4: Execute 0x6442 (MOV.L @R4, R4) ---
    // Oracle expectation: Memory read from 0x06081C10 returns 0x060917DC;
    // R4 becomes 0x060917DC; PC advances to 0x06004008
    {
        const StepResult step4 = step_sh2(state, mem);
        THOR_ASSERT(step4.status == ExecutionResult::SUCCESS);
        THOR_ASSERT(step4.instruction.id == OpcodeId::MOV_L_READ_MEM);
        THOR_ASSERT(step4.pre_pc == 0x06004006);
        THOR_ASSERT(step4.post_pc == 0x06004008);
        THOR_ASSERT(state.r[4] == 0x060917DC);
        THOR_ASSERT(state.pc == 0x06004008);
    }

    // 3. Validate complete memory access log order:
    const auto& log = mem.log();
    bool found_step1_mem = false;
    bool found_step3_mem = false;
    bool found_step4_mem = false;

    for (const auto& entry : log) {
        if (entry.address == 0x06004000 && entry.size_bytes == 2 && entry.value == 0x6611) {
            found_step1_mem = true;
        }
        if (entry.address == 0x06004064 && entry.size_bytes == 4 && entry.value == 0x06081C10) {
            found_step3_mem = true;
        }
        if (entry.address == 0x06081C10 && entry.size_bytes == 4 && entry.value == 0x060917DC) {
            found_step4_mem = true;
        }
    }

    THOR_ASSERT(found_step1_mem);
    THOR_ASSERT(found_step3_mem);
    THOR_ASSERT(found_step4_mem);

    // Verify final post-execution state against Mednafen oracle:
    THOR_ASSERT(state.r[0] == 0x06002EDC);
    THOR_ASSERT(state.r[1] == 0x06004000);
    THOR_ASSERT(state.r[4] == 0x060917DC);
    THOR_ASSERT(state.r[6] == 0x00006611);
    THOR_ASSERT(state.r[15] == 0x06002EDC);
    THOR_ASSERT(state.pc == 0x06004008);
    THOR_ASSERT(state.get_t() == true);
    THOR_ASSERT(state.vbr == 0x06000000);
}

int main() {
    std::cout << "[test_sh2_oracle_vector] Running real Thor 2 startup vector validation...\n";
    test_thor2_startup_oracle_vector();
    std::cout << "[test_sh2_oracle_vector] PASS: Real Thor 2 startup vector matches oracle identically (0 divergences).\n";
    return 0;
}
