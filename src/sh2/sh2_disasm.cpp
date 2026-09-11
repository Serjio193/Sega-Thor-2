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
        case OpcodeId::STS_MACL:
            ss << "sts macl, r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::STS_MACH:
            ss << "sts mach, r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::STS_PR:
            ss << "sts pr, r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::LDS_MACL:
            ss << "lds r" << static_cast<int>(rm) << ", macl";
            return ss.str();
        case OpcodeId::LDS_MACH:
            ss << "lds r" << static_cast<int>(rm) << ", mach";
            return ss.str();
        case OpcodeId::LDS_PR:
            ss << "lds r" << static_cast<int>(rm) << ", pr";
            return ss.str();
        case OpcodeId::STS_L_MACL_PREDEC:
            ss << "sts.l macl, @-r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::STS_L_MACH_PREDEC:
            ss << "sts.l mach, @-r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::LDS_L_MACL_POSTINC:
            ss << "lds.l @r" << static_cast<int>(rm) << "+, macl";
            return ss.str();
        case OpcodeId::LDS_L_MACH_POSTINC:
            ss << "lds.l @r" << static_cast<int>(rm) << "+, mach";
            return ss.str();
        case OpcodeId::MOV_B_READ_POSTINC:
            ss << "mov.b @r" << static_cast<int>(rm) << "+, r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_B_WRITE_PREDEC:
            ss << "mov.b r" << static_cast<int>(rm) << ", @-r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_W_WRITE_PREDEC:
            ss << "mov.w r" << static_cast<int>(rm) << ", @-r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOVA:
            ss << "mova @(0x" << std::hex << (disp * 4u) << ", pc), r0";
            return ss.str();
        case OpcodeId::NOT_REG:
            ss << "not r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::SWAP_B:
            ss << "swap.b r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::SWAP_W:
            ss << "swap.w r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::NEGC:
            ss << "negc r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::NEG:
            ss << "neg r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::XOR_REG:
            ss << "xor r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::XOR_IMM:
            ss << "xor #" << static_cast<int>(disp) << ", r0";
            return ss.str();
        case OpcodeId::OR_IMM:
            ss << "or #" << static_cast<int>(disp) << ", r0";
            return ss.str();
        case OpcodeId::DIV0U:
            return "div0u";
        case OpcodeId::DIV0S:
            ss << "div0s r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::DIV1:
            ss << "div1 r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::ROTL:
            ss << "rotl r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::ROTR:
            ss << "rotr r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::ROTCR:
            ss << "rotcr r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::SHAL:
            ss << "shal r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::SUBC:
            ss << "subc r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::SUBV:
            ss << "subv r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::ADDC:
            ss << "addc r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::ADDV:
            ss << "addv r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MULU_W:
            ss << "mulu.w r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MULS_W:
            ss << "muls.w r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::DMULU_L:
            ss << "dmulu.l r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::DMULS_L:
            ss << "dmuls.l r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::CMP_STR:
            ss << "cmp/str r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::STC_SR:
            ss << "stc sr, r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::STC_GBR:
            ss << "stc gbr, r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::STC_VBR:
            ss << "stc vbr, r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::LDC_SR:
            ss << "ldc r" << static_cast<int>(rm) << ", sr";
            return ss.str();
        case OpcodeId::LDC_GBR:
            ss << "ldc r" << static_cast<int>(rm) << ", gbr";
            return ss.str();
        case OpcodeId::LDC_VBR:
            ss << "ldc r" << static_cast<int>(rm) << ", vbr";
            return ss.str();
        case OpcodeId::STC_L_SR_PREDEC:
            ss << "stc.l sr, @-r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::STC_L_GBR_PREDEC:
            ss << "stc.l gbr, @-r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::STC_L_VBR_PREDEC:
            ss << "stc.l vbr, @-r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::LDC_L_SR_POSTINC:
            ss << "ldc.l @r" << static_cast<int>(rm) << "+, sr";
            return ss.str();
        case OpcodeId::LDC_L_GBR_POSTINC:
            ss << "ldc.l @r" << static_cast<int>(rm) << "+, gbr";
            return ss.str();
        case OpcodeId::LDC_L_VBR_POSTINC:
            ss << "ldc.l @r" << static_cast<int>(rm) << "+, vbr";
            return ss.str();
        case OpcodeId::SLEEP:
            return "sleep";
        case OpcodeId::RTE:
            return "rte";
        case OpcodeId::TRAPA:
            ss << "trapa #" << static_cast<int>(disp);
            return ss.str();
        case OpcodeId::MUL_L:
            ss << "mul.l r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MAC_L:
            ss << "mac.l @r" << static_cast<int>(rm) << "+, @r" << static_cast<int>(rn) << "+";
            return ss.str();
        case OpcodeId::MAC_W:
            ss << "mac.w @r" << static_cast<int>(rm) << "+, @r" << static_cast<int>(rn) << "+";
            return ss.str();
        case OpcodeId::BSRF:
            ss << "bsrf r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::BRAF:
            ss << "braf r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::TAS_B:
            ss << "tas.b @r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::XTRCT:
            ss << "xtrct r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        case OpcodeId::MOV_B_GBR_WRITE:
            ss << "mov.b r0, @(0x" << std::hex << disp << ", gbr)";
            return ss.str();
        case OpcodeId::MOV_W_GBR_WRITE:
            ss << "mov.w r0, @(0x" << std::hex << (disp * 2u) << ", gbr)";
            return ss.str();
        case OpcodeId::MOV_L_GBR_WRITE:
            ss << "mov.l r0, @(0x" << std::hex << (disp * 4u) << ", gbr)";
            return ss.str();
        case OpcodeId::MOV_B_GBR_READ:
            ss << "mov.b @(0x" << std::hex << disp << ", gbr), r0";
            return ss.str();
        case OpcodeId::MOV_W_GBR_READ:
            ss << "mov.w @(0x" << std::hex << (disp * 2u) << ", gbr), r0";
            return ss.str();
        case OpcodeId::MOV_L_GBR_READ:
            ss << "mov.l @(0x" << std::hex << (disp * 4u) << ", gbr), r0";
            return ss.str();
        case OpcodeId::TST_B_GBR:
            ss << "tst.b #0x" << std::hex << disp << ", @(r0, gbr)";
            return ss.str();
        case OpcodeId::AND_B_GBR:
            ss << "and.b #0x" << std::hex << disp << ", @(r0, gbr)";
            return ss.str();
        case OpcodeId::XOR_B_GBR:
            ss << "xor.b #0x" << std::hex << disp << ", @(r0, gbr)";
            return ss.str();
        case OpcodeId::OR_B_GBR:
            ss << "or.b #0x" << std::hex << disp << ", @(r0, gbr)";
            return ss.str();
        default:
            ss << ".word 0x" << std::hex << std::setw(4) << std::setfill('0') << raw_opcode;
            return ss.str();
    }
}

} // namespace thor::sh2
