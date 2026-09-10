#include "thor/sh2/sh2_types.hpp"

#include <iomanip>
#include <sstream>

namespace thor::sh2 {

std::string Sh2Instruction::mnemonic() const {
    std::ostringstream ss;
    switch (id) {
        case OpcodeId::MOV_W_READ_MEM:
            ss << "mov.w @r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_REG:
            ss << "mov r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_L_PC_REL:
            ss << "mov.l @(0x" << std::hex << (disp * 4u) << ", pc), r"
               << std::dec << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_W_PC_REL:
            ss << "mov.w @(0x" << std::hex << (disp * 2u) << ", pc), r"
               << std::dec << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_L_READ_MEM:
            ss << "mov.l @r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_L_READ_POSTINC:
            ss << "mov.l @r" << static_cast<int>(rm) << "+, r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_L_WRITE_PREDEC:
            ss << "mov.l r" << static_cast<int>(rm) << ", @-r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::STS_L_PR_PREDEC:
            ss << "sts.l pr, @-r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::LDS_L_PR_POSTINC:
            ss << "lds.l @r" << static_cast<int>(rm) << "+, pr";
            return ss.str();
        case OpcodeId::MOV_IMM:
            ss << "mov #" << static_cast<int>(static_cast<int8_t>(disp)) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::ADD_IMM:
            ss << "add #" << static_cast<int>(static_cast<int8_t>(disp)) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_W_WRITE_MEM:
            ss << "mov.w r" << static_cast<int>(rm) << ", @r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_L_WRITE_MEM:
            ss << "mov.l r" << static_cast<int>(rm) << ", @r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::TST_REG:
            ss << "tst r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::CMP_EQ_IMM:
            ss << "cmp/eq #" << static_cast<int>(static_cast<int8_t>(disp)) << ", r0";
            return ss.str();
        case OpcodeId::CMP_EQ_REG:
            ss << "cmp/eq r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::BF:
            ss << "bf 0x" << std::hex << compute_branch_target();
            return ss.str();
        case OpcodeId::BT:
            ss << "bt 0x" << std::hex << compute_branch_target();
            return ss.str();
        case OpcodeId::BRA:
            ss << "bra 0x" << std::hex << compute_branch_target();
            return ss.str();
        case OpcodeId::BSR:
            ss << "bsr 0x" << std::hex << compute_branch_target();
            return ss.str();
        case OpcodeId::JMP:
            ss << "jmp @r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::JSR:
            ss << "jsr @r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::NOP:
            return "nop";
        case OpcodeId::RTS:
            return "rts";
        case OpcodeId::MOV_L_DISP_READ:
            ss << "mov.l @(0x" << std::hex << (disp * 4u) << ", r" << std::dec << static_cast<int>(rm) << "), r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_L_DISP_WRITE:
            ss << "mov.l r" << static_cast<int>(rm) << ", @(0x" << std::hex << (disp * 4u) << ", r" << std::dec << static_cast<int>(rn) << ")";
            return ss.str();
        case OpcodeId::MOV_W_DISP_READ:
            ss << "mov.w @(0x" << std::hex << (disp * 2u) << ", r" << std::dec << static_cast<int>(rm) << "), r0";
            return ss.str();
        case OpcodeId::MOV_W_DISP_WRITE:
            ss << "mov.w r0, @(0x" << std::hex << (disp * 2u) << ", r" << std::dec << static_cast<int>(rn) << ")";
            return ss.str();
        case OpcodeId::MOV_B_READ_MEM:
            ss << "mov.b @r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_B_WRITE_MEM:
            ss << "mov.b r" << static_cast<int>(rm) << ", @r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::ADD_REG:
            ss << "add r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::SUB_REG:
            ss << "sub r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::SHLL:
            ss << "shll r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::SHLR:
            ss << "shlr r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::SHLL2:
            ss << "shll2 r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::SHLR2:
            ss << "shlr2 r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::CLRMAC:
            return "clrmac";
        case OpcodeId::CLRT:
            return "clrt";
        case OpcodeId::SETT:
            return "sett";
        case OpcodeId::SHAR:
            ss << "shar r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::BT_S:
            ss << "bt/s 0x" << std::hex << compute_branch_target();
            return ss.str();
        case OpcodeId::BF_S:
            ss << "bf/s 0x" << std::hex << compute_branch_target();
            return ss.str();
        case OpcodeId::EXTU_B:
            ss << "extu.b r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::EXTU_W:
            ss << "extu.w r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::EXTS_B:
            ss << "exts.b r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::EXTS_W:
            ss << "exts.w r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::CMP_PZ:
            ss << "cmp/pz r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::CMP_PL:
            ss << "cmp/pl r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_W_READ_POSTINC:
            ss << "mov.w @r" << static_cast<int>(rm) << "+, r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::AND_REG:
            ss << "and r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::OR_REG:
            ss << "or r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::CMP_HS:
            ss << "cmp/hs r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::CMP_GE:
            ss << "cmp/ge r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::CMP_HI:
            ss << "cmp/hi r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::CMP_GT:
            ss << "cmp/gt r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::ROTCL:
            ss << "rotcl r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::AND_IMM:
            ss << "and #0x" << std::hex << disp << ", r0";
            return ss.str();
        case OpcodeId::TST_IMM:
            ss << "tst #0x" << std::hex << disp << ", r0";
            return ss.str();
        case OpcodeId::MOV_B_DISP_READ:
            ss << "mov.b @(0x" << std::hex << disp << ", r" << std::dec << static_cast<int>(rm) << "), r0";
            return ss.str();
        case OpcodeId::MOV_B_DISP_WRITE:
            ss << "mov.b r0, @(0x" << std::hex << disp << ", r" << std::dec << static_cast<int>(rn) << ")";
            return ss.str();
        case OpcodeId::MOV_W_R0_READ:
            ss << "mov.w @(r0, r" << static_cast<int>(rm) << "), r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_L_R0_READ:
            ss << "mov.l @(r0, r" << static_cast<int>(rm) << "), r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_B_R0_READ:
            ss << "mov.b @(r0, r" << static_cast<int>(rm) << "), r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_L_R0_WRITE:
            ss << "mov.l r" << static_cast<int>(rm) << ", @(r0, r" << static_cast<int>(rn) << ")";
            return ss.str();
        case OpcodeId::MOV_W_R0_WRITE:
            ss << "mov.w r" << static_cast<int>(rm) << ", @(r0, r" << static_cast<int>(rn) << ")";
            return ss.str();
        case OpcodeId::MOV_B_R0_WRITE:
            ss << "mov.b r" << static_cast<int>(rm) << ", @(r0, r" << static_cast<int>(rn) << ")";
            return ss.str();
        case OpcodeId::SHLL8:
            ss << "shll8 r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::SHLL16:
            ss << "shll16 r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::SHLR8:
            ss << "shlr8 r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::SHLR16:
            ss << "shlr16 r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::DT:
            ss << "dt r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOVT:
            ss << "movt r" << static_cast<int>(rn);
            return ss.str();
        default:
            ss << ".word 0x" << std::hex << std::setw(4) << std::setfill('0') << raw_opcode;
            return ss.str();
    }
}

} // namespace thor::sh2
