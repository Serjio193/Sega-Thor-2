#pragma once

#include <cstdint>
#include <vector>
#include <span>
#include "thor/hw/vdp1.hpp"
#include "thor/hw/vdp2.hpp"
#include "thor/hw/scsp.hpp"

namespace thor::hw {

inline constexpr uint32_t DEFAULT_SCREEN_WIDTH = 320;
inline constexpr uint32_t DEFAULT_SCREEN_HEIGHT = 224;

/// Complete Native Saturn Hardware Bridge.
/// Bridges host SH-2 execution to native VDP1, VDP2, and SCSP subsystems.
class NativeSaturnSystem {
public:
    NativeSaturnSystem();

    void reset() noexcept;

    // Subsystem accessors
    [[nodiscard]] Vdp1Engine& vdp1() noexcept { return vdp1_; }
    [[nodiscard]] const Vdp1Engine& vdp1() const noexcept { return vdp1_; }

    [[nodiscard]] Vdp2Engine& vdp2() noexcept { return vdp2_; }
    [[nodiscard]] const Vdp2Engine& vdp2() const noexcept { return vdp2_; }

    [[nodiscard]] ScspEngine& scsp() noexcept { return scsp_; }
    [[nodiscard]] const ScspEngine& scsp() const noexcept { return scsp_; }

    // Memory accessors
    [[nodiscard]] std::span<uint8_t> vdp1_vram() noexcept { return vdp1_vram_; }
    [[nodiscard]] std::span<const uint8_t> vdp1_vram() const noexcept { return vdp1_vram_; }

    [[nodiscard]] std::span<uint8_t> vdp2_vram() noexcept { return vdp2_vram_; }
    [[nodiscard]] std::span<const uint8_t> vdp2_vram() const noexcept { return vdp2_vram_; }

    [[nodiscard]] std::span<uint8_t> vdp2_cram() noexcept { return vdp2_cram_; }
    [[nodiscard]] std::span<const uint8_t> vdp2_cram() const noexcept { return vdp2_cram_; }

    [[nodiscard]] std::span<uint8_t> sound_ram() noexcept { return sound_ram_; }
    [[nodiscard]] std::span<const uint8_t> sound_ram() const noexcept { return sound_ram_; }

    // MMIO Read / Write dispatch (SH-2 to Saturn B-Bus / Peripherals)
    [[nodiscard]] bool write_mmio_u16(uint32_t address, uint16_t value) noexcept;
    [[nodiscard]] bool write_mmio_u32(uint32_t address, uint32_t value) noexcept;
    [[nodiscard]] uint16_t read_mmio_u16(uint32_t address) const noexcept;
    [[nodiscard]] uint32_t read_mmio_u32(uint32_t address) const noexcept;

    // Unified Native Frame Presentation
    // Renders VDP1 sprites, composites VDP2 planes, and produces a 320x224 RGBA8888 frame.
    void render_frame(
        std::span<uint32_t> framebuffer_out,
        uint32_t width = DEFAULT_SCREEN_WIDTH,
        uint32_t height = DEFAULT_SCREEN_HEIGHT) noexcept;

    // Native Audio Synthesis
    // Renders PCM16 stereo interleaved samples (L, R, L, R...) from active SCSP slots.
    void render_audio(
        std::span<int16_t> pcm_out,
        size_t sample_frames) noexcept;

private:
    Vdp1Engine vdp1_{};
    Vdp2Engine vdp2_{};
    ScspEngine scsp_{};

    std::vector<uint8_t> vdp1_vram_{};
    std::vector<uint8_t> vdp2_vram_{};
    std::vector<uint8_t> vdp2_cram_{};
    std::vector<uint8_t> sound_ram_{};
    uint16_t vdp2_tvmd_ = 0;
};

} // namespace thor::hw
