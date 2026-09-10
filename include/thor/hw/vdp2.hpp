#pragma once

#include <cstdint>
#include <array>
#include <span>
#include <utility>
#include "thor/hw/vdp2_types.hpp"

namespace thor::hw {

inline constexpr uint32_t VDP2_VRAM_SIZE = 0x80000; // 512 KB
inline constexpr uint32_t VDP2_CRAM_SIZE = 0x1000;  // 4 KB

class Vdp2Engine {
public:
    Vdp2Engine() noexcept;

    void reset() noexcept;

    void set_plane_config(Vdp2PlaneType plane, const Vdp2PlaneConfig& config) noexcept;
    [[nodiscard]] const Vdp2PlaneConfig& plane_config(Vdp2PlaneType plane) const noexcept;

    void set_rbg0_matrix(const Vdp2RotationMatrix& matrix) noexcept { rbg0_matrix_ = matrix; }
    [[nodiscard]] const Vdp2RotationMatrix& rbg0_matrix() const noexcept { return rbg0_matrix_; }

    void set_cram_mode(Vdp2CramMode mode) noexcept { cram_mode_ = mode; }
    [[nodiscard]] Vdp2CramMode cram_mode() const noexcept { return cram_mode_; }

    [[nodiscard]] static Vdp2Rgba decode_bgr555(uint16_t bgr) noexcept;
    [[nodiscard]] static Vdp2Rgba decode_rgb888(uint32_t rgb) noexcept;

    [[nodiscard]] Vdp2Rgba decode_cram(
        std::span<const uint8_t> cram,
        uint32_t color_index) const noexcept;

    [[nodiscard]] std::pair<int32_t, int32_t> transform_rbg0(
        int32_t screen_x,
        int32_t screen_y) const noexcept;

    [[nodiscard]] Vdp2Rgba arbitrate_pixel(
        const std::array<Vdp2Rgba, static_cast<size_t>(Vdp2PlaneType::COUNT)>& inputs) const noexcept;

private:
    std::array<Vdp2PlaneConfig, static_cast<size_t>(Vdp2PlaneType::COUNT)> planes_{};
    Vdp2RotationMatrix rbg0_matrix_{};
    Vdp2CramMode cram_mode_ = Vdp2CramMode::MODE_0_1024_15B;
    Vdp2Rgba back_color_{0, 0, 0, 255};
};

} // namespace thor::hw
