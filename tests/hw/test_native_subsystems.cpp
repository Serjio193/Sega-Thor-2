#include <iostream>
#include <vector>
#include "thor/hw/native_system.hpp"

using namespace thor::hw;

static void write_u16_be(uint8_t* p, uint16_t v) {
    p[0] = static_cast<uint8_t>((v >> 8) & 0xFF);
    p[1] = static_cast<uint8_t>(v & 0xFF);
}

static void write_i16_be(uint8_t* p, int16_t v) {
    write_u16_be(p, static_cast<uint16_t>(v));
}

int main() {
    std::cout << "[TEST] Running D16 Native Subsystem Replacement Tests...\n";

    NativeSaturnSystem sys;

    // 1. Memory Buffers Verification
    if (sys.vdp1_vram().size() != 0x80000 ||
        sys.vdp2_vram().size() != 0x80000 ||
        sys.vdp2_cram().size() != 0x1000 ||
        sys.sound_ram().size() != 0x80000) {
        std::cerr << "Buffer allocation size mismatch\n";
        return 1;
    }

    // 2. MMIO Dispatch: VDP1, VDP2, SCSP
    if (!sys.write_mmio_u16(0x25D00000, 0x0001)) return 2;
    if (sys.vdp1().tvmr() != 0x0001) return 3;

    if (!sys.write_mmio_u16(0x05D00002, 0x0003)) return 4;
    if (sys.vdp1().fbcr() != 0x0003) return 5;

    if (sys.read_mmio_u16(0x25D00010) != 0x0002) return 6;

    // CRAM write
    if (!sys.write_mmio_u16(0x25F00020, 0x7C00)) return 7;
    if (sys.vdp2_cram()[0x20] != 0x7C || sys.vdp2_cram()[0x21] != 0x00) return 8;

    // Sound RAM write
    if (!sys.write_mmio_u16(0x25A00040, 0x1234)) return 9;
    if (sys.sound_ram()[0x40] != 0x12 || sys.sound_ram()[0x41] != 0x34) return 10;

    // Unmapped MMIO
    if (sys.write_mmio_u16(0x10000000, 0x9999)) return 11;
    if (sys.read_mmio_u16(0x10000000) != 0) return 12;

    // 3. Integrated Frame Rendering
    Vdp2PlaneConfig sprite_cfg{};
    sprite_cfg.enabled = true;
    sprite_cfg.priority = 4;
    sys.vdp2().set_plane_config(Vdp2PlaneType::SPRITE_PLANE, sprite_cfg);

    // Setup VDP1 command list at VRAM offset 0: Red sprite (color 0x001F) at (50, 50)
    uint8_t* v1 = sys.vdp1_vram().data();
    write_u16_be(v1 + 0, 0x0000);  // NORMAL_SPRITE, JUMP_NEXT
    write_u16_be(v1 + 2, 0x0000);  // CMDLINK
    write_u16_be(v1 + 4, 0x0000);  // CMDPMOD
    write_u16_be(v1 + 6, 0x001F);  // Color = Red (BGR555)
    write_u16_be(v1 + 8, 0x0000);  // CMDSRCA
    write_u16_be(v1 + 10, 0x0210); // 16x16
    write_i16_be(v1 + 12, 50);     // XA = 50
    write_i16_be(v1 + 14, 50);     // YA = 50
    write_u16_be(v1 + 32, 0x8000); // END_MARKER at next command

    std::vector<uint32_t> fb(320 * 224, 0);
    sys.render_frame(fb, 320, 224);

    // Pixel inside sprite at (55, 55): Red RGBA
    uint32_t sprite_pix = fb[55 * 320 + 55];
    uint8_t spr_r = static_cast<uint8_t>(sprite_pix & 0xFF);
    uint8_t spr_g = static_cast<uint8_t>((sprite_pix >> 8) & 0xFF);
    uint8_t spr_b = static_cast<uint8_t>((sprite_pix >> 16) & 0xFF);
    if (spr_r != 255 || spr_g != 0 || spr_b != 0) {
        std::cerr << "Sprite pixel color mismatch: R=" << (int)spr_r << " G=" << (int)spr_g << " B=" << (int)spr_b << "\n";
        return 13;
    }

    // Pixel outside sprite at (10, 10): Back color (Black)
    uint32_t bg_pix = fb[10 * 320 + 10];
    uint8_t bg_r = static_cast<uint8_t>(bg_pix & 0xFF);
    uint8_t bg_g = static_cast<uint8_t>((bg_pix >> 8) & 0xFF);
    uint8_t bg_b = static_cast<uint8_t>((bg_pix >> 16) & 0xFF);
    if (bg_r != 0 || bg_g != 0 || bg_b != 0) {
        std::cerr << "Background pixel color mismatch\n";
        return 14;
    }

    // 4. Integrated Audio Synthesis
    // Populate sample data in Sound RAM at 0x0100
    for (size_t i = 0; i < 256; ++i) {
        sys.sound_ram()[0x0100 + i] = static_cast<uint8_t>((i % 2 == 0) ? 0x40 : 0x00);
    }

    ScspCommandPacket play_cmd{};
    play_cmd.command_type = ScspCommandType::BGM_PLAY;
    play_cmd.target_id = 7;
    play_cmd.volume = 110;
    if (!sys.scsp().enqueue_command(play_cmd)) return 15;
    sys.scsp().process_next_command();

    ScspSlotConfig slot0{};
    slot0.enabled = true;
    slot0.volume = 127;
    slot0.pan = 0;
    slot0.start_address = 0x0100;
    sys.scsp().configure_slot(0, slot0);

    std::vector<int16_t> audio_buf(128 * 2, 0);
    sys.render_audio(audio_buf, 128);

    bool has_audio = false;
    for (int16_t s : audio_buf) {
        if (s != 0) {
            has_audio = true;
            break;
        }
    }
    if (!has_audio) {
        std::cerr << "Audio synthesis produced silence when playing\n";
        return 16;
    }

    // Stop audio
    ScspCommandPacket stop_cmd{};
    stop_cmd.command_type = ScspCommandType::BGM_STOP;
    if (!sys.scsp().enqueue_command(stop_cmd)) return 17;
    sys.scsp().process_next_command();

    sys.render_audio(audio_buf, 128);
    for (int16_t s : audio_buf) {
        if (s != 0) {
            std::cerr << "Audio synthesis produced sound when stopped\n";
            return 18;
        }
    }

    std::cout << "[TEST] D16 Native Subsystem Replacement Tests PASSED.\n";
    return 0;
}
