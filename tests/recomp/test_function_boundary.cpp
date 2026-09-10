#include <iostream>
#include "tests/sh2/test_framework.hpp"
#include "thor/recomp/function_boundary.hpp"

using namespace thor::recomp;

static void test_canonical_catalog_entries() {
    const auto catalog = FunctionBoundaryCatalog::create_canonical_catalog();
    THOR_ASSERT(catalog.size() == 4);

    const auto* boot = catalog.find_by_entry(0x06004000);
    THOR_ASSERT(boot != nullptr);
    THOR_ASSERT(boot->function_id == "sub_06004000_boot");
    THOR_ASSERT(boot->entry_kind == FunctionEntryKind::MODULE_ENTRY);
    THOR_ASSERT(boot->is_verified);

    const auto* loader = catalog.find_by_entry(0x0600A0F8);
    THOR_ASSERT(loader != nullptr);
    THOR_ASSERT(loader->entry_kind == FunctionEntryKind::INDIRECT_CALL_TARGET);
    THOR_ASSERT(loader->exit_kind == FunctionExitKind::SUBROUTINE_RETURN);

    const auto* th2_low = catalog.find_by_entry(0x002E9910);
    THOR_ASSERT(th2_low != nullptr);
    THOR_ASSERT(th2_low->module_name == "TH2.LOW");

    const auto* set07 = catalog.find_by_entry(0x060D8000);
    THOR_ASSERT(set07 != nullptr);
    THOR_ASSERT(set07->module_name == "SET07.BIN");
}

static void test_lookup_by_id() {
    const auto catalog = FunctionBoundaryCatalog::create_canonical_catalog();

    const auto* f1 = catalog.find_by_id("sub_06004000_boot");
    THOR_ASSERT(f1 != nullptr);
    THOR_ASSERT(f1->entry_address == 0x06004000);

    const auto* f2 = catalog.find_by_id("sub_0600A0F8_load_file");
    THOR_ASSERT(f2 != nullptr);
    THOR_ASSERT(f2->entry_address == 0x0600A0F8);

    const auto* non_existent = catalog.find_by_id("sub_nonexistent");
    THOR_ASSERT(non_existent == nullptr);
}

static void test_find_containing_pc() {
    const auto catalog = FunctionBoundaryCatalog::create_canonical_catalog();

    // Entry point matches
    const auto* f_entry = catalog.find_containing_pc(0x06004000);
    THOR_ASSERT(f_entry != nullptr);
    THOR_ASSERT(f_entry->entry_address == 0x06004000);

    // Internal basic block matches
    const auto* f_block = catalog.find_containing_pc(0x06004280);
    THOR_ASSERT(f_block != nullptr);
    THOR_ASSERT(f_block->entry_address == 0x06004000);

    // Unregistered PC returns nullptr
    const auto* f_unknown = catalog.find_containing_pc(0x06001234);
    THOR_ASSERT(f_unknown == nullptr);
}

static void test_call_graph_relationships() {
    const auto catalog = FunctionBoundaryCatalog::create_canonical_catalog();

    // sub_06004000 calls sub_0600A0F8
    const auto callees = catalog.get_callees(0x06004000);
    THOR_ASSERT(callees.size() == 1);
    THOR_ASSERT(callees[0] == 0x0600A0F8);

    // sub_0600A0F8 callers include sub_06004000
    const auto callers = catalog.get_callers(0x0600A0F8);
    THOR_ASSERT(callers.size() == 1);
    THOR_ASSERT(callers[0] == 0x06004000);
}

static void test_registration_validation() {
    FunctionBoundaryCatalog catalog;

    // Valid function
    THOR_ASSERT(catalog.register_function(FunctionDescriptor{
        .function_id = "test_sub",
        .entry_address = 0x06001000,
        .module_name = "TEST.BIN"
    }));

    // Duplicate entry address rejected fail-closed
    THOR_ASSERT(!catalog.register_function(FunctionDescriptor{
        .function_id = "test_sub_dup",
        .entry_address = 0x06001000,
        .module_name = "TEST.BIN"
    }));

    // Empty ID rejected
    THOR_ASSERT(!catalog.register_function(FunctionDescriptor{
        .function_id = "",
        .entry_address = 0x06002000,
        .module_name = "TEST.BIN"
    }));

    // Zero address rejected
    THOR_ASSERT(!catalog.register_function(FunctionDescriptor{
        .function_id = "test_zero",
        .entry_address = 0,
        .module_name = "TEST.BIN"
    }));
}

static void test_string_conversions() {
    THOR_ASSERT(std::string(function_entry_kind_to_string(FunctionEntryKind::MODULE_ENTRY)) == "MODULE_ENTRY");
    THOR_ASSERT(std::string(function_entry_kind_to_string(FunctionEntryKind::DIRECT_CALL_TARGET)) == "DIRECT_CALL_TARGET");
    THOR_ASSERT(std::string(function_entry_kind_to_string(FunctionEntryKind::INDIRECT_CALL_TARGET)) == "INDIRECT_CALL_TARGET");
    THOR_ASSERT(std::string(function_entry_kind_to_string(FunctionEntryKind::EXCEPTION_VECTOR)) == "EXCEPTION_VECTOR");

    THOR_ASSERT(std::string(function_exit_kind_to_string(FunctionExitKind::SUBROUTINE_RETURN)) == "SUBROUTINE_RETURN");
    THOR_ASSERT(std::string(function_exit_kind_to_string(FunctionExitKind::EXCEPTION_RETURN)) == "EXCEPTION_RETURN");
    THOR_ASSERT(std::string(function_exit_kind_to_string(FunctionExitKind::TAIL_CALL)) == "TAIL_CALL");
    THOR_ASSERT(std::string(function_exit_kind_to_string(FunctionExitKind::NON_RETURNING)) == "NON_RETURNING");
}

int main() {
    std::cout << "Running test_function_boundary...\n";
    test_canonical_catalog_entries();
    test_lookup_by_id();
    test_find_containing_pc();
    test_call_graph_relationships();
    test_registration_validation();
    test_string_conversions();
    std::cout << "All test_function_boundary cases passed!\n";
    return 0;
}
