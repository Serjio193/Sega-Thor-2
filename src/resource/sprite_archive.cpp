#include "thor/resource/sprite_archive.hpp"
#include <cstring>

namespace thor::resource {

namespace {

uint16_t read_be16(const uint8_t* p) noexcept {
    return static_cast<uint16_t>((static_cast<uint16_t>(p[0]) << 8) | p[1]);
}

uint32_t read_be32(const uint8_t* p) noexcept {
    return (static_cast<uint32_t>(p[0]) << 24) |
           (static_cast<uint32_t>(p[1]) << 16) |
           (static_cast<uint32_t>(p[2]) << 8)  |
           static_cast<uint32_t>(p[3]);
}

void write_be16(uint8_t* p, uint16_t val) noexcept {
    p[0] = static_cast<uint8_t>(val >> 8);
    p[1] = static_cast<uint8_t>(val & 0xFF);
}

void write_be32(uint8_t* p, uint32_t val) noexcept {
    p[0] = static_cast<uint8_t>(val >> 24);
    p[1] = static_cast<uint8_t>((val >> 16) & 0xFF);
    p[2] = static_cast<uint8_t>((val >> 8) & 0xFF);
    p[3] = static_cast<uint8_t>(val & 0xFF);
}

} // anonymous namespace

std::optional<SpriteArchive> SpriteArchive::decode(std::span<const uint8_t> bytes) {
    if (bytes.size() < SpriteArchiveHeader::CANONICAL_HEADER_SIZE) {
        return std::nullopt;
    }

    SpriteArchiveHeader hdr{
        .header_size = read_be32(bytes.data()),
        .anim_script_offset = read_be32(bytes.data() + 4),
        .sprite_data_offset = read_be32(bytes.data() + 8)
    };

    if (!hdr.is_valid(bytes.size())) {
        return std::nullopt;
    }

    SpriteArchive archive;
    archive.header_ = hdr;

    // Decode 16-bit offset table between header and anim_script_offset
    size_t offset_table_bytes = hdr.anim_script_offset - hdr.header_size;
    size_t num_offsets = offset_table_bytes / 2;
    archive.anim_offsets_.reserve(num_offsets);

    const uint8_t* offset_ptr = bytes.data() + hdr.header_size;
    for (size_t i = 0; i < num_offsets; ++i) {
        archive.anim_offsets_.push_back(read_be16(offset_ptr + (i * 2)));
    }

    // Slice animation script data
    size_t script_bytes = hdr.sprite_data_offset - hdr.anim_script_offset;
    archive.anim_script_data_.resize(script_bytes);
    if (script_bytes > 0) {
        std::memcpy(archive.anim_script_data_.data(), bytes.data() + hdr.anim_script_offset, script_bytes);
    }

    // Slice sprite pixel data
    size_t sprite_bytes = bytes.size() - hdr.sprite_data_offset;
    archive.sprite_data_.resize(sprite_bytes);
    if (sprite_bytes > 0) {
        std::memcpy(archive.sprite_data_.data(), bytes.data() + hdr.sprite_data_offset, sprite_bytes);
    }

    return archive;
}

std::vector<uint8_t> SpriteArchive::encode() const {
    size_t total = total_size();
    std::vector<uint8_t> out(total);

    // Write header
    write_be32(out.data(), header_.header_size);
    write_be32(out.data() + 4, header_.anim_script_offset);
    write_be32(out.data() + 8, header_.sprite_data_offset);

    // Write offset table
    uint8_t* p = out.data() + header_.header_size;
    for (uint16_t off : anim_offsets_) {
        write_be16(p, off);
        p += 2;
    }

    // Write animation script data
    if (!anim_script_data_.empty()) {
        std::memcpy(out.data() + header_.anim_script_offset, anim_script_data_.data(), anim_script_data_.size());
    }

    // Write sprite pixel data
    if (!sprite_data_.empty()) {
        std::memcpy(out.data() + header_.sprite_data_offset, sprite_data_.data(), sprite_data_.size());
    }

    return out;
}

size_t SpriteArchive::total_size() const noexcept {
    return SpriteArchiveHeader::CANONICAL_HEADER_SIZE +
           (anim_offsets_.size() * 2) +
           anim_script_data_.size() +
           sprite_data_.size();
}

} // namespace thor::resource
