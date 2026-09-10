#include "thor/sh2/sh2_decoder.hpp"

namespace thor::sh2 {

bool decode_sh2_ext(uint16_t opcode, uint32_t pc, Sh2Instruction& instr) noexcept {
    (void)pc;
    const uint16_t hi = (opcode >> 12) & 0x0Fu;
    const uint16_t lo = opcode & 0x0Fu;
    const uint8_t rn = static_cast<uint8_t>((opcode >> 8) & 0x0Fu);
    const uint8_t rm = static_cast<uint8_t>((opcode >> 4) & 0x0Fu);

    // 0x4n21: SHAR Rn
    if ((opcode & 0xF0FFu) == 0x4021u) {
        instr.id = OpcodeId::SHAR;
        instr.rn = rn;
        return true;
    }

    // 0x8Ddd: BT/S label (8-bit signed displacement)
    if ((opcode & 0xFF00u) == 0x8D00u) {
        instr.id = OpcodeId::BT_S;
        instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        instr.flow = ControlFlowType::BRANCH_CONDITIONAL;
        instr.has_delay_slot = true;
        return true;
    }

    // 0x8Fdd: BF/S label (8-bit signed displacement)
    if ((opcode & 0xFF00u) == 0x8F00u) {
        instr.id = OpcodeId::BF_S;
        instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        instr.flow = ControlFlowType::BRANCH_CONDITIONAL;
        instr.has_delay_slot = true;
        return true;
    }

    // 0x6nmC: EXTU.B Rm, Rn
    if (hi == 0x6u && lo == 0xCu) {
        instr.id = OpcodeId::EXTU_B;
        instr.rn = rn; instr.rm = rm;
        return true;
    }

    // 0x6nmD: EXTU.W Rm, Rn
    if (hi == 0x6u && lo == 0xDu) {
        instr.id = OpcodeId::EXTU_W;
        instr.rn = rn; instr.rm = rm;
        return true;
    }

    // 0x6nmE: EXTS.B Rm, Rn
    if (hi == 0x6u && lo == 0xEu) {
        instr.id = OpcodeId::EXTS_B;
        instr.rn = rn; instr.rm = rm;
        return true;
    }

    // 0x6nmF: EXTS.W Rm, Rn
    if (hi == 0x6u && lo == 0xFu) {
        instr.id = OpcodeId::EXTS_W;
        instr.rn = rn; instr.rm = rm;
        return true;
    }

    // 0x4n11: CMP/PZ Rn
    if ((opcode & 0xF0FFu) == 0x4011u) {
        instr.id = OpcodeId::CMP_PZ;
        instr.rn = rn;
        return true;
    }

    // 0x4n15: CMP/PL Rn
    if ((opcode & 0xF0FFu) == 0x4015u) {
        instr.id = OpcodeId::CMP_PL;
        instr.rn = rn;
        return true;
    }

    // 0x6nm5: MOV.W @Rm+, Rn
    if (hi == 0x6u && lo == 0x5u) {
        instr.id = OpcodeId::MOV_W_READ_POSTINC;
        instr.rn = rn; instr.rm = rm;
        instr.mem_access = MemoryAccessType::READ_S16;
        return true;
    }

    // 0x2nm9: AND Rm, Rn
    if (hi == 0x2u && lo == 0x9u) {
        instr.id = OpcodeId::AND_REG;
        instr.rn = rn; instr.rm = rm;
        return true;
    }

    // 0x2nmB: OR Rm, Rn
    if (hi == 0x2u && lo == 0xBu) {
        instr.id = OpcodeId::OR_REG;
        instr.rn = rn; instr.rm = rm;
        return true;
    }

    // 0x3nm2: CMP/HS Rm, Rn
    if (hi == 0x3u && lo == 0x2u) {
        instr.id = OpcodeId::CMP_HS;
        instr.rn = rn; instr.rm = rm;
        return true;
    }

    // 0x3nm3: CMP/GE Rm, Rn
    if (hi == 0x3u && lo == 0x3u) {
        instr.id = OpcodeId::CMP_GE;
        instr.rn = rn; instr.rm = rm;
        return true;
    }

    // 0x3nm6: CMP/HI Rm, Rn
    if (hi == 0x3u && lo == 0x6u) {
        instr.id = OpcodeId::CMP_HI;
        instr.rn = rn; instr.rm = rm;
        return true;
    }

    // 0x3nm7: CMP/GT Rm, Rn
    if (hi == 0x3u && lo == 0x7u) {
        instr.id = OpcodeId::CMP_GT;
        instr.rn = rn; instr.rm = rm;
        return true;
    }

    // 0x4n24: ROTCL Rn
    if ((opcode & 0xF0FFu) == 0x4024u) {
        instr.id = OpcodeId::ROTCL;
        instr.rn = rn;
        return true;
    }

    // 0xC9ii: AND #imm, R0
    if ((opcode & 0xFF00u) == 0xC900u) {
        instr.id = OpcodeId::AND_IMM;
        instr.rn = 0;
        instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        return true;
    }

    // 0xC8ii: TST #imm, R0
    if ((opcode & 0xFF00u) == 0xC800u) {
        instr.id = OpcodeId::TST_IMM;
        instr.rn = 0;
        instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        return true;
    }

    // 0x84md: MOV.B @(disp, Rm), R0
    if ((opcode & 0xFF00u) == 0x8400u) {
        instr.id = OpcodeId::MOV_B_DISP_READ;
        instr.rn = 0;
        instr.rm = static_cast<uint8_t>((opcode >> 4) & 0x0Fu);
        instr.disp = static_cast<uint32_t>(lo);
        instr.mem_access = MemoryAccessType::READ_S8;
        return true;
    }

    // 0x80nd: MOV.B R0, @(disp, Rn)
    if ((opcode & 0xFF00u) == 0x8000u) {
        instr.id = OpcodeId::MOV_B_DISP_WRITE;
        instr.rn = static_cast<uint8_t>((opcode >> 4) & 0x0Fu);
        instr.rm = 0;
        instr.disp = static_cast<uint32_t>(lo);
        instr.mem_access = MemoryAccessType::WRITE_U8;
        return true;
    }

    // 0x0nmD: MOV.W @(R0, Rm), Rn
    if (hi == 0x0u && lo == 0xDu) {
        instr.id = OpcodeId::MOV_W_R0_READ;
        instr.rn = rn; instr.rm = rm;
        instr.mem_access = MemoryAccessType::READ_S16;
        return true;
    }

    // 0x0nmE: MOV.L @(R0, Rm), Rn
    if (hi == 0x0u && lo == 0xEu) {
        instr.id = OpcodeId::MOV_L_R0_READ;
        instr.rn = rn; instr.rm = rm;
        instr.mem_access = MemoryAccessType::READ_U32;
        return true;
    }

    // 0x0nmC: MOV.B @(R0, Rm), Rn
    if (hi == 0x0u && lo == 0xCu) {
        instr.id = OpcodeId::MOV_B_R0_READ;
        instr.rn = rn; instr.rm = rm;
        instr.mem_access = MemoryAccessType::READ_S8;
        return true;
    }

    // 0x0nm6: MOV.L Rm, @(R0, Rn)
    if (hi == 0x0u && lo == 0x6u) {
        instr.id = OpcodeId::MOV_L_R0_WRITE;
        instr.rn = rn; instr.rm = rm;
        instr.mem_access = MemoryAccessType::WRITE_U32;
        return true;
    }

    // 0x0nm5: MOV.W Rm, @(R0, Rn)
    if (hi == 0x0u && lo == 0x5u) {
        instr.id = OpcodeId::MOV_W_R0_WRITE;
        instr.rn = rn; instr.rm = rm;
        instr.mem_access = MemoryAccessType::WRITE_U16;
        return true;
    }

    // 0x0nm4: MOV.B Rm, @(R0, Rn)
    if (hi == 0x0u && lo == 0x4u) {
        instr.id = OpcodeId::MOV_B_R0_WRITE;
        instr.rn = rn; instr.rm = rm;
        instr.mem_access = MemoryAccessType::WRITE_U8;
        return true;
    }

    // 0x4n18: SHLL8 Rn
    if ((opcode & 0xF0FFu) == 0x4018u) {
        instr.id = OpcodeId::SHLL8;
        instr.rn = rn;
        return true;
    }

    // 0x4n28: SHLL16 Rn
    if ((opcode & 0xF0FFu) == 0x4028u) {
        instr.id = OpcodeId::SHLL16;
        instr.rn = rn;
        return true;
    }

    // 0x4n19: SHLR8 Rn
    if ((opcode & 0xF0FFu) == 0x4019u) {
        instr.id = OpcodeId::SHLR8;
        instr.rn = rn;
        return true;
    }

    // 0x4n29: SHLR16 Rn
    if ((opcode & 0xF0FFu) == 0x4029u) {
        instr.id = OpcodeId::SHLR16;
        instr.rn = rn;
        return true;
    }

    // 0x4n10: DT Rn
    if ((opcode & 0xF0FFu) == 0x4010u) {
        instr.id = OpcodeId::DT;
        instr.rn = rn;
        return true;
    }

    // 0x0n29: MOVT Rn
    if ((opcode & 0xF0FFu) == 0x0029u) {
        instr.id = OpcodeId::MOVT;
        instr.rn = rn;
        return true;
    }

    return false;
}

} // namespace thor::sh2
