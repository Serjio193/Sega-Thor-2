#include <iostream>
#include "thor/recomp/block_identity.hpp"
#include "tests/sh2/test_framework.hpp"

using namespace thor::recomp;
using namespace thor::sh2;

static void setup_valid_memory(Sh2FlatMemory& mem) {
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
    mem.clear_log();
}

static void test_positive_eligibility() {
    Sh2FlatMemory mem;
    setup_valid_memory(mem);

    const auto proven = make_bb_06004000_descriptor();
    const auto query = make_bb_06004000_descriptor();

    const auto result = check_block_eligibility(proven, query, mem);
    THOR_ASSERT(result == EligibilityResult::ELIGIBLE);
    // Non-architectural observation: peek8 must not produce guest memory log entries
    THOR_ASSERT(mem.log().empty());
}

static void test_negative_wrong_revision() {
    Sh2FlatMemory mem;
    setup_valid_memory(mem);

    const auto proven = make_bb_06004000_descriptor();
    auto query = make_bb_06004000_descriptor();
    query.revision_id = "thor2_pal_unverified";

    const auto result = check_block_eligibility(proven, query, mem);
    THOR_ASSERT(result == EligibilityResult::REVISION_MISMATCH);
    THOR_ASSERT(mem.log().empty());
}

static void test_negative_wrong_module() {
    Sh2FlatMemory mem;
    setup_valid_memory(mem);

    const auto proven = make_bb_06004000_descriptor();
    auto query = make_bb_06004000_descriptor();
    query.module_name = "TH2.LOW";

    const auto result = check_block_eligibility(proven, query, mem);
    THOR_ASSERT(result == EligibilityResult::MODULE_MISMATCH);
}

static void test_negative_unproven_provenance() {
    Sh2FlatMemory mem;
    setup_valid_memory(mem);

    const auto proven = make_bb_06004000_descriptor();
    auto query = make_bb_06004000_descriptor();
    query.module_provenance_proven = false;

    const auto result = check_block_eligibility(proven, query, mem);
    THOR_ASSERT(result == EligibilityResult::PROVENANCE_NOT_PROVEN);
}

static void test_negative_wrong_cpu() {
    Sh2FlatMemory mem;
    setup_valid_memory(mem);

    const auto proven = make_bb_06004000_descriptor();
    auto query = make_bb_06004000_descriptor();
    query.cpu = CpuTarget::SLAVE_SH2;

    const auto result = check_block_eligibility(proven, query, mem);
    THOR_ASSERT(result == EligibilityResult::CPU_MISMATCH);
}

static void test_negative_wrong_address_range() {
    Sh2FlatMemory mem;
    setup_valid_memory(mem);

    const auto proven = make_bb_06004000_descriptor();
    auto query = make_bb_06004000_descriptor();
    query.start_pc = 0x06004002u;

    const auto result = check_block_eligibility(proven, query, mem);
    THOR_ASSERT(result == EligibilityResult::ADDRESS_RANGE_MISMATCH);
}

static void test_negative_content_byte_mutation() {
    const auto proven = make_bb_06004000_descriptor();

    for (size_t i = 0; i < proven.expected_bytes.size(); ++i) {
        Sh2FlatMemory mem;
        setup_valid_memory(mem);
        // Mutate one byte
        mem.write8(0x06004000u + static_cast<uint32_t>(i), proven.expected_bytes[i] ^ 0xAA);
        mem.clear_log();

        const auto query = make_bb_06004000_descriptor();
        const auto result = check_block_eligibility(proven, query, mem);
        THOR_ASSERT(result == EligibilityResult::CONTENT_BYTE_MISMATCH);
        THOR_ASSERT(mem.log().empty());
    }
}

static void test_negative_invalid_validity_state() {
    Sh2FlatMemory mem;
    setup_valid_memory(mem);

    const auto proven = make_bb_06004000_descriptor();

    auto query_inv = make_bb_06004000_descriptor();
    query_inv.validity = BlockValidity::INVALIDATED;
    THOR_ASSERT(check_block_eligibility(proven, query_inv, mem) == EligibilityResult::INVALID_STATE);

    auto query_unv = make_bb_06004000_descriptor();
    query_unv.validity = BlockValidity::UNVERIFIED;
    THOR_ASSERT(check_block_eligibility(proven, query_unv, mem) == EligibilityResult::INVALID_STATE);
}

static void test_candidate_06004280_eligibility_and_negative_controls() {
    const auto proven = make_bb_06004280_descriptor();
    THOR_ASSERT(proven.expected_bytes.size() == 10);
    THOR_ASSERT(proven.start_pc == 0x06004280u);
    THOR_ASSERT(proven.end_pc == 0x06004288u);

    Sh2FlatMemory mem;
    for (size_t i = 0; i < proven.expected_bytes.size(); ++i) {
        mem.write8(proven.start_pc + static_cast<uint32_t>(i), proven.expected_bytes[i]);
    }
    mem.clear_log();

    // Positive
    const auto query = make_bb_06004280_descriptor();
    THOR_ASSERT(check_block_eligibility(proven, query, mem) == EligibilityResult::ELIGIBLE);
    THOR_ASSERT(mem.log().empty()); // Zero guest access log contamination

    // Wrong revision
    auto q_rev = query; q_rev.revision_id = "wrong_rev";
    THOR_ASSERT(check_block_eligibility(proven, q_rev, mem) == EligibilityResult::REVISION_MISMATCH);

    // Wrong module
    auto q_mod = query; q_mod.module_name = "OTHER.BIN";
    THOR_ASSERT(check_block_eligibility(proven, q_mod, mem) == EligibilityResult::MODULE_MISMATCH);

    // Wrong CPU
    auto q_cpu = query; q_cpu.cpu = CpuTarget::SLAVE_SH2;
    THOR_ASSERT(check_block_eligibility(proven, q_cpu, mem) == EligibilityResult::CPU_MISMATCH);

    // Wrong range
    auto q_range = query; q_range.start_pc = 0x06004282u;
    THOR_ASSERT(check_block_eligibility(proven, q_range, mem) == EligibilityResult::ADDRESS_RANGE_MISMATCH);

    // Invalid validity
    auto q_val = query; q_val.validity = BlockValidity::INVALIDATED;
    THOR_ASSERT(check_block_eligibility(proven, q_val, mem) == EligibilityResult::INVALID_STATE);

    // Each candidate byte corruption (10 byte positions)
    for (size_t i = 0; i < proven.expected_bytes.size(); ++i) {
        Sh2FlatMemory corrupt_mem = mem;
        corrupt_mem.write8(proven.start_pc + static_cast<uint32_t>(i), proven.expected_bytes[i] ^ 0xFF);
        corrupt_mem.clear_log();
        THOR_ASSERT(check_block_eligibility(proven, query, corrupt_mem) == EligibilityResult::CONTENT_BYTE_MISMATCH);
        THOR_ASSERT(corrupt_mem.log().empty());
    }
}

int main() {
    std::cout << "Running test_executable_identity...\n";
    test_positive_eligibility();
    test_negative_wrong_revision();
    test_negative_wrong_module();
    test_negative_unproven_provenance();
    test_negative_wrong_cpu();
    test_negative_wrong_address_range();
    test_negative_content_byte_mutation();
    test_negative_invalid_validity_state();
    test_candidate_06004280_eligibility_and_negative_controls();
    std::cout << "All test_executable_identity cases passed!\n";
    return 0;
}
