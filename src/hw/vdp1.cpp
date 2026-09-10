#include "thor/hw/vdp1.hpp"

namespace thor::hw {

const char* vdp1_command_type_to_string(Vdp1CommandType type) noexcept {
    switch (type) {
    case Vdp1CommandType::NORMAL_SPRITE:    return "NORMAL_SPRITE";
    case Vdp1CommandType::SCALED_SPRITE:    return "SCALED_SPRITE";
    case Vdp1CommandType::DISTORTED_SPRITE: return "DISTORTED_SPRITE";
    case Vdp1CommandType::POLYGON:          return "POLYGON";
    case Vdp1CommandType::POLYLINE:         return "POLYLINE";
    case Vdp1CommandType::LINE:             return "LINE";
    case Vdp1CommandType::USER_CLIPPING:    return "USER_CLIPPING";
    case Vdp1CommandType::SYSTEM_CLIPPING:  return "SYSTEM_CLIPPING";
    case Vdp1CommandType::LOCAL_COORDINATE: return "LOCAL_COORDINATE";
    case Vdp1CommandType::END_MARKER:       return "END_MARKER";
    default:                                return "INVALID";
    }
}

const char* vdp1_jump_mode_to_string(Vdp1JumpMode mode) noexcept {
    switch (mode) {
    case Vdp1JumpMode::JUMP_NEXT:   return "JUMP_NEXT";
    case Vdp1JumpMode::JUMP_ASSIGN: return "JUMP_ASSIGN";
    case Vdp1JumpMode::JUMP_CALL:   return "JUMP_CALL";
    case Vdp1JumpMode::JUMP_RETURN: return "JUMP_RETURN";
    case Vdp1JumpMode::JUMP_SKIP:   return "JUMP_SKIP";
    default:                        return "INVALID";
    }
}

const char* vdp1_color_mode_to_string(Vdp1ColorMode mode) noexcept {
    switch (mode) {
    case Vdp1ColorMode::COLOR_BANK_16:  return "COLOR_BANK_16";
    case Vdp1ColorMode::LOOKUP_16:      return "LOOKUP_16";
    case Vdp1ColorMode::COLOR_BANK_64:  return "COLOR_BANK_64";
    case Vdp1ColorMode::COLOR_BANK_128: return "COLOR_BANK_128";
    case Vdp1ColorMode::COLOR_BANK_256: return "COLOR_BANK_256";
    case Vdp1ColorMode::RGB_32K:        return "RGB_32K";
    default:                            return "INVALID";
    }
}

static inline uint16_t read_u16_be(const uint8_t* p) noexcept {
    return static_cast<uint16_t>((static_cast<uint16_t>(p[0]) << 8) | p[1]);
}

static inline int16_t read_i16_be(const uint8_t* p) noexcept {
    return static_cast<int16_t>(read_u16_be(p));
}

Vdp1Engine::Vdp1Engine() noexcept {
    reset();
}

void Vdp1Engine::reset() noexcept {
    user_clip_ = {0, 0, 319, 223};
    system_clip_ = {0, 0, 319, 223};
    local_coord_ = {0, 0};
    tvmr_ = 0;
    fbcr_ = 0;
    ptmr_ = 0;
    edsr_ = 0x0002;
    call_stack_depth_ = 0;
}

Vdp1Command Vdp1Engine::parse_command(
    std::span<const uint8_t> vram,
    uint32_t offset) noexcept {

    Vdp1Command cmd{};
    cmd.vram_offset = offset;

    if (offset + 32 > vram.size()) {
        cmd.command_type = Vdp1CommandType::INVALID;
        return cmd;
    }

    const uint8_t* p = vram.data() + offset;
    const uint16_t cmdctrl = read_u16_be(p + 0);
    const uint16_t cmdlink = read_u16_be(p + 2);
    const uint16_t cmdpmod = read_u16_be(p + 4);
    const uint16_t cmdcolr = read_u16_be(p + 6);
    const uint16_t cmdsrca = read_u16_be(p + 8);
    const uint16_t cmdsize = read_u16_be(p + 10);

    cmd.is_end = (cmdctrl & 0x8000u) != 0;
    const uint8_t raw_type = static_cast<uint8_t>(cmdctrl & 0x000Fu);
    switch (raw_type) {
    case 0x0: cmd.command_type = Vdp1CommandType::NORMAL_SPRITE; break;
    case 0x1: cmd.command_type = Vdp1CommandType::SCALED_SPRITE; break;
    case 0x2: cmd.command_type = Vdp1CommandType::DISTORTED_SPRITE; break;
    case 0x4: cmd.command_type = Vdp1CommandType::POLYGON; break;
    case 0x5: cmd.command_type = Vdp1CommandType::POLYLINE; break;
    case 0x6: cmd.command_type = Vdp1CommandType::LINE; break;
    case 0x8: cmd.command_type = Vdp1CommandType::USER_CLIPPING; break;
    case 0x9: cmd.command_type = Vdp1CommandType::SYSTEM_CLIPPING; break;
    case 0xA: cmd.command_type = Vdp1CommandType::LOCAL_COORDINATE; break;
    default:  cmd.command_type = Vdp1CommandType::INVALID; break;
    }

    const uint8_t raw_jp = static_cast<uint8_t>((cmdctrl >> 8) & 0x07u);
    switch (raw_jp) {
    case 0x0: cmd.jump_mode = Vdp1JumpMode::JUMP_NEXT; break;
    case 0x1: cmd.jump_mode = Vdp1JumpMode::JUMP_ASSIGN; break;
    case 0x2: cmd.jump_mode = Vdp1JumpMode::JUMP_CALL; break;
    case 0x3: cmd.jump_mode = Vdp1JumpMode::JUMP_RETURN; break;
    case 0x4: cmd.jump_mode = Vdp1JumpMode::JUMP_SKIP; break;
    default:  cmd.jump_mode = Vdp1JumpMode::INVALID; break;
    }

    cmd.next_link_offset = static_cast<uint32_t>((cmdlink << 3) & (VDP1_VRAM_SIZE - 1));

    cmd.draw_mode.end_code_disable = (cmdpmod & 0x0080u) != 0;
    cmd.draw_mode.transparent_disable = (cmdpmod & 0x0100u) != 0;
    cmd.draw_mode.gouraud_shading = (cmdpmod & 0x0400u) != 0;
    cmd.draw_mode.mesh = (cmdpmod & 0x0001u) != 0;
    cmd.draw_mode.color_calculation = static_cast<uint8_t>((cmdpmod >> 6) & 0x07u);

    const uint8_t raw_col_mode = static_cast<uint8_t>((cmdpmod >> 3) & 0x07u);
    switch (raw_col_mode) {
    case 0x0: cmd.color_mode = Vdp1ColorMode::COLOR_BANK_16; break;
    case 0x1: cmd.color_mode = Vdp1ColorMode::LOOKUP_16; break;
    case 0x2: cmd.color_mode = Vdp1ColorMode::COLOR_BANK_64; break;
    case 0x3: cmd.color_mode = Vdp1ColorMode::COLOR_BANK_128; break;
    case 0x4: cmd.color_mode = Vdp1ColorMode::COLOR_BANK_256; break;
    case 0x5: cmd.color_mode = Vdp1ColorMode::RGB_32K; break;
    default:  cmd.color_mode = Vdp1ColorMode::INVALID; break;
    }

    cmd.color_data = cmdcolr;
    cmd.char_address = static_cast<uint32_t>((cmdsrca << 3) & (VDP1_VRAM_SIZE - 1));
    cmd.char_width = static_cast<uint16_t>(((cmdsize >> 8) & 0x3Fu) * 8);
    cmd.char_height = static_cast<uint16_t>(cmdsize & 0xFFu);

    cmd.vertices[0] = {read_i16_be(p + 12), read_i16_be(p + 14)};
    cmd.vertices[1] = {read_i16_be(p + 16), read_i16_be(p + 18)};
    cmd.vertices[2] = {read_i16_be(p + 20), read_i16_be(p + 22)};
    cmd.vertices[3] = {read_i16_be(p + 24), read_i16_be(p + 26)};

    cmd.gouraud_address = static_cast<uint32_t>((read_u16_be(p + 28) << 3) & (VDP1_VRAM_SIZE - 1));

    return cmd;
}

std::vector<Vdp1Command> Vdp1Engine::trace_display_list(
    std::span<const uint8_t> vram,
    uint32_t start_offset,
    uint32_t max_commands) {

    std::vector<Vdp1Command> list;
    list.reserve(32);

    uint32_t curr_offset = start_offset & (VDP1_VRAM_SIZE - 1);
    call_stack_depth_ = 0;

    while (list.size() < max_commands) {
        if (curr_offset + 32 > vram.size()) {
            break;
        }

        Vdp1Command cmd = parse_command(vram, curr_offset);
        if (cmd.command_type == Vdp1CommandType::INVALID) {
            break;
        }

        if (cmd.command_type == Vdp1CommandType::USER_CLIPPING) {
            user_clip_.min_x = cmd.vertices[0].x;
            user_clip_.min_y = cmd.vertices[0].y;
            user_clip_.max_x = cmd.vertices[2].x;
            user_clip_.max_y = cmd.vertices[2].y;
        } else if (cmd.command_type == Vdp1CommandType::SYSTEM_CLIPPING) {
            system_clip_.min_x = cmd.vertices[0].x;
            system_clip_.min_y = cmd.vertices[0].y;
            system_clip_.max_x = cmd.vertices[2].x;
            system_clip_.max_y = cmd.vertices[2].y;
        } else if (cmd.command_type == Vdp1CommandType::LOCAL_COORDINATE) {
            local_coord_.x = cmd.vertices[0].x;
            local_coord_.y = cmd.vertices[0].y;
        }

        list.push_back(cmd);

        if (cmd.is_end) {
            break;
        }

        switch (cmd.jump_mode) {
        case Vdp1JumpMode::JUMP_NEXT:
            curr_offset = (curr_offset + 32) & (VDP1_VRAM_SIZE - 1);
            break;
        case Vdp1JumpMode::JUMP_ASSIGN:
            curr_offset = cmd.next_link_offset;
            break;
        case Vdp1JumpMode::JUMP_CALL:
            if (call_stack_depth_ < VDP1_MAX_CALL_STACK) {
                call_stack_[call_stack_depth_++] = (curr_offset + 32) & (VDP1_VRAM_SIZE - 1);
            }
            curr_offset = cmd.next_link_offset;
            break;
        case Vdp1JumpMode::JUMP_RETURN:
            if (call_stack_depth_ > 0) {
                curr_offset = call_stack_[--call_stack_depth_];
            } else {
                curr_offset = (curr_offset + 32) & (VDP1_VRAM_SIZE - 1);
            }
            break;
        case Vdp1JumpMode::JUMP_SKIP:
            curr_offset = (curr_offset + 64) & (VDP1_VRAM_SIZE - 1);
            break;
        default:
            curr_offset = (curr_offset + 32) & (VDP1_VRAM_SIZE - 1);
            break;
        }
    }

    return list;
}

Vdp1Vertex Vdp1Engine::apply_local_coordinate(const Vdp1Vertex& v) const noexcept {
    return Vdp1Vertex{
        static_cast<int16_t>(v.x + local_coord_.x),
        static_cast<int16_t>(v.y + local_coord_.y)
    };
}

bool Vdp1Engine::is_inside_clipping(
    const Vdp1Vertex& v,
    const Vdp1ClippingRect& clip) noexcept {
    return (v.x >= clip.min_x && v.x <= clip.max_x &&
            v.y >= clip.min_y && v.y <= clip.max_y);
}

} // namespace thor::hw
