#include "thor/hw/native_system.hpp"
#include <algorithm>
#include <cstring>

namespace thor::hw {

NativeSaturnSystem::NativeSaturnSystem() {
    vdp1_vram_.resize(VDP1_VRAM_SIZE, 0);
    vdp2_vram_.resize(VDP2_VRAM_SIZE, 0);
    vdp2_cram_.resize(VDP2_CRAM_SIZE, 0);
    sound_ram_.resize(SCSP_SOUND_RAM_SIZE, 0);
    reset();
}

void NativeSaturnSystem::reset() noexcept {
    vdp1_.reset();
    vdp2_.reset();
    scsp_.reset();
}

bool NativeSaturnSystem::write_mmio_u16(uint32_t address, uint16_t value) noexcept {
    const uint32_t masked = address & 0x1FFFFFFFu;

    // VDP1 Registers
    if (masked >= 0x05D00000u && masked <= 0x05D0001Eu) {
        switch (masked) {
        case 0x05D00000u: vdp1_.set_tvmr(value); return true;
        case 0x05D00002u: vdp1_.set_fbcr(value); return true;
        case 0x05D00004u: vdp1_.set_ptmr(value); return true;
        case 0x05D00010u: vdp1_.set_edsr(value); return true;
        default: return true;
        }
    }

    // VDP2 CRAM write
    if (masked >= 0x05F00000u && masked <= 0x05F00FFFu) {
        const uint32_t off = masked - 0x05F00000u;
        if (off + 2 <= vdp2_cram_.size()) {
            vdp2_cram_[off + 0] = static_cast<uint8_t>((value >> 8) & 0xFFu);
            vdp2_cram_[off + 1] = static_cast<uint8_t>(value & 0xFFu);
            return true;
        }
    }

    // Sound RAM / SCSP Mailbox write
    if (masked >= 0x05A00000u && masked <= 0x05A7FFFFu) {
        const uint32_t off = masked - 0x05A00000u;
        if (off + 2 <= sound_ram_.size()) {
            sound_ram_[off + 0] = static_cast<uint8_t>((value >> 8) & 0xFFu);
            sound_ram_[off + 1] = static_cast<uint8_t>(value & 0xFFu);
            return true;
        }
    }

    return false;
}

bool NativeSaturnSystem::write_mmio_u32(uint32_t address, uint32_t value) noexcept {
    bool ok1 = write_mmio_u16(address, static_cast<uint16_t>((value >> 16) & 0xFFFFu));
    bool ok2 = write_mmio_u16(address + 2, static_cast<uint16_t>(value & 0xFFFFu));
    return ok1 && ok2;
}

uint16_t NativeSaturnSystem::read_mmio_u16(uint32_t address) const noexcept {
    const uint32_t masked = address & 0x1FFFFFFFu;
    if (masked >= 0x05D00000u && masked <= 0x05D0001Eu) {
        switch (masked) {
        case 0x05D00000u: return vdp1_.tvmr();
        case 0x05D00002u: return vdp1_.fbcr();
        case 0x05D00004u: return vdp1_.ptmr();
        case 0x05D00010u: return vdp1_.edsr();
        default: return 0;
        }
    }
    return 0;
}

uint32_t NativeSaturnSystem::read_mmio_u32(uint32_t address) const noexcept {
    const uint32_t high = read_mmio_u16(address);
    const uint32_t low = read_mmio_u16(address + 2);
    return (high << 16) | low;
}

void NativeSaturnSystem::render_frame(
    std::span<uint32_t> framebuffer_out,
    uint32_t width,
    uint32_t height) noexcept {

    if (framebuffer_out.size() < width * height) {
        return;
    }

    // Step 1: Trace VDP1 Display List
    auto vdp1_cmds = vdp1_.trace_display_list(vdp1_vram_, 0);

    // Rasterize sprites into temporary sprite buffer
    std::vector<Vdp2Rgba> sprite_plane(width * height, Vdp2Rgba{0, 0, 0, 0});
    for (const auto& cmd : vdp1_cmds) {
        if (cmd.command_type == Vdp1CommandType::NORMAL_SPRITE ||
            cmd.command_type == Vdp1CommandType::POLYGON) {
            Vdp1Vertex v0 = vdp1_.apply_local_coordinate(cmd.vertices[0]);
            const int16_t w = static_cast<int16_t>(cmd.char_width > 0 ? cmd.char_width : 16);
            const int16_t h = static_cast<int16_t>(cmd.char_height > 0 ? cmd.char_height : 16);

            for (int16_t dy = 0; dy < h; ++dy) {
                const int16_t sy = static_cast<int16_t>(v0.y + dy);
                if (sy < 0 || sy >= static_cast<int16_t>(height)) continue;
                for (int16_t dx = 0; dx < w; ++dx) {
                    const int16_t sx = static_cast<int16_t>(v0.x + dx);
                    if (sx < 0 || sx >= static_cast<int16_t>(width)) continue;

                    if (Vdp1Engine::is_inside_clipping(Vdp1Vertex{sx, sy}, vdp1_.user_clipping())) {
                        Vdp2Rgba col = Vdp2Engine::decode_bgr555(cmd.color_data);
                        sprite_plane[sy * width + sx] = col;
                    }
                }
            }
        }
    }

    // Step 2: Composite VDP2 Planes and Arbitrate Final Pixel Colors
    for (uint32_t y = 0; y < height; ++y) {
        for (uint32_t x = 0; x < width; ++x) {
            std::array<Vdp2Rgba, static_cast<size_t>(Vdp2PlaneType::COUNT)> inputs{};
            inputs[static_cast<size_t>(Vdp2PlaneType::SPRITE_PLANE)] = sprite_plane[y * width + x];

            Vdp2Rgba final_pixel = vdp2_.arbitrate_pixel(inputs);
            framebuffer_out[y * width + x] = final_pixel.to_u32();
        }
    }
}

void NativeSaturnSystem::render_audio(
    std::span<int16_t> pcm_out,
    size_t sample_frames) noexcept {

    if (pcm_out.size() < sample_frames * 2) {
        return;
    }
    std::fill(pcm_out.begin(), pcm_out.begin() + (sample_frames * 2), static_cast<int16_t>(0));

    if (scsp_.driver_status() != ScspDriverStatus::PLAYING) {
        return;
    }

    // Synthesize active PCM slots
    for (size_t s = 0; s < SCSP_NUM_SLOTS; ++s) {
        const auto& slot = scsp_.slot(s);
        if (!slot.enabled) continue;

        const uint32_t vol = (static_cast<uint32_t>(slot.volume) * scsp_.master_volume()) / 127u;
        const int32_t pan = slot.pan; // -64..+63
        const int32_t left_gain = std::clamp(64 - pan, 0, 128);
        const int32_t right_gain = std::clamp(64 + pan, 0, 128);

        for (size_t f = 0; f < sample_frames; ++f) {
            // Read sample from sound RAM if within bounds
            const uint32_t addr = slot.start_address + (static_cast<uint32_t>(f) * 2);
            int16_t sample = 0;
            if (addr + 2 <= sound_ram_.size()) {
                sample = static_cast<int16_t>(
                    (static_cast<uint16_t>(sound_ram_[addr]) << 8) | sound_ram_[addr + 1]);
            } else {
                // Fallback synthetic wave
                sample = static_cast<int16_t>((f % 32 < 16) ? 8000 : -8000);
            }

            const int32_t scaled = (sample * static_cast<int32_t>(vol)) / 127;
            const int32_t out_l = (scaled * left_gain) / 128;
            const int32_t out_r = (scaled * right_gain) / 128;

            pcm_out[f * 2 + 0] = static_cast<int16_t>(std::clamp(pcm_out[f * 2 + 0] + out_l, -32768, 32767));
            pcm_out[f * 2 + 1] = static_cast<int16_t>(std::clamp(pcm_out[f * 2 + 1] + out_r, -32768, 32767));
        }
    }
}

} // namespace thor::hw
