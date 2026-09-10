#pragma once

#include <cstdint>
#include <cstddef>
#include <vector>
#include <string>
#include <span>
#include <optional>
#include <memory>
#include "thor/sh2/sh2_state.hpp"
#include "thor/sh2/sh2_memory.hpp"
#include "thor/hw/native_system.hpp"
#include "thor/recomp/native_dispatcher.hpp"

namespace thor::runtime {

struct RuntimeMetrics {
    uint64_t total_cycles = 0;
    uint64_t native_cycles = 0;
    uint64_t fallback_cycles = 0;
    uint64_t native_instructions = 0;
    uint64_t fallback_instructions = 0;
    uint32_t frames_rendered = 0;
    uint32_t audio_buffers_rendered = 0;

    [[nodiscard]] double native_instruction_ratio() const noexcept {
        uint64_t total = native_instructions + fallback_instructions;
        return (total == 0) ? 0.0 : static_cast<double>(native_instructions) / static_cast<double>(total);
    }

    [[nodiscard]] bool has_measured_dependency_reduction() const noexcept {
        return native_instructions > 0;
    }
};

class StandaloneRuntime : public thor::sh2::ISh2Memory {
public:
    StandaloneRuntime();
    ~StandaloneRuntime() override = default;

    void boot();
    bool load_module(uint32_t vma, const uint8_t* data, size_t size);

    // ISh2Memory overrides
    uint8_t read8(uint32_t addr) override;
    uint16_t read16(uint32_t addr) override;
    uint32_t read32(uint32_t addr) override;
    [[nodiscard]] uint8_t peek8(uint32_t addr) const override;
    void write8(uint32_t addr, uint8_t val) override;
    void write16(uint32_t addr, uint16_t val) override;
    void write32(uint32_t addr, uint32_t val) override;

    // Execution control
    bool step();
    uint32_t run_cycles(uint32_t max_cycles);
    void run_frame();

    // Subsystems
    [[nodiscard]] thor::sh2::Sh2CpuState& master_cpu() noexcept { return master_cpu_; }
    [[nodiscard]] const thor::sh2::Sh2CpuState& master_cpu() const noexcept { return master_cpu_; }
    [[nodiscard]] thor::hw::NativeSaturnSystem& native_system() noexcept { return native_system_; }
    [[nodiscard]] const thor::hw::NativeSaturnSystem& native_system() const noexcept { return native_system_; }
    [[nodiscard]] const RuntimeMetrics& metrics() const noexcept { return metrics_; }

    [[nodiscard]] const std::vector<uint32_t>& framebuffer() const noexcept { return framebuffer_; }
    [[nodiscard]] const std::vector<int16_t>& audio_buffer() const noexcept { return audio_buffer_; }

private:
    [[nodiscard]] bool is_high_work_ram(uint32_t addr) const noexcept;
    [[nodiscard]] bool is_low_work_ram(uint32_t addr) const noexcept;
    [[nodiscard]] bool is_hardware_mmio(uint32_t addr) const noexcept;

    std::vector<uint8_t> high_work_ram_;
    std::vector<uint8_t> low_work_ram_;
    thor::sh2::Sh2CpuState master_cpu_{};
    thor::hw::NativeSaturnSystem native_system_{};
    thor::recomp::NativeDispatcher native_dispatcher_{};
    RuntimeMetrics metrics_{};
    std::vector<uint32_t> framebuffer_;
    std::vector<int16_t> audio_buffer_;
};

} // namespace thor::runtime
