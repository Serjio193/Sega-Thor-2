#include "thor/recomp/block_identity.hpp"

namespace thor::recomp {

const char* eligibility_result_to_string(EligibilityResult result) noexcept {
    switch (result) {
    case EligibilityResult::ELIGIBLE:
        return "ELIGIBLE";
    case EligibilityResult::REVISION_MISMATCH:
        return "REVISION_MISMATCH";
    case EligibilityResult::MODULE_MISMATCH:
        return "MODULE_MISMATCH";
    case EligibilityResult::PROVENANCE_NOT_PROVEN:
        return "PROVENANCE_NOT_PROVEN";
    case EligibilityResult::CPU_MISMATCH:
        return "CPU_MISMATCH";
    case EligibilityResult::ADDRESS_RANGE_MISMATCH:
        return "ADDRESS_RANGE_MISMATCH";
    case EligibilityResult::CONTENT_BYTE_MISMATCH:
        return "CONTENT_BYTE_MISMATCH";
    case EligibilityResult::INVALID_STATE:
        return "INVALID_STATE";
    default:
        return "UNKNOWN_ERROR";
    }
}

EligibilityResult check_block_eligibility(
    const BlockIdentityDescriptor& proven_desc,
    const BlockIdentityDescriptor& query_desc,
    const thor::sh2::ISh2Memory& memory) noexcept {

    if (query_desc.validity != BlockValidity::VALID || proven_desc.validity != BlockValidity::VALID) {
        return EligibilityResult::INVALID_STATE;
    }

    if (query_desc.revision_id != proven_desc.revision_id) {
        return EligibilityResult::REVISION_MISMATCH;
    }

    if (query_desc.module_name != proven_desc.module_name) {
        return EligibilityResult::MODULE_MISMATCH;
    }

    if (!query_desc.module_provenance_proven || !proven_desc.module_provenance_proven) {
        return EligibilityResult::PROVENANCE_NOT_PROVEN;
    }

    if (query_desc.cpu != proven_desc.cpu) {
        return EligibilityResult::CPU_MISMATCH;
    }

    if (query_desc.start_pc != proven_desc.start_pc || query_desc.end_pc != proven_desc.end_pc) {
        return EligibilityResult::ADDRESS_RANGE_MISMATCH;
    }

    const size_t byte_count = proven_desc.expected_bytes.size();
    if (query_desc.expected_bytes.size() != byte_count) {
        return EligibilityResult::CONTENT_BYTE_MISMATCH;
    }

    for (size_t i = 0; i < byte_count; ++i) {
        const uint32_t addr = proven_desc.start_pc + static_cast<uint32_t>(i);
        // Host-side non-architectural observation: peek8 does not pollute guest access log
        const uint8_t live_byte = memory.peek8(addr);
        if (live_byte != proven_desc.expected_bytes[i]) {
            return EligibilityResult::CONTENT_BYTE_MISMATCH;
        }
    }

    return EligibilityResult::ELIGIBLE;
}

BlockIdentityDescriptor make_bb_06004000_descriptor() {
    return BlockIdentityDescriptor{
        .revision_id = "thor2_ntsc_patched_fe11d2fb",
        .module_name = "0TH2.BIN",
        .module_provenance_proven = true,
        .cpu = CpuTarget::MASTER_SH2,
        .start_pc = 0x06004000u,
        .end_pc = 0x0600400Au,
        .expected_bytes = {
            0x66, 0x11, // 0x06004000: MOV.W @R1, R6
            0x6F, 0x03, // 0x06004002: MOV R0, R15
            0xD4, 0x17, // 0x06004004: MOV.L @(0x5C, PC), R4
            0x64, 0x42, // 0x06004006: MOV.L @R4, R4
            0xA0, 0x03, // 0x06004008: BRA 0x06004012
            0x00, 0x09  // 0x0600400A: NOP (delay slot)
        },
        .validity = BlockValidity::VALID
    };
}

} // namespace thor::recomp
