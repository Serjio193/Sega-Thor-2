#include <iostream>
#include "thor/recomp/shadow_checker.hpp"
#include "thor/sh2/sh2_memory.hpp"
#include "tests/sh2/test_framework.hpp"

using namespace thor::recomp;
using namespace thor::sh2;

static void test_register_value_faults(uint32_t& detected_count) {
    Sh2CpuState o_cpu{}, c_cpu{};
    std::vector<MemoryLogEntry> o_log, c_log;
    BoundedEventMetadata o_meta{}, c_meta{};

    // Corrupt R0, R4, R6, R15 individually
    const uint32_t regs_to_test[] = {0, 4, 6, 15};
    for (uint32_t r : regs_to_test) {
        c_cpu = o_cpu;
        c_cpu.r[r] ^= 0x55AA55AA;

        const auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
        THOR_ASSERT(!res.is_match());
        THOR_ASSERT(res.status == ShadowStatus::DIVERGENCE);
        THOR_ASSERT(!res.divergences.empty());
        THOR_ASSERT(res.divergences[0].category == DivergenceCategory::REGISTER);
        THOR_ASSERT(res.divergences[0].index == r);
        detected_count++;
    }
}

static void test_pc_and_sr_faults(uint32_t& detected_count) {
    Sh2CpuState o_cpu{}, c_cpu{};
    std::vector<MemoryLogEntry> o_log, c_log;
    BoundedEventMetadata o_meta{}, c_meta{};

    // Corrupt PC
    c_cpu = o_cpu;
    c_cpu.pc = 0x0600400Cu;
    auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
    THOR_ASSERT(!res.is_match());
    THOR_ASSERT(res.divergences[0].category == DivergenceCategory::PROGRAM_COUNTER);
    detected_count++;

    // Corrupt SR (T bit)
    c_cpu = o_cpu;
    c_cpu.sr = o_cpu.sr ^ 1u;
    res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
    THOR_ASSERT(!res.is_match());
    THOR_ASSERT(res.divergences[0].category == DivergenceCategory::STATUS_REGISTER);
    detected_count++;
}

static void test_memory_write_faults(uint32_t& detected_count) {
    Sh2CpuState o_cpu{}, c_cpu{};
    BoundedEventMetadata o_meta{}, c_meta{};

    const MemoryLogEntry baseline_write{MemoryAccessKind::WRITE, 0x06080000u, 0x12345678u, 4};

    // 1. Omitted write (oracle has write, candidate has none)
    {
        std::vector<MemoryLogEntry> o_log = {baseline_write};
        std::vector<MemoryLogEntry> c_log = {};
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
        THOR_ASSERT(!res.is_match());
        THOR_ASSERT(res.divergences[0].category == DivergenceCategory::MEMORY_EFFECT_COUNT);
        detected_count++;
    }

    // 2. Added write (candidate has unexpected write)
    {
        std::vector<MemoryLogEntry> o_log = {};
        std::vector<MemoryLogEntry> c_log = {baseline_write};
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
        THOR_ASSERT(!res.is_match());
        THOR_ASSERT(res.divergences[0].category == DivergenceCategory::MEMORY_EFFECT_COUNT);
        detected_count++;
    }

    // 3. Wrong-address write
    {
        std::vector<MemoryLogEntry> o_log = {baseline_write};
        std::vector<MemoryLogEntry> c_log = {{MemoryAccessKind::WRITE, 0x06080004u, 0x12345678u, 4}};
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
        THOR_ASSERT(!res.is_match());
        THOR_ASSERT(res.divergences[0].category == DivergenceCategory::MEMORY_EFFECT_ADDRESS);
        detected_count++;
    }

    // 4. Wrong-width write
    {
        std::vector<MemoryLogEntry> o_log = {baseline_write};
        std::vector<MemoryLogEntry> c_log = {{MemoryAccessKind::WRITE, 0x06080000u, 0x12345678u, 2}};
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
        THOR_ASSERT(!res.is_match());
        THOR_ASSERT(res.divergences[0].category == DivergenceCategory::MEMORY_EFFECT_SIZE);
        detected_count++;
    }

    // 5. Corrupted-value write
    {
        std::vector<MemoryLogEntry> o_log = {baseline_write};
        std::vector<MemoryLogEntry> c_log = {{MemoryAccessKind::WRITE, 0x06080000u, 0xDEADBEEFu, 4}};
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
        THOR_ASSERT(!res.is_match());
        THOR_ASSERT(res.divergences[0].category == DivergenceCategory::MEMORY_EFFECT_VALUE);
        detected_count++;
    }
}

static void test_ordered_memory_effects_fault(uint32_t& detected_count) {
    Sh2CpuState o_cpu{}, c_cpu{};
    BoundedEventMetadata o_meta{}, c_meta{};

    const MemoryLogEntry read_a{MemoryAccessKind::READ, 0x06004000u, 0x6611u, 2};
    const MemoryLogEntry read_b{MemoryAccessKind::READ, 0x06004064u, 0x06081C10u, 4};

    // Oracle: A then B. Candidate: B then A (reversed order).
    std::vector<MemoryLogEntry> o_log = {read_a, read_b};
    std::vector<MemoryLogEntry> c_log = {read_b, read_a};

    const auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
    THOR_ASSERT(!res.is_match());
    THOR_ASSERT(res.status == ShadowStatus::DIVERGENCE);
    // Reversed order must flag address/value/size mismatch on index 0
    bool found_order_divergence = false;
    for (const auto& d : res.divergences) {
        if (d.category == DivergenceCategory::MEMORY_EFFECT_ADDRESS) {
            found_order_divergence = true;
            break;
        }
    }
    THOR_ASSERT(found_order_divergence);
    detected_count++;
}

static void test_event_safety_metadata_faults(uint32_t& detected_count) {
    Sh2CpuState o_cpu{}, c_cpu{};
    std::vector<MemoryLogEntry> o_log, c_log;
    BoundedEventMetadata o_meta{};

    // Injected MMIO access
    {
        BoundedEventMetadata c_meta = o_meta;
        c_meta.mmio_accessed = true;
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
        THOR_ASSERT(!res.is_match());
        THOR_ASSERT(res.divergences[0].category == DivergenceCategory::EVENT_SAFETY_METADATA);
        detected_count++;
    }
    // Injected IRQ accepted
    {
        BoundedEventMetadata c_meta = o_meta;
        c_meta.irq_accepted = true;
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
        THOR_ASSERT(!res.is_match());
        THOR_ASSERT(res.divergences[0].category == DivergenceCategory::EVENT_SAFETY_METADATA);
        detected_count++;
    }
    // Injected SCU DMA crossing
    {
        BoundedEventMetadata c_meta = o_meta;
        c_meta.scu_dma_crossing = true;
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
        THOR_ASSERT(!res.is_match());
        THOR_ASSERT(res.divergences[0].category == DivergenceCategory::EVENT_SAFETY_METADATA);
        detected_count++;
    }
    // Injected Slave SH-2 activity
    {
        BoundedEventMetadata c_meta = o_meta;
        c_meta.slave_sh2_active = true;
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
        THOR_ASSERT(!res.is_match());
        THOR_ASSERT(res.divergences[0].category == DivergenceCategory::EVENT_SAFETY_METADATA);
        detected_count++;
    }
    // Injected delay slot non-atomicity
    {
        BoundedEventMetadata c_meta = o_meta;
        c_meta.delay_slot_atomic = false;
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
        THOR_ASSERT(!res.is_match());
        THOR_ASSERT(res.divergences[0].category == DivergenceCategory::EVENT_SAFETY_METADATA);
        detected_count++;
    }
}

static void test_fail_closed_guard_faults(uint32_t& detected_count) {
    BlockPreState pre_state{};
    const uint8_t bytes[] = {0x66, 0x11, 0x6F, 0x03, 0xD4, 0x17, 0x64, 0x42, 0xA0, 0x03, 0x00, 0x09};
    for (size_t i = 0; i < sizeof(bytes); ++i) {
        pre_state.memory.write8(0x06004000u + static_cast<uint32_t>(i), bytes[i]);
    }
    const auto block = discover_basic_block(0x06004000u, pre_state.memory);
    const auto proven_desc = make_bb_06004000_descriptor();

    auto dummy_candidate = [](Sh2CpuState&, ISh2Memory&) {};

    // 1. Ineligible revision
    {
        auto cand_desc = proven_desc;
        cand_desc.revision_id = "wrong_rev";
        auto res = ShadowChecker::run_and_compare(proven_desc, cand_desc, block, dummy_candidate, pre_state);
        THOR_ASSERT(res.status == ShadowStatus::INELIGIBLE);
        detected_count++;
    }
    // 2. Ineligible module
    {
        auto cand_desc = proven_desc;
        cand_desc.module_name = "TH2.LOW";
        auto res = ShadowChecker::run_and_compare(proven_desc, cand_desc, block, dummy_candidate, pre_state);
        THOR_ASSERT(res.status == ShadowStatus::INELIGIBLE);
        detected_count++;
    }
    // 3. Unproven provenance
    {
        auto cand_desc = proven_desc;
        cand_desc.module_provenance_proven = false;
        auto res = ShadowChecker::run_and_compare(proven_desc, cand_desc, block, dummy_candidate, pre_state);
        THOR_ASSERT(res.status == ShadowStatus::INELIGIBLE);
        detected_count++;
    }
    // 4. Ineligible CPU
    {
        auto cand_desc = proven_desc;
        cand_desc.cpu = CpuTarget::SLAVE_SH2;
        auto res = ShadowChecker::run_and_compare(proven_desc, cand_desc, block, dummy_candidate, pre_state);
        THOR_ASSERT(res.status == ShadowStatus::INELIGIBLE);
        detected_count++;
    }
    // 5. Ineligible range
    {
        auto cand_desc = proven_desc;
        cand_desc.start_pc = 0x06004002u;
        auto res = ShadowChecker::run_and_compare(proven_desc, cand_desc, block, dummy_candidate, pre_state);
        THOR_ASSERT(res.status == ShadowStatus::INELIGIBLE);
        detected_count++;
    }
    // 6. Mutated byte in pre-state RAM
    {
        auto bad_pre_state = pre_state;
        bad_pre_state.memory.write8(0x06004000u, 0x00);
        auto res = ShadowChecker::run_and_compare(proven_desc, proven_desc, block, dummy_candidate, bad_pre_state);
        THOR_ASSERT(res.status == ShadowStatus::INELIGIBLE);
        detected_count++;
    }
    // 7. Invalid validity state
    {
        auto cand_desc = proven_desc;
        cand_desc.validity = BlockValidity::INVALIDATED;
        auto res = ShadowChecker::run_and_compare(proven_desc, cand_desc, block, dummy_candidate, pre_state);
        THOR_ASSERT(res.status == ShadowStatus::INELIGIBLE);
        detected_count++;
    }
}

static void test_delayed_control_state_faults(uint32_t& detected_count) {
    Sh2CpuState o_cpu{}, c_cpu{};
    std::vector<MemoryLogEntry> o_log, c_log;
    BoundedEventMetadata o_meta{}, c_meta{};

    // A. Same PC/registers but candidate leaves delayed_pc set -> DIVERGENCE
    {
        o_cpu.pc = 0x0600A0F8u;
        o_cpu.delayed_pc = std::nullopt;
        c_cpu = o_cpu;
        c_cpu.delayed_pc = 0x0600A0F8u;
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
        THOR_ASSERT(!res.is_match() && res.divergences[0].category == DivergenceCategory::DELAYED_CONTROL_STATE);
        detected_count++;
    }

    // B. Both pending but different delayed targets -> DIVERGENCE
    {
        o_cpu.delayed_pc = 0x0600A0F8u;
        c_cpu = o_cpu;
        c_cpu.delayed_pc = 0x0600BEEFu;
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
        THOR_ASSERT(!res.is_match() && res.divergences[0].category == DivergenceCategory::DELAYED_CONTROL_STATE);
        detected_count++;
    }

    // C. Both nullopt -> MATCH
    {
        o_cpu.delayed_pc = std::nullopt;
        c_cpu = o_cpu;
        c_cpu.delayed_pc = std::nullopt;
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
        THOR_ASSERT(res.is_match());
    }

    // D. Zero delayed target vs nullopt -> DIVERGENCE
    {
        o_cpu.delayed_pc = std::nullopt;
        c_cpu = o_cpu;
        c_cpu.delayed_pc = 0x00000000u;
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, c_log, c_meta);
        THOR_ASSERT(!res.is_match() && res.divergences[0].category == DivergenceCategory::DELAYED_CONTROL_STATE);
        detected_count++;
    }
}

static void test_candidate_06004280_negative_controls(uint32_t& detected_count) {
    // Pinned baseline for bb_06004280
    Sh2CpuState o_cpu{};
    o_cpu.r[5] = 0x002DA000u;
    o_cpu.r[4] = 0x06081C20u;
    o_cpu.r[3] = 0x0600A0F8u;
    o_cpu.pr = 0x0600428Au;
    o_cpu.pc = 0x0600A0F8u;
    o_cpu.delayed_pc = std::nullopt;

    const std::vector<MemoryLogEntry> o_log = {
        {MemoryAccessKind::READ, 0x0600435Cu, 0x002DA000u, 4},
        {MemoryAccessKind::READ, 0x06004360u, 0x06081C20u, 4},
        {MemoryAccessKind::READ, 0x06004364u, 0x0600A0F8u, 4}
    };
    const BoundedEventMetadata o_meta{};

    // 1. PR corruption
    {
        auto c_cpu = o_cpu; c_cpu.pr ^= 0x04;
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, o_log, o_meta);
        THOR_ASSERT(!res.is_match() && res.divergences[0].category == DivergenceCategory::CONTROL_REGISTER);
        detected_count++;
    }
    // 2. PC/target corruption
    {
        auto c_cpu = o_cpu; c_cpu.pc ^= 0x04;
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, o_log, o_meta);
        THOR_ASSERT(!res.is_match() && res.divergences[0].category == DivergenceCategory::PROGRAM_COUNTER);
        detected_count++;
    }
    // 3. delayed_pc left pending
    {
        auto c_cpu = o_cpu; c_cpu.delayed_pc = 0x0600A0F8u;
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, c_cpu, o_log, o_meta);
        THOR_ASSERT(!res.is_match() && res.divergences[0].category == DivergenceCategory::DELAYED_CONTROL_STATE);
        detected_count++;
    }
    // 4. One literal read omitted
    {
        std::vector<MemoryLogEntry> c_log = {o_log[0], o_log[1]};
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, o_cpu, c_log, o_meta);
        THOR_ASSERT(!res.is_match() && res.divergences[0].category == DivergenceCategory::MEMORY_EFFECT_COUNT);
        detected_count++;
    }
    // 5. Wrong literal address
    {
        auto c_log = o_log; c_log[0].address = 0x06004358u;
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, o_cpu, c_log, o_meta);
        THOR_ASSERT(!res.is_match() && res.divergences[0].category == DivergenceCategory::MEMORY_EFFECT_ADDRESS);
        detected_count++;
    }
    // 6. Wrong read order
    {
        auto c_log = o_log; std::swap(c_log[0], c_log[1]);
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, o_cpu, c_log, o_meta);
        THOR_ASSERT(!res.is_match() && res.divergences[0].category == DivergenceCategory::MEMORY_EFFECT_ADDRESS);
        detected_count++;
    }
    // 7. Wrong read width
    {
        auto c_log = o_log; c_log[0].size_bytes = 2;
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, o_cpu, c_log, o_meta);
        THOR_ASSERT(!res.is_match() && res.divergences[0].category == DivergenceCategory::MEMORY_EFFECT_SIZE);
        detected_count++;
    }
    // 8. Extra memory effect
    {
        auto c_log = o_log;
        c_log.push_back({MemoryAccessKind::READ, 0x06004368u, 0x00000000u, 4});
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, o_cpu, c_log, o_meta);
        THOR_ASSERT(!res.is_match() && res.divergences[0].category == DivergenceCategory::MEMORY_EFFECT_COUNT);
        detected_count++;
    }
    // 9. Event metadata mismatch
    {
        auto c_meta = o_meta; c_meta.slave_sh2_active = true;
        auto res = ShadowChecker::compare_outcomes(o_cpu, o_log, o_meta, o_cpu, o_log, c_meta);
        THOR_ASSERT(!res.is_match() && res.divergences[0].category == DivergenceCategory::EVENT_SAFETY_METADATA);
        detected_count++;
    }
    // 10. Identity byte corruption
    {
        auto p_desc = make_bb_06004000_descriptor(); // Will test with 06004280 once created
        p_desc.expected_bytes[0] ^= 0xFF;
        Sh2FlatMemory mem;
        auto res = check_block_eligibility(make_bb_06004000_descriptor(), p_desc, mem);
        THOR_ASSERT(res == EligibilityResult::CONTENT_BYTE_MISMATCH);
        detected_count++;
    }
}

int main() {
    std::cout << "Running test_shadow_negative...\n";
    uint32_t detected_count = 0;
    test_register_value_faults(detected_count);
    test_pc_and_sr_faults(detected_count);
    test_memory_write_faults(detected_count);
    test_ordered_memory_effects_fault(detected_count);
    test_event_safety_metadata_faults(detected_count);
    test_fail_closed_guard_faults(detected_count);
    test_delayed_control_state_faults(detected_count);
    test_candidate_06004280_negative_controls(detected_count);

    std::cout << "100% of negative control faults detected (" << detected_count << "/" << detected_count << "), 0 false passes!\n";
    return 0;
}
