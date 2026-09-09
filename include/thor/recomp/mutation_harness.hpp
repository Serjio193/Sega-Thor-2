#pragma once

#include <cstdint>
#include <string>
#include <vector>

#include "thor/sh2/sh2_memory.hpp"

namespace thor::recomp {

enum class MutationKind {
    BYTE_FLIP,
    NOP_INSTRUCTION,
    ARBITRARY_BYTES
};

enum class MutationStatus {
    SUCCESS,
    SPEC_INVALID,
    ORIGINAL_MISMATCH,
    RANGE_UNAUTHORIZED,
    APPLY_VERIFY_FAILED,
    RESTORE_PRECONDITION_FAILED,
    RESTORE_VERIFY_FAILED
};

struct MutationSpec {
    uint32_t address = 0;
    std::vector<uint8_t> expected_original;
    std::vector<uint8_t> replacement_bytes;
    MutationKind kind = MutationKind::ARBITRARY_BYTES;
    std::string description;
};

struct MutationResult {
    MutationStatus status = MutationStatus::SPEC_INVALID;
    bool mutation_applied = false;
    bool restoration_verified = false;
    std::string detail;
};

class GuestMutationHarness {
public:
    GuestMutationHarness(uint32_t auth_start, uint32_t auth_size);

    MutationStatus validate_spec(
        const MutationSpec& spec,
        std::string& out_detail
    ) const;

    MutationResult apply_and_verify(
        thor::sh2::ISh2Memory& memory,
        const MutationSpec& spec
    );

    MutationResult restore_and_verify(
        thor::sh2::ISh2Memory& memory,
        const MutationSpec& spec
    );

    static MutationSpec create_nop_mutation(
        uint32_t instruction_addr,
        uint16_t expected_opcode,
        const std::string& desc = "SH-2 NOP replacement"
    );

    static MutationSpec create_byte_flip(
        uint32_t byte_addr,
        uint8_t expected_byte,
        uint8_t bit_mask = 0x01,
        const std::string& desc = "Single bit flip"
    );

    uint32_t authorized_start() const { return m_auth_start; }
    uint32_t authorized_size() const { return m_auth_size; }

private:
    uint32_t m_auth_start;
    uint32_t m_auth_size;
};

} // namespace thor::recomp
