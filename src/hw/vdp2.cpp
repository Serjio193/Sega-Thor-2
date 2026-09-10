#include "thor/hw/vdp2.hpp"
#include <algorithm>

namespace thor::hw {

const char* vdp2_plane_type_to_string(Vdp2PlaneType type) noexcept {
    switch (type) {
    case Vdp2PlaneType::NBG0:         return "NBG0";
    case Vdp2PlaneType::NBG1:         return "NBG1";
    case Vdp2PlaneType::NBG2:         return "NBG2";
    case Vdp2PlaneType::NBG3:         return "NBG3";
    case Vdp2PlaneType::RBG0:         return "RBG0";
    case Vdp2PlaneType::SPRITE_PLANE: return "SPRITE_PLANE";
    case Vdp2PlaneType::BACK_PLANE:   return "BACK_PLANE";
    default:                          return "UNKNOWN";
    }
}

const char* vdp2_cram_mode_to_string(Vdp2CramMode mode) noexcept {
    switch (mode) {
    case Vdp2CramMode::MODE_0_1024_15B: return "MODE_0_1024_15B";
    case Vdp2CramMode::MODE_1_2048_15B: return "MODE_1_2048_15B";
    case Vdp2CramMode::MODE_2_1024_24B: return "MODE_2_1024_24B";
    default:                            return "UNKNOWN";
    }
}

Vdp2Engine::Vdp2Engine() noexcept {
    reset();
}

void Vdp2Engine::reset() noexcept {
    for (size_t i = 0; i < planes_.size(); ++i) {
        planes_[i] = Vdp2PlaneConfig{};
    }
    planes_[static_cast<size_t>(Vdp2PlaneType::BACK_PLANE)].enabled = true;
    planes_[static_cast<size_t>(Vdp2PlaneType::BACK_PLANE)].priority = 0;

    rbg0_matrix_ = Vdp2RotationMatrix{};
    cram_mode_ = Vdp2CramMode::MODE_0_1024_15B;
    back_color_ = Vdp2Rgba{0, 0, 0, 255};
}

void Vdp2Engine::set_plane_config(Vdp2PlaneType plane, const Vdp2PlaneConfig& config) noexcept {
    const size_t idx = static_cast<size_t>(plane);
    if (idx < planes_.size()) {
        planes_[idx] = config;
    }
}

const Vdp2PlaneConfig& Vdp2Engine::plane_config(Vdp2PlaneType plane) const noexcept {
    const size_t idx = static_cast<size_t>(plane);
    if (idx < planes_.size()) {
        return planes_[idx];
    }
    static const Vdp2PlaneConfig g_default_plane;
    return g_default_plane;
}

Vdp2Rgba Vdp2Engine::decode_bgr555(uint16_t bgr) noexcept {
    const uint8_t r5 = static_cast<uint8_t>(bgr & 0x001Fu);
    const uint8_t g5 = static_cast<uint8_t>((bgr >> 5) & 0x001Fu);
    const uint8_t b5 = static_cast<uint8_t>((bgr >> 10) & 0x001Fu);

    return Vdp2Rgba{
        static_cast<uint8_t>((r5 << 3) | (r5 >> 2)),
        static_cast<uint8_t>((g5 << 3) | (g5 >> 2)),
        static_cast<uint8_t>((b5 << 3) | (b5 >> 2)),
        255
    };
}

Vdp2Rgba Vdp2Engine::decode_rgb888(uint32_t rgb) noexcept {
    return Vdp2Rgba{
        static_cast<uint8_t>((rgb >> 16) & 0xFFu),
        static_cast<uint8_t>((rgb >> 8) & 0xFFu),
        static_cast<uint8_t>(rgb & 0xFFu),
        255
    };
}

Vdp2Rgba Vdp2Engine::decode_cram(
    std::span<const uint8_t> cram,
    uint32_t color_index) const noexcept {

    if (cram_mode_ == Vdp2CramMode::MODE_2_1024_24B) {
        const uint32_t offset = (color_index * 4) & (VDP2_CRAM_SIZE - 4);
        if (offset + 4 > cram.size()) return back_color_;
        const uint32_t rgb = (static_cast<uint32_t>(cram[offset + 0]) << 16) |
                             (static_cast<uint32_t>(cram[offset + 1]) << 8)  |
                              static_cast<uint32_t>(cram[offset + 2]);
        return decode_rgb888(rgb);
    } else {
        const uint32_t offset = (color_index * 2) & (VDP2_CRAM_SIZE - 2);
        if (offset + 2 > cram.size()) return back_color_;
        const uint16_t bgr = static_cast<uint16_t>(
            (static_cast<uint16_t>(cram[offset + 0]) << 8) | cram[offset + 1]);
        return decode_bgr555(bgr);
    }
}

std::pair<int32_t, int32_t> Vdp2Engine::transform_rbg0(
    int32_t screen_x,
    int32_t screen_y) const noexcept {

    const int64_t dx = screen_x - rbg0_matrix_.cx;
    const int64_t dy = screen_y - rbg0_matrix_.cy;

    const int64_t tx0 = (static_cast<int64_t>(rbg0_matrix_.a) * dx) + (static_cast<int64_t>(rbg0_matrix_.b) * dy);
    const int64_t ty0 = (static_cast<int64_t>(rbg0_matrix_.c) * dx) + (static_cast<int64_t>(rbg0_matrix_.d) * dy);

    const int32_t rx = static_cast<int32_t>((tx0 >> 16) + rbg0_matrix_.cx);
    const int32_t ry = static_cast<int32_t>((ty0 >> 16) + rbg0_matrix_.cy);

    return {rx, ry};
}

Vdp2Rgba Vdp2Engine::arbitrate_pixel(
    const std::array<Vdp2Rgba, static_cast<size_t>(Vdp2PlaneType::COUNT)>& inputs) const noexcept {

    int16_t top_prio = -1;
    size_t top_plane_idx = static_cast<size_t>(Vdp2PlaneType::COUNT);

    for (size_t i = 0; i < planes_.size(); ++i) {
        if (!planes_[i].enabled) continue;
        if (inputs[i].a == 0) continue;

        const int16_t p = planes_[i].priority;
        if (p > top_prio) {
            top_prio = p;
            top_plane_idx = i;
        }
    }

    if (top_plane_idx == static_cast<size_t>(Vdp2PlaneType::COUNT)) {
        return back_color_;
    }

    const Vdp2Rgba top_pixel = inputs[top_plane_idx];
    const Vdp2PlaneConfig& top_cfg = planes_[top_plane_idx];

    if (!top_cfg.color_calc_enable) {
        return top_pixel;
    }

    int16_t sec_prio = -1;
    size_t sec_plane_idx = static_cast<size_t>(Vdp2PlaneType::COUNT);
    for (size_t i = 0; i < planes_.size(); ++i) {
        if (i == top_plane_idx) continue;
        if (!planes_[i].enabled) continue;
        if (inputs[i].a == 0) continue;

        const int16_t p = planes_[i].priority;
        if (p > sec_prio && p <= top_prio) {
            sec_prio = p;
            sec_plane_idx = i;
        }
    }

    if (sec_plane_idx == static_cast<size_t>(Vdp2PlaneType::COUNT)) {
        return top_pixel;
    }

    const Vdp2Rgba sec_pixel = inputs[sec_plane_idx];
    const uint32_t ratio = std::min<uint32_t>(32u, static_cast<uint32_t>(top_cfg.color_calc_ratio));
    const uint32_t inv_ratio = 32u - ratio;

    const uint8_t r = static_cast<uint8_t>(std::min(255u, (top_pixel.r * ratio + sec_pixel.r * inv_ratio) / 32u));
    const uint8_t g = static_cast<uint8_t>(std::min(255u, (top_pixel.g * ratio + sec_pixel.g * inv_ratio) / 32u));
    const uint8_t b = static_cast<uint8_t>(std::min(255u, (top_pixel.b * ratio + sec_pixel.b * inv_ratio) / 32u));

    return Vdp2Rgba{r, g, b, 255};
}

} // namespace thor::hw
