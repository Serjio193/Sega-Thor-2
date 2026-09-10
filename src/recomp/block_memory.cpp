#include "thor/recomp/block_memory.hpp"

namespace thor::recomp {

MemoryRegionClass classify_memory_address(uint32_t addr) noexcept {
    // High Work RAM: 0x06000000 .. 0x060FFFFF (mirror up to 0x06FFFFFF, uncached mirror 0x26000000..0x260FFFFF)
    if ((addr >= 0x06000000u && addr <= 0x060FFFFFu) ||
        (addr >= 0x26000000u && addr <= 0x260FFFFFu)) {
        return MemoryRegionClass::RAM;
    }
    // Low Work RAM: 0x00200000 .. 0x002FFFFF (uncached mirror 0x20200000..0x202FFFFF)
    if ((addr >= 0x00200000u && addr <= 0x002FFFFFu) ||
        (addr >= 0x20200000u && addr <= 0x202FFFFFu)) {
        return MemoryRegionClass::RAM;
    }
    // BIOS / Boot ROM: 0x00000000 .. 0x0007FFFF
    if (addr <= 0x0007FFFFu) {
        return MemoryRegionClass::ROM;
    }
    // MMIO areas: SCU (0x25FE0000..), VDP1/VDP2 (0x25C00000..0x25EFFFFF),
    // SCSP (0x25B00000..), CD-block (0x25890000..)
    if ((addr >= 0x25800000u && addr <= 0x25FFFFFFu) ||
        (addr >= 0x05800000u && addr <= 0x05FFFFFFu)) {
        return MemoryRegionClass::MMIO_PROHIBITED;
    }
    // SH-2 on-chip registers / peripheral area: 0xFFFFFE00 .. 0xFFFFFFFF
    if (addr >= 0xFFFFFE00u) {
        return MemoryRegionClass::MMIO_PROHIBITED;
    }
    return MemoryRegionClass::UNKNOWN;
}

bool validate_runtime_memory_dependency(
    const MemoryDependencyDescriptor& dep,
    uint32_t runtime_address
) noexcept {
    const uint32_t num_bytes = memory_access_width_bytes(dep.width);
    if (num_bytes == 0 || num_bytes > 4) {
        return false;
    }
    // Checked address wrap: runtime_address + (num_bytes - 1) must not overflow uint32
    if (runtime_address > UINT32_MAX - (num_bytes - 1u)) {
        return false;
    }

    const MemoryRegionClass start_reg = classify_memory_address(runtime_address);
    if (start_reg == MemoryRegionClass::MMIO_PROHIBITED || start_reg == MemoryRegionClass::UNKNOWN) {
        return false; // Prohibited MMIO or unclassified unknown region fails closed
    }

    // Validate entire access interval: all accessed bytes must remain within the same permitted region
    for (uint32_t i = 1; i < num_bytes; ++i) {
        const uint32_t byte_addr = runtime_address + i;
        const MemoryRegionClass byte_reg = classify_memory_address(byte_addr);
        if (byte_reg != start_reg) {
            return false;
        }
    }

    if (dep.address_source == AddressSourceKind::STATIC_ADDRESS) {
        if (!dep.static_address.has_value() || *dep.static_address != runtime_address) {
            return false;
        }
        return (start_reg == dep.region_class);
    }

    // For REGISTER_AT_EXECUTION:
    return (start_reg == MemoryRegionClass::RAM || start_reg == MemoryRegionClass::ROM);
}

std::optional<BlockMemoryContract> derive_block_memory_contract(
    const thor::sh2::Sh2BasicBlock& block
) noexcept {
    if (block.instructions.empty()) {
        return std::nullopt;
    }

    BlockMemoryContract contract{};
    contract.block_start_pc = block.start_address;

    for (const auto& ins : block.instructions) {
        switch (ins.id) {
        case thor::sh2::OpcodeId::MOV_W_READ_MEM: {
            MemoryDependencyDescriptor dep{};
            dep.instruction_pc = ins.pc;
            dep.access_kind = thor::sh2::MemoryAccessKind::READ;
            dep.width = MemoryAccessWidth::S16;
            dep.address_source = AddressSourceKind::REGISTER_AT_EXECUTION;
            dep.source_register = ins.rm;
            dep.static_address = std::nullopt;
            dep.region_class = MemoryRegionClass::RUNTIME_CLASSIFICATION_REQUIRED;
            contract.dependencies.push_back(dep);
            break;
        }

        case thor::sh2::OpcodeId::MOV_L_PC_REL: {
            const uint32_t ea = ((ins.pc + 4u) & ~3u) + (ins.disp * 4u);
            const MemoryRegionClass reg = classify_memory_address(ea);
            if (reg == MemoryRegionClass::MMIO_PROHIBITED) {
                return std::nullopt; // MMIO static access fails closed
            }
            MemoryDependencyDescriptor dep{};
            dep.instruction_pc = ins.pc;
            dep.access_kind = thor::sh2::MemoryAccessKind::READ;
            dep.width = MemoryAccessWidth::U32;
            dep.address_source = AddressSourceKind::STATIC_ADDRESS;
            dep.static_address = ea;
            dep.source_register = std::nullopt;
            dep.region_class = reg;
            contract.dependencies.push_back(dep);
            break;
        }

        case thor::sh2::OpcodeId::MOV_L_READ_MEM: {
            MemoryDependencyDescriptor dep{};
            dep.instruction_pc = ins.pc;
            dep.access_kind = thor::sh2::MemoryAccessKind::READ;
            dep.width = MemoryAccessWidth::U32;
            dep.address_source = AddressSourceKind::REGISTER_AT_EXECUTION;
            dep.source_register = ins.rm;
            dep.static_address = std::nullopt;
            dep.region_class = MemoryRegionClass::RUNTIME_CLASSIFICATION_REQUIRED;
            contract.dependencies.push_back(dep);
            break;
        }

        case thor::sh2::OpcodeId::MOV_REG:
        case thor::sh2::OpcodeId::BRA:
        case thor::sh2::OpcodeId::NOP:
        case thor::sh2::OpcodeId::JSR:
            // These instructions have NO architectural data memory dependencies.
            break;

        default:
            // Unsupported instruction memory behavior fails closed
            return std::nullopt;
        }
    }

    return contract;
}

} // namespace thor::recomp
