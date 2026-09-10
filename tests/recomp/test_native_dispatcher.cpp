#include <iostream>
#include <cstdint>
#include <cstring>
#include <vector>

#include "thor/recomp/native_bridge.h"
#include "thor/recomp/native_dispatcher.hpp"
#include "tests/sh2/test_framework.hpp"

// Timing contracts distinguishing block duration vs subsequent instruction boundary
constexpr uint32_t BB_06004000_ENTRY_CYCLE = 305462360u;
constexpr uint32_t BB_06004000_EXIT_CYCLE = 305462387u;
constexpr uint32_t BB_06004000_NEXT_INSTR_COMPLETION_CYCLE = 305462388u;

constexpr uint32_t BLOCK_DURATION = BB_06004000_EXIT_CYCLE - BB_06004000_ENTRY_CYCLE;
constexpr uint32_t NEXT_INSTRUCTION_COMPLETION_BOUNDARY_DELTA =
    BB_06004000_NEXT_INSTR_COMPLETION_CYCLE - BB_06004000_ENTRY_CYCLE;

static_assert(BLOCK_DURATION == 27u, "Block duration must be 27 cycles");
static_assert(NEXT_INSTRUCTION_COMPLETION_BOUNDARY_DELTA == 28u,
    "Next instruction completion boundary must be delta 28");

struct TestSaturnHardware {
    std::vector<uint8_t> ram = std::vector<uint8_t>(0x00100000, 0); // 1MB HWR simulation
    bool slave_active = false;
    bool dma_active = false;
    bool irq_pending = false;

    static uint8_t cb_read8(uint32_t addr, void* user_data) {
        auto* self = static_cast<TestSaturnHardware*>(user_data);
        uint32_t offset = addr & 0x000FFFFFu;
        return self->ram[offset];
    }
    static uint16_t cb_read16(uint32_t addr, void* user_data) {
        auto* self = static_cast<TestSaturnHardware*>(user_data);
        uint32_t offset = addr & 0x000FFFFFu;
        return static_cast<uint16_t>((self->ram[offset] << 8) | self->ram[offset + 1]);
    }
    static uint32_t cb_read32(uint32_t addr, void* user_data) {
        auto* self = static_cast<TestSaturnHardware*>(user_data);
        uint32_t offset = addr & 0x000FFFFFu;
        return (static_cast<uint32_t>(self->ram[offset]) << 24) |
               (static_cast<uint32_t>(self->ram[offset + 1]) << 16) |
               (static_cast<uint32_t>(self->ram[offset + 2]) << 8) |
               static_cast<uint32_t>(self->ram[offset + 3]);
    }
    static void cb_write8(uint32_t addr, uint8_t val, void* user_data) {
        auto* self = static_cast<TestSaturnHardware*>(user_data);
        self->ram[addr & 0x000FFFFFu] = val;
    }
    static void cb_write16(uint32_t addr, uint16_t val, void* user_data) {
        auto* self = static_cast<TestSaturnHardware*>(user_data);
        uint32_t offset = addr & 0x000FFFFFu;
        self->ram[offset] = static_cast<uint8_t>(val >> 8);
        self->ram[offset + 1] = static_cast<uint8_t>(val);
    }
    static void cb_write32(uint32_t addr, uint32_t val, void* user_data) {
        auto* self = static_cast<TestSaturnHardware*>(user_data);
        uint32_t offset = addr & 0x000FFFFFu;
        self->ram[offset] = static_cast<uint8_t>(val >> 24);
        self->ram[offset + 1] = static_cast<uint8_t>(val >> 16);
        self->ram[offset + 2] = static_cast<uint8_t>(val >> 8);
        self->ram[offset + 3] = static_cast<uint8_t>(val);
    }
    static bool cb_is_slave_active(void* user_data) {
        return static_cast<TestSaturnHardware*>(user_data)->slave_active;
    }
    static bool cb_is_dma_active(void* user_data) {
        return static_cast<TestSaturnHardware*>(user_data)->dma_active;
    }
    static bool cb_is_irq_pending(void* user_data) {
        return static_cast<TestSaturnHardware*>(user_data)->irq_pending;
    }

    ThorHardwareCallbacks make_callbacks() {
        return ThorHardwareCallbacks{
            .read8 = cb_read8,
            .read16 = cb_read16,
            .read32 = cb_read32,
            .write8 = cb_write8,
            .write16 = cb_write16,
            .write32 = cb_write32,
            .is_slave_active = cb_is_slave_active,
            .is_dma_active = cb_is_dma_active,
            .is_irq_pending = cb_is_irq_pending,
            .user_data = this
        };
    }

    void setup_canonical_startup_memory() {
        const uint8_t opcodes[] = {
            0x66, 0x11, 0x6F, 0x03, 0xD4, 0x17, 0x64, 0x42, 0xA0, 0x03, 0x00, 0x09
        };
        for (size_t i = 0; i < sizeof(opcodes); ++i) {
            cb_write8(0x06004000u + static_cast<uint32_t>(i), opcodes[i], this);
        }
        cb_write32(0x06004064u, 0x06081C10u, this);
        cb_write32(0x06081C10u, 0x060917DCu, this);
    }
};

static ThorCpuRegs make_canonical_entry_regs() {
    ThorCpuRegs r{};
    r.r[0] = 0x06002EDCu;
    r.r[1] = 0x06004000u;
    r.r[4] = 0x00002650u;
    r.r[6] = 0x00000000u;
    r.r[15] = 0x06001000u;
    r.pc = 0x06004000u;
    r.sr = 0x00000001u;
    r.pr = 0x06002244u;
    return r;
}

static void test_interpreter_mode_fallback() {
    auto& dispatcher = thor::recomp::NativeDispatcher::instance();
    dispatcher.reset_stats();
    dispatcher.set_mode(THOR_NATIVE_MODE_INTERPRETER);

    TestSaturnHardware hw;
    hw.setup_canonical_startup_memory();
    ThorHardwareCallbacks cb = hw.make_callbacks();

    ThorCpuRegs regs = make_canonical_entry_regs();
    ThorCpuRegs original_regs = regs;
    uint32_t target_pc = 0;
    uint32_t cycles = 0;

    bool handled = dispatcher.dispatch_step(0x06004000u, regs, target_pc, cycles, cb);
    THOR_ASSERT(!handled);
    THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
    THOR_ASSERT(dispatcher.get_stats().native_executed_count == 0);
    // Verify zero partial commit
    THOR_ASSERT(std::memcmp(&regs, &original_regs, sizeof(ThorCpuRegs)) == 0);
}

static void test_shadow_verify_mode() {
    auto& dispatcher = thor::recomp::NativeDispatcher::instance();
    dispatcher.reset_stats();
    dispatcher.set_mode(THOR_NATIVE_MODE_SHADOW_VERIFY);

    TestSaturnHardware hw;
    hw.setup_canonical_startup_memory();
    ThorHardwareCallbacks cb = hw.make_callbacks();

    ThorCpuRegs regs = make_canonical_entry_regs();
    ThorCpuRegs original_regs = regs;
    uint32_t target_pc = 0;
    uint32_t cycles = 0;

    bool handled = dispatcher.dispatch_step(0x06004000u, regs, target_pc, cycles, cb);
    THOR_ASSERT(!handled); // Shadow verify mode does NOT commit to live state
    THOR_ASSERT(dispatcher.get_stats().shadow_match_count == 1);
    THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
    THOR_ASSERT(dispatcher.get_stats().native_executed_count == 0);
    THOR_ASSERT(std::memcmp(&regs, &original_regs, sizeof(ThorCpuRegs)) == 0);
}

static void test_native_override_positive() {
    auto& dispatcher = thor::recomp::NativeDispatcher::instance();
    dispatcher.reset_stats();
    dispatcher.set_mode(THOR_NATIVE_MODE_NATIVE_OVERRIDE);

    TestSaturnHardware hw;
    hw.setup_canonical_startup_memory();
    ThorHardwareCallbacks cb = hw.make_callbacks();

    ThorCpuRegs regs = make_canonical_entry_regs();
    uint32_t target_pc = 0;
    uint32_t cycles = 0;

    bool handled = dispatcher.dispatch_step(0x06004000u, regs, target_pc, cycles, cb);
    THOR_ASSERT(handled);
    THOR_ASSERT(dispatcher.get_stats().shadow_match_count == 1);
    THOR_ASSERT(dispatcher.get_stats().native_executed_count == 1);
    THOR_ASSERT(dispatcher.get_stats().fallback_count == 0);

    // Verify post-execution architectural state
    THOR_ASSERT(regs.r[6] == 0x00006611u);
    THOR_ASSERT(regs.r[15] == 0x06002EDCu);
    THOR_ASSERT(regs.r[4] == 0x060917DCu);
    THOR_ASSERT(target_pc == 0x06004012u);
    THOR_ASSERT(cycles == 27u);
}

static void test_negative_controls() {
    auto& dispatcher = thor::recomp::NativeDispatcher::instance();
    dispatcher.set_mode(THOR_NATIVE_MODE_NATIVE_OVERRIDE);

    // Negative 1: Wrong revision
    {
        dispatcher.reset_stats();
        dispatcher.inject_ineligible_revision(true);
        TestSaturnHardware hw;
        hw.setup_canonical_startup_memory();
        ThorHardwareCallbacks cb = hw.make_callbacks();
        ThorCpuRegs regs = make_canonical_entry_regs();
        ThorCpuRegs orig = regs;
        uint32_t target_pc = 0, cycles = 0;
        bool handled = dispatcher.dispatch_step(0x06004000u, regs, target_pc, cycles, cb);
        THOR_ASSERT(!handled);
        THOR_ASSERT(dispatcher.get_stats().ineligible_count == 1);
        THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
        THOR_ASSERT(std::memcmp(&regs, &orig, sizeof(ThorCpuRegs)) == 0);
        dispatcher.inject_ineligible_revision(false);
    }

    // Negative 2: Content byte corruption
    {
        dispatcher.reset_stats();
        dispatcher.inject_ineligible_content(true);
        TestSaturnHardware hw;
        hw.setup_canonical_startup_memory();
        ThorHardwareCallbacks cb = hw.make_callbacks();
        ThorCpuRegs regs = make_canonical_entry_regs();
        ThorCpuRegs orig = regs;
        uint32_t target_pc = 0, cycles = 0;
        bool handled = dispatcher.dispatch_step(0x06004000u, regs, target_pc, cycles, cb);
        THOR_ASSERT(!handled);
        THOR_ASSERT(dispatcher.get_stats().ineligible_count == 1);
        THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
        THOR_ASSERT(std::memcmp(&regs, &orig, sizeof(ThorCpuRegs)) == 0);
        dispatcher.inject_ineligible_content(false);
    }

    // Negative 3: Slave SH-2 active
    {
        dispatcher.reset_stats();
        TestSaturnHardware hw;
        hw.setup_canonical_startup_memory();
        hw.slave_active = true;
        ThorHardwareCallbacks cb = hw.make_callbacks();
        ThorCpuRegs regs = make_canonical_entry_regs();
        ThorCpuRegs orig = regs;
        uint32_t target_pc = 0, cycles = 0;
        bool handled = dispatcher.dispatch_step(0x06004000u, regs, target_pc, cycles, cb);
        THOR_ASSERT(!handled);
        THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
        THOR_ASSERT(std::memcmp(&regs, &orig, sizeof(ThorCpuRegs)) == 0);
    }

    // Negative 4: SCU DMA active
    {
        dispatcher.reset_stats();
        TestSaturnHardware hw;
        hw.setup_canonical_startup_memory();
        hw.dma_active = true;
        ThorHardwareCallbacks cb = hw.make_callbacks();
        ThorCpuRegs regs = make_canonical_entry_regs();
        ThorCpuRegs orig = regs;
        uint32_t target_pc = 0, cycles = 0;
        bool handled = dispatcher.dispatch_step(0x06004000u, regs, target_pc, cycles, cb);
        THOR_ASSERT(!handled);
        THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
        THOR_ASSERT(std::memcmp(&regs, &orig, sizeof(ThorCpuRegs)) == 0);
    }

    // Negative 5: IRQ pending
    {
        dispatcher.reset_stats();
        TestSaturnHardware hw;
        hw.setup_canonical_startup_memory();
        hw.irq_pending = true;
        ThorHardwareCallbacks cb = hw.make_callbacks();
        ThorCpuRegs regs = make_canonical_entry_regs();
        ThorCpuRegs orig = regs;
        uint32_t target_pc = 0, cycles = 0;
        bool handled = dispatcher.dispatch_step(0x06004000u, regs, target_pc, cycles, cb);
        THOR_ASSERT(!handled);
        THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
        THOR_ASSERT(std::memcmp(&regs, &orig, sizeof(ThorCpuRegs)) == 0);
    }

    // Negative 6: Forced shadow divergence
    {
        dispatcher.reset_stats();
        dispatcher.inject_forced_divergence(true);
        TestSaturnHardware hw;
        hw.setup_canonical_startup_memory();
        ThorHardwareCallbacks cb = hw.make_callbacks();
        ThorCpuRegs regs = make_canonical_entry_regs();
        ThorCpuRegs orig = regs;
        uint32_t target_pc = 0, cycles = 0;
        bool handled = dispatcher.dispatch_step(0x06004000u, regs, target_pc, cycles, cb);
        THOR_ASSERT(!handled);
        THOR_ASSERT(dispatcher.get_stats().shadow_divergence_count == 1);
        THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
        THOR_ASSERT(dispatcher.get_stats().native_executed_count == 0);
        THOR_ASSERT(std::memcmp(&regs, &orig, sizeof(ThorCpuRegs)) == 0); // ZERO partial commit
        dispatcher.inject_forced_divergence(false);
    }

    // Negative 7: Unregistered PC
    {
        dispatcher.reset_stats();
        TestSaturnHardware hw;
        ThorHardwareCallbacks cb = hw.make_callbacks();
        ThorCpuRegs regs = make_canonical_entry_regs();
        uint32_t target_pc = 0, cycles = 0;
        bool handled = dispatcher.dispatch_step(0x06004002u, regs, target_pc, cycles, cb);
        THOR_ASSERT(!handled);
        THOR_ASSERT(dispatcher.get_stats().dispatch_attempts == 0);
    }
}

static void test_dynamic_target_resolution_regression() {
    auto& dispatcher = thor::recomp::NativeDispatcher::instance();
    dispatcher.set_mode(THOR_NATIVE_MODE_NATIVE_OVERRIDE);
    dispatcher.reset_stats();

    TestSaturnHardware hw;
    hw.setup_canonical_startup_memory();
    ThorHardwareCallbacks cb = hw.make_callbacks();
    ThorCpuRegs regs = make_canonical_entry_regs();
    uint32_t target_pc = 0, cycles = 0;

    bool handled = dispatcher.dispatch_step(0x06004000u, regs, target_pc, cycles, cb);
    THOR_ASSERT(handled);
    // Verified that out_target_pc matches live_cpu.pc (0x06004012) resolved through exit descriptor
    THOR_ASSERT(target_pc == 0x06004012u);
    THOR_ASSERT(regs.pc == 0x06004012u);
    THOR_ASSERT(cycles == 27u);

    // Negative: Forced divergence mutating PC must fail closed with zero partial commit
    dispatcher.reset_stats();
    dispatcher.inject_forced_divergence(true);
    ThorCpuRegs orig = regs;
    target_pc = 0;
    cycles = 0;
    handled = dispatcher.dispatch_step(0x06004000u, regs, target_pc, cycles, cb);
    THOR_ASSERT(!handled);
    THOR_ASSERT(dispatcher.get_stats().shadow_divergence_count == 1);
    THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
    THOR_ASSERT(std::memcmp(&regs, &orig, sizeof(ThorCpuRegs)) == 0);
    dispatcher.inject_forced_divergence(false);
}

static void test_registration_validation() {
    auto& dispatcher = thor::recomp::NativeDispatcher::instance();

    auto make_valid = []() {
        thor::recomp::RegisteredNativeBlock b{};
        b.proven_identity = thor::recomp::make_bb_06004000_descriptor();
        thor::sh2::Sh2FlatMemory dummy_mem;
        for (size_t i = 0; i < b.proven_identity.expected_bytes.size(); ++i) {
            dummy_mem.write8(0x06004000u + static_cast<uint32_t>(i), b.proven_identity.expected_bytes[i]);
        }
        b.oracle_block = thor::sh2::discover_basic_block(0x06004000u, dummy_mem);
        b.candidate_fn = [](thor::sh2::Sh2CpuState&, thor::sh2::ISh2Memory&) {};
        b.exit_descriptor = *thor::recomp::derive_block_exit_descriptor(b.oracle_block);
        b.memory_contract = *thor::recomp::derive_block_memory_contract(b.oracle_block);
        b.cycle_cost = 27u;
        return b;
    };

    // Positive
    THOR_ASSERT(dispatcher.register_block(make_valid()));

    // Null candidate function
    {
        auto b = make_valid();
        b.candidate_fn = nullptr;
        THOR_ASSERT(!dispatcher.register_block(b));
    }
    // Empty instructions
    {
        auto b = make_valid();
        b.oracle_block.instructions.clear();
        THOR_ASSERT(!dispatcher.register_block(b));
    }
    // Range mismatch
    {
        auto b = make_valid();
        b.proven_identity.start_pc = 0x06004002u;
        THOR_ASSERT(!dispatcher.register_block(b));
    }
    // Exit descriptor mismatch
    {
        auto b = make_valid();
        b.exit_descriptor.kind = thor::recomp::BlockExitKind::CONDITIONAL;
        THOR_ASSERT(!dispatcher.register_block(b));
    }
    // Memory contract mismatch
    {
        auto b = make_valid();
        b.memory_contract.block_start_pc ^= 1u;
        THOR_ASSERT(!dispatcher.register_block(b));
    }
    // Zero cycle cost
    {
        auto b = make_valid();
        b.cycle_cost = 0;
        THOR_ASSERT(!dispatcher.register_block(b));
    }
    // Memory contract has WRITE dependency (must be rejected)
    {
        auto b = make_valid();
        b.memory_contract.dependencies.push_back(thor::recomp::MemoryDependencyDescriptor{
            .instruction_pc = 0x06004000u,
            .access_kind = thor::sh2::MemoryAccessKind::WRITE,
            .width = thor::recomp::MemoryAccessWidth::U32,
            .address_source = thor::recomp::AddressSourceKind::STATIC_ADDRESS,
            .static_address = 0x06001000u,
            .source_register = std::nullopt,
            .region_class = thor::recomp::MemoryRegionClass::RAM
        });
        THOR_ASSERT(!dispatcher.register_block(b));
    }
}

int main() {
    std::cout << "Running NativeDispatcher and Fail-Closed Verification Tests...\n";

    test_interpreter_mode_fallback();
    std::cout << "  PASS: test_interpreter_mode_fallback\n";

    test_shadow_verify_mode();
    std::cout << "  PASS: test_shadow_verify_mode\n";

    test_native_override_positive();
    std::cout << "  PASS: test_native_override_positive\n";

    test_negative_controls();
    std::cout << "  PASS: test_negative_controls (7 negative scenarios)\n";

    test_dynamic_target_resolution_regression();
    std::cout << "  PASS: test_dynamic_target_resolution_regression\n";

    test_registration_validation();
    std::cout << "  PASS: test_registration_validation\n";

    std::cout << "All NativeDispatcher tests passed successfully.\n";
    return 0;
}
