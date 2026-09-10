#include "thor/recomp/block_timing.hpp"

namespace thor::recomp {

const char* execution_boundary_type_to_string(ExecutionBoundaryType type) noexcept {
    switch (type) {
    case ExecutionBoundaryType::ATOMIC_COMPUTATION:
        return "ATOMIC_COMPUTATION";
    case ExecutionBoundaryType::MMIO_SYNCHRONOUS:
        return "MMIO_SYNCHRONOUS";
    case ExecutionBoundaryType::INTERRUPT_WINDOW:
        return "INTERRUPT_WINDOW";
    case ExecutionBoundaryType::DMA_ASYNCHRONOUS:
        return "DMA_ASYNCHRONOUS";
    default:
        return "UNKNOWN";
    }
}

bool is_saturn_mmio_address(uint32_t address) noexcept {
    // Check SH-2 on-chip peripherals (0xFFFFFE00..0xFFFFFFFF)
    if (address >= 0xFFFFFE00u) {
        return true;
    }
    // Check Saturn B-Bus / VDP1 / VDP2 / SCU / SCSP MMIO
    // A-Bus / B-Bus mirrors at 0x25800000..0x25FFFFFF and 0x05800000..0x05FFFFFF
    const uint32_t masked = address & 0x1FFFFFFFu;
    if (masked >= 0x05800000u && masked <= 0x05FFFFFFu) {
        return true;
    }
    return false;
}

BlockTimingClassification classify_block_timing(
    const thor::sh2::Sh2BasicBlock& block,
    const BlockMemoryContract& contract,
    const BoundedEventMetadata& event_metadata) noexcept {

    BlockTimingClassification result{};
    result.estimated_cycles = static_cast<uint32_t>(block.instructions.size() * 2);

    // 1. DMA check: if SCU DMA or concurrent transfer is active
    if (event_metadata.scu_dma_crossing) {
        result.boundary_type = ExecutionBoundaryType::DMA_ASYNCHRONOUS;
        result.is_timing_sensitive = true;
        result.requires_synchronization_barrier = true;
        result.requires_interpreter_fallback = true;
        result.boundary_reason = "SCU DMA active across block execution span";
        return result;
    }

    // 2. Interrupt check: if an IRQ is accepted or pending in the window
    if (event_metadata.irq_accepted) {
        result.boundary_type = ExecutionBoundaryType::INTERRUPT_WINDOW;
        result.is_timing_sensitive = true;
        result.requires_synchronization_barrier = true;
        result.requires_interpreter_fallback = true;
        result.boundary_reason = "Interrupt accepted during block execution window";
        return result;
    }

    // 3. MMIO check: inspect event metadata or memory contract accesses
    if (event_metadata.mmio_accessed) {
        result.boundary_type = ExecutionBoundaryType::MMIO_SYNCHRONOUS;
        result.is_timing_sensitive = true;
        result.requires_synchronization_barrier = true;
        result.requires_interpreter_fallback = false;
        result.boundary_reason = "Direct MMIO register accessed";
        return result;
    }

    // Inspect static memory contract dependencies for MMIO addresses
    for (const auto& dep : contract.dependencies) {
        if (dep.region_class == MemoryRegionClass::MMIO_PROHIBITED) {
            result.boundary_type = ExecutionBoundaryType::MMIO_SYNCHRONOUS;
            result.is_timing_sensitive = true;
            result.requires_synchronization_barrier = true;
            result.requires_interpreter_fallback = false;
            result.boundary_reason = "Contract dependency classified as MMIO";
            return result;
        }
        if (dep.static_address.has_value() && is_saturn_mmio_address(*dep.static_address)) {
            result.boundary_type = ExecutionBoundaryType::MMIO_SYNCHRONOUS;
            result.is_timing_sensitive = true;
            result.requires_synchronization_barrier = true;
            result.requires_interpreter_fallback = false;
            result.boundary_reason = "Contract dependency accesses Saturn MMIO address";
            return result;
        }
    }

    // 4. Default: Atomic pure computation
    result.boundary_type = ExecutionBoundaryType::ATOMIC_COMPUTATION;
    result.is_timing_sensitive = false;
    result.requires_synchronization_barrier = false;
    result.requires_interpreter_fallback = false;
    result.boundary_reason = "Pure atomic CPU computation";
    return result;
}

} // namespace thor::recomp
