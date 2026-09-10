#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include "thor/sh2/sh2_memory.hpp"

namespace thor::recomp {

enum class CpuTarget : uint8_t {
    MASTER_SH2 = 0,
    SLAVE_SH2
};

enum class BlockValidity : uint8_t {
    VALID = 0,
    INVALIDATED,
    UNVERIFIED
};

enum class EligibilityResult : uint8_t {
    ELIGIBLE = 0,
    REVISION_MISMATCH,
    MODULE_MISMATCH,
    PROVENANCE_NOT_PROVEN,
    CPU_MISMATCH,
    ADDRESS_RANGE_MISMATCH,
    CONTENT_BYTE_MISMATCH,
    GENERATION_MISMATCH,
    INVALID_STATE
};

[[nodiscard]] const char* eligibility_result_to_string(EligibilityResult result) noexcept;

struct BlockIdentityDescriptor {
    std::string revision_id;
    std::string module_name;
    bool module_provenance_proven = false;
    CpuTarget cpu = CpuTarget::MASTER_SH2;
    uint32_t generation = 0;
    uint32_t start_pc = 0;
    uint32_t end_pc = 0;
    std::vector<uint8_t> expected_bytes;
    BlockValidity validity = BlockValidity::VALID;
};

/// Reusable fail-closed eligibility guard for native / generated execution.
/// Inspects memory using peek8 (host-side observation) to ensure zero guest access log contamination.
[[nodiscard]] EligibilityResult check_block_eligibility(
    const BlockIdentityDescriptor& proven_desc,
    const BlockIdentityDescriptor& query_desc,
    const thor::sh2::ISh2Memory& memory) noexcept;

/// Constructs the proven canonical descriptor for Thor 2 startup block bb_06004000.
[[nodiscard]] BlockIdentityDescriptor make_bb_06004000_descriptor();

/// Constructs the proven canonical descriptor for Thor 2 indirect candidate block bb_06004280.
[[nodiscard]] BlockIdentityDescriptor make_bb_06004280_descriptor();

/// Constructs the proven canonical descriptor for Thor 2 stage overlay block bb_060D8000 (SET07.BIN).
[[nodiscard]] BlockIdentityDescriptor make_bb_060D8000_set07_descriptor();

} // namespace thor::recomp
