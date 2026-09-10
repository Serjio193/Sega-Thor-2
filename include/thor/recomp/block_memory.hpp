#pragma once

#include <cstdint>
#include <optional>
#include <vector>
#include "thor/sh2/sh2_block.hpp"
#include "thor/sh2/sh2_types.hpp"

namespace thor::recomp {

enum class AddressSourceKind : uint8_t {
    STATIC_ADDRESS = 0,
    REGISTER_AT_EXECUTION
};

enum class MemoryAccessWidth : uint8_t {
    U8 = 1,
    S8 = 2,
    U16 = 3,
    S16 = 4,
    U32 = 5
};

enum class MemoryRegionClass : uint8_t {
    RAM = 0,
    ROM,
    MMIO_PROHIBITED,
    UNKNOWN
};

struct MemoryDependencyDescriptor {
    uint32_t instruction_pc = 0;
    thor::sh2::MemoryAccessKind access_kind = thor::sh2::MemoryAccessKind::READ;
    MemoryAccessWidth width = MemoryAccessWidth::U32;
    AddressSourceKind address_source = AddressSourceKind::STATIC_ADDRESS;
    std::optional<uint32_t> static_address = std::nullopt;
    std::optional<uint8_t> source_register = std::nullopt;
    MemoryRegionClass region_class = MemoryRegionClass::RAM;

    bool operator==(const MemoryDependencyDescriptor& other) const = default;
};

struct BlockMemoryContract {
    uint32_t block_start_pc = 0;
    std::vector<MemoryDependencyDescriptor> dependencies{};

    bool operator==(const BlockMemoryContract& other) const = default;
};

/// Classifies a guest memory address into RAM, ROM, MMIO_PROHIBITED, or UNKNOWN.
[[nodiscard]] MemoryRegionClass classify_memory_address(uint32_t addr) noexcept;

/// Deterministically derives the BlockMemoryContract from an Sh2BasicBlock.
/// Returns std::nullopt if the block contains instructions whose memory behavior
/// is unsupported, unrepresentable, or accesses prohibited MMIO addresses.
[[nodiscard]] std::optional<BlockMemoryContract> derive_block_memory_contract(
    const thor::sh2::Sh2BasicBlock& block
) noexcept;

} // namespace thor::recomp
