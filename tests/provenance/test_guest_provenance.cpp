#include <cassert>
#include <iostream>
#include <vector>
#include <string>

#include "thor/provenance/guest_address.hpp"
#include "thor/provenance/guest_view.hpp"
#include "thor/provenance/saturn_runtime_table.hpp"
#include "thor/sh2/sh2_memory.hpp"

using namespace thor::provenance;

void test_guest_address_basic() {
    std::cout << "[RUN] test_guest_address_basic...\n";

    GuestAddress<uint32_t> null_addr(0);
    assert(null_addr.is_null());
    assert(!null_addr);
    assert(null_addr.vma() == 0);

    GuestAddress<uint32_t> high_ram(0x06004000u);
    assert(!high_ram.is_null());
    assert(static_cast<bool>(high_ram));
    assert(high_ram.vma() == 0x06004000u);
    assert(high_ram.raw() == 0x06004000u);
    assert(high_ram.is_aligned());
    assert(high_ram.domain() == MemoryDomain::HIGH_WORK_RAM);

    // Alignment checking
    GuestAddress<uint32_t> unaligned_u32(0x06004001u);
    assert(!unaligned_u32.is_aligned());

    GuestAddress<uint16_t> aligned_u16(0x06004002u);
    assert(aligned_u16.is_aligned());

    GuestAddress<uint16_t> unaligned_u16(0x06004003u);
    assert(!unaligned_u16.is_aligned());

    GuestAddress<uint8_t> byte_addr(0x06004003u);
    assert(byte_addr.is_aligned());

    // Domain classification
    assert(GuestAddress<>(0x002DA000u).domain() == MemoryDomain::LOW_WORK_RAM);
    assert(GuestAddress<>(0x05C00000u).domain() == MemoryDomain::VDP1_VRAM);
    assert(GuestAddress<>(0x05E00000u).domain() == MemoryDomain::VDP2_VRAM);
    assert(GuestAddress<>(0x05A00000u).domain() == MemoryDomain::SOUND_RAM);
    assert(GuestAddress<>(0x05800000u).domain() == MemoryDomain::MMIO);
    assert(GuestAddress<>(0xFFFFFEE0u).domain() == MemoryDomain::MMIO);
    assert(GuestAddress<>(0x00000200u).domain() == MemoryDomain::BOOT_ROM);

    // Offsets and indexing
    auto offset_addr = high_ram.offset_bytes(16);
    assert(offset_addr.vma() == 0x06004010u);

    auto elem_addr = high_ram.element(4);
    assert(elem_addr.vma() == 0x06004010u);

    // Cast
    auto cast_addr = high_ram.cast<uint16_t>();
    assert(cast_addr.vma() == 0x06004000u);
    assert(cast_addr.is_aligned());

    std::cout << "  [PASS] test_guest_address_basic\n";
}

void test_guest_ptr_provenance() {
    std::cout << "[RUN] test_guest_ptr_provenance...\n";

    GuestPtr<uint32_t> ptr(0x06004000u, "0TH2.BIN", 0x0000u);
    assert(ptr.vma() == 0x06004000u);
    assert(ptr.is_aligned());
    assert(!ptr.is_null());
    assert(ptr.domain() == MemoryDomain::HIGH_WORK_RAM);
    assert(ptr.provenance().module_name == "0TH2.BIN");
    assert(ptr.provenance().file_offset == 0x0000u);

    // Provenance preservation on offset
    auto next_ptr = ptr.offset_bytes(0x20);
    assert(next_ptr.vma() == 0x06004020u);
    assert(next_ptr.provenance().module_name == "0TH2.BIN");
    assert(next_ptr.provenance().file_offset == 0x0020u);
    assert(next_ptr.domain() == MemoryDomain::HIGH_WORK_RAM);

    // Element indexing
    auto elem3 = ptr.element(3);
    assert(elem3.vma() == 0x0600400Cu);
    assert(elem3.provenance().file_offset == 0x000Cu);

    // Casting
    auto void_ptr = ptr.cast<void>();
    assert(void_ptr.vma() == 0x06004000u);
    assert(void_ptr.provenance().module_name == "0TH2.BIN");

    std::cout << "  [PASS] test_guest_ptr_provenance\n";
}

void test_guest_view_memory_access() {
    std::cout << "[RUN] test_guest_view_memory_access...\n";

    thor::sh2::Sh2FlatMemory mem;
    GuestView view(mem);

    // Write primitives via GuestView
    bool ok1 = view.write(GuestAddress<uint32_t>(0x06004000u), 0x12345678u);
    assert(ok1);
    bool ok2 = view.write(GuestAddress<uint16_t>(0x06004004u), static_cast<uint16_t>(0xABCDu));
    assert(ok2);
    bool ok3 = view.write(GuestAddress<uint8_t>(0x06004006u), static_cast<uint8_t>(0xEFu));
    assert(ok3);

    // Read back and verify big-endian layout in backing memory
    assert(mem.read8(0x06004000u) == 0x12);
    assert(mem.read8(0x06004001u) == 0x34);
    assert(mem.read8(0x06004002u) == 0x56);
    assert(mem.read8(0x06004003u) == 0x78);
    assert(mem.read16(0x06004004u) == 0xABCDu);
    assert(mem.read8(0x06004006u) == 0xEFu);

    // Read through GuestView
    auto r32 = view.read(GuestAddress<uint32_t>(0x06004000u));
    assert(r32.has_value() && *r32 == 0x12345678u);

    auto r16 = view.read(GuestAddress<uint16_t>(0x06004004u));
    assert(r16.has_value() && *r16 == 0xABCDu);

    auto r8 = view.read(GuestAddress<uint8_t>(0x06004006u));
    assert(r8.has_value() && *r8 == 0xEFu);

    // Fail-closed checks on unaligned accesses
    auto bad_r32 = view.read(GuestAddress<uint32_t>(0x06004001u));
    assert(!bad_r32.has_value());

    auto bad_r16 = view.read(GuestAddress<uint16_t>(0x06004003u));
    assert(!bad_r16.has_value());

    bool bad_w32 = view.write(GuestAddress<uint32_t>(0x06004001u), 0x99999999u);
    assert(!bad_w32);

    // Fail-closed checks on null addresses
    auto null_r32 = view.read(GuestAddress<uint32_t>(0));
    assert(!null_r32.has_value());

    bool null_w32 = view.write(GuestAddress<uint32_t>(0), 0x11111111u);
    assert(!null_w32);

    // String reading
    const char* str = "TH2.LOW";
    for (size_t i = 0; i < 8; ++i) {
        mem.write8(0x06081C20u + static_cast<uint32_t>(i), static_cast<uint8_t>(str[i]));
    }
    auto str_read = view.read_string(GuestAddress<char>(0x06081C20u));
    assert(str_read.has_value() && *str_read == "TH2.LOW");

    std::cout << "  [PASS] test_guest_view_memory_access\n";
}

void test_saturn_startup_table_provenance() {
    std::cout << "[RUN] test_saturn_startup_table_provenance...\n";

    thor::sh2::Sh2FlatMemory mem;
    GuestView view(mem);

    // Populate with verified Thor 2 boot table contents at 0x06081C04..0x06081C18
    const uint32_t exp_rom_src = 0x06080000u;
    const uint32_t exp_ram_dst = 0x06090000u;
    const uint32_t exp_ram_lim = 0x06091000u;
    const uint32_t exp_bss_st  = 0x060917DCu; // Proven value dynamically verified at cycle 305462363
    const uint32_t exp_bss_en  = 0x060A0000u;

    mem.write32(0x06081C04u, exp_rom_src);
    mem.write32(0x06081C08u, exp_ram_dst);
    mem.write32(0x06081C0Cu, exp_ram_lim);
    mem.write32(0x06081C10u, exp_bss_st);
    mem.write32(0x06081C14u, exp_bss_en);

    auto decoded = SaturnStartupTable::read_from(view);
    assert(decoded.has_value());
    assert(decoded->data_rom_src == exp_rom_src);
    assert(decoded->data_ram_dst == exp_ram_dst);
    assert(decoded->data_ram_limit == exp_ram_lim);
    assert(decoded->bss_start_addr == exp_bss_st);
    assert(decoded->bss_end_addr == exp_bss_en);
    assert(decoded->data_size() == 0x1000u);
    assert(decoded->bss_size() == (exp_bss_en - exp_bss_st));

    // File entry check
    SaturnFileLoadEntry file_entry{};
    assert(file_entry.name_address.vma() == 0x06081C20u);
    assert(file_entry.target_load_address.vma() == 0x002DA000u);
    assert(file_entry.expected_filename == "TH2.LOW");

    std::cout << "  [PASS] test_saturn_startup_table_provenance\n";
}

void test_differential_equivalence() {
    std::cout << "[RUN] test_differential_equivalence...\n";

    thor::sh2::Sh2FlatMemory mem;
    GuestView view(mem);

    // Write 64 entries of test pattern
    for (uint32_t i = 0; i < 64; ++i) {
        uint32_t addr = 0x06010000u + (i * 4);
        uint32_t pattern = 0xCAFEBABE + (i * 0x1001);
        mem.write32(addr, pattern);
    }

    // Verify 100% equivalence: reading through GuestView/GuestPtr matches raw ISh2Memory::read32 bit-for-bit
    GuestPtr<uint32_t> base_ptr(0x06010000u, "0TH2.BIN", 0xC000u);
    for (uint32_t i = 0; i < 64; ++i) {
        auto entry_ptr = base_ptr.element(i);
        uint32_t raw_val = mem.read32(entry_ptr.vma());
        auto typed_val = view.read(entry_ptr);

        assert(typed_val.has_value());
        assert(*typed_val == raw_val);
        assert(entry_ptr.provenance().file_offset == (0xC000u + i * 4));
    }

    std::cout << "  [PASS] test_differential_equivalence\n";
}

int main() {
    std::cout << "=== RUNNING GATE V-09 / D13 GUEST PROVENANCE TEST SUITE ===\n";
    test_guest_address_basic();
    test_guest_ptr_provenance();
    test_guest_view_memory_access();
    test_saturn_startup_table_provenance();
    test_differential_equivalence();
    std::cout << "=== ALL GUEST PROVENANCE TESTS PASSED (V-09: PASS) ===\n";
    return 0;
}
