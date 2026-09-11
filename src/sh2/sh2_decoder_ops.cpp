#include "thor/sh2/sh2_decoder.hpp"

namespace thor::sh2 {

bool decode_sh2_ops(uint16_t opcode, uint32_t pc, Sh2Instruction& instr) noexcept {
    (void)pc;
    const uint16_t hi = (opcode >> 12) & 0x0Fu;
    const uint16_t lo = opcode & 0x0Fu;
    const uint8_t rn = static_cast<uint8_t>((opcode >> 8) & 0x0Fu);
    const uint8_t rm = static_cast<uint8_t>((opcode >> 4) & 0x0Fu);

    // 0x0n0A: STS MACH, Rn / 0x0n1A: STS MACL, Rn / 0x0n2A: STS PR, Rn
    if (hi == 0x0u && (opcode & 0x00FFu) == 0x000Au) {
        instr.id = OpcodeId::STS_MACH;
        instr.rn = rn;
        return true;
    }
    if (hi == 0x0u && (opcode & 0x00FFu) == 0x001Au) {
        instr.id = OpcodeId::STS_MACL;
        instr.rn = rn;
        return true;
    }
    if (hi == 0x0u && (opcode & 0x00FFu) == 0x002Au) {
        instr.id = OpcodeId::STS_PR;
        instr.rn = rn;
        return true;
    }

    // 0x0n02: STC SR, Rn / 0x0n12: STC GBR, Rn / 0x0n22: STC VBR, Rn
    if (hi == 0x0u && (opcode & 0x00FFu) == 0x0002u) {
        instr.id = OpcodeId::STC_SR;
        instr.rn = rn;
        return true;
    }
    if (hi == 0x0u && (opcode & 0x00FFu) == 0x0012u) {
        instr.id = OpcodeId::STC_GBR;
        instr.rn = rn;
        return true;
    }
    if (hi == 0x0u && (opcode & 0x00FFu) == 0x0022u) {
        instr.id = OpcodeId::STC_VBR;
        instr.rn = rn;
        return true;
    }

    // 0x4m0A: LDS Rm, MACH / 0x4m1A: LDS Rm, MACL / 0x4m2A: LDS Rm, PR
    if (hi == 0x4u && (opcode & 0x00FFu) == 0x000Au) {
        instr.id = OpcodeId::LDS_MACH;
        instr.rm = rn; // on SH-2 LDS Rm, reg has Rm in bits 11..8
        return true;
    }
    if (hi == 0x4u && (opcode & 0x00FFu) == 0x001Au) {
        instr.id = OpcodeId::LDS_MACL;
        instr.rm = rn;
        return true;
    }
    if (hi == 0x4u && (opcode & 0x00FFu) == 0x002Au) {
        instr.id = OpcodeId::LDS_PR;
        instr.rm = rn;
        return true;
    }

    // 0x4n02: STS.L MACH, @-Rn / 0x4n12: STS.L MACL, @-Rn
    if (hi == 0x4u && (opcode & 0x00FFu) == 0x0002u) {
        instr.id = OpcodeId::STS_L_MACH_PREDEC;
        instr.rn = rn;
        instr.mem_access = MemoryAccessType::WRITE_U32;
        return true;
    }
    if (hi == 0x4u && (opcode & 0x00FFu) == 0x0012u) {
        instr.id = OpcodeId::STS_L_MACL_PREDEC;
        instr.rn = rn;
        instr.mem_access = MemoryAccessType::WRITE_U32;
        return true;
    }

    // 0x4m06: LDS.L @Rm+, MACH / 0x4m16: LDS.L @Rm+, MACL
    if (hi == 0x4u && (opcode & 0x00FFu) == 0x0006u) {
        instr.id = OpcodeId::LDS_L_MACH_POSTINC;
        instr.rm = rn;
        instr.mem_access = MemoryAccessType::READ_U32;
        return true;
    }
    if (hi == 0x4u && (opcode & 0x00FFu) == 0x0016u) {
        instr.id = OpcodeId::LDS_L_MACL_POSTINC;
        instr.rm = rn;
        instr.mem_access = MemoryAccessType::READ_U32;
        return true;
    }

    // 0x4m0E: LDC Rm, SR / 0x4m1E: LDC Rm, GBR / 0x4m2E: LDC Rm, VBR
    if (hi == 0x4u && (opcode & 0x00FFu) == 0x000Eu) {
        instr.id = OpcodeId::LDC_SR;
        instr.rm = rn;
        return true;
    }
    if (hi == 0x4u && (opcode & 0x00FFu) == 0x001Eu) {
        instr.id = OpcodeId::LDC_GBR;
        instr.rm = rn;
        return true;
    }
    if (hi == 0x4u && (opcode & 0x00FFu) == 0x002Eu) {
        instr.id = OpcodeId::LDC_VBR;
        instr.rm = rn;
        return true;
    }

    // 0x4n03: STC.L SR, @-Rn / 0x4n13: STC.L GBR, @-Rn / 0x4n23: STC.L VBR, @-Rn
    if (hi == 0x4u && (opcode & 0x00FFu) == 0x0003u) {
        instr.id = OpcodeId::STC_L_SR_PREDEC;
        instr.rn = rn;
        instr.mem_access = MemoryAccessType::WRITE_U32;
        return true;
    }
    if (hi == 0x4u && (opcode & 0x00FFu) == 0x0013u) {
        instr.id = OpcodeId::STC_L_GBR_PREDEC;
        instr.rn = rn;
        instr.mem_access = MemoryAccessType::WRITE_U32;
        return true;
    }
    if (hi == 0x4u && (opcode & 0x00FFu) == 0x0023u) {
        instr.id = OpcodeId::STC_L_VBR_PREDEC;
        instr.rn = rn;
        instr.mem_access = MemoryAccessType::WRITE_U32;
        return true;
    }

    // 0x4m07: LDC.L @Rm+, SR / 0x4m17: LDC.L @Rm+, GBR / 0x4m27: LDC.L @Rm+, VBR
    if (hi == 0x4u && (opcode & 0x00FFu) == 0x0007u) {
        instr.id = OpcodeId::LDC_L_SR_POSTINC;
        instr.rm = rn;
        instr.mem_access = MemoryAccessType::READ_U32;
        return true;
    }
    if (hi == 0x4u && (opcode & 0x00FFu) == 0x0017u) {
        instr.id = OpcodeId::LDC_L_GBR_POSTINC;
        instr.rm = rn;
        instr.mem_access = MemoryAccessType::READ_U32;
        return true;
    }
    if (hi == 0x4u && (opcode & 0x00FFu) == 0x0027u) {
        instr.id = OpcodeId::LDC_L_VBR_POSTINC;
        instr.rm = rn;
        instr.mem_access = MemoryAccessType::READ_U32;
        return true;
    }

    // 0x6nm4: MOV.B @Rm+, Rn
    if (hi == 0x6u && lo == 0x4u) {
        instr.id = OpcodeId::MOV_B_READ_POSTINC;
        instr.rn = rn; instr.rm = rm;
        instr.mem_access = MemoryAccessType::READ_S8;
        return true;
    }

    // 0x2nm4: MOV.B Rm, @-Rn
    if (hi == 0x2u && lo == 0x4u) {
        instr.id = OpcodeId::MOV_B_WRITE_PREDEC;
        instr.rn = rn; instr.rm = rm;
        instr.mem_access = MemoryAccessType::WRITE_U8;
        return true;
    }

    // 0x2nm5: MOV.W Rm, @-Rn
    if (hi == 0x2u && lo == 0x5u) {
        instr.id = OpcodeId::MOV_W_WRITE_PREDEC;
        instr.rn = rn; instr.rm = rm;
        instr.mem_access = MemoryAccessType::WRITE_U16;
        return true;
    }

    // 0xC7dd: MOVA @(disp, PC), R0
    if ((opcode & 0xFF00u) == 0xC700u) {
        instr.id = OpcodeId::MOVA;
        instr.rn = 0;
        instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        return true;
    }

    // 0x6nm7: NOT Rm, Rn / 0x6nm8: SWAP.B Rm, Rn / 0x6nm9: SWAP.W Rm, Rn / 0x6nmA: NEGC / 0x6nmB: NEG
    if (hi == 0x6u && lo == 0x7u) {
        instr.id = OpcodeId::NOT_REG;
        instr.rn = rn; instr.rm = rm;
        return true;
    }
    if (hi == 0x6u && lo == 0x8u) {
        instr.id = OpcodeId::SWAP_B;
        instr.rn = rn; instr.rm = rm;
        return true;
    }
    if (hi == 0x6u && lo == 0x9u) {
        instr.id = OpcodeId::SWAP_W;
        instr.rn = rn; instr.rm = rm;
        return true;
    }
    if (hi == 0x6u && lo == 0xAu) {
        instr.id = OpcodeId::NEGC;
        instr.rn = rn; instr.rm = rm;
        return true;
    }
    if (hi == 0x6u && lo == 0xBu) {
        instr.id = OpcodeId::NEG;
        instr.rn = rn; instr.rm = rm;
        return true;
    }

    // 0x2nmA: XOR Rm, Rn / 0x2nm7: DIV0S / 0x2nmC: CMP/STR / 0x2nmE: MULU.W / 0x2nmF: MULS.W
    if (hi == 0x2u && lo == 0xAu) {
        instr.id = OpcodeId::XOR_REG;
        instr.rn = rn; instr.rm = rm;
        return true;
    }
    if (hi == 0x2u && lo == 0x7u) {
        instr.id = OpcodeId::DIV0S;
        instr.rn = rn; instr.rm = rm;
        return true;
    }
    if (hi == 0x2u && lo == 0xCu) {
        instr.id = OpcodeId::CMP_STR;
        instr.rn = rn; instr.rm = rm;
        return true;
    }
    if (hi == 0x2u && lo == 0xEu) {
        instr.id = OpcodeId::MULU_W;
        instr.rn = rn; instr.rm = rm;
        return true;
    }
    if (hi == 0x2u && lo == 0xFu) {
        instr.id = OpcodeId::MULS_W;
        instr.rn = rn; instr.rm = rm;
        return true;
    }

    // 0xCAii: XOR #imm, R0 / 0xCBii: OR #imm, R0 / 0xC3ii: TRAPA #imm
    if ((opcode & 0xFF00u) == 0xCA00u) {
        instr.id = OpcodeId::XOR_IMM;
        instr.rn = 0;
        instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        return true;
    }
    if ((opcode & 0xFF00u) == 0xCB00u) {
        instr.id = OpcodeId::OR_IMM;
        instr.rn = 0;
        instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        return true;
    }
    if ((opcode & 0xFF00u) == 0xC300u) {
        instr.id = OpcodeId::TRAPA;
        instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        instr.flow = ControlFlowType::CALL;
        return true;
    }

    // 0x0019: DIV0U / 0x001B: SLEEP / 0x002B: RTE
    if (opcode == 0x0019u) {
        instr.id = OpcodeId::DIV0U;
        return true;
    }
    if (opcode == 0x001Bu) {
        instr.id = OpcodeId::SLEEP;
        return true;
    }
    if (opcode == 0x002Bu) {
        instr.id = OpcodeId::RTE;
        instr.flow = ControlFlowType::RETURN;
        instr.has_delay_slot = true;
        return true;
    }

    // 0x3nm4: DIV1 / 0x3nm5: DMULU.L / 0x3nmA: SUBC / 0x3nmB: SUBV / 0x3nmD: DMULS.L / 0x3nmE: ADDC / 0x3nmF: ADDV
    if (hi == 0x3u && lo == 0x4u) {
        instr.id = OpcodeId::DIV1;
        instr.rn = rn; instr.rm = rm;
        return true;
    }
    if (hi == 0x3u && lo == 0x5u) {
        instr.id = OpcodeId::DMULU_L;
        instr.rn = rn; instr.rm = rm;
        return true;
    }
    if (hi == 0x3u && lo == 0xAu) {
        instr.id = OpcodeId::SUBC;
        instr.rn = rn; instr.rm = rm;
        return true;
    }
    if (hi == 0x3u && lo == 0xBu) {
        instr.id = OpcodeId::SUBV;
        instr.rn = rn; instr.rm = rm;
        return true;
    }
    if (hi == 0x3u && lo == 0xDu) {
        instr.id = OpcodeId::DMULS_L;
        instr.rn = rn; instr.rm = rm;
        return true;
    }
    if (hi == 0x3u && lo == 0xEu) {
        instr.id = OpcodeId::ADDC;
        instr.rn = rn; instr.rm = rm;
        return true;
    }
    if (hi == 0x3u && lo == 0xFu) {
        instr.id = OpcodeId::ADDV;
        instr.rn = rn; instr.rm = rm;
        return true;
    }

    // 0x4n04: ROTL / 0x4n05: ROTR / 0x4n25: ROTCR / 0x4n20: SHAL
    if ((opcode & 0xF0FFu) == 0x4004u) {
        instr.id = OpcodeId::ROTL;
        instr.rn = rn;
        return true;
    }
    if ((opcode & 0xF0FFu) == 0x4005u) {
        instr.id = OpcodeId::ROTR;
        instr.rn = rn;
        return true;
    }
    if ((opcode & 0xF0FFu) == 0x4025u) {
        instr.id = OpcodeId::ROTCR;
        instr.rn = rn;
        return true;
    }
    if ((opcode & 0xF0FFu) == 0x4020u) {
        instr.id = OpcodeId::SHAL;
        instr.rn = rn;
        return true;
    }

    // 0x0nm7: MUL.L Rm, Rn / 0x0nmF: MAC.L @Rm+, @Rn+ / 0x4nmF: MAC.W @Rm+, @Rn+
    if (hi == 0x0u && lo == 0x7u) {
        instr.id = OpcodeId::MUL_L;
        instr.rn = rn; instr.rm = rm;
        return true;
    }
    if (hi == 0x0u && lo == 0xFu) {
        instr.id = OpcodeId::MAC_L;
        instr.rn = rn; instr.rm = rm;
        instr.mem_access = MemoryAccessType::READ_U32;
        return true;
    }
    if (hi == 0x4u && lo == 0xFu) {
        instr.id = OpcodeId::MAC_W;
        instr.rn = rn; instr.rm = rm;
        instr.mem_access = MemoryAccessType::READ_S16;
        return true;
    }

    // 0x0n03: BSRF Rn / 0x0n23: BRAF Rn / 0x4n1B: TAS.B @Rn
    if ((opcode & 0xF0FFu) == 0x0003u) {
        instr.id = OpcodeId::BSRF;
        instr.rn = rn;
        instr.flow = ControlFlowType::CALL;
        instr.has_delay_slot = true;
        return true;
    }
    if ((opcode & 0xF0FFu) == 0x0023u) {
        instr.id = OpcodeId::BRAF;
        instr.rn = rn;
        instr.flow = ControlFlowType::BRANCH;
        instr.has_delay_slot = true;
        return true;
    }
    if ((opcode & 0xF0FFu) == 0x401Bu) {
        instr.id = OpcodeId::TAS_B;
        instr.rn = rn;
        instr.mem_access = MemoryAccessType::WRITE_U8;
        return true;
    }

    // 0x2nmD: XTRCT Rm, Rn
    if (hi == 0x2u && lo == 0xDu) {
        instr.id = OpcodeId::XTRCT;
        instr.rn = rn; instr.rm = rm;
        return true;
    }

    // GBR-relative data transfers
    if ((opcode & 0xFF00u) == 0xC000u) {
        instr.id = OpcodeId::MOV_B_GBR_WRITE;
        instr.rn = 0; instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        instr.mem_access = MemoryAccessType::WRITE_U8;
        return true;
    }
    if ((opcode & 0xFF00u) == 0xC100u) {
        instr.id = OpcodeId::MOV_W_GBR_WRITE;
        instr.rn = 0; instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        instr.mem_access = MemoryAccessType::WRITE_U16;
        return true;
    }
    if ((opcode & 0xFF00u) == 0xC200u) {
        instr.id = OpcodeId::MOV_L_GBR_WRITE;
        instr.rn = 0; instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        instr.mem_access = MemoryAccessType::WRITE_U32;
        return true;
    }
    if ((opcode & 0xFF00u) == 0xC400u) {
        instr.id = OpcodeId::MOV_B_GBR_READ;
        instr.rn = 0; instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        instr.mem_access = MemoryAccessType::READ_S8;
        return true;
    }
    if ((opcode & 0xFF00u) == 0xC500u) {
        instr.id = OpcodeId::MOV_W_GBR_READ;
        instr.rn = 0; instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        instr.mem_access = MemoryAccessType::READ_S16;
        return true;
    }
    if ((opcode & 0xFF00u) == 0xC600u) {
        instr.id = OpcodeId::MOV_L_GBR_READ;
        instr.rn = 0; instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        instr.mem_access = MemoryAccessType::READ_U32;
        return true;
    }

    // GBR-relative bitwise operations
    if ((opcode & 0xFF00u) == 0xCC00u) {
        instr.id = OpcodeId::TST_B_GBR;
        instr.rn = 0; instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        return true;
    }
    if ((opcode & 0xFF00u) == 0xCD00u) {
        instr.id = OpcodeId::AND_B_GBR;
        instr.rn = 0; instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        return true;
    }
    if ((opcode & 0xFF00u) == 0xCE00u) {
        instr.id = OpcodeId::XOR_B_GBR;
        instr.rn = 0; instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        return true;
    }
    if ((opcode & 0xFF00u) == 0xCF00u) {
        instr.id = OpcodeId::OR_B_GBR;
        instr.rn = 0; instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        return true;
    }

    return false;
}

} // namespace thor::sh2
