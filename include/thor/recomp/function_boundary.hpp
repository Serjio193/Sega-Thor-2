#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace thor::recomp {

enum class FunctionEntryKind : uint8_t {
    MODULE_ENTRY = 0,       // Primary module or overlay execution entrypoint
    DIRECT_CALL_TARGET,     // Target of BSR or JSR instruction
    INDIRECT_CALL_TARGET,   // Target of JSR @Rn resolved at runtime
    EXCEPTION_VECTOR        // Target of CPU or interrupt exception vector
};

enum class FunctionExitKind : uint8_t {
    SUBROUTINE_RETURN = 0,  // Terminated by RTS with delay slot
    EXCEPTION_RETURN,       // Terminated by RTE with delay slot
    TAIL_CALL,              // Terminated by branch/jump to another function
    NON_RETURNING           // Halts, loops indefinitely, or transfers execution irrevocably
};

[[nodiscard]] const char* function_entry_kind_to_string(FunctionEntryKind kind) noexcept;
[[nodiscard]] const char* function_exit_kind_to_string(FunctionExitKind kind) noexcept;

/// Evidence-backed function descriptor.
/// Per AGENTS.md, function boundaries are hypotheses over CFG evidence, not unverified assumptions.
struct FunctionDescriptor {
    std::string function_id{};
    uint32_t entry_address = 0;
    std::string module_name{};
    FunctionEntryKind entry_kind = FunctionEntryKind::DIRECT_CALL_TARGET;
    FunctionExitKind exit_kind = FunctionExitKind::SUBROUTINE_RETURN;
    std::vector<uint32_t> basic_block_addresses{};
    std::vector<uint32_t> return_addresses{};
    std::vector<uint32_t> callees{};
    bool is_verified = false;
};

/// Evidence-backed catalog of recovered functions and call graphs.
class FunctionBoundaryCatalog {
public:
    FunctionBoundaryCatalog() = default;

    bool register_function(FunctionDescriptor func);

    [[nodiscard]] const FunctionDescriptor* find_by_entry(uint32_t entry_address) const noexcept;
    [[nodiscard]] const FunctionDescriptor* find_by_id(const std::string& id) const noexcept;
    [[nodiscard]] const FunctionDescriptor* find_containing_pc(uint32_t pc) const noexcept;

    [[nodiscard]] std::vector<uint32_t> get_callees(uint32_t caller_entry) const;
    [[nodiscard]] std::vector<uint32_t> get_callers(uint32_t callee_entry) const;

    [[nodiscard]] size_t size() const noexcept { return m_by_entry.size(); }

    /// Populates canonical catalog with verified Thor 2 primary subroutines.
    static FunctionBoundaryCatalog create_canonical_catalog();

private:
    std::unordered_map<uint32_t, FunctionDescriptor> m_by_entry{};
    std::unordered_map<std::string, uint32_t> m_by_id{};
    std::unordered_map<uint32_t, std::vector<uint32_t>> m_callers_map{};
};

} // namespace thor::recomp
