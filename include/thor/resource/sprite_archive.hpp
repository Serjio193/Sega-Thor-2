#pragma once

#include <cstdint>
#include <cstddef>
#include <vector>
#include <span>
#include <optional>
#include <string_view>

namespace thor::resource {

/// Header for Ancient character/spirit sprite package archives (.BIN).
/// Observed across BAW.BIN, DIT.BIN, EFREET.BIN, SHADE.BIN, ARELE.BIN, BRAS.BIN, P0.BIN..P3.BIN.
struct SpriteArchiveHeader {
    static constexpr uint32_t CANONICAL_HEADER_SIZE = 12u;

    uint32_t header_size = CANONICAL_HEADER_SIZE;
    uint32_t anim_script_offset = 0;
    uint32_t sprite_data_offset = 0;

    [[nodiscard]] constexpr bool is_valid(size_t total_file_size) const noexcept {
        if (header_size != CANONICAL_HEADER_SIZE) return false;
        if (anim_script_offset < header_size) return false;
        if (sprite_data_offset < anim_script_offset) return false;
        if (sprite_data_offset > total_file_size) return false;
        if ((anim_script_offset - header_size) % 2 != 0) return false;
        return true;
    }
};

/// Strongly-typed model of the Ancient Sprite Package format.
class SpriteArchive {
public:
    SpriteArchive() = default;

    /// Decode raw archive bytes into structured representation.
    [[nodiscard]] static std::optional<SpriteArchive> decode(std::span<const uint8_t> bytes);

    /// Encode structured archive into byte-identical binary representation.
    [[nodiscard]] std::vector<uint8_t> encode() const;

    [[nodiscard]] const SpriteArchiveHeader& header() const noexcept { return header_; }
    [[nodiscard]] const std::vector<uint16_t>& animation_offsets() const noexcept { return anim_offsets_; }
    [[nodiscard]] const std::vector<uint8_t>& animation_script_data() const noexcept { return anim_script_data_; }
    [[nodiscard]] const std::vector<uint8_t>& sprite_graphics_data() const noexcept { return sprite_data_; }

    [[nodiscard]] size_t total_size() const noexcept;

    void set_header(const SpriteArchiveHeader& hdr) noexcept { header_ = hdr; }
    void set_animation_offsets(std::vector<uint16_t> offsets) { anim_offsets_ = std::move(offsets); }
    void set_animation_script_data(std::vector<uint8_t> data) { anim_script_data_ = std::move(data); }
    void set_sprite_graphics_data(std::vector<uint8_t> data) { sprite_data_ = std::move(data); }

private:
    SpriteArchiveHeader header_{};
    std::vector<uint16_t> anim_offsets_{};
    std::vector<uint8_t> anim_script_data_{};
    std::vector<uint8_t> sprite_data_{};
};

} // namespace thor::resource
