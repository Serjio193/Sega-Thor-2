#pragma once

#include "thor/sh2/sh2_types.hpp"
#include <cstdint>
#include <vector>

namespace thor::sh2 {

struct ReferenceDecodeVector {
    uint16_t raw_opcode = 0;
    uint32_t pc = 0;
    OpcodeId expected_id = OpcodeId::UNKNOWN;
    uint8_t expected_rn = 0;
    uint8_t expected_rm = 0;
    uint32_t expected_disp = 0;
    ControlFlowType expected_flow = ControlFlowType::SEQUENTIAL;
    bool expected_has_delay_slot = false;
    MemoryAccessType expected_mem_access = MemoryAccessType::NONE;
    uint32_t expected_target = 0;
    uint32_t expected_ea = 0;
    const char* mnemonic_str = nullptr;
    const char* hardware_manual_ref = nullptr;
    const char* mednafen_ref = nullptr;
    const char* catherine_ref = nullptr;
};

inline const std::vector<ReferenceDecodeVector>& get_reference_decode_manifest() {
    static const std::vector<ReferenceDecodeVector> manifest = {
        {
            0x6611, 0x06004000,
            OpcodeId::MOV_W_READ_MEM, 6, 1, 0,
            ControlFlowType::SEQUENTIAL, false, MemoryAccessType::READ_S16,
            0, 0x06004000,
            "mov.w @r1, r6",
            "Hitachi SH-1/SH-2 Programming Manual Rev 4.0 Sec 5.25",
            "AJBats/mednafen-saturn-debug (commit 15542666) sh7095_opdefs.inc:31 OP_MOV_W_REGINDIR_REG",
            "hazzaclark/catherine (commit 462f483c) sh2_decoder.cpp:154 MOVWL"
        },
        {
            0x6F03, 0x06004002,
            OpcodeId::MOV_REG, 15, 0, 0,
            ControlFlowType::SEQUENTIAL, false, MemoryAccessType::NONE,
            0, 0,
            "mov r0, r15",
            "Hitachi SH-1/SH-2 Programming Manual Rev 4.0 Sec 5.23",
            "AJBats/mednafen-saturn-debug (commit 15542666) sh7095_opdefs.inc:26 OP_MOV_REG_REG",
            "hazzaclark/catherine (commit 462f483c) sh2_decoder.cpp:158 MOV"
        },
        {
            0xD417, 0x06004004,
            OpcodeId::MOV_L_PC_REL, 4, 0, 0x17,
            ControlFlowType::SEQUENTIAL, false, MemoryAccessType::READ_U32,
            0, 0x06004064,
            "mov.l @(0x5c, pc), r4",
            "Hitachi SH-1/SH-2 Programming Manual Rev 4.0 Sec 5.22",
            "AJBats/mednafen-saturn-debug (commit 15542666) sh7095_opdefs.inc:25 OP_MOV_L_PCREL_REG",
            "hazzaclark/catherine (commit 462f483c) sh2_decoder.cpp:218 MOVLL4"
        },
        {
            0x6442, 0x06004006,
            OpcodeId::MOV_L_READ_MEM, 4, 4, 0,
            ControlFlowType::SEQUENTIAL, false, MemoryAccessType::READ_U32,
            0, 0x06081C10,
            "mov.l @r4, r4",
            "Hitachi SH-1/SH-2 Programming Manual Rev 4.0 Sec 5.26",
            "AJBats/mednafen-saturn-debug (commit 15542666) sh7095_opdefs.inc:32 OP_MOV_L_REGINDIR_REG",
            "hazzaclark/catherine (commit 462f483c) sh2_decoder.cpp:156 MOVLL"
        },
        {
            0xA003, 0x06004008,
            OpcodeId::BRA, 0, 0, 0x003,
            ControlFlowType::BRANCH, true, MemoryAccessType::NONE,
            0x06004012, 0,
            "bra 0x6004012",
            "Hitachi SH-1/SH-2 Programming Manual Rev 4.0 Sec 5.10",
            "AJBats/mednafen-saturn-debug (commit 15542666) sh7095_opdefs.inc:126 OP_BRA",
            "hazzaclark/catherine (commit 462f483c) sh2_decoder.cpp:180 BRA"
        },
        {
            0x0009, 0x0600400A,
            OpcodeId::NOP, 0, 0, 0,
            ControlFlowType::SEQUENTIAL, false, MemoryAccessType::NONE,
            0, 0,
            "nop",
            "Hitachi SH-1/SH-2 Programming Manual Rev 4.0 Sec 5.34",
            "AJBats/mednafen-saturn-debug (commit 15542666) sh7095_opdefs.inc:139 OP_NOP",
            "hazzaclark/catherine (commit 462f483c) sh2_decoder.cpp:108 NOP"
        }
    };
    return manifest;
}

} // namespace thor::sh2
