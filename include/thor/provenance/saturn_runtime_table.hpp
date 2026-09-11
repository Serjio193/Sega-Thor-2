#pragma once

#include "thor/provenance/guest_address.hpp"
#include "thor/provenance/guest_view.hpp"
#include <optional>
#include <string_view>

namespace thor::provenance {

/// Canonical Saturn SDK startup memory initialization table.
/// Proven by dynamic execution of bb_06004000 and the boot initialization loop (0x0600400C..0x0600401A).
/// Located at 0x06081C04..0x06081C18 in High Work RAM (0TH2.BIN, offset 0x7DC04).
struct SaturnStartupTable {
    static constexpr uint32_t CANONICAL_VMA = 0x06081C04u;
    static constexpr uint32_t TABLE_SIZE_BYTES = 20u;

    GuestAddress<uint32_t> data_rom_start{0x06081C04u};
    GuestAddress<uint32_t> data_ram_start{0x06081C08u};
    GuestAddress<uint32_t> data_ram_end{0x06081C0Cu};
    GuestAddress<uint32_t> bss_start{0x06081C10u};
    GuestAddress<uint32_t> bss_end{0x06081C14u};

    /// Resolved values read from guest memory via GuestView.
    struct ResolvedValues {
        uint32_t data_rom_src = 0;
        uint32_t data_ram_dst = 0;
        uint32_t data_ram_limit = 0;
        uint32_t bss_start_addr = 0;
        uint32_t bss_end_addr = 0;

        [[nodiscard]] constexpr uint32_t data_size() const noexcept {
            return (data_ram_limit >= data_ram_dst) ? (data_ram_limit - data_ram_dst) : 0;
        }

        [[nodiscard]] constexpr uint32_t bss_size() const noexcept {
            return (bss_end_addr >= bss_start_addr) ? (bss_end_addr - bss_start_addr) : 0;
        }
    };

    /// Read and decode the startup table from guest memory with fail-closed validation.
    [[nodiscard]] static std::optional<ResolvedValues> read_from(const GuestView& view) {
        auto rom_src = view.read(GuestAddress<uint32_t>(0x06081C04u));
        auto ram_dst = view.read(GuestAddress<uint32_t>(0x06081C08u));
        auto ram_lim = view.read(GuestAddress<uint32_t>(0x06081C0Cu));
        auto bss_st  = view.read(GuestAddress<uint32_t>(0x06081C10u));
        auto bss_en  = view.read(GuestAddress<uint32_t>(0x06081C14u));

        if (!rom_src || !ram_dst || !ram_lim || !bss_st || !bss_en) {
            return std::nullopt;
        }

        return ResolvedValues{
            .data_rom_src = *rom_src,
            .data_ram_dst = *ram_dst,
            .data_ram_limit = *ram_lim,
            .bss_start_addr = *bss_st,
            .bss_end_addr = *bss_en
        };
    }
};

/// File load descriptor table entry as used by 0TH2.BIN sub_0600A0F8.
/// Proven by V-02b dynamic trace loading TH2.LOW to 0x002DA000.
struct SaturnFileLoadEntry {
    static constexpr uint32_t CANONICAL_TH2_LOW_NAME_VMA = 0x06081C20u;
    static constexpr uint32_t CANONICAL_TH2_LOW_LOAD_VMA = 0x002DA000u;

    GuestAddress<char> name_address{CANONICAL_TH2_LOW_NAME_VMA};
    GuestAddress<void> target_load_address{CANONICAL_TH2_LOW_LOAD_VMA};
    std::string_view expected_filename{"TH2.LOW"};
};

} // namespace thor::provenance
