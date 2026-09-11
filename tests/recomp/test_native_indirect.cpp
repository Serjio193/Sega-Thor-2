#include <iostream>
#include <cstdint>
#include <cstring>
#include <vector>

#include "thor/recomp/native_bridge.h"
#include "thor/recomp/native_dispatcher.hpp"
#include "tests/sh2/test_framework.hpp"

struct TestSaturnHardware {
    std::vector<uint8_t> ram = std::vector<uint8_t>(0x00100000, 0); // 1MB HWR simulation (0x06000000..0x060FFFFF)
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

    void setup_canonical_all_memory() {
        // bb_06004000 opcodes and pointers
        const uint8_t opcodes0[] = {
            0x66, 0x11, 0x6F, 0x03, 0xD4, 0x17, 0x64, 0x42, 0xA0, 0x03, 0x00, 0x09
        };
        for (size_t i = 0; i < sizeof(opcodes0); ++i) {
            cb_write8(0x06004000u + static_cast<uint32_t>(i), opcodes0[i], this);
        }
        cb_write32(0x06004064u, 0x06081C10u, this);
        cb_write32(0x06081C10u, 0x060917DCu, this);

        // bb_06004280 opcodes and literals
        const uint8_t opcodes1[] = {
            0xD5, 0x36, 0xD4, 0x37, 0xD3, 0x37, 0x43, 0x0B, 0x00, 0x09
        };
        for (size_t i = 0; i < sizeof(opcodes1); ++i) {
            cb_write8(0x06004280u + static_cast<uint32_t>(i), opcodes1[i], this);
        }
        cb_write32(0x0600435Cu, 0x002DA000u, this);
        cb_write32(0x06004360u, 0x06081C20u, this);
        cb_write32(0x06004364u, 0x0600A0F8u, this);
    }
};

static ThorCpuRegs make_hit2_regs() {
    ThorCpuRegs regs{};
    regs.pc = 0x06004280u;
    regs.r[0] = 0x00000023u;
    regs.r[1] = 0x06093B14u;
    regs.r[2] = 0x00000028u;
    regs.r[3] = 0x06094F28u;
    regs.r[4] = 0x00000000u;
    regs.r[5] = 0x06094B68u;
    regs.r[6] = 0x00000BC5u;
    regs.r[7] = 0x00000008u;
    regs.r[11] = 0x06096523u;
    regs.r[12] = 0x06088708u;
    regs.r[13] = 0x00000001u;
    regs.r[14] = 0x00000002u;
    regs.r[15] = 0x06002ED8u;
    regs.sr = 0x00000001u;
    regs.pr = 0x06004280u;
    regs.vbr = 0x06000000u;
    return regs;
}

static ThorCpuRegs make_bb0_regs() {
    ThorCpuRegs regs{};
    regs.pc = 0x06004000u;
    regs.r[0] = 0x06002EDCu;
    regs.r[1] = 0x06004000u;
    regs.r[3] = 0x00002650u;
    regs.r[4] = 0x00002650u;
    regs.r[5] = 0x060002DCu;
    regs.r[7] = 0x06000D00u;
    regs.r[15] = 0x06001000u;
    regs.sr = 0x00000001u;
    regs.vbr = 0x06000000u;
    return regs;
}

static void test_native_indirect_positive() {
    thor_native_init();
    thor_native_reset_stats();
    thor_native_set_mode(THOR_NATIVE_MODE_NATIVE_OVERRIDE);
    thor_native_set_block_mask(THOR_BLOCK_MASK_ALL);

    TestSaturnHardware hw;
    hw.setup_canonical_all_memory();
    auto cb = hw.make_callbacks();

    ThorCpuRegs regs = make_hit2_regs();
    uint32_t target_pc = 0;
    uint32_t cycles_adv = 0;

    bool ok = thor_native_dispatch_step(0x06004280u, &regs, &target_pc, &cycles_adv, &cb);
    THOR_ASSERT(ok);
    THOR_ASSERT(target_pc == 0x0600A0F8u);
    // Canonical D9 timing evidence: ARCHITECTURAL_BLOCK_DURATION = 21 cycles
    THOR_ASSERT(cycles_adv == 21u);

    // Register checks
    THOR_ASSERT(regs.r[5] == 0x002DA000u);
    THOR_ASSERT(regs.r[4] == 0x06081C20u);
    THOR_ASSERT(regs.r[3] == 0x0600A0F8u);
    THOR_ASSERT(regs.pr == 0x0600428Au);
    THOR_ASSERT(regs.pc == 0x0600A0F8u);

    ThorNativeStats stats{};
    thor_native_get_stats(&stats);
    THOR_ASSERT(stats.dispatch_attempts == 1);
    THOR_ASSERT(stats.native_executed_count == 1);
    THOR_ASSERT(stats.fallback_count == 0);
    THOR_ASSERT(stats.shadow_match_count == 1);
    THOR_ASSERT(stats.shadow_divergence_count == 0);

    uint64_t executed = 0, fallback = 0;
    THOR_ASSERT(thor_native_get_block_stats(0x06004280u, &executed, &fallback));
    THOR_ASSERT(executed == 1);
    THOR_ASSERT(fallback == 0);
}

static void test_dynamic_target_anti_hardcoding() {
    thor_native_init();
    thor_native_reset_stats();
    thor_native_set_mode(THOR_NATIVE_MODE_NATIVE_OVERRIDE);
    thor_native_set_block_mask(THOR_BLOCK_MASK_ALL);

    TestSaturnHardware hw;
    hw.setup_canonical_all_memory();

    // Mutate literal pool to an alternate valid target
    hw.cb_write32(0x06004364u, 0x0600BEEFu, &hw);
    auto cb = hw.make_callbacks();

    ThorCpuRegs regs = make_hit2_regs();
    uint32_t target_pc = 0;
    uint32_t cycles_adv = 0;

    bool ok = thor_native_dispatch_step(0x06004280u, &regs, &target_pc, &cycles_adv, &cb);
    THOR_ASSERT(ok);
    THOR_ASSERT(target_pc == 0x0600BEEFu);
    THOR_ASSERT(regs.r[3] == 0x0600BEEFu);
    THOR_ASSERT(regs.pc == 0x0600BEEFu);
    THOR_ASSERT(regs.pr == 0x0600428Au);
}

static void test_block_mask_gating() {
    thor_native_init();
    thor_native_set_mode(THOR_NATIVE_MODE_NATIVE_OVERRIDE);

    TestSaturnHardware hw;
    hw.setup_canonical_all_memory();
    auto cb = hw.make_callbacks();

    // Mode A: THOR_BLOCK_MASK_NONE
    {
        thor_native_reset_stats();
        thor_native_set_block_mask(THOR_BLOCK_MASK_NONE);

        ThorCpuRegs r0 = make_bb0_regs();
        uint32_t tgt = 0, cyc = 0;
        THOR_ASSERT(!thor_native_dispatch_step(0x06004000u, &r0, &tgt, &cyc, &cb));

        ThorCpuRegs r1 = make_hit2_regs();
        THOR_ASSERT(!thor_native_dispatch_step(0x06004280u, &r1, &tgt, &cyc, &cb));

        uint64_t exec0 = 0, fb0 = 0, exec1 = 0, fb1 = 0;
        thor_native_get_block_stats(0x06004000u, &exec0, &fb0);
        thor_native_get_block_stats(0x06004280u, &exec1, &fb1);
        THOR_ASSERT(exec0 == 0 && fb0 == 1);
        THOR_ASSERT(exec1 == 0 && fb1 == 1);
    }

    // Mode B: D8_ONLY (THOR_BLOCK_MASK_BB_06004000)
    {
        thor_native_reset_stats();
        thor_native_set_block_mask(THOR_BLOCK_MASK_BB_06004000);

        ThorCpuRegs r0 = make_bb0_regs();
        uint32_t tgt = 0, cyc = 0;
        THOR_ASSERT(thor_native_dispatch_step(0x06004000u, &r0, &tgt, &cyc, &cb));
        THOR_ASSERT(tgt == 0x06004012u);

        ThorCpuRegs r1 = make_hit2_regs();
        THOR_ASSERT(!thor_native_dispatch_step(0x06004280u, &r1, &tgt, &cyc, &cb));

        uint64_t exec0 = 0, fb0 = 0, exec1 = 0, fb1 = 0;
        thor_native_get_block_stats(0x06004000u, &exec0, &fb0);
        thor_native_get_block_stats(0x06004280u, &exec1, &fb1);
        THOR_ASSERT(exec0 == 1 && fb0 == 0);
        THOR_ASSERT(exec1 == 0 && fb1 == 1);
    }

    // Mode C: D9_ONLY (THOR_BLOCK_MASK_BB_06004280)
    {
        thor_native_reset_stats();
        thor_native_set_block_mask(THOR_BLOCK_MASK_BB_06004280);

        ThorCpuRegs r0 = make_bb0_regs();
        uint32_t tgt = 0, cyc = 0;
        THOR_ASSERT(!thor_native_dispatch_step(0x06004000u, &r0, &tgt, &cyc, &cb));

        ThorCpuRegs r1 = make_hit2_regs();
        THOR_ASSERT(thor_native_dispatch_step(0x06004280u, &r1, &tgt, &cyc, &cb));
        THOR_ASSERT(tgt == 0x0600A0F8u);

        uint64_t exec0 = 0, fb0 = 0, exec1 = 0, fb1 = 0;
        thor_native_get_block_stats(0x06004000u, &exec0, &fb0);
        thor_native_get_block_stats(0x06004280u, &exec1, &fb1);
        THOR_ASSERT(exec0 == 0 && fb0 == 1);
        THOR_ASSERT(exec1 == 1 && fb1 == 0);
    }

    // Mode D: D8_PLUS_D9 (THOR_BLOCK_MASK_BB_06004000 | THOR_BLOCK_MASK_BB_06004280)
    {
        thor_native_reset_stats();
        thor_native_set_block_mask(THOR_BLOCK_MASK_BB_06004000 | THOR_BLOCK_MASK_BB_06004280);

        ThorCpuRegs r0 = make_bb0_regs();
        uint32_t tgt = 0, cyc = 0;
        THOR_ASSERT(thor_native_dispatch_step(0x06004000u, &r0, &tgt, &cyc, &cb));
        THOR_ASSERT(tgt == 0x06004012u);

        ThorCpuRegs r1 = make_hit2_regs();
        THOR_ASSERT(thor_native_dispatch_step(0x06004280u, &r1, &tgt, &cyc, &cb));
        THOR_ASSERT(tgt == 0x0600A0F8u);

        uint64_t exec0 = 0, fb0 = 0, exec1 = 0, fb1 = 0;
        thor_native_get_block_stats(0x06004000u, &exec0, &fb0);
        thor_native_get_block_stats(0x06004280u, &exec1, &fb1);
        THOR_ASSERT(exec0 == 1 && fb0 == 0);
        THOR_ASSERT(exec1 == 1 && fb1 == 0);
    }
}

static void test_indirect_negative_controls() {
    auto& dispatcher = thor::recomp::NativeDispatcher::instance();
    dispatcher.set_mode(THOR_NATIVE_MODE_NATIVE_OVERRIDE);
    dispatcher.set_block_mask(THOR_BLOCK_MASK_ALL);

    TestSaturnHardware hw;
    hw.setup_canonical_all_memory();

    // 1. Interpreter mode -> fallback
    {
        dispatcher.reset_stats();
        dispatcher.set_mode(THOR_NATIVE_MODE_INTERPRETER);
        ThorCpuRegs regs = make_hit2_regs();
        uint32_t tgt = 0, cyc = 0;
        auto cb = hw.make_callbacks();
        THOR_ASSERT(!dispatcher.dispatch_step(0x06004280u, regs, tgt, cyc, cb));
        THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
        dispatcher.set_mode(THOR_NATIVE_MODE_NATIVE_OVERRIDE);
    }

    // 2. Slave SH-2 active -> fallback
    {
        dispatcher.reset_stats();
        hw.slave_active = true;
        ThorCpuRegs regs = make_hit2_regs();
        uint32_t tgt = 0, cyc = 0;
        auto cb = hw.make_callbacks();
        THOR_ASSERT(!dispatcher.dispatch_step(0x06004280u, regs, tgt, cyc, cb));
        THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
        hw.slave_active = false;
    }

    // 3. DMA active -> fallback
    {
        dispatcher.reset_stats();
        hw.dma_active = true;
        ThorCpuRegs regs = make_hit2_regs();
        uint32_t tgt = 0, cyc = 0;
        auto cb = hw.make_callbacks();
        THOR_ASSERT(!dispatcher.dispatch_step(0x06004280u, regs, tgt, cyc, cb));
        THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
        hw.dma_active = false;
    }

    // 4. IRQ pending -> fallback
    {
        dispatcher.reset_stats();
        hw.irq_pending = true;
        ThorCpuRegs regs = make_hit2_regs();
        uint32_t tgt = 0, cyc = 0;
        auto cb = hw.make_callbacks();
        THOR_ASSERT(!dispatcher.dispatch_step(0x06004280u, regs, tgt, cyc, cb));
        THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
        hw.irq_pending = false;
    }

    // 5. Ineligible content -> fallback
    {
        dispatcher.reset_stats();
        dispatcher.inject_ineligible_content(true);
        ThorCpuRegs regs = make_hit2_regs();
        uint32_t tgt = 0, cyc = 0;
        auto cb = hw.make_callbacks();
        THOR_ASSERT(!dispatcher.dispatch_step(0x06004280u, regs, tgt, cyc, cb));
        THOR_ASSERT(dispatcher.get_stats().ineligible_count == 1);
        THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
        dispatcher.inject_ineligible_content(false);
    }

    // 6. Shadow divergence -> fallback
    {
        dispatcher.reset_stats();
        dispatcher.inject_forced_divergence(true);
        ThorCpuRegs regs = make_hit2_regs();
        uint32_t tgt = 0, cyc = 0;
        auto cb = hw.make_callbacks();
        THOR_ASSERT(!dispatcher.dispatch_step(0x06004280u, regs, tgt, cyc, cb));
        THOR_ASSERT(dispatcher.get_stats().shadow_divergence_count == 1);
        THOR_ASSERT(dispatcher.get_stats().fallback_count == 1);
        dispatcher.inject_forced_divergence(false);
    }
}

int main() {
    std::cout << "Running Native Indirect Dispatcher Verification Tests...\n";

    test_native_indirect_positive();
    std::cout << "  PASS: test_native_indirect_positive\n";

    test_dynamic_target_anti_hardcoding();
    std::cout << "  PASS: test_dynamic_target_anti_hardcoding\n";

    test_block_mask_gating();
    std::cout << "  PASS: test_block_mask_gating (A/B/C/D modes + stats)\n";

    test_indirect_negative_controls();
    std::cout << "  PASS: test_indirect_negative_controls (6 negative scenarios)\n";

    std::cout << "All Native Indirect Dispatcher tests passed successfully.\n";
    return 0;
}
