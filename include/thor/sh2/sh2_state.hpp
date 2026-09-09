#pragma once

#include <array>
#include <cstdint>

namespace thor::sh2 {

/// Architectural CPU register state of an SH-2 processor.
struct Sh2CpuState {
    std::array<uint32_t, 16> r{}; // General registers R0..R15 (R15 is SP)
    uint32_t pc = 0;              // Program counter
    uint32_t pr = 0;              // Procedure register (subroutine return)
    uint32_t sr = 0;              // Status register (bit 0 = T flag)
    uint32_t gbr = 0;             // Global base register
    uint32_t vbr = 0;             // Vector base register
    uint32_t mach = 0;            // Multiply-accumulate high
    uint32_t macl = 0;            // Multiply-accumulate low

    [[nodiscard]] constexpr bool get_t() const noexcept {
        return (sr & 1u) != 0;
    }

    constexpr void set_t(bool t) noexcept {
        if (t) {
            sr |= 1u;
        } else {
            sr &= ~1u;
        }
    }

    bool operator==(const Sh2CpuState& other) const noexcept = default;
};

} // namespace thor::sh2
