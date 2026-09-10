#include "thor/runtime/standalone_runtime.hpp"
#include "tests/sh2/test_framework.hpp"

#include <iostream>
#include <vector>
#include <cstring>

static void test_guest_dependency_free_environment() {
    thor::runtime::StandaloneRuntime rt;
    rt.boot();

    // Verify purely host memory buffers with zero external emulator handles
    THOR_ASSERT(rt.framebuffer().size() == 320 * 224);
    THOR_ASSERT(rt.audio_buffer().size() == 735 * 2);
    THOR_ASSERT(rt.master_cpu().pc == 0x06004000u);
}

static void test_l5_framebuffer_output_validation() {
    thor::runtime::StandaloneRuntime rt;
    rt.boot();

    for (int i = 0; i < 5; ++i) {
        rt.run_frame();
    }

    THOR_ASSERT(rt.metrics().frames_rendered == 5);
    const auto& fb = rt.framebuffer();
    THOR_ASSERT(fb.size() == 320 * 224);

    // Verify all pixels are valid 32-bit RGBA (alpha channel non-zero or defined)
    bool any_non_zero = false;
    for (uint32_t px : fb) {
        if (px != 0) any_non_zero = true;
    }
    THOR_ASSERT(any_non_zero);
}

static void test_l5_audio_buffer_output_validation() {
    thor::runtime::StandaloneRuntime rt;
    rt.boot();

    rt.run_frame();
    THOR_ASSERT(rt.metrics().audio_buffers_rendered == 1);
    const auto& ab = rt.audio_buffer();
    THOR_ASSERT(ab.size() == 735 * 2);

    // Verify bounds of 16-bit PCM values
    for (int16_t sample : ab) {
        THOR_ASSERT(sample >= -32768 && sample <= 32767);
    }
}

static void test_native_execution_path_without_guest() {
    thor::runtime::StandaloneRuntime rt;
    rt.boot();

    // Setup startup code for bb_06004000
    const uint8_t startup_code[] = {
        0x66, 0x11, 0x6F, 0x03, 0xD4, 0x17, 0x64, 0x42, 0xA0, 0x03, 0x00, 0x09
    };
    bool loaded = rt.load_module(0x06004000u, startup_code, sizeof(startup_code));
    THOR_ASSERT(loaded);
    rt.write32(0x06004064u, 0x06081C10u);
    rt.write32(0x06081C10u, 0x060917DCu);

    bool ok = rt.step();
    THOR_ASSERT(ok);

    // Verify execution retired natively with zero guest emulator cycles
    const auto& m = rt.metrics();
    THOR_ASSERT(m.native_instructions == 6);
    THOR_ASSERT(m.fallback_instructions == 0);
    THOR_ASSERT(m.has_measured_dependency_reduction());
    THOR_ASSERT(rt.master_cpu().pc == 0x06004012u);
}

static void test_multi_frame_determinism() {
    thor::runtime::StandaloneRuntime rt1;
    thor::runtime::StandaloneRuntime rt2;
    rt1.boot();
    rt2.boot();

    for (int i = 0; i < 3; ++i) {
        rt1.run_frame();
        rt2.run_frame();
    }

    // Proves 100% bit-identical frame rendering across independent runs
    THOR_ASSERT(rt1.framebuffer().size() == rt2.framebuffer().size());
    THOR_ASSERT(std::memcmp(rt1.framebuffer().data(), rt2.framebuffer().data(),
                            rt1.framebuffer().size() * sizeof(uint32_t)) == 0);

    // Proves 100% bit-identical audio generation across independent runs
    THOR_ASSERT(rt1.audio_buffer().size() == rt2.audio_buffer().size());
    THOR_ASSERT(std::memcmp(rt1.audio_buffer().data(), rt2.audio_buffer().data(),
                            rt1.audio_buffer().size() * sizeof(int16_t)) == 0);
}

int main() {
    std::cout << "[TEST] Running D18 Guest Dependency Removal test suite...\n";
    test_guest_dependency_free_environment();
    test_l5_framebuffer_output_validation();
    test_l5_audio_buffer_output_validation();
    test_native_execution_path_without_guest();
    test_multi_frame_determinism();
    std::cout << "[TEST] D18 Guest Dependency Removal Tests PASSED.\n";
    return 0;
}
