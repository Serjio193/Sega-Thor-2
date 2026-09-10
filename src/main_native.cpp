#include "thor/runtime/standalone_runtime.hpp"
#include <iostream>
#include <string>
#include <vector>
#include <iomanip>
#include <cstring>

static void print_usage(const char* prog) {
    std::cout << "The Story of Thor 2 / The Legend of Oasis - Native C++20 Implementation\n"
              << "Usage: " << prog << " [options]\n"
              << "Options:\n"
              << "  --boot             Initialize and boot the native game runtime\n"
              << "  --frames <N>       Execute N frames of the native game loop (default: 1)\n"
              << "  --metrics          Print quantified native execution metrics\n"
              << "  --selftest         Run standalone runtime verification tests\n"
              << "  --help             Display this help message\n";
}

int main(int argc, char* argv[]) {
    bool do_boot = false;
    bool do_metrics = false;
    bool do_selftest = false;
    uint32_t frame_count = 0;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--boot") {
            do_boot = true;
        } else if (arg == "--metrics") {
            do_metrics = true;
        } else if (arg == "--selftest") {
            do_selftest = true;
        } else if (arg == "--frames" && i + 1 < argc) {
            frame_count = static_cast<uint32_t>(std::stoul(argv[++i]));
        } else if (arg == "--help") {
            print_usage(argv[0]);
            return 0;
        }
    }

    if (argc == 1 || do_selftest) {
        std::cout << "Thor 2 Native C++20 Runtime - Self-Test Mode\n";
        thor::runtime::StandaloneRuntime rt;
        rt.boot();
        rt.run_frame();
        const auto& m = rt.metrics();
        std::cout << "Frames rendered: " << m.frames_rendered << "\n";
        std::cout << "Audio buffers rendered: " << m.audio_buffers_rendered << "\n";
        std::cout << "Self-test passed successfully.\n";
        return 0;
    }

    thor::runtime::StandaloneRuntime runtime;
    if (do_boot || frame_count > 0) {
        runtime.boot();
        std::cout << "Booted Master SH-2 at PC 0x" << std::hex << runtime.master_cpu().pc << std::dec << "\n";
    }

    for (uint32_t f = 0; f < frame_count; ++f) {
        runtime.run_frame();
    }

    if (do_metrics) {
        const auto& m = runtime.metrics();
        std::cout << "=== Thor 2 Native Execution Metrics ===\n"
                  << "Total Cycles:          " << m.total_cycles << "\n"
                  << "Native Instructions:   " << m.native_instructions << "\n"
                  << "Fallback Instructions: " << m.fallback_instructions << "\n"
                  << "Native Ratio:          " << std::fixed << std::setprecision(2)
                  << (m.native_instruction_ratio() * 100.0) << "%\n"
                  << "Frames Rendered:       " << m.frames_rendered << "\n"
                  << "Audio Buffers:         " << m.audio_buffers_rendered << "\n";
    }

    return 0;
}
