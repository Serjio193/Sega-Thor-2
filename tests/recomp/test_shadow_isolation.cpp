#include <iostream>
#include "bb_06004000.hpp"
#include "thor/recomp/shadow_checker.hpp"
#include "thor/sh2/sh2_block.hpp"
#include "tests/sh2/test_framework.hpp"

using namespace thor::recomp;
using namespace thor::sh2;

static void setup_test_block(Sh2FlatMemory& mem) {
    const uint8_t bytes[] = {
        0x66, 0x11, 0x6F, 0x03, 0xD4, 0x17, 0x64, 0x42, 0xA0, 0x03, 0x00, 0x09
    };
    for (size_t i = 0; i < sizeof(bytes); ++i) {
        mem.write8(0x06004000u + static_cast<uint32_t>(i), bytes[i]);
    }
}

static void test_candidate_cannot_mutate_oracle_or_prestate() {
    BlockPreState pre_state{};
    setup_test_block(pre_state.memory);
    pre_state.memory.write32(0x06085000u, 0x11223344u);
    pre_state.memory.clear_log();

    pre_state.cpu_state.pc = 0x06004000u;
    pre_state.cpu_state.r[0] = 0xAAAA0000u;
    pre_state.cpu_state.r[4] = 0x06085000u;

    const auto proven_desc = make_bb_06004000_descriptor();
    const auto block = discover_basic_block(0x06004000u, pre_state.memory);
    pre_state.memory.clear_log();

    // Intentionally mutating candidate function: writes aggressively to memory and CPU
    auto aggressive_candidate = [](Sh2CpuState& state, ISh2Memory& mem) {
        state.r[0] = 0xDEADBEEFu;
        state.r[1] = 0xBADF00D0u;
        state.pc = 0x06004012u;
        mem.write32(0x06085000u, 0x99999999u);
        mem.write32(0x06090000u, 0x88888888u);
    };

    // Before run, capture pre_state values
    const uint32_t orig_r0 = pre_state.cpu_state.r[0];
    const uint32_t orig_val = pre_state.memory.peek8(0x06085000u);

    const auto res = ShadowChecker::run_and_compare(
        proven_desc, proven_desc, block, aggressive_candidate, pre_state);

    // Assert that the aggressive mutations caused divergence
    THOR_ASSERT(!res.is_match());
    THOR_ASSERT(res.status == ShadowStatus::DIVERGENCE);

    // Prove pre_state remains completely immutable
    THOR_ASSERT(pre_state.cpu_state.r[0] == orig_r0);
    THOR_ASSERT(pre_state.memory.peek8(0x06085000u) == orig_val);
    THOR_ASSERT(pre_state.memory.peek8(0x06090000u) == 0); // never modified
    THOR_ASSERT(pre_state.memory.log().empty());           // log never contaminated
}

static void test_oracle_cannot_mutate_candidate_prestate() {
    BlockPreState pre_state{};
    setup_test_block(pre_state.memory);
    pre_state.memory.write16(0x06004000u, 0x6611);
    pre_state.memory.write32(0x06004064u, 0x06081C10u);
    pre_state.memory.write32(0x06081C10u, 0x060917DCu);
    pre_state.memory.clear_log();

    pre_state.cpu_state.pc = 0x06004000u;
    pre_state.cpu_state.r[0] = 0x06002EDCu;
    pre_state.cpu_state.r[1] = 0x06004000u;

    const auto proven_desc = make_bb_06004000_descriptor();
    const auto block = discover_basic_block(0x06004000u, pre_state.memory);
    pre_state.memory.clear_log();

    // Candidate verifies its input pre-state matches the original pre_state
    bool candidate_saw_clean_prestate = false;
    auto verifying_candidate = [&](Sh2CpuState& state, ISh2Memory& mem) {
        if (state.r[0] == 0x06002EDCu &&
            state.r[1] == 0x06004000u &&
            mem.peek8(0x06004000u) == 0x66) {
            candidate_saw_clean_prestate = true;
        }
        thor::generated::bb_06004000(state, mem);
    };

    const auto res = ShadowChecker::run_and_compare(
        proven_desc, proven_desc, block, verifying_candidate, pre_state);

    THOR_ASSERT(candidate_saw_clean_prestate);
    THOR_ASSERT(res.is_match());
}

static void test_aliased_context_negative_fixture() {
    // Deliberately construct an aliasing situation where candidate shares memory
    Sh2FlatMemory shared_mem;
    setup_test_block(shared_mem);

    Sh2CpuState shared_cpu{};
    shared_cpu.pc = 0x06004000u;

    // Direct outcome comparison with aliased memory references
    BoundedEventMetadata meta{};
    const auto res = ShadowChecker::compare_outcomes(
        shared_cpu, shared_mem.log(), meta,
        shared_cpu, shared_mem.log(), meta);

    // Baseline match
    THOR_ASSERT(res.is_match());

    // When run_and_compare enforces isolation:
    // Verify that run_and_compare creates distinct objects by checking their addresses
    BlockPreState pre_state{};
    setup_test_block(pre_state.memory);
    pre_state.memory.write16(0x06004000u, 0x6611);
    pre_state.memory.write32(0x06004064u, 0x06081C10u);
    pre_state.memory.write32(0x06081C10u, 0x060917DCu);
    pre_state.cpu_state.pc = 0x06004000u;
    pre_state.cpu_state.r[0] = 0x06002EDCu;
    pre_state.cpu_state.r[1] = 0x06004000u;

    const auto proven_desc = make_bb_06004000_descriptor();
    const auto block = discover_basic_block(0x06004000u, pre_state.memory);
    pre_state.memory.clear_log();

    const void* candidate_mem_addr = nullptr;
    const void* candidate_cpu_addr = nullptr;

    auto inspect_candidate = [&](Sh2CpuState& state, ISh2Memory& mem) {
        candidate_cpu_addr = &state;
        candidate_mem_addr = &mem;
        thor::generated::bb_06004000(state, mem);
    };

    const auto run_res = ShadowChecker::run_and_compare(proven_desc, proven_desc, block, inspect_candidate, pre_state);
    THOR_ASSERT(run_res.is_match());

    // Assert that candidate memory and CPU addresses are completely distinct from pre_state
    THOR_ASSERT(candidate_mem_addr != nullptr);
    THOR_ASSERT(candidate_cpu_addr != nullptr);
    THOR_ASSERT(candidate_mem_addr != &pre_state.memory);
    THOR_ASSERT(candidate_cpu_addr != &pre_state.cpu_state);
}

int main() {
    std::cout << "Running test_shadow_isolation...\n";
    test_candidate_cannot_mutate_oracle_or_prestate();
    test_oracle_cannot_mutate_candidate_prestate();
    test_aliased_context_negative_fixture();
    std::cout << "All pre-state isolation and anti-aliasing tests passed!\n";
    return 0;
}
