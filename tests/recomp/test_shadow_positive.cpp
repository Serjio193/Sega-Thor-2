#include <iostream>
#include "bb_06004000.hpp"
#include "bb_06004280.hpp"
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

static Sh2BasicBlock get_canonical_cand_block(Sh2FlatMemory& mem) {
    const uint8_t bytes[] = {
        0xD5, 0x36, // 0x06004280: MOV.L @(0xD8, PC), R5
        0xD4, 0x37, // 0x06004282: MOV.L @(0xDC, PC), R4
        0xD3, 0x37, // 0x06004284: MOV.L @(0xDC, PC), R3
        0x43, 0x0B, // 0x06004286: JSR @R3
        0x00, 0x09  // 0x06004288: NOP
    };
    for (size_t i = 0; i < sizeof(bytes); ++i) {
        mem.write8(0x06004280u + static_cast<uint32_t>(i), bytes[i]);
    }
    const auto block = discover_basic_block(0x06004280u, mem);
    THOR_ASSERT(!block.instructions.empty());
    return block;
}

static void test_shadow_candidate_06004280_real_cold_boot(uint32_t& comparisons) {
    BlockPreState pre_state{};
    const auto block = get_canonical_cand_block(pre_state.memory);

    // Materialize isolated literal pool data dependencies
    pre_state.memory.write32(0x0600435Cu, 0x002DA000u);
    pre_state.memory.write32(0x06004360u, 0x06081C20u);
    pre_state.memory.write32(0x06004364u, 0x0600A0F8u);

    // Mednafen cold boot Hit 2 arrival register state
    pre_state.cpu_state.pc = 0x06004280u;
    pre_state.cpu_state.r[0] = 0x00000023u;
    pre_state.cpu_state.r[1] = 0x06093B14u;
    pre_state.cpu_state.r[2] = 0x00000028u;
    pre_state.cpu_state.r[3] = 0x06094F28u;
    pre_state.cpu_state.r[4] = 0x00000000u;
    pre_state.cpu_state.r[5] = 0x06094B68u;
    pre_state.cpu_state.r[6] = 0x00000BC5u;
    pre_state.cpu_state.r[7] = 0x00000008u;
    pre_state.cpu_state.r[11] = 0x06096523u;
    pre_state.cpu_state.r[12] = 0x06088708u;
    pre_state.cpu_state.r[13] = 0x00000001u;
    pre_state.cpu_state.r[14] = 0x00000002u;
    pre_state.cpu_state.r[15] = 0x06002ED8u;
    pre_state.cpu_state.sr = 0x00000001u;
    pre_state.cpu_state.pr = 0x06004280u;
    pre_state.cpu_state.vbr = 0x06000000u;

    const auto proven_desc = make_bb_06004280_descriptor();
    const auto candidate_desc = make_bb_06004280_descriptor();

    const auto result = ShadowChecker::run_and_compare(
        proven_desc, candidate_desc, block,
        thor::generated::bb_06004280, pre_state);

    THOR_ASSERT(result.is_match());
    THOR_ASSERT(result.status == ShadowStatus::MATCH);
    THOR_ASSERT(result.divergences.empty());

    // Outer check against expected post-transition state
    Sh2CpuState test_cpu = pre_state.cpu_state;
    Sh2FlatMemory test_mem = pre_state.memory;
    thor::generated::bb_06004280(test_cpu, test_mem);

    THOR_ASSERT(test_cpu.r[5] == 0x002DA000u);
    THOR_ASSERT(test_cpu.r[4] == 0x06081C20u);
    THOR_ASSERT(test_cpu.r[3] == 0x0600A0F8u);
    THOR_ASSERT(test_cpu.pr == 0x0600428Au);
    THOR_ASSERT(test_cpu.pc == 0x0600A0F8u);
    THOR_ASSERT(!test_cpu.has_delayed_branch());

    comparisons++;
}

static void test_shadow_candidate_06004280_synthetic_target_controls(uint32_t& comparisons) {
    const uint32_t test_targets[] = {
        0x0600A0F8u, // Vector A: Normal target
        0x0600BEEFu, // Vector B: Alternate target
        0x00000000u  // Vector C: Zero target
    };

    const auto proven_desc = make_bb_06004280_descriptor();
    const auto candidate_desc = make_bb_06004280_descriptor();

    for (uint32_t tgt : test_targets) {
        BlockPreState pre_state{};
        const auto block = get_canonical_cand_block(pre_state.memory);
        pre_state.memory.write32(0x0600435Cu, 0x002DA000u);
        pre_state.memory.write32(0x06004360u, 0x06081C20u);
        pre_state.memory.write32(0x06004364u, tgt);

        pre_state.cpu_state.pc = 0x06004280u;
        pre_state.cpu_state.sr = 0x00000001u;

        const auto result = ShadowChecker::run_and_compare(
            proven_desc, candidate_desc, block,
            thor::generated::bb_06004280, pre_state);

        THOR_ASSERT(result.is_match());
        THOR_ASSERT(result.status == ShadowStatus::MATCH);
        THOR_ASSERT(result.divergences.empty());

        Sh2CpuState test_cpu = pre_state.cpu_state;
        Sh2FlatMemory test_mem = pre_state.memory;
        thor::generated::bb_06004280(test_cpu, test_mem);
        THOR_ASSERT(test_cpu.pc == tgt);
        THOR_ASSERT(test_cpu.pr == 0x0600428Au);
        THOR_ASSERT(!test_cpu.has_delayed_branch());

        comparisons++;
    }
}

int main() {
    std::cout << "Running test_shadow_positive...\n";
    uint32_t comparisons = 0;
    test_shadow_synthetic_vector_a(comparisons);
    test_shadow_synthetic_vector_sign_extension(comparisons);
    test_shadow_synthetic_vector_zero_boundary(comparisons);
    test_shadow_real_thor2_cold_boot(comparisons);
    test_shadow_candidate_06004280_real_cold_boot(comparisons);
    test_shadow_candidate_06004280_synthetic_target_controls(comparisons);

    std::cout << "All " << comparisons << " positive shadow comparisons passed with 0 divergences!\n";
    return 0;
}
