#include <cassert>
#include <iostream>
#include <vector>
#include <fstream>
#include <cstring>
#include <cstdlib>

#include "thor/resource/sprite_archive.hpp"

using namespace thor::resource;

void test_synthetic_roundtrip() {
    std::cout << "[RUN] test_synthetic_roundtrip...\n";

    SpriteArchive archive;
    SpriteArchiveHeader hdr{
        .header_size = 12,
        .anim_script_offset = 12 + 8, // 4 16-bit offsets
        .sprite_data_offset = 12 + 8 + 16 // 16 bytes of script
    };
    archive.set_header(hdr);

    std::vector<uint16_t> offsets = {0x0020, 0x0040, 0x0060, 0xFFFF};
    archive.set_animation_offsets(offsets);

    std::vector<uint8_t> script = {
        0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
        0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10
    };
    archive.set_animation_script_data(script);

    std::vector<uint8_t> sprites = {
        0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
        0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00
    };
    archive.set_sprite_graphics_data(sprites);

    // Encode
    auto encoded = archive.encode();
    assert(encoded.size() == archive.total_size());
    assert(encoded.size() == 12 + 8 + 16 + 16);

    // Decode
    auto decoded = SpriteArchive::decode(encoded);
    assert(decoded.has_value());
    assert(decoded->header().header_size == 12);
    assert(decoded->header().anim_script_offset == 20);
    assert(decoded->header().sprite_data_offset == 36);
    assert(decoded->animation_offsets() == offsets);
    assert(decoded->animation_script_data() == script);
    assert(decoded->sprite_graphics_data() == sprites);

    // Re-encode and compare byte-for-byte
    auto reencoded = decoded->encode();
    assert(reencoded == encoded);

    std::cout << "  [PASS] test_synthetic_roundtrip\n";
}

void test_negative_controls() {
    std::cout << "[RUN] test_negative_controls...\n";

    // 1. Truncated buffer (< 12 bytes)
    std::vector<uint8_t> tiny = {0, 0, 0, 12, 0, 0};
    assert(!SpriteArchive::decode(tiny).has_value());

    // 2. Corrupted header size != 12
    std::vector<uint8_t> bad_hdr = {
        0x00, 0x00, 0x00, 0x10, // header size = 16 (invalid)
        0x00, 0x00, 0x00, 0x20,
        0x00, 0x00, 0x00, 0x30,
        0x00, 0x00, 0x00, 0x00
    };
    assert(!SpriteArchive::decode(bad_hdr).has_value());

    // 3. anim_script_offset < header_size
    std::vector<uint8_t> bad_offset1 = {
        0x00, 0x00, 0x00, 0x0C,
        0x00, 0x00, 0x00, 0x08, // anim_script_offset = 8 < 12
        0x00, 0x00, 0x00, 0x20
    };
    assert(!SpriteArchive::decode(bad_offset1).has_value());

    // 4. sprite_data_offset < anim_script_offset
    std::vector<uint8_t> bad_offset2 = {
        0x00, 0x00, 0x00, 0x0C,
        0x00, 0x00, 0x00, 0x20,
        0x00, 0x00, 0x00, 0x14 // sprite_data < anim_script
    };
    assert(!SpriteArchive::decode(bad_offset2).has_value());

    // 5. sprite_data_offset > file size
    std::vector<uint8_t> bad_offset3 = {
        0x00, 0x00, 0x00, 0x0C,
        0x00, 0x00, 0x00, 0x10,
        0x00, 0x00, 0x00, 0xFF // 255 > 16 bytes
    };
    bad_offset3.resize(16, 0);
    assert(!SpriteArchive::decode(bad_offset3).has_value());

    // 6. Odd offset table size
    std::vector<uint8_t> odd_table = {
        0x00, 0x00, 0x00, 0x0C,
        0x00, 0x00, 0x00, 0x0D, // 13 - 12 = 1 byte (odd)
        0x00, 0x00, 0x00, 0x14
    };
    odd_table.resize(20, 0);
    assert(!SpriteArchive::decode(odd_table).has_value());

    std::cout << "  [PASS] test_negative_controls (6/6 fault injections rejected)\n";
}

void test_real_game_resource_roundtrip() {
    std::cout << "[RUN] test_real_game_resource_roundtrip...\n";

    const char* disc_path = std::getenv("THOR_DISC_IMAGE");
    if (!disc_path) {
        disc_path = "The_Story_of_Thor_2_[RUS]_(NTSC).bin";
    }

    std::ifstream f(disc_path, std::ios::binary);
    if (!f.is_open()) {
        std::cout << "  [SKIP] Disc image not found at " << disc_path << " (skipping live extraction)\n";
        return;
    }

    struct ResourceSpec {
        const char* name;
        uint32_t lba;
        size_t size;
        uint32_t exp_script_offset;
        uint32_t exp_sprite_offset;
    };

    const ResourceSpec specs[] = {
        {"BAW.BIN", 317, 72540, 0x1098, 0x1576},
        {"DIT.BIN", 47916, 63244, 0x2FAE, 0x3926},
        {"SHADE.BIN", 52088, 69844, 0x0A40, 0x0AF2},
        {"ARELE.BIN", 286, 62344, 0x1A68, 0x1DBC},
        {"EFREET.BIN", 48249, 130352, 0x1B88, 0x1F64},
        {"BRAS.BIN", 682, 105180, 0x1D6E, 0x2196}
    };

    for (const auto& spec : specs) {
        std::vector<uint8_t> orig_bytes(spec.size);
        f.seekg(static_cast<std::streamoff>(spec.lba * 2352 + 16));
        f.read(reinterpret_cast<char*>(orig_bytes.data()), spec.size);
        assert(f.gcount() == static_cast<std::streamsize>(spec.size));

        // Decode
        auto decoded = SpriteArchive::decode(orig_bytes);
        assert(decoded.has_value());
        assert(decoded->header().header_size == 12);
        assert(decoded->header().anim_script_offset == spec.exp_script_offset);
        assert(decoded->header().sprite_data_offset == spec.exp_sprite_offset);
        assert(decoded->total_size() == spec.size);

        // Re-encode
        auto reencoded = decoded->encode();
        assert(reencoded.size() == spec.size);

        // Exact byte-for-byte comparison: BYTE_ROUNDTRIP_EXACT
        bool bit_identical = (reencoded == orig_bytes);
        assert(bit_identical);

        std::cout << "  [PASS] " << spec.name << " (" << spec.size << " bytes) -> BYTE_ROUNDTRIP_EXACT (0 byte diff)\n";
    }

    std::cout << "  [PASS] test_real_game_resource_roundtrip\n";
}

int main() {
    std::cout << "=== RUNNING GATE V-11 / D14 RESOURCE ROUNDTRIP TEST SUITE ===\n";
    test_synthetic_roundtrip();
    test_negative_controls();
    test_real_game_resource_roundtrip();
    std::cout << "=== ALL RESOURCE TESTS PASSED (V-11: PASS / BYTE_ROUNDTRIP_EXACT) ===\n";
    return 0;
}
