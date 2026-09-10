#include "thor/runtime/standalone_runtime.hpp"
#include "tests/sh2/test_framework.hpp"

#include <iostream>
#include <vector>
#include <cstring>

static void test_runtime_init() {
    thor::runtime::StandaloneRuntime rt;
    rt.boot();

    THOR_ASSERT(rt.master_cpu().pc == 0x06004000u);
    THOR_ASSERT(rt.master_cpu().r[15] == 0x06001000u);
    THOR_ASSERT(rt.master_cpu().sr == 0x00000001u);
    THOR_ASSERT(rt.framebuffer().size() == 320 * 224);
    THOR_ASSERT(rt.audio_buffer().size() == 735 * 2);
    THOR_ASSERT(rt.metrics().total_cycles == 0);
    THOR_ASSERT(rt.metrics().native_instructions == 0);
    THOR_ASSERT(!rt.metrics().has_measured_dependency_reduction());
}

static void test_runtime_memory_and_modules() {
    thor::runtime::StandaloneRuntime rt;
    const uint8_t test_data[] = { 0x12, 0x34, 0x56, 0x78 };

    // Load into High Work RAM
    bool loaded = rt.load_module(0x06004000u, test_data, sizeof(test_data));
    THOR_ASSERT(loaded);
    THOR_ASSERT(rt.read8(0x06004000u) == 0x12);
    THOR_ASSERT(rt.read8(0x06004001u) == 0x34);
    THOR_ASSERT(rt.read16(0x06004000u) == 0x1234);
    THOR_ASSERT(rt.read32(0x06004000u) == 0x12345678);

    // Load into Low Work RAM
    bool loaded_low = rt.load_module(0x002DA000u, test_data, sizeof(test_data));
    THOR_ASSERT(loaded_low);
    THOR_ASSERT(rt.read32(0x002DA000u) == 0x12345678);

    // Write tests
    rt.write8(0x06005000u, 0xAB);
    THOR_ASSERT(rt.read8(0x06005000u) == 0xAB);

    rt.write16(0x06005002u, 0xCDEF);
    THOR_ASSERT(rt.read16(0x06005002u) == 0xCDEF);

    rt.write32(0x06005004u, 0xDEADBEEF);
    THOR_ASSERT(rt.read32(0x06005004u) == 0xDEADBEEF);
}

static void test_runtime_mmio_dispatch() {
    thor::runtime::StandaloneRuntime rt;

    // Write to VDP1 VRAM via MMIO (0x05D00000)
    rt.write32(0x05D00000u, 0x12345678);
    THOR_ASSERT(rt.read32(0x05D00000u) == 0x12345678);

    // Write to VDP2 TVMD register (0x05E00000)
    rt.write16(0x05E00000u, 0x8000);
    THOR_ASSERT(rt.read16(0x05E00000u) == 0x8000);

    // Write to SCSP Sound RAM (0x05A00000)
    rt.write8(0x05A00010u, 0x55);
    THOR_ASSERT(rt.read8(0x05A00010u) == 0x55);
}

static void test_runtime_native_block_execution() {
    thor::runtime::StandaloneRuntime rt;
    rt.boot();

    // Populate memory for canonical bb_06004000
    const uint8_t startup_code[] = {
        0x66, 0x11, // MOV.W @R1, R6
        0x6F, 0x03, // MOV R0, R15
        0xD4, 0x17, // MOV.L @(0x5C, PC), R4
        0x64, 0x42, // MOV.L @R4, R4
        0xA0, 0x03, // BRA 0x06004012
        0x00, 0x09  // NOP
    };
    bool loaded = rt.load_module(0x06004000u, startup_code, sizeof(startup_code));
    THOR_ASSERT(loaded);

    // Write PC-relative constant pool target at 0x06004064 -> 0x06081C10
    rt.write32(0x06004064u, 0x06081C10u);
    // Write value at 0x06081C10 -> 0x060917DC
    rt.write32(0x06081C10u, 0x060917DCu);

    // Execute step: should hit native block bb_06004000!
    bool step_ok = rt.step();
    THOR_ASSERT(step_ok);

    // Target PC must be 0x06004012
    THOR_ASSERT(rt.master_cpu().pc == 0x06004012u);
    THOR_ASSERT(rt.master_cpu().r[6] == 0x00006611u);
    THOR_ASSERT(rt.master_cpu().r[15] == 0x06002EDCu);
    THOR_ASSERT(rt.master_cpu().r[4] == 0x060917DCu);

    // Verify quantified metrics
    const auto& m = rt.metrics();
    THOR_ASSERT(m.native_instructions == 6);
    THOR_ASSERT(m.native_cycles == 27);
    THOR_ASSERT(m.total_cycles == 27);
    THOR_ASSERT(m.has_measured_dependency_reduction());
    THOR_ASSERT(m.native_instruction_ratio() == 1.0);
}

static void test_runtime_fallback_interpreter() {
    thor::runtime::StandaloneRuntime rt;
    rt.boot();

    // Set PC to an uncompiled address and write NOP (0x0009)
    rt.master_cpu().pc = 0x06005000u;
    rt.write16(0x06005000u, 0x0009u);

    bool step_ok = rt.step();
    THOR_ASSERT(step_ok);
    THOR_ASSERT(rt.master_cpu().pc == 0x06005002u);
    THOR_ASSERT(rt.metrics().fallback_instructions == 1);
    THOR_ASSERT(rt.metrics().fallback_cycles >= 1);
}

static void test_runtime_frame_and_audio() {
    thor::runtime::StandaloneRuntime rt;
    rt.boot();

    rt.run_frame();
    THOR_ASSERT(rt.metrics().frames_rendered == 1);
    THOR_ASSERT(rt.metrics().audio_buffers_rendered == 1);
    THOR_ASSERT(rt.framebuffer().size() == 320 * 224);
    THOR_ASSERT(rt.audio_buffer().size() == 735 * 2);
}

int main() {
    std::cout << "[TEST] Running D17 Standalone Runtime test suite...\n";
    test_runtime_init();
    test_runtime_memory_and_modules();
    test_runtime_mmio_dispatch();
    test_runtime_native_block_execution();
    test_runtime_fallback_interpreter();
    test_runtime_frame_and_audio();
    std::cout << "[TEST] D17 Standalone Runtime Tests PASSED.\n";
    return 0;
}
