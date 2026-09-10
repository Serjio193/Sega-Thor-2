#include "thor/recomp/block_memory.hpp"
#include "thor/sh2/sh2_block.hpp"
#include "thor/sh2/sh2_memory.hpp"
#include "tests/sh2/test_framework.hpp"

#include <iostream>

using namespace thor::recomp;
using namespace thor::sh2;

static Sh2BasicBlock make_bb0() {
    Sh2FlatMemory mem;
    // 0x06004000..0x0600400A:
    // 66 11 (MOV.W @R1, R6)
    // 6F 03 (MOV R0, R15)
    // D4 17 (MOV.L @(0x5c, PC), R4)
    // 64 42 (MOV.L @R4, R4)
    // A0 03 (BRA 0x06004012)
    // 00 09 (NOP)
    const uint8_t bytes[] = {
        0x66, 0x11, 0x6F, 0x03, 0xD4, 0x17, 0x64, 0x42, 0xA0, 0x03, 0x00, 0x09
    };
    for (size_t i = 0; i < sizeof(bytes); ++i) {
        mem.write8(0x06004000u + static_cast<uint32_t>(i), bytes[i]);
    }
    return discover_basic_block(0x06004000u, mem);
}

static Sh2BasicBlock make_cand_block() {
    Sh2FlatMemory mem;
    // 0x06004280..0x06004288:
    // D5 36 (MOV.L @(0xd8, PC), R5)
    // D4 37 (MOV.L @(0xdc, PC), R4)
    // D3 37 (MOV.L @(0xdc, PC), R3)
    // 43 0B (JSR @R3)
    // 00 09 (NOP)
    const uint8_t bytes[] = {
        0xD5, 0x36, 0xD4, 0x37, 0xD3, 0x37, 0x43, 0x0B, 0x00, 0x09
    };
    for (size_t i = 0; i < sizeof(bytes); ++i) {
        mem.write8(0x06004280u + static_cast<uint32_t>(i), bytes[i]);
    }
    return discover_basic_block(0x06004280u, mem);
}

static void test_candidate_block_memory_contract() {
    Sh2BasicBlock cand = make_cand_block();
    auto opt_contract = derive_block_memory_contract(cand);
    THOR_ASSERT(opt_contract.has_value());

    const BlockMemoryContract& contract = *opt_contract;
    THOR_ASSERT(contract.block_start_pc == 0x06004280u);

    // Exactly 3 architectural data reads (JSR and NOP add zero data dependencies)
    THOR_ASSERT(contract.dependencies.size() == 3);

    // Dependency 0: 0x06004280 MOV.L @(disp, PC), R5 -> 0x0600435C
    const auto& dep0 = contract.dependencies[0];
    THOR_ASSERT(dep0.instruction_pc == 0x06004280u);
    THOR_ASSERT(dep0.access_kind == MemoryAccessKind::READ);
    THOR_ASSERT(dep0.width == MemoryAccessWidth::U32);
    THOR_ASSERT(dep0.address_source == AddressSourceKind::STATIC_ADDRESS);
    THOR_ASSERT(dep0.static_address.has_value() && *dep0.static_address == 0x0600435Cu);
    THOR_ASSERT(!dep0.source_register.has_value());
    THOR_ASSERT(dep0.region_class == MemoryRegionClass::RAM);

    // Dependency 1: 0x06004282 MOV.L @(disp, PC), R4 -> 0x06004360
    const auto& dep1 = contract.dependencies[1];
    THOR_ASSERT(dep1.instruction_pc == 0x06004282u);
    THOR_ASSERT(dep1.access_kind == MemoryAccessKind::READ);
    THOR_ASSERT(dep1.width == MemoryAccessWidth::U32);
    THOR_ASSERT(dep1.address_source == AddressSourceKind::STATIC_ADDRESS);
    THOR_ASSERT(dep1.static_address.has_value() && *dep1.static_address == 0x06004360u);
    THOR_ASSERT(!dep1.source_register.has_value());
    THOR_ASSERT(dep1.region_class == MemoryRegionClass::RAM);

    // Dependency 2: 0x06004284 MOV.L @(disp, PC), R3 -> 0x06004364
    const auto& dep2 = contract.dependencies[2];
    THOR_ASSERT(dep2.instruction_pc == 0x06004284u);
    THOR_ASSERT(dep2.access_kind == MemoryAccessKind::READ);
    THOR_ASSERT(dep2.width == MemoryAccessWidth::U32);
    THOR_ASSERT(dep2.address_source == AddressSourceKind::STATIC_ADDRESS);
    THOR_ASSERT(dep2.static_address.has_value() && *dep2.static_address == 0x06004364u);
    THOR_ASSERT(!dep2.source_register.has_value());
    THOR_ASSERT(dep2.region_class == MemoryRegionClass::RAM);

    std::cout << "  [OK] test_candidate_block_memory_contract\n";
}

static void test_bb0_memory_contract() {
    Sh2BasicBlock bb0 = make_bb0();
    auto opt_contract = derive_block_memory_contract(bb0);
    THOR_ASSERT(opt_contract.has_value());

    const BlockMemoryContract& contract = *opt_contract;
    THOR_ASSERT(contract.block_start_pc == 0x06004000u);

    // Exactly 3 architectural data reads: MOV.W @R1, MOV.L @(disp,PC), MOV.L @R4
    THOR_ASSERT(contract.dependencies.size() == 3);

    // Dependency 0: 0x06004000 MOV.W @R1, R6 -> READ_S16, REGISTER_AT_EXECUTION(1)
    const auto& dep0 = contract.dependencies[0];
    THOR_ASSERT(dep0.instruction_pc == 0x06004000u);
    THOR_ASSERT(dep0.access_kind == MemoryAccessKind::READ);
    THOR_ASSERT(dep0.width == MemoryAccessWidth::S16);
    THOR_ASSERT(dep0.address_source == AddressSourceKind::REGISTER_AT_EXECUTION);
    THOR_ASSERT(dep0.source_register.has_value() && *dep0.source_register == 1);
    THOR_ASSERT(!dep0.static_address.has_value());

    // Dependency 1: 0x06004004 MOV.L @(0x5c, PC), R4 -> READ_U32, STATIC_ADDRESS 0x06004064
    const auto& dep1 = contract.dependencies[1];
    THOR_ASSERT(dep1.instruction_pc == 0x06004004u);
    THOR_ASSERT(dep1.access_kind == MemoryAccessKind::READ);
    THOR_ASSERT(dep1.width == MemoryAccessWidth::U32);
    THOR_ASSERT(dep1.address_source == AddressSourceKind::STATIC_ADDRESS);
    THOR_ASSERT(dep1.static_address.has_value() && *dep1.static_address == 0x06004064u);
    THOR_ASSERT(!dep1.source_register.has_value());
    THOR_ASSERT(dep1.region_class == MemoryRegionClass::RAM);

    // Dependency 2: 0x06004006 MOV.L @R4, R4 -> READ_U32, REGISTER_AT_EXECUTION(4)
    const auto& dep2 = contract.dependencies[2];
    THOR_ASSERT(dep2.instruction_pc == 0x06004006u);
    THOR_ASSERT(dep2.access_kind == MemoryAccessKind::READ);
    THOR_ASSERT(dep2.width == MemoryAccessWidth::U32);
    THOR_ASSERT(dep2.address_source == AddressSourceKind::REGISTER_AT_EXECUTION);
    THOR_ASSERT(dep2.source_register.has_value() && *dep2.source_register == 4);
    THOR_ASSERT(!dep2.static_address.has_value());

    std::cout << "  [OK] test_bb0_memory_contract\n";
}

static void test_memory_contract_negative_controls() {
    // 1. Empty block fails closed
    Sh2BasicBlock empty_block{};
    THOR_ASSERT(!derive_block_memory_contract(empty_block).has_value());

    // 2. Block containing unknown opcode fails closed
    Sh2BasicBlock unk_block = make_bb0();
    unk_block.instructions[1].id = OpcodeId::UNKNOWN;
    THOR_ASSERT(!derive_block_memory_contract(unk_block).has_value());

    // 3. Static address pointing into prohibited MMIO fails closed
    Sh2BasicBlock mmio_block = make_cand_block();
    // Corrupt disp so ea points into SCU MMIO range 0x25FE0000
    // disp to produce 0x25FE0000:
    // ((0x06004280 + 4) & ~3) + disp * 4 = 0x25FE0000 -> disp = (0x25FE0000 - 0x06004284)/4
    mmio_block.instructions[0].disp = (0x25FE0000u - 0x06004284u) / 4u;
    THOR_ASSERT(!derive_block_memory_contract(mmio_block).has_value());

    // 4. MemoryRegionClass classification checks
    THOR_ASSERT(classify_memory_address(0x06004000u) == MemoryRegionClass::RAM);
    THOR_ASSERT(classify_memory_address(0x26004000u) == MemoryRegionClass::RAM);
    THOR_ASSERT(classify_memory_address(0x00200000u) == MemoryRegionClass::RAM);
    THOR_ASSERT(classify_memory_address(0x00000000u) == MemoryRegionClass::ROM);
    THOR_ASSERT(classify_memory_address(0x25FE0000u) == MemoryRegionClass::MMIO_PROHIBITED);
    THOR_ASSERT(classify_memory_address(0xFFFFFE10u) == MemoryRegionClass::MMIO_PROHIBITED);

    std::cout << "  [OK] test_memory_contract_negative_controls\n";
}

int main() {
    std::cout << "=== D9.2 Declarative Memory Dependency Contract Unit Tests ===\n";
    test_candidate_block_memory_contract();
    test_bb0_memory_contract();
    test_memory_contract_negative_controls();
    std::cout << "ALL BLOCK MEMORY TESTS PASSED.\n";
    return 0;
}
