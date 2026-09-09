#include <iostream>
#include <sstream>
#include <iomanip>
#include "bb_06004000.hpp"
#include "thor/sh2/sh2_block.hpp"
#include "thor/sh2/sh2_memory.hpp"
#include "tests/sh2/test_framework.hpp"

using namespace thor::sh2;

struct DivergenceReport {
    bool has_divergence = false;
    std::string details;
};

static DivergenceReport compare_cpu_and_memory(
    const Sh2CpuState& expected_cpu, const Sh2FlatMemory& expected_mem,
    const Sh2CpuState& actual_cpu, const Sh2FlatMemory& actual_mem) {

    std::ostringstream ss;
    bool div = false;

    for (size_t i = 0; i < 16; ++i) {
        if (expected_cpu.r[i] != actual_cpu.r[i]) {
            div = true;
            ss << "R" << i << " mismatch: expected 0x" << std::hex << expected_cpu.r[i]
               << " actual 0x" << actual_cpu.r[i] << "; ";
        }
    }

    if (expected_cpu.pc != actual_cpu.pc) {
        div = true;
        ss << "PC mismatch: expected 0x" << std::hex << expected_cpu.pc
           << " actual 0x" << actual_cpu.pc << "; ";
    }
    if (expected_cpu.sr != actual_cpu.sr) {
        div = true;
        ss << "SR mismatch: expected 0x" << std::hex << expected_cpu.sr
           << " actual 0x" << actual_cpu.sr << "; ";
    }
    if (expected_cpu.pr != actual_cpu.pr) {
        div = true;
        ss << "PR mismatch; ";
    }
    if (expected_cpu.gbr != actual_cpu.gbr) {
        div = true;
        ss << "GBR mismatch; ";
    }
    if (expected_cpu.vbr != actual_cpu.vbr) {
        div = true;
        ss << "VBR mismatch; ";
    }
    if (expected_cpu.mach != actual_cpu.mach) {
        div = true;
        ss << "MACH mismatch; ";
    }
    if (expected_cpu.macl != actual_cpu.macl) {
        div = true;
        ss << "MACL mismatch; ";
    }

    // Compare memory log
    const auto& exp_log = expected_mem.log();
    const auto& act_log = actual_mem.log();
    if (exp_log.size() != act_log.size()) {
        div = true;
        ss << "Memory log size mismatch: expected " << exp_log.size()
           << " actual " << act_log.size() << "; ";
    } else {
        for (size_t i = 0; i < exp_log.size(); ++i) {
            if (exp_log[i] != act_log[i]) {
                div = true;
                ss << "Memory log entry " << i << " mismatch; ";
            }
        }
    }

    return DivergenceReport{.has_divergence = div, .details = ss.str()};
}

static Sh2BasicBlock get_canonical_block(ISh2Memory& mem) {
    const uint8_t bytes[] = {
        0x66, 0x11, 0x6F, 0x03, 0xD4, 0x17, 0x64, 0x42, 0xA0, 0x03, 0x00, 0x09
    };
    for (size_t i = 0; i < sizeof(bytes); ++i) {
        mem.write8(0x06004000u + static_cast<uint32_t>(i), bytes[i]);
    }
    const auto block = discover_basic_block(0x06004000u, mem);
    THOR_ASSERT(!block.instructions.empty());
    return block;
}

static void test_synthetic_vector_a() {
    Sh2FlatMemory mem_interp;
    const auto block = get_canonical_block(mem_interp);

    Sh2FlatMemory mem_gen;
    get_canonical_block(mem_gen);

    // Setup input memory at dereference addresses
    mem_interp.write16(0x06004000u, 0x1234);
    mem_gen.write16(0x06004000u, 0x1234);

    mem_interp.write32(0x06004064u, 0x06085000u);
    mem_gen.write32(0x06004064u, 0x06085000u);

    mem_interp.write32(0x06085000u, 0xDEADBEEFu);
    mem_gen.write32(0x06085000u, 0xDEADBEEFu);

    Sh2CpuState state_interp{};
    state_interp.pc = 0x06004000u;
    state_interp.r[0] = 0x06002000u;
    state_interp.r[1] = 0x06004000u;
    state_interp.r[4] = 0x11112222u;
    state_interp.r[6] = 0x00000000u;
    state_interp.r[15] = 0x06001000u;
    state_interp.sr = 0x00000001u;

    Sh2CpuState state_gen = state_interp;

    // Execute interpreter
    mem_interp.clear_log();
    const auto res = execute_basic_block(block, state_interp, mem_interp);
    THOR_ASSERT(res == ExecutionResult::SUCCESS);

    // Execute generated native code
    mem_gen.clear_log();
    thor::generated::bb_06004000(state_gen, mem_gen);

    const auto report = compare_cpu_and_memory(state_interp, mem_interp, state_gen, mem_gen);
    THOR_ASSERT(!report.has_divergence);
    THOR_ASSERT(state_gen.pc == 0x06004012u);
    THOR_ASSERT(state_gen.r[6] == 0x00001234u);
    THOR_ASSERT(state_gen.r[15] == 0x06002000u);
    THOR_ASSERT(state_gen.r[4] == 0xDEADBEEFu);
}

static void test_synthetic_vector_sign_extension() {
    Sh2FlatMemory mem_interp;
    const auto block = get_canonical_block(mem_interp);

    Sh2FlatMemory mem_gen;
    get_canonical_block(mem_gen);

    // Negative 16-bit word (0x8001 -> sign-extends to 0xFFFF8001)
    mem_interp.write16(0x06004000u, 0x8001);
    mem_gen.write16(0x06004000u, 0x8001);

    mem_interp.write32(0x06004064u, 0x06089000u);
    mem_gen.write32(0x06004064u, 0x06089000u);

    mem_interp.write32(0x06089000u, 0x80000000u);
    mem_gen.write32(0x06089000u, 0x80000000u);

    Sh2CpuState state_interp{};
    state_interp.pc = 0x06004000u;
    state_interp.r[0] = 0x06002AAAu;
    state_interp.r[1] = 0x06004000u;

    Sh2CpuState state_gen = state_interp;

    mem_interp.clear_log();
    const auto res = execute_basic_block(block, state_interp, mem_interp);
    THOR_ASSERT(res == ExecutionResult::SUCCESS);

    mem_gen.clear_log();
    thor::generated::bb_06004000(state_gen, mem_gen);

    const auto report = compare_cpu_and_memory(state_interp, mem_interp, state_gen, mem_gen);
    THOR_ASSERT(!report.has_divergence);
    THOR_ASSERT(state_gen.r[6] == 0xFFFF8001u);
    THOR_ASSERT(state_gen.r[4] == 0x80000000u);
}

static void test_real_thor2_oracle_replay() {
    Sh2FlatMemory mem_interp;
    const auto block = get_canonical_block(mem_interp);

    Sh2FlatMemory mem_gen;
    get_canonical_block(mem_gen);

    // Exact Thor 2 startup values from Mednafen cold-boot trace
    mem_interp.write16(0x06004000u, 0x6611);
    mem_gen.write16(0x06004000u, 0x6611);

    mem_interp.write32(0x06004064u, 0x06081C10u);
    mem_gen.write32(0x06004064u, 0x06081C10u);

    mem_interp.write32(0x06081C10u, 0x060917DCu);
    mem_gen.write32(0x06081C10u, 0x060917DCu);

    Sh2CpuState state_interp{};
    state_interp.pc = 0x06004000u;
    state_interp.r[0] = 0x06002EDCu;
    state_interp.r[1] = 0x06004000u;
    state_interp.r[2] = 0x00000000u;
    state_interp.r[3] = 0x00002650u;
    state_interp.r[4] = 0x00002650u;
    state_interp.r[5] = 0x060002DCu;
    state_interp.r[6] = 0x00000000u;
    state_interp.r[7] = 0x06000D00u;
    state_interp.r[15] = 0x06001000u;
    state_interp.sr = 0x00000001u;
    state_interp.vbr = 0x06000000u;

    Sh2CpuState state_gen = state_interp;

    mem_interp.clear_log();
    const auto res = execute_basic_block(block, state_interp, mem_interp);
    THOR_ASSERT(res == ExecutionResult::SUCCESS);

    mem_gen.clear_log();
    thor::generated::bb_06004000(state_gen, mem_gen);

    const auto report = compare_cpu_and_memory(state_interp, mem_interp, state_gen, mem_gen);
    THOR_ASSERT(!report.has_divergence);

    // Exact verification against Mednafen oracle post-state
    THOR_ASSERT(state_gen.r[0] == 0x06002EDCu);
    THOR_ASSERT(state_gen.r[1] == 0x06004000u);
    THOR_ASSERT(state_gen.r[4] == 0x060917DCu);
    THOR_ASSERT(state_gen.r[6] == 0x00006611u);
    THOR_ASSERT(state_gen.r[15] == 0x06002EDCu);
    THOR_ASSERT(state_gen.pc == 0x06004012u);
    THOR_ASSERT(state_gen.sr == 0x00000001u);
    THOR_ASSERT(state_gen.vbr == 0x06000000u);

    // Memory access log verification (3 ordered reads, 0 writes)
    const auto& log = mem_gen.log();
    THOR_ASSERT(log.size() == 3);
    THOR_ASSERT(log[0].kind == MemoryAccessKind::READ && log[0].address == 0x06004000u && log[0].value == 0x6611u);
    THOR_ASSERT(log[1].kind == MemoryAccessKind::READ && log[1].address == 0x06004064u && log[1].value == 0x06081C10u);
    THOR_ASSERT(log[2].kind == MemoryAccessKind::READ && log[2].address == 0x06081C10u && log[2].value == 0x060917DCu);
}

static void test_negative_control_post_state_corruption() {
    Sh2CpuState exp_state{};
    exp_state.pc = 0x06004012u;
    exp_state.r[4] = 0x060917DCu;

    Sh2CpuState corrupted_state = exp_state;
    corrupted_state.r[4] = 0xDEADBEEFu; // Corrupt R4

    Sh2FlatMemory exp_mem, act_mem;
    auto report = compare_cpu_and_memory(exp_state, exp_mem, corrupted_state, act_mem);
    THOR_ASSERT(report.has_divergence);

    // Corrupt PC
    corrupted_state = exp_state;
    corrupted_state.pc = 0x0600400Cu;
    report = compare_cpu_and_memory(exp_state, exp_mem, corrupted_state, act_mem);
    THOR_ASSERT(report.has_divergence);

    // Corrupt memory log
    corrupted_state = exp_state;
    act_mem.read8(0x1000); // Unmatched read
    report = compare_cpu_and_memory(exp_state, exp_mem, corrupted_state, act_mem);
    THOR_ASSERT(report.has_divergence);
}

int main() {
    std::cout << "Running test_v07a_transition...\n";
    test_synthetic_vector_a();
    test_synthetic_vector_sign_extension();
    test_real_thor2_oracle_replay();
    test_negative_control_post_state_corruption();
    std::cout << "All V-07A transition tests passed with 0 divergences!\n";
    return 0;
}
