#pragma once

#include <cstdint>
#include <string>
#include "thor/recomp/block_memory.hpp"
#include "thor/recomp/shadow_checker.hpp"
#include "thor/sh2/sh2_block.hpp"

namespace thor::recomp {

enum class ExecutionBoundaryType : uint8_t {
    ATOMIC_COMPUTATION = 0,     // Pure CPU ALU/register/stack computation; no external visible events.
    MMIO_SYNCHRONOUS,           // Accesses hardware MMIO registers (VDP/SCU/SCSP/SH2 peripherals).
    INTERRUPT_WINDOW,           // Window where unmasked interrupts may be serviced.
    DMA_ASYNCHRONOUS            // Memory area concurrently modified or transferred by DMA.
};

[[nodiscard]] const char* execution_boundary_type_to_string(ExecutionBoundaryType type) noexcept;

/// Result of evaluating timing, interrupt, and DMA boundaries for a candidate block.
struct BlockTimingClassification {
    ExecutionBoundaryType boundary_type = ExecutionBoundaryType::ATOMIC_COMPUTATION;
    bool is_timing_sensitive = false;
    bool requires_synchronization_barrier = false;
    bool requires_interpreter_fallback = false;
    uint32_t estimated_cycles = 0;
    std::string boundary_reason;
};

/// Helper: returns true if the address falls within known Saturn MMIO or peripheral regions.
[[nodiscard]] bool is_saturn_mmio_address(uint32_t address) noexcept;

/// Classifies a basic block and its execution environment according to D10 boundary criteria.
[[nodiscard]] BlockTimingClassification classify_block_timing(
    const thor::sh2::Sh2BasicBlock& block,
    const BlockMemoryContract& contract,
    const BoundedEventMetadata& event_metadata) noexcept;

} // namespace thor::recomp
