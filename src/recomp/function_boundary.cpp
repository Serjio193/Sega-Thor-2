#include "thor/recomp/function_boundary.hpp"
#include <algorithm>

namespace thor::recomp {

const char* function_entry_kind_to_string(FunctionEntryKind kind) noexcept {
    switch (kind) {
    case FunctionEntryKind::MODULE_ENTRY:
        return "MODULE_ENTRY";
    case FunctionEntryKind::DIRECT_CALL_TARGET:
        return "DIRECT_CALL_TARGET";
    case FunctionEntryKind::INDIRECT_CALL_TARGET:
        return "INDIRECT_CALL_TARGET";
    case FunctionEntryKind::EXCEPTION_VECTOR:
        return "EXCEPTION_VECTOR";
    default:
        return "UNKNOWN";
    }
}

const char* function_exit_kind_to_string(FunctionExitKind kind) noexcept {
    switch (kind) {
    case FunctionExitKind::SUBROUTINE_RETURN:
        return "SUBROUTINE_RETURN";
    case FunctionExitKind::EXCEPTION_RETURN:
        return "EXCEPTION_RETURN";
    case FunctionExitKind::TAIL_CALL:
        return "TAIL_CALL";
    case FunctionExitKind::NON_RETURNING:
        return "NON_RETURNING";
    default:
        return "UNKNOWN";
    }
}

bool FunctionBoundaryCatalog::register_function(FunctionDescriptor func) {
    if (func.entry_address == 0 || func.function_id.empty()) {
        return false;
    }
    if (m_by_entry.find(func.entry_address) != m_by_entry.end()) {
        return false;
    }

    const uint32_t entry = func.entry_address;
    for (uint32_t callee : func.callees) {
        m_callers_map[callee].push_back(entry);
    }

    m_by_id[func.function_id] = entry;
    m_by_entry[entry] = std::move(func);
    return true;
}

const FunctionDescriptor* FunctionBoundaryCatalog::find_by_entry(uint32_t entry_address) const noexcept {
    auto it = m_by_entry.find(entry_address);
    if (it != m_by_entry.end()) {
        return &it->second;
    }
    return nullptr;
}

const FunctionDescriptor* FunctionBoundaryCatalog::find_by_id(const std::string& id) const noexcept {
    auto it = m_by_id.find(id);
    if (it != m_by_id.end()) {
        return find_by_entry(it->second);
    }
    return nullptr;
}

const FunctionDescriptor* FunctionBoundaryCatalog::find_containing_pc(uint32_t pc) const noexcept {
    for (const auto& [entry, desc] : m_by_entry) {
        if (entry == pc) {
            return &desc;
        }
        for (uint32_t bb_addr : desc.basic_block_addresses) {
            if (bb_addr == pc) {
                return &desc;
            }
        }
    }
    return nullptr;
}

std::vector<uint32_t> FunctionBoundaryCatalog::get_callees(uint32_t caller_entry) const {
    const auto* desc = find_by_entry(caller_entry);
    if (desc != nullptr) {
        return desc->callees;
    }
    return {};
}

std::vector<uint32_t> FunctionBoundaryCatalog::get_callers(uint32_t callee_entry) const {
    auto it = m_callers_map.find(callee_entry);
    if (it != m_callers_map.end()) {
        return it->second;
    }
    return {};
}

FunctionBoundaryCatalog FunctionBoundaryCatalog::create_canonical_catalog() {
    FunctionBoundaryCatalog catalog;

    // 1. Primary entry subroutine in 0TH2.BIN
    catalog.register_function(FunctionDescriptor{
        .function_id = "sub_06004000_boot",
        .entry_address = 0x06004000,
        .module_name = "0TH2.BIN",
        .entry_kind = FunctionEntryKind::MODULE_ENTRY,
        .exit_kind = FunctionExitKind::NON_RETURNING,
        .basic_block_addresses = {0x06004000, 0x06004012, 0x06004280},
        .return_addresses = {},
        .callees = {0x0600A0F8},
        .is_verified = true
    });

    // 2. CD block file loader subroutine in 0TH2.BIN
    catalog.register_function(FunctionDescriptor{
        .function_id = "sub_0600A0F8_load_file",
        .entry_address = 0x0600A0F8,
        .module_name = "0TH2.BIN",
        .entry_kind = FunctionEntryKind::INDIRECT_CALL_TARGET,
        .exit_kind = FunctionExitKind::SUBROUTINE_RETURN,
        .basic_block_addresses = {0x0600A0F8},
        .return_addresses = {0x0600428A},
        .callees = {},
        .is_verified = true
    });

    // 3. Low Work RAM engine entry subroutine in TH2.LOW
    catalog.register_function(FunctionDescriptor{
        .function_id = "sub_002E9910_engine_start",
        .entry_address = 0x002E9910,
        .module_name = "TH2.LOW",
        .entry_kind = FunctionEntryKind::MODULE_ENTRY,
        .exit_kind = FunctionExitKind::NON_RETURNING,
        .basic_block_addresses = {0x002E9910},
        .return_addresses = {},
        .callees = {},
        .is_verified = true
    });

    // 4. Stage overlay entry subroutine in SET07.BIN
    catalog.register_function(FunctionDescriptor{
        .function_id = "sub_060D8000_stage_overlay",
        .entry_address = 0x060D8000,
        .module_name = "SET07.BIN",
        .entry_kind = FunctionEntryKind::MODULE_ENTRY,
        .exit_kind = FunctionExitKind::NON_RETURNING,
        .basic_block_addresses = {0x060D8000},
        .return_addresses = {},
        .callees = {},
        .is_verified = true
    });

    return catalog;
}

} // namespace thor::recomp
