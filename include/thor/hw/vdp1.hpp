#pragma once

#include <cstdint>
#include <vector>
#include <array>
#include <span>
#include "thor/hw/vdp1_types.hpp"

namespace thor::hw {

inline constexpr size_t VDP1_MAX_CALL_STACK = 2;
inline constexpr uint32_t VDP1_VRAM_SIZE = 0x80000; // 512 KB

class Vdp1Engine {
public:
    Vdp1Engine() noexcept;

    void reset() noexcept;

    [[nodiscard]] static Vdp1Command parse_command(
        std::span<const uint8_t> vram,
        uint32_t offset) noexcept;

    [[nodiscard]] std::vector<Vdp1Command> trace_display_list(
        std::span<const uint8_t> vram,
        uint32_t start_offset,
        uint32_t max_commands = 2048);

    void set_user_clipping(const Vdp1ClippingRect& rect) noexcept { user_clip_ = rect; }
    [[nodiscard]] const Vdp1ClippingRect& user_clipping() const noexcept { return user_clip_; }

    void set_system_clipping(const Vdp1ClippingRect& rect) noexcept { system_clip_ = rect; }
    [[nodiscard]] const Vdp1ClippingRect& system_clipping() const noexcept { return system_clip_; }

    void set_local_coordinate(int16_t x, int16_t y) noexcept { local_coord_ = {x, y}; }
    [[nodiscard]] const Vdp1Vertex& local_coordinate() const noexcept { return local_coord_; }

    [[nodiscard]] Vdp1Vertex apply_local_coordinate(const Vdp1Vertex& v) const noexcept;

    [[nodiscard]] static bool is_inside_clipping(
        const Vdp1Vertex& v,
        const Vdp1ClippingRect& clip) noexcept;

    void set_tvmr(uint16_t val) noexcept { tvmr_ = val; }
    [[nodiscard]] uint16_t tvmr() const noexcept { return tvmr_; }

    void set_fbcr(uint16_t val) noexcept { fbcr_ = val; }
    [[nodiscard]] uint16_t fbcr() const noexcept { return fbcr_; }

    void set_ptmr(uint16_t val) noexcept { ptmr_ = val; }
    [[nodiscard]] uint16_t ptmr() const noexcept { return ptmr_; }

    [[nodiscard]] uint16_t edsr() const noexcept { return edsr_; }
    void set_edsr(uint16_t val) noexcept { edsr_ = val; }

private:
    Vdp1ClippingRect user_clip_{0, 0, 319, 223};
    Vdp1ClippingRect system_clip_{0, 0, 319, 223};
    Vdp1Vertex local_coord_{0, 0};

    uint16_t tvmr_ = 0;
    uint16_t fbcr_ = 0;
    uint16_t ptmr_ = 0;
    uint16_t edsr_ = 0x0002;

    std::array<uint32_t, VDP1_MAX_CALL_STACK> call_stack_{};
    size_t call_stack_depth_ = 0;
};

} // namespace thor::hw
