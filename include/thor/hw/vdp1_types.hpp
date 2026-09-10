#pragma once

#include <cstdint>
#include <string>

namespace thor::hw {

enum class Vdp1CommandType : uint8_t {
    NORMAL_SPRITE    = 0x0,
    SCALED_SPRITE    = 0x1,
    DISTORTED_SPRITE = 0x2,
    POLYGON          = 0x4,
    POLYLINE         = 0x5,
    LINE             = 0x6,
    USER_CLIPPING    = 0x8,
    SYSTEM_CLIPPING  = 0x9,
    LOCAL_COORDINATE = 0xA,
    END_MARKER       = 0xF,
    INVALID          = 0xFF
};

enum class Vdp1JumpMode : uint8_t {
    JUMP_NEXT   = 0x0,
    JUMP_ASSIGN = 0x1,
    JUMP_CALL   = 0x2,
    JUMP_RETURN = 0x3,
    JUMP_SKIP   = 0x4,
    INVALID     = 0xFF
};

enum class Vdp1ColorMode : uint8_t {
    COLOR_BANK_16  = 0x0,
    LOOKUP_16      = 0x1,
    COLOR_BANK_64  = 0x2,
    COLOR_BANK_128 = 0x3,
    COLOR_BANK_256 = 0x4,
    RGB_32K        = 0x5,
    INVALID        = 0xFF
};

struct Vdp1Vertex {
    int16_t x = 0;
    int16_t y = 0;
};

struct Vdp1DrawMode {
    bool end_code_disable = false;
    bool transparent_disable = false;
    bool gouraud_shading = false;
    bool mesh = false;
    uint8_t color_calculation = 0; // 0=Replace, 1=Cannot, 2=Half-luminance, 3=Half-transparency, 4=Gouraud
};

struct Vdp1Command {
    uint32_t vram_offset = 0;
    Vdp1CommandType command_type = Vdp1CommandType::INVALID;
    Vdp1JumpMode jump_mode = Vdp1JumpMode::JUMP_NEXT;
    uint32_t next_link_offset = 0;
    Vdp1DrawMode draw_mode{};
    Vdp1ColorMode color_mode = Vdp1ColorMode::COLOR_BANK_16;
    uint16_t color_data = 0;
    uint32_t char_address = 0;
    uint16_t char_width = 0;
    uint16_t char_height = 0;
    Vdp1Vertex vertices[4]{};
    uint32_t gouraud_address = 0;
    bool is_end = false;
};

struct Vdp1ClippingRect {
    int16_t min_x = 0;
    int16_t min_y = 0;
    int16_t max_x = 319;
    int16_t max_y = 223;
};

[[nodiscard]] const char* vdp1_command_type_to_string(Vdp1CommandType type) noexcept;
[[nodiscard]] const char* vdp1_jump_mode_to_string(Vdp1JumpMode mode) noexcept;
[[nodiscard]] const char* vdp1_color_mode_to_string(Vdp1ColorMode mode) noexcept;

} // namespace thor::hw
