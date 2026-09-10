#include <iostream>
#include "tests/sh2/test_framework.hpp"
#include "thor/recomp/block_timing.hpp"

using namespace thor::recomp;
using namespace thor::sh2;

static void test_atomic_computation() {
    Sh2BasicBlock block{};
    block.start_address = 0x06004000;
    block.end_address = 0x06004008;
    block.instructions.resize(4);

    BlockMemoryContract contract{};
    BoundedEventMetadata event_meta{};
    event_meta.mmio_accessed = false;
    event_meta.irq_accepted = false;
    event_meta.scu_dma_crossing = false;
    event_meta.slave_sh2_active = false;
    event_meta.delay_slot_atomic = true;

    const auto result = classify_block_timing(block, contract, event_meta);
    THOR_ASSERT(result.boundary_type == ExecutionBoundaryType::ATOMIC_COMPUTATION);
    THOR_ASSERT(!result.is_timing_sensitive);
    THOR_ASSERT(!result.requires_synchronization_barrier);
    THOR_ASSERT(!result.requires_interpreter_fallback);
    THOR_ASSERT(result.estimated_cycles == 8);
}

static void test_mmio_event_classification() {
    Sh2BasicBlock block{};
    block.instructions.resize(2);

    BlockMemoryContract contract{};
    BoundedEventMetadata event_meta{};
    event_meta.mmio_accessed = true;

    const auto result = classify_block_timing(block, contract, event_meta);
    THOR_ASSERT(result.boundary_type == ExecutionBoundaryType::MMIO_SYNCHRONOUS);
    THOR_ASSERT(result.is_timing_sensitive);
    THOR_ASSERT(result.requires_synchronization_barrier);
    THOR_ASSERT(!result.requires_interpreter_fallback);
}

static void test_contract_mmio_detection() {
    Sh2BasicBlock block{};
    block.instructions.resize(3);

    // VDP2 register access (e.g. 0x25F80000 or mirror 0x05F80000)
    BlockMemoryContract contract{};
    contract.dependencies.push_back({
        .instruction_pc = 0x06004000,
        .access_kind = thor::sh2::MemoryAccessKind::WRITE,
        .width = MemoryAccessWidth::U32,
        .address_source = AddressSourceKind::STATIC_ADDRESS,
        .static_address = 0x25F80000,
        .region_class = MemoryRegionClass::MMIO_PROHIBITED
    });

    BoundedEventMetadata event_meta{};

    const auto result = classify_block_timing(block, contract, event_meta);
    THOR_ASSERT(result.boundary_type == ExecutionBoundaryType::MMIO_SYNCHRONOUS);
    THOR_ASSERT(result.is_timing_sensitive);
    THOR_ASSERT(result.requires_synchronization_barrier);
}

static void test_interrupt_window_classification() {
    Sh2BasicBlock block{};
    block.instructions.resize(5);

    BlockMemoryContract contract{};
    BoundedEventMetadata event_meta{};
    event_meta.irq_accepted = true;

    const auto result = classify_block_timing(block, contract, event_meta);
    THOR_ASSERT(result.boundary_type == ExecutionBoundaryType::INTERRUPT_WINDOW);
    THOR_ASSERT(result.is_timing_sensitive);
    THOR_ASSERT(result.requires_synchronization_barrier);
    THOR_ASSERT(result.requires_interpreter_fallback);
}

static void test_dma_crossing_classification() {
    Sh2BasicBlock block{};
    block.instructions.resize(6);

    BlockMemoryContract contract{};
    BoundedEventMetadata event_meta{};
    event_meta.scu_dma_crossing = true;

    const auto result = classify_block_timing(block, contract, event_meta);
    THOR_ASSERT(result.boundary_type == ExecutionBoundaryType::DMA_ASYNCHRONOUS);
    THOR_ASSERT(result.is_timing_sensitive);
    THOR_ASSERT(result.requires_synchronization_barrier);
    THOR_ASSERT(result.requires_interpreter_fallback);
}

static void test_address_check_and_string_conversions() {
    THOR_ASSERT(is_saturn_mmio_address(0xFFFFFE00));
    THOR_ASSERT(is_saturn_mmio_address(0xFFFFFFFF));
    THOR_ASSERT(is_saturn_mmio_address(0x25F80000));
    THOR_ASSERT(is_saturn_mmio_address(0x05F80000));
    THOR_ASSERT(!is_saturn_mmio_address(0x06004000));
    THOR_ASSERT(!is_saturn_mmio_address(0x002DA000));

    THOR_ASSERT(std::string(execution_boundary_type_to_string(ExecutionBoundaryType::ATOMIC_COMPUTATION)) == "ATOMIC_COMPUTATION");
    THOR_ASSERT(std::string(execution_boundary_type_to_string(ExecutionBoundaryType::MMIO_SYNCHRONOUS)) == "MMIO_SYNCHRONOUS");
    THOR_ASSERT(std::string(execution_boundary_type_to_string(ExecutionBoundaryType::INTERRUPT_WINDOW)) == "INTERRUPT_WINDOW");
    THOR_ASSERT(std::string(execution_boundary_type_to_string(ExecutionBoundaryType::DMA_ASYNCHRONOUS)) == "DMA_ASYNCHRONOUS");
}

int main() {
    std::cout << "Running test_block_timing...\n";
    test_atomic_computation();
    test_mmio_event_classification();
    test_contract_mmio_detection();
    test_interrupt_window_classification();
    test_dma_crossing_classification();
    test_address_check_and_string_conversions();
    std::cout << "All test_block_timing cases passed!\n";
    return 0;
}
