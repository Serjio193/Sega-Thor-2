#include <iostream>
#include <vector>
#include <cstring>

#include "thor/recomp/mutation_harness.hpp"
#include "thor/recomp/native_dispatcher.hpp"
#include "tests/sh2/test_framework.hpp"

struct SimulatedSaturnRam : public thor::sh2::ISh2Memory {
    std::vector<uint8_t> ram = std::vector<uint8_t>(0x00100000, 0); // 1MB HWR

    uint8_t read8(uint32_t addr) override {
        return ram[addr & 0x000FFFFFu];
    }
    [[nodiscard]] uint8_t peek8(uint32_t addr) const override {
        return ram[addr & 0x000FFFFFu];
    }
    uint16_t read16(uint32_t addr) override {
        uint32_t off = addr & 0x000FFFFFu;
        return static_cast<uint16_t>((ram[off] << 8) | ram[off + 1]);
    }
    uint32_t read32(uint32_t addr) override {
        uint32_t off = addr & 0x000FFFFFu;
        return (static_cast<uint32_t>(ram[off]) << 24) |
               (static_cast<uint32_t>(ram[off + 1]) << 16) |
               (static_cast<uint32_t>(ram[off + 2]) << 8) |
               static_cast<uint32_t>(ram[off + 3]);
    }
    void write8(uint32_t addr, uint8_t val) override {
        ram[addr & 0x000FFFFFu] = val;
    }
    void write16(uint32_t addr, uint16_t val) override {
        uint32_t off = addr & 0x000FFFFFu;
        ram[off] = static_cast<uint8_t>(val >> 8);
        ram[off + 1] = static_cast<uint8_t>(val & 0xFF);
    }
    void write32(uint32_t addr, uint32_t val) override {
        uint32_t off = addr & 0x000FFFFFu;
        ram[off] = static_cast<uint8_t>(val >> 24);
        ram[off + 1] = static_cast<uint8_t>((val >> 16) & 0xFF);
        ram[off + 2] = static_cast<uint8_t>((val >> 8) & 0xFF);
        ram[off + 3] = static_cast<uint8_t>(val & 0xFF);
    }

    void setup_canonical_startup() {
        const uint8_t opcodes[12] = {
            0x66, 0x11, // MOV.W @R1, R6
            0x6F, 0x03, // MOV R0, R15
            0xD4, 0x17, // MOV.L @(0x5C, PC), R4
            0x64, 0x42, // MOV.L @R4, R4
            0xA0, 0x03, // BRA 0x06004012
            0x00, 0x09  // NOP
        };
        for (size_t i = 0; i < 12; ++i) {
            write8(0x06004000u + static_cast<uint32_t>(i), opcodes[i]);
        }
        write32(0x06004064u, 0x06081C10u);
        write32(0x06081C10u, 0x060917DCu);
        write16(0x06004000u, 0x6611u);
    }

    ThorHardwareCallbacks make_callbacks() {
        ThorHardwareCallbacks cb{};
        cb.user_data = this;
        cb.read8 = [](uint32_t a, void* u) { return static_cast<SimulatedSaturnRam*>(u)->read8(a); };
        cb.read16 = [](uint32_t a, void* u) { return static_cast<SimulatedSaturnRam*>(u)->read16(a); };
        cb.read32 = [](uint32_t a, void* u) { return static_cast<SimulatedSaturnRam*>(u)->read32(a); };
        cb.write8 = [](uint32_t a, uint8_t v, void* u) { static_cast<SimulatedSaturnRam*>(u)->write8(a, v); };
        cb.write16 = [](uint32_t a, uint16_t v, void* u) { static_cast<SimulatedSaturnRam*>(u)->write16(a, v); };
        cb.write32 = [](uint32_t a, uint32_t v, void* u) { static_cast<SimulatedSaturnRam*>(u)->write32(a, v); };
        cb.is_slave_active = [](void*) { return false; };
        cb.is_dma_active = [](void*) { return false; };
        cb.is_irq_pending = [](void*) { return false; };
        return cb;
    }
};

static ThorCpuRegs make_canonical_entry_regs() {
    ThorCpuRegs r{};
    r.r[0] = 0x06002EDCu;
    r.r[1] = 0x06004000u;
    r.r[15] = 0x06001000u;
    r.pc = 0x06004000u;
    r.sr = 0x00000001u;
    r.pr = 0x06002244u;
    return r;
}

static void test_harness_negative_controls() {
    SimulatedSaturnRam mem;
    mem.setup_canonical_startup();

    thor::recomp::GuestMutationHarness harness(0x06004000u, 12u);

    // Negative 1: Range unauthorized (below range)
    auto spec_low = thor::recomp::GuestMutationHarness::create_byte_flip(0x06003FFFu, 0x00);
    auto res_low = harness.apply_and_verify(mem, spec_low);
    THOR_ASSERT(res_low.status == thor::recomp::MutationStatus::RANGE_UNAUTHORIZED);
    THOR_ASSERT(!res_low.mutation_applied);

    // Negative 2: Range unauthorized (above range)
    auto spec_high = thor::recomp::GuestMutationHarness::create_byte_flip(0x0600400Cu, 0x00);
    auto res_high = harness.apply_and_verify(mem, spec_high);
    THOR_ASSERT(res_high.status == thor::recomp::MutationStatus::RANGE_UNAUTHORIZED);
    THOR_ASSERT(!res_high.mutation_applied);

    // Negative 3: Original byte mismatch (expected 0xFF, but memory has 0x66)
    auto spec_mismatch = thor::recomp::GuestMutationHarness::create_byte_flip(0x06004000u, 0xFF);
    auto res_mismatch = harness.apply_and_verify(mem, spec_mismatch);
    THOR_ASSERT(res_mismatch.status == thor::recomp::MutationStatus::ORIGINAL_MISMATCH);
    THOR_ASSERT(!res_mismatch.mutation_applied);
    // Confirm memory was NOT modified
    THOR_ASSERT(mem.read8(0x06004000u) == 0x66u);

    // Negative 4: Restore without original bytes fails closed
    thor::recomp::MutationSpec empty_restore_spec{};
    empty_restore_spec.address = 0x06004000u;
    empty_restore_spec.replacement_bytes = {0x00};
    auto res_empty = harness.restore_and_verify(mem, empty_restore_spec);
    THOR_ASSERT(res_empty.status == thor::recomp::MutationStatus::RESTORE_VERIFY_FAILED);
}

static void test_twelve_byte_mutation_matrix() {
    SimulatedSaturnRam mem;
    mem.setup_canonical_startup();
    auto cb = mem.make_callbacks();

    auto& dispatcher = thor::recomp::NativeDispatcher::instance();
    dispatcher.set_mode(THOR_NATIVE_MODE_NATIVE_OVERRIDE);

    thor::recomp::GuestMutationHarness harness(0x06004000u, 12u);

    const uint8_t canonical_bytes[12] = {
        0x66, 0x11, 0x6F, 0x03, 0xD4, 0x17, 0x64, 0x42, 0xA0, 0x03, 0x00, 0x09
    };

    // Test each of the 12 byte positions in bb_06004000
    for (uint32_t i = 0; i < 12; ++i) {
        uint32_t target_addr = 0x06004000u + i;
        uint8_t orig_byte = canonical_bytes[i];

        dispatcher.reset_stats();
        auto spec = thor::recomp::GuestMutationHarness::create_byte_flip(target_addr, orig_byte, 0x01);
        auto apply_res = harness.apply_and_verify(mem, spec);
        THOR_ASSERT(apply_res.status == thor::recomp::MutationStatus::SUCCESS);
        THOR_ASSERT(apply_res.mutation_applied);

        // Attempt dispatch with mutated byte
        ThorCpuRegs regs = make_canonical_entry_regs();
        ThorCpuRegs original_regs = regs;
        uint32_t target_pc = 0, cycles = 0;
        bool handled = dispatcher.dispatch_step(0x06004000u, regs, target_pc, cycles, cb);

        // Must be rejected fail-closed
        THOR_ASSERT(!handled);
        THOR_ASSERT(dispatcher.get_stats().ineligible_count == 1);
        THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
        THOR_ASSERT(dispatcher.get_stats().native_executed_count == 0);
        THOR_ASSERT(std::memcmp(&regs, &original_regs, sizeof(ThorCpuRegs)) == 0);

        // Exact restoration
        auto restore_res = harness.restore_and_verify(mem, spec);
        THOR_ASSERT(restore_res.status == thor::recomp::MutationStatus::SUCCESS);
        THOR_ASSERT(restore_res.restoration_verified);

        // Verify clean baseline succeeds after restore
        dispatcher.reset_stats();
        handled = dispatcher.dispatch_step(0x06004000u, regs, target_pc, cycles, cb);
        THOR_ASSERT(handled);
        THOR_ASSERT(dispatcher.get_stats().native_executed_count == 1);
        THOR_ASSERT(regs.r[6] == 0x00006611u);
        THOR_ASSERT(regs.r[15] == 0x06002EDCu);
        THOR_ASSERT(regs.r[4] == 0x060917DCu);

        // Reset memory for next loop
        mem.setup_canonical_startup();
    }
}

static void test_instruction_nop_replacements() {
    SimulatedSaturnRam mem;
    mem.setup_canonical_startup();
    auto cb = mem.make_callbacks();

    auto& dispatcher = thor::recomp::NativeDispatcher::instance();
    dispatcher.set_mode(THOR_NATIVE_MODE_NATIVE_OVERRIDE);

    thor::recomp::GuestMutationHarness harness(0x06004000u, 12u);

    struct InstrEntry {
        uint32_t addr;
        uint16_t opcode;
        const char* name;
    };

    const InstrEntry instructions[6] = {
        {0x06004000u, 0x6611u, "MOV.W @R1, R6"},
        {0x06004002u, 0x6F03u, "MOV R0, R15"},
        {0x06004004u, 0xD417u, "MOV.L @(0x5C, PC), R4"},
        {0x06004006u, 0x6442u, "MOV.L @R4, R4"},
        {0x06004008u, 0xA003u, "BRA 0x06004012"},
        {0x0600400Au, 0x0009u, "NOP (Delay slot)"}
    };

    for (size_t i = 0; i < 6; ++i) {
        dispatcher.reset_stats();

        // For delay slot NOP, mutate to 0x0000 instead of NOP
        thor::recomp::MutationSpec spec;
        if (instructions[i].opcode == 0x0009u) {
            spec.address = instructions[i].addr;
            spec.expected_original = {0x00, 0x09};
            spec.replacement_bytes = {0x00, 0x00};
            spec.kind = thor::recomp::MutationKind::ARBITRARY_BYTES;
            spec.description = "Delay slot zeroing";
        } else {
            spec = thor::recomp::GuestMutationHarness::create_nop_mutation(
                instructions[i].addr, instructions[i].opcode, instructions[i].name);
        }

        auto apply_res = harness.apply_and_verify(mem, spec);
        THOR_ASSERT(apply_res.status == thor::recomp::MutationStatus::SUCCESS);

        ThorCpuRegs regs = make_canonical_entry_regs();
        ThorCpuRegs original_regs = regs;
        uint32_t target_pc = 0, cycles = 0;
        bool handled = dispatcher.dispatch_step(0x06004000u, regs, target_pc, cycles, cb);

        THOR_ASSERT(!handled);
        THOR_ASSERT(dispatcher.get_stats().ineligible_count == 1);
        THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
        THOR_ASSERT(dispatcher.get_stats().native_executed_count == 0);
        THOR_ASSERT(std::memcmp(&regs, &original_regs, sizeof(ThorCpuRegs)) == 0);

        auto restore_res = harness.restore_and_verify(mem, spec);
        THOR_ASSERT(restore_res.status == thor::recomp::MutationStatus::SUCCESS);

        // Verify clean execution after restore
        dispatcher.reset_stats();
        handled = dispatcher.dispatch_step(0x06004000u, regs, target_pc, cycles, cb);
        THOR_ASSERT(handled);
        THOR_ASSERT(dispatcher.get_stats().native_executed_count == 1);

        mem.setup_canonical_startup();
    }
}

int main() {
    std::cout << "Running GuestMutationHarness and M-02 Fault-Injection Tests...\n";

    test_harness_negative_controls();
    std::cout << "  PASS: test_harness_negative_controls (range, mismatch, restore failure checks)\n";

    test_twelve_byte_mutation_matrix();
    std::cout << "  PASS: test_twelve_byte_mutation_matrix (12/12 byte positions detected & rejected)\n";

    test_instruction_nop_replacements();
    std::cout << "  PASS: test_instruction_nop_replacements (all instructions NOP-tested & restored)\n";

    std::cout << "All GuestMutationHarness tests passed successfully.\n";
    return 0;
}
