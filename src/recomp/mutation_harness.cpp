#include "thor/recomp/mutation_harness.hpp"

namespace thor::recomp {

GuestMutationHarness::GuestMutationHarness(uint32_t auth_start, uint32_t auth_size)
    : m_auth_start(auth_start), m_auth_size(auth_size) {}

MutationResult GuestMutationHarness::apply_and_verify(
    thor::sh2::ISh2Memory& memory,
    const MutationSpec& spec
) {
    MutationResult res;
    if (spec.replacement_bytes.empty()) {
        res.status = MutationStatus::APPLY_VERIFY_FAILED;
        res.detail = "Empty replacement bytes";
        return res;
    }

    uint64_t end_addr = static_cast<uint64_t>(spec.address) + spec.replacement_bytes.size();
    if (spec.address < m_auth_start || end_addr > (static_cast<uint64_t>(m_auth_start) + m_auth_size)) {
        res.status = MutationStatus::RANGE_UNAUTHORIZED;
        res.detail = "Mutation target address outside authorized range";
        return res;
    }

    // Verify original bytes
    if (!spec.expected_original.empty()) {
        for (size_t i = 0; i < spec.expected_original.size(); ++i) {
            uint8_t actual = memory.read8(spec.address + static_cast<uint32_t>(i));
            if (actual != spec.expected_original[i]) {
                res.status = MutationStatus::ORIGINAL_MISMATCH;
                res.detail = "Pre-mutation byte mismatch at address " + std::to_string(spec.address + i);
                return res;
            }
        }
    }

    // Apply mutation
    for (size_t i = 0; i < spec.replacement_bytes.size(); ++i) {
        memory.write8(spec.address + static_cast<uint32_t>(i), spec.replacement_bytes[i]);
    }

    // Verify applied
    for (size_t i = 0; i < spec.replacement_bytes.size(); ++i) {
        uint8_t actual = memory.read8(spec.address + static_cast<uint32_t>(i));
        if (actual != spec.replacement_bytes[i]) {
            res.status = MutationStatus::APPLY_VERIFY_FAILED;
            res.detail = "Post-mutation byte verification failed";
            return res;
        }
    }

    res.status = MutationStatus::SUCCESS;
    res.mutation_applied = true;
    res.detail = "Mutation applied and verified";
    return res;
}

MutationResult GuestMutationHarness::restore_and_verify(
    thor::sh2::ISh2Memory& memory,
    const MutationSpec& spec
) {
    MutationResult res;
    if (spec.expected_original.empty()) {
        res.status = MutationStatus::RESTORE_VERIFY_FAILED;
        res.detail = "Cannot restore without expected original bytes";
        return res;
    }

    // Restore original bytes
    for (size_t i = 0; i < spec.expected_original.size(); ++i) {
        memory.write8(spec.address + static_cast<uint32_t>(i), spec.expected_original[i]);
    }

    // Verify restore
    for (size_t i = 0; i < spec.expected_original.size(); ++i) {
        uint8_t actual = memory.read8(spec.address + static_cast<uint32_t>(i));
        if (actual != spec.expected_original[i]) {
            res.status = MutationStatus::RESTORE_VERIFY_FAILED;
            res.detail = "Restored byte verification failed";
            return res;
        }
    }

    res.status = MutationStatus::SUCCESS;
    res.restoration_verified = true;
    res.detail = "Restoration applied and verified";
    return res;
}

MutationSpec GuestMutationHarness::create_nop_mutation(
    uint32_t instruction_addr,
    uint16_t expected_opcode,
    const std::string& desc
) {
    MutationSpec spec;
    spec.address = instruction_addr;
    spec.expected_original = {
        static_cast<uint8_t>(expected_opcode >> 8),
        static_cast<uint8_t>(expected_opcode & 0xFF)
    };
    spec.replacement_bytes = {0x00, 0x09}; // SH-2 NOP
    spec.kind = MutationKind::NOP_INSTRUCTION;
    spec.description = desc;
    return spec;
}

MutationSpec GuestMutationHarness::create_byte_flip(
    uint32_t byte_addr,
    uint8_t expected_byte,
    uint8_t bit_mask,
    const std::string& desc
) {
    MutationSpec spec;
    spec.address = byte_addr;
    spec.expected_original = {expected_byte};
    spec.replacement_bytes = {static_cast<uint8_t>(expected_byte ^ bit_mask)};
    spec.kind = MutationKind::BYTE_FLIP;
    spec.description = desc;
    return spec;
}

} // namespace thor::recomp
