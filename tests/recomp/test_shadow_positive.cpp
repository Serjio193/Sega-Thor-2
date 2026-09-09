#include <iostream>
#include "bb_06004000.hpp"
#include "thor/recomp/shadow_checker.hpp"
#include "thor/sh2/sh2_block.hpp"
#include "tests/sh2/test_framework.hpp"

using namespace thor::recomp;
using namespace thor::sh2;

static void setup_canonical_block_bytes(Sh2FlatMemory& mem) {
    const uint8_t bytes[] = {
        0x66, 0x11, // 0x06004000: MOV.W @R1, R6
        0x6F, 0x03, // 0x06004002: MOV R0, R15
        0xD4, 0x17, // 0x06004004: MOV.L @(0x5C, PC), R4
        0x64, 0x42, // 0x06004006: MOV.L @R4, R4
        0xA0, 0x03, // 0x06004008: BRA 0x06004012
        0x00, 0x09  // 0x0600400A: NOP
    };
    for (size_t i = 0; i < sizeof(bytes); ++i) {
        mem.write8(0x06004000u + static_cast<uint32_t>(i), bytes[i]);
    }
}

static Sh2BasicBlock get_canonical_block(Sh2FlatMemory& mem) {
    setup_canonical_block_bytes(mem);
    const auto block = discover_basic_block(0x06004000u, mem);
    THOR_ASSERT(!block.instructions.empty());
    return block;
}

static void test_shadow_synthetic_vector_a(uint32_t& comparisons) {
    BlockPreState pre_state{};
    setup_canonical_block_bytes(pre_state.memory);

    // Arbitrary distinct non-zero registers and memory pointers
    pre_state.memory.write16(0x06004000u, 0x1234);
    pre_state.memory.write32(0x06004064u, 0x06085000u);
    pre_state.memory.write32(0x06085000u, 0xDEADBEEFu);

    pre_state.cpu_state.pc = 0x06004000u;
    pre_state.cpu_state.r[0] = 0x06002000u;
    pre_state.cpu_state.r[1] = 0x06004000u;
    pre_state.cpu_state.r[4] = 0x11112222u;
    pre_state.cpu_state.r[15] = 0x06001000u;
    pre_state.cpu_state.sr = 0x00000001u;

    const auto proven_desc = make_bb_06004000_descriptor();
    const auto candidate_desc = make_bb_06004000_descriptor();
    const auto block = get_canonical_block(pre_state.memory);

    const auto result = ShadowChecker::run_and_compare(
        proven_desc, candidate_desc, block,
        thor::generated::bb_06004000, pre_state);

    THOR_ASSERT(result.is_match());
    THOR_ASSERT(result.status == ShadowStatus::MATCH);
    THOR_ASSERT(result.divergences.empty());
    comparisons++;
}

static void test_shadow_synthetic_vector_sign_extension(uint32_t& comparisons) {
    BlockPreState pre_state{};
    setup_canonical_block_bytes(pre_state.memory);

    // Negative 16-bit word (0x8001 -> sign-extends to 0xFFFF8001)
    pre_state.memory.write16(0x06004000u, 0x8001);
    pre_state.memory.write32(0x06004064u, 0x06089000u);
    pre_state.memory.write32(0x06089000u, 0x80000000u);

    pre_state.cpu_state.pc = 0x06004000u;
    pre_state.cpu_state.r[0] = 0x06002AAAu;
    pre_state.cpu_state.r[1] = 0x06004000u;

    const auto proven_desc = make_bb_06004000_descriptor();
    const auto candidate_desc = make_bb_06004000_descriptor();
    const auto block = get_canonical_block(pre_state.memory);

    const auto result = ShadowChecker::run_and_compare(
        proven_desc, candidate_desc, block,
        thor::generated::bb_06004000, pre_state);

    THOR_ASSERT(result.is_match());
    THOR_ASSERT(result.divergences.empty());
    comparisons++;
}

static void test_shadow_synthetic_vector_zero_boundary(uint32_t& comparisons) {
    BlockPreState pre_state{};
    setup_canonical_block_bytes(pre_state.memory);

    pre_state.memory.write16(0x06004000u, 0x0000);
    pre_state.memory.write32(0x06004064u, 0x06080000u);
    pre_state.memory.write32(0x06080000u, 0x00000000u);

    pre_state.cpu_state.pc = 0x06004000u;
    pre_state.cpu_state.r[0] = 0x00000000u;
    pre_state.cpu_state.r[1] = 0x06004000u;

    const auto proven_desc = make_bb_06004000_descriptor();
    const auto candidate_desc = make_bb_06004000_descriptor();
    const auto block = get_canonical_block(pre_state.memory);

    const auto result = ShadowChecker::run_and_compare(
        proven_desc, candidate_desc, block,
        thor::generated::bb_06004000, pre_state);

    THOR_ASSERT(result.is_match());
    comparisons++;
}

static void test_shadow_real_thor2_cold_boot(uint32_t& comparisons) {
    BlockPreState pre_state{};
    setup_canonical_block_bytes(pre_state.memory);

    // Exact Thor 2 startup inputs from Mednafen cold-boot trace
    pre_state.memory.write16(0x06004000u, 0x6611);
    pre_state.memory.write32(0x06004064u, 0x06081C10u);
    pre_state.memory.write32(0x06081C10u, 0x060917DCu);

    pre_state.cpu_state.pc = 0x06004000u;
    pre_state.cpu_state.r[0] = 0x06002EDCu;
    pre_state.cpu_state.r[1] = 0x06004000u;
    pre_state.cpu_state.r[2] = 0x00000000u;
    pre_state.cpu_state.r[3] = 0x00002650u;
    pre_state.cpu_state.r[4] = 0x00002650u;
    pre_state.cpu_state.r[5] = 0x060002DCu;
    pre_state.cpu_state.r[6] = 0x00000000u;
    pre_state.cpu_state.r[7] = 0x06000D00u;
    pre_state.cpu_state.r[15] = 0x06001000u;
    pre_state.cpu_state.sr = 0x00000001u;
    pre_state.cpu_state.vbr = 0x06000000u;

    const auto proven_desc = make_bb_06004000_descriptor();
    const auto candidate_desc = make_bb_06004000_descriptor();
    const auto block = get_canonical_block(pre_state.memory);

    const auto result = ShadowChecker::run_and_compare(
        proven_desc, candidate_desc, block,
        thor::generated::bb_06004000, pre_state);

    THOR_ASSERT(result.is_match());
    THOR_ASSERT(result.status == ShadowStatus::MATCH);
    THOR_ASSERT(result.divergences.empty());

    // Outer check against accepted Mednafen oracle post-state constants
    Sh2CpuState test_cpu = pre_state.cpu_state;
    Sh2FlatMemory test_mem = pre_state.memory;
    thor::generated::bb_06004000(test_cpu, test_mem);

    THOR_ASSERT(test_cpu.r[0] == 0x06002EDCu);
    THOR_ASSERT(test_cpu.r[1] == 0x06004000u);
    THOR_ASSERT(test_cpu.r[4] == 0x060917DCu);
    THOR_ASSERT(test_cpu.r[6] == 0x00006611u);
    THOR_ASSERT(test_cpu.r[15] == 0x06002EDCu);
    THOR_ASSERT(test_cpu.pc == 0x06004012u);
    THOR_ASSERT(test_cpu.sr == 0x00000001u);
    THOR_ASSERT(test_cpu.vbr == 0x06000000u);

    comparisons++;
}

int main() {
    std::cout << "Running test_shadow_positive...\n";
    uint32_t comparisons = 0;
    test_shadow_synthetic_vector_a(comparisons);
    test_shadow_synthetic_vector_sign_extension(comparisons);
    test_shadow_synthetic_vector_zero_boundary(comparisons);
    test_shadow_real_thor2_cold_boot(comparisons);

    std::cout << "All " << comparisons << " positive shadow comparisons passed with 0 divergences!\n";
    return 0;
}
