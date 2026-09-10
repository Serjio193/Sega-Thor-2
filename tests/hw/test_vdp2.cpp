#include <iostream>
#include <vector>
#include <string>
#include "thor/hw/vdp2.hpp"

using namespace thor::hw;

int main() {
    std::cout << "[TEST] Running VDP2 Subsystem Contract Tests...\n";

    Vdp2Engine engine;

    // 1. Color decoding: BGR555
    Vdp2Rgba red = Vdp2Engine::decode_bgr555(0x001F);
    if (red.r != 255 || red.g != 0 || red.b != 0 || red.a != 255) {
        std::cerr << "red decode failure\n";
        return 1;
    }

    Vdp2Rgba green = Vdp2Engine::decode_bgr555(0x03E0);
    if (green.r != 0 || green.g != 255 || green.b != 0) {
        std::cerr << "green decode failure\n";
        return 2;
    }

    Vdp2Rgba blue = Vdp2Engine::decode_bgr555(0x7C00);
    if (blue.r != 0 || blue.g != 0 || blue.b != 255) {
        std::cerr << "blue decode failure\n";
        return 3;
    }

    // 2. Color decoding: RGB888
    Vdp2Rgba custom = Vdp2Engine::decode_rgb888(0x123456);
    if (custom.r != 0x12 || custom.g != 0x34 || custom.b != 0x56) {
        std::cerr << "rgb888 decode failure\n";
        return 4;
    }

    // 3. CRAM reading
    std::vector<uint8_t> cram(4096, 0);
    cram[20] = 0x7C;
    cram[21] = 0x00;
    Vdp2Rgba cram_col = engine.decode_cram(cram, 10);
    if (cram_col.b != 255 || cram_col.r != 0 || cram_col.g != 0) {
        std::cerr << "cram decode failure\n";
        return 5;
    }

    // 4. RBG0 Rotation Matrix
    Vdp2RotationMatrix rot{};
    rot.a = 0x00020000;
    rot.b = 0;
    rot.c = 0;
    rot.d = 0x00020000;
    rot.cx = 160;
    rot.cy = 112;
    engine.set_rbg0_matrix(rot);

    auto transformed = engine.transform_rbg0(170, 122);
    if (transformed.first != 180 || transformed.second != 132) {
        std::cerr << "rbg0 transform failure\n";
        return 6;
    }

    // 5. Plane Priority Arbitration & Color Calculation
    Vdp2PlaneConfig nbg0{};
    nbg0.enabled = true;
    nbg0.priority = 5;
    nbg0.color_calc_enable = true;
    nbg0.color_calc_ratio = 16;
    engine.set_plane_config(Vdp2PlaneType::NBG0, nbg0);

    Vdp2PlaneConfig nbg1{};
    nbg1.enabled = true;
    nbg1.priority = 3;
    engine.set_plane_config(Vdp2PlaneType::NBG1, nbg1);

    std::array<Vdp2Rgba, static_cast<size_t>(Vdp2PlaneType::COUNT)> inputs{};
    inputs[static_cast<size_t>(Vdp2PlaneType::NBG0)] = Vdp2Rgba{255, 255, 255, 255};
    inputs[static_cast<size_t>(Vdp2PlaneType::NBG1)] = Vdp2Rgba{0, 0, 0, 255};

    Vdp2Rgba blended = engine.arbitrate_pixel(inputs);
    if (blended.r < 126 || blended.r > 128 ||
        blended.g < 126 || blended.g > 128 ||
        blended.b < 126 || blended.b > 128) {
        std::cerr << "arbitrate_pixel blend failure\n";
        return 7;
    }

    // 6. String representations
    if (std::string(vdp2_plane_type_to_string(Vdp2PlaneType::NBG0)) != "NBG0" ||
        std::string(vdp2_cram_mode_to_string(Vdp2CramMode::MODE_0_1024_15B)) != "MODE_0_1024_15B") {
        std::cerr << "string conversion failure\n";
        return 8;
    }

    std::cout << "[TEST] VDP2 Subsystem Contract Tests PASSED.\n";
    return 0;
}
