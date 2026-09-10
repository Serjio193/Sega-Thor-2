#pragma once

#include <cstdint>
#include <string>

namespace thor::hw {

enum class Vdp2PlaneType : uint8_t {
    NBG0 = 0,
    NBG1,
    NBG2,
    NBG3,
    RBG0,
    SPRITE_PLANE,
    BACK_PLANE,
    COUNT
};

enum class Vdp2CramMode : uint8_t {
    MODE_0_1024_15B = 0,
    MODE_1_2048_15B = 1,
    MODE_2_1024_24B = 2
};

enum class Vdp2ColorFormat : uint8_t {
    PALETTE_16 = 0,
    PALETTE_256,
    PALETTE_2048,
    RGB_32K,
    RGB_16M
};

struct Vdp2PlaneConfig {
    bool enabled = false;
    uint8_t priority = 0; // 0 (hidden) .. 7 (top)
    int32_t scroll_x = 0;
    int32_t scroll_y = 0;
    bool color_calc_enable = false;
    uint8_t color_calc_ratio = 16; // 0..31
    Vdp2ColorFormat color_format = Vdp2ColorFormat::PALETTE_256;
};

struct Vdp2RotationMatrix {
    int32_t a = 0x00010000; // 1.0 fixed-point 16.16
    int32_t b = 0;
    int32_t c = 0;
    int32_t d = 0x00010000; // 1.0
    int32_t cx = 0;
    int32_t cy = 0;
};

struct Vdp2Rgba {
    uint8_t r = 0;
    uint8_t g = 0;
    uint8_t b = 0;
    uint8_t a = 255;

    [[nodiscard]] constexpr uint32_t to_u32() const noexcept {
        return (static_cast<uint32_t>(a) << 24) |
               (static_cast<uint32_t>(b) << 16) |
               (static_cast<uint32_t>(g) << 8)  |
               static_cast<uint32_t>(r);
    }
};

[[nodiscard]] const char* vdp2_plane_type_to_string(Vdp2PlaneType type) noexcept;
[[nodiscard]] const char* vdp2_cram_mode_to_string(Vdp2CramMode mode) noexcept;

} // namespace thor::hw
