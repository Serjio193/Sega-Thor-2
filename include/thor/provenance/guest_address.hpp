#pragma once

#include <cstdint>
#include <cstddef>
#include <string_view>
#include <concepts>
#include <compare>

namespace thor::provenance {

/// Saturn memory domains as observed in Thor 2.
enum class MemoryDomain : uint8_t {
    UNKNOWN = 0,
    HIGH_WORK_RAM, // 0x06000000..0x060FFFFF (or mirrored 0x26000000)
    LOW_WORK_RAM,  // 0x00200000..0x002FFFFF (or mirrored 0x20200000)
    VDP1_VRAM,     // 0x05C00000..0x05C7FFFF
    VDP2_VRAM,     // 0x05E00000..0x05E7FFFF
    SOUND_RAM,     // 0x05A00000..0x05A7FFFF
    MMIO,          // 0x05800000..0x05FFFFFF / 0xFFFFFE00..0xFFFFFFFF
    BOOT_ROM       // 0x00000000..0x000FFFFF
};

/// Classify a 32-bit guest address into its authoritative Saturn memory domain.
[[nodiscard]] constexpr MemoryDomain classify_guest_memory_domain(uint32_t addr) noexcept {
    const uint32_t masked = addr & 0x1FFFFFFFu;
    if (masked >= 0x06000000u && masked < 0x06100000u) return MemoryDomain::HIGH_WORK_RAM;
    if (masked >= 0x00200000u && masked < 0x00300000u) return MemoryDomain::LOW_WORK_RAM;
    if (masked >= 0x05C00000u && masked < 0x05C80000u) return MemoryDomain::VDP1_VRAM;
    if (masked >= 0x05E00000u && masked < 0x05E80000u) return MemoryDomain::VDP2_VRAM;
    if (masked >= 0x05A00000u && masked < 0x05A80000u) return MemoryDomain::SOUND_RAM;
    if (masked >= 0x05800000u && masked < 0x06000000u) return MemoryDomain::MMIO;
    if (addr >= 0xFFFFFE00u) return MemoryDomain::MMIO;
    if (masked < 0x00100000u) return MemoryDomain::BOOT_ROM;
    return MemoryDomain::UNKNOWN;
}

/// Provenance metadata attaching a guest address to its original Saturn revision and disc file.
struct AddressProvenance {
    uint32_t vma = 0;
    std::string_view module_name{};
    uint32_t file_offset = 0;
    MemoryDomain domain = MemoryDomain::UNKNOWN;

    [[nodiscard]] constexpr bool has_provenance() const noexcept {
        return !module_name.empty() || domain != MemoryDomain::UNKNOWN;
    }
};

/// Strongly-typed guest address wrapper preventing accidental arithmetic and preserving VMA.
template <typename T = void>
class GuestAddress {
public:
    using value_type = T;

    constexpr GuestAddress() noexcept : vma_(0) {}
    explicit constexpr GuestAddress(uint32_t vma) noexcept : vma_(vma) {}

    [[nodiscard]] constexpr uint32_t vma() const noexcept { return vma_; }
    [[nodiscard]] constexpr uint32_t raw() const noexcept { return vma_; }
    [[nodiscard]] constexpr bool is_null() const noexcept { return vma_ == 0; }
    [[nodiscard]] constexpr explicit operator bool() const noexcept { return vma_ != 0; }

    [[nodiscard]] constexpr MemoryDomain domain() const noexcept {
        return classify_guest_memory_domain(vma_);
    }

    [[nodiscard]] constexpr bool is_aligned() const noexcept {
        if constexpr (std::is_void_v<T>) {
            return true;
        } else {
            return (vma_ % alignof(T)) == 0;
        }
    }

    [[nodiscard]] constexpr GuestAddress<T> offset_bytes(int32_t delta) const noexcept {
        return GuestAddress<T>(static_cast<uint32_t>(static_cast<int64_t>(vma_) + delta));
    }

    [[nodiscard]] constexpr GuestAddress<T> element(size_t index) const noexcept {
        static_assert(!std::is_void_v<T>, "Cannot index GuestAddress<void>");
        return offset_bytes(static_cast<int32_t>(index * sizeof(T)));
    }

    template <typename U>
    [[nodiscard]] constexpr GuestAddress<U> cast() const noexcept {
        return GuestAddress<U>(vma_);
    }

    auto operator<=>(const GuestAddress&) const = default;

private:
    uint32_t vma_ = 0;
};

/// Strongly-typed guest pointer combining GuestAddress<T> with explicit provenance tracking.
template <typename T>
class GuestPtr {
public:
    using value_type = T;

    constexpr GuestPtr() noexcept = default;
    constexpr GuestPtr(GuestAddress<T> addr, AddressProvenance prov) noexcept
        : addr_(addr), prov_(prov) {}

    explicit constexpr GuestPtr(uint32_t vma, std::string_view module_name = {}, uint32_t file_offset = 0) noexcept
        : addr_(vma), prov_{vma, module_name, file_offset, classify_guest_memory_domain(vma)} {}

    [[nodiscard]] constexpr GuestAddress<T> address() const noexcept { return addr_; }
    [[nodiscard]] constexpr uint32_t vma() const noexcept { return addr_.vma(); }
    [[nodiscard]] constexpr const AddressProvenance& provenance() const noexcept { return prov_; }
    [[nodiscard]] constexpr bool is_null() const noexcept { return addr_.is_null(); }
    [[nodiscard]] constexpr bool is_aligned() const noexcept { return addr_.is_aligned(); }
    [[nodiscard]] constexpr MemoryDomain domain() const noexcept { return prov_.domain; }

    [[nodiscard]] constexpr GuestPtr<T> offset_bytes(int32_t delta) const noexcept {
        AddressProvenance new_prov = prov_;
        new_prov.vma = addr_.offset_bytes(delta).vma();
        new_prov.file_offset += delta;
        new_prov.domain = classify_guest_memory_domain(new_prov.vma);
        return GuestPtr<T>(addr_.offset_bytes(delta), new_prov);
    }

    [[nodiscard]] constexpr GuestPtr<T> element(size_t index) const noexcept {
        static_assert(!std::is_void_v<T>, "Cannot index GuestPtr<void>");
        return offset_bytes(static_cast<int32_t>(index * sizeof(T)));
    }

    template <typename U>
    [[nodiscard]] constexpr GuestPtr<U> cast() const noexcept {
        return GuestPtr<U>(addr_.template cast<U>(), prov_);
    }

    auto operator<=>(const GuestPtr&) const = default;

private:
    GuestAddress<T> addr_{};
    AddressProvenance prov_{};
};

} // namespace thor::provenance
