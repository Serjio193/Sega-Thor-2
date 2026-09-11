#pragma once

#include "thor/provenance/guest_address.hpp"
#include "thor/sh2/sh2_memory.hpp"
#include <optional>
#include <cstring>
#include <bit>

namespace thor::provenance {

/// Utility for safe, big-endian, typed reads and writes to guest memory.
class GuestView {
public:
    explicit GuestView(thor::sh2::ISh2Memory& mem) noexcept : mem_(mem) {}

    [[nodiscard]] thor::sh2::ISh2Memory& memory() noexcept { return mem_; }
    [[nodiscard]] const thor::sh2::ISh2Memory& memory() const noexcept { return mem_; }

    /// Read raw primitive with strict alignment and null checking.
    template <typename T>
    [[nodiscard]] std::optional<T> read(GuestAddress<T> addr) const {
        if (addr.is_null() || !addr.is_aligned()) {
            return std::nullopt;
        }

        if constexpr (sizeof(T) == 1) {
            uint8_t b = mem_.read8(addr.vma());
            T val;
            std::memcpy(&val, &b, 1);
            return val;
        } else if constexpr (sizeof(T) == 2) {
            uint16_t w = mem_.read16(addr.vma());
            T val;
            std::memcpy(&val, &w, 2);
            return val;
        } else if constexpr (sizeof(T) == 4) {
            uint32_t dw = mem_.read32(addr.vma());
            T val;
            std::memcpy(&val, &dw, 4);
            return val;
        } else {
            // Multi-byte or composite structure: read byte by byte
            T val{};
            auto* dst = reinterpret_cast<uint8_t*>(&val);
            for (size_t i = 0; i < sizeof(T); ++i) {
                dst[i] = mem_.read8(addr.vma() + static_cast<uint32_t>(i));
            }
            return val;
        }
    }

    template <typename T>
    [[nodiscard]] std::optional<T> read(GuestPtr<T> ptr) const {
        return read(ptr.address());
    }

    /// Write raw primitive with strict alignment and null checking.
    template <typename T>
    bool write(GuestAddress<T> addr, const T& val) {
        if (addr.is_null() || !addr.is_aligned()) {
            return false;
        }

        if constexpr (sizeof(T) == 1) {
            uint8_t b;
            std::memcpy(&b, &val, 1);
            mem_.write8(addr.vma(), b);
            return true;
        } else if constexpr (sizeof(T) == 2) {
            uint16_t w;
            std::memcpy(&w, &val, 2);
            mem_.write16(addr.vma(), w);
            return true;
        } else if constexpr (sizeof(T) == 4) {
            uint32_t dw;
            std::memcpy(&dw, &val, 4);
            mem_.write32(addr.vma(), dw);
            return true;
        } else {
            const auto* src = reinterpret_cast<const uint8_t*>(&val);
            for (size_t i = 0; i < sizeof(T); ++i) {
                mem_.write8(addr.vma() + static_cast<uint32_t>(i), src[i]);
            }
            return true;
        }
    }

    template <typename T>
    bool write(GuestPtr<T> ptr, const T& val) {
        return write(ptr.address(), val);
    }

    /// Read a null-terminated ASCII string from guest memory up to max_len bytes.
    [[nodiscard]] std::optional<std::string> read_string(GuestAddress<char> addr, size_t max_len = 256) const {
        if (addr.is_null()) return std::nullopt;
        std::string result;
        result.reserve(32);
        for (size_t i = 0; i < max_len; ++i) {
            uint8_t ch = mem_.read8(addr.vma() + static_cast<uint32_t>(i));
            if (ch == 0) return result;
            result.push_back(static_cast<char>(ch));
        }
        return result; // hit max_len without null terminator
    }

private:
    thor::sh2::ISh2Memory& mem_;
};

} // namespace thor::provenance
