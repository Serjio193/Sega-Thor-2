#include <iostream>
#include <vector>
#include <string>
#include "thor/hw/vdp1.hpp"

using namespace thor::hw;

static void write_u16_be(uint8_t* p, uint16_t v) {
    p[0] = static_cast<uint8_t>((v >> 8) & 0xFF);
    p[1] = static_cast<uint8_t>(v & 0xFF);
}

static void write_i16_be(uint8_t* p, int16_t v) {
    write_u16_be(p, static_cast<uint16_t>(v));
}

int main() {
    std::cout << "[TEST] Running VDP1 Subsystem Contract Tests...\n";

    Vdp1Engine engine;
    if (engine.tvmr() != 0 || engine.edsr() != 0x0002) {
        std::cerr << "Engine init failure\n";
        return 1;
    }

    std::vector<uint8_t> vram(1024, 0);

    // 1. Normal Sprite Command at offset 0
    write_u16_be(&vram[0], 0x0000);
    write_u16_be(&vram[2], 0x0000);
    write_u16_be(&vram[4], 0x0000);
    write_u16_be(&vram[6], 0x0123);
    write_u16_be(&vram[8], 0x0100);
    write_u16_be(&vram[10], 0x0210);
    write_i16_be(&vram[12], 100);
    write_i16_be(&vram[14], 50);

    Vdp1Command cmd0 = Vdp1Engine::parse_command(vram, 0);
    if (cmd0.command_type != Vdp1CommandType::NORMAL_SPRITE ||
        cmd0.jump_mode != Vdp1JumpMode::JUMP_NEXT ||
        cmd0.char_address != 0x0800 ||
        cmd0.char_width != 16 ||
        cmd0.char_height != 16 ||
        cmd0.vertices[0].x != 100 ||
        cmd0.vertices[0].y != 50 ||
        cmd0.is_end) {
        std::cerr << "cmd0 parse failure\n";
        return 2;
    }

    // 2. Call command at offset 32 jumping to offset 128
    write_u16_be(&vram[32], 0x0208);
    write_u16_be(&vram[34], 16);
    write_i16_be(&vram[44], 10);
    write_i16_be(&vram[46], 20);
    write_i16_be(&vram[52], 300);
    write_i16_be(&vram[54], 200);

    // 3. Subroutine at offset 128 returning
    write_u16_be(&vram[128], 0x0304);

    // 4. Return target at offset 64 with END_MARKER
    write_u16_be(&vram[64], 0x8000);

    auto trace = engine.trace_display_list(vram, 0);
    if (trace.size() != 4 ||
        trace[0].command_type != Vdp1CommandType::NORMAL_SPRITE ||
        trace[1].command_type != Vdp1CommandType::USER_CLIPPING ||
        trace[2].command_type != Vdp1CommandType::POLYGON ||
        !trace[3].is_end) {
        std::cerr << "trace execution failure\n";
        return 3;
    }

    // Verify user clipping was updated by command 1
    if (engine.user_clipping().min_x != 10 ||
        engine.user_clipping().min_y != 20 ||
        engine.user_clipping().max_x != 300 ||
        engine.user_clipping().max_y != 200) {
        std::cerr << "clipping update failure\n";
        return 4;
    }

    // 5. Local coordinate transform and clipping tests
    engine.set_local_coordinate(50, -25);
    Vdp1Vertex v{10, 20};
    Vdp1Vertex transformed = engine.apply_local_coordinate(v);
    if (transformed.x != 60 || transformed.y != -5) {
        std::cerr << "local coord failure\n";
        return 5;
    }

    if (!Vdp1Engine::is_inside_clipping(Vdp1Vertex{100, 100}, engine.user_clipping()) ||
        Vdp1Engine::is_inside_clipping(Vdp1Vertex{5, 100}, engine.user_clipping()) ||
        Vdp1Engine::is_inside_clipping(Vdp1Vertex{100, 250}, engine.user_clipping())) {
        std::cerr << "is_inside_clipping failure\n";
        return 6;
    }

    // 6. String representations
    if (std::string(vdp1_command_type_to_string(Vdp1CommandType::NORMAL_SPRITE)) != "NORMAL_SPRITE" ||
        std::string(vdp1_jump_mode_to_string(Vdp1JumpMode::JUMP_CALL)) != "JUMP_CALL" ||
        std::string(vdp1_color_mode_to_string(Vdp1ColorMode::RGB_32K)) != "RGB_32K") {
        std::cerr << "string conversion failure\n";
        return 7;
    }

    std::cout << "[TEST] VDP1 Subsystem Contract Tests PASSED.\n";
    return 0;
}
