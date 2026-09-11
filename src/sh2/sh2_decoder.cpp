#include "thor/sh2/sh2_decoder.hpp"

namespace thor::sh2 {

Sh2Instruction decode_sh2(uint16_t opcode, uint32_t pc) noexcept {
    Sh2Instruction instr{};
    instr.raw_opcode = opcode;
    instr.pc = pc;
    instr.length = 2;
    instr.flow = ControlFlowType::SEQUENTIAL;
    instr.has_delay_slot = false;

    const uint16_t hi = (opcode >> 12) & 0x0Fu;
    const uint16_t lo = opcode & 0x0Fu;
    const uint8_t rn = static_cast<uint8_t>((opcode >> 8) & 0x0Fu);
    const uint8_t rm = static_cast<uint8_t>((opcode >> 4) & 0x0Fu);

    // Target subset:
    // 0x6nm1: MOV.W @Rm, Rn
    if (hi == 0x6u && lo == 0x1u) {
        instr.id = OpcodeId::MOV_W_READ_MEM;
        instr.rn = rn;
        instr.rm = rm;
        instr.mem_access = MemoryAccessType::READ_S16;
        return instr;
    }

    // 0x6nm2: MOV.L @Rm, Rn
    if (hi == 0x6u && lo == 0x2u) {
        instr.id = OpcodeId::MOV_L_READ_MEM;
        instr.rn = rn;
        instr.rm = rm;
        instr.mem_access = MemoryAccessType::READ_U32;
        return instr;
    }

    // 0x6nm3: MOV Rm, Rn
    if (hi == 0x6u && lo == 0x3u) {
        instr.id = OpcodeId::MOV_REG;
        instr.rn = rn;
        instr.rm = rm;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0xDndd: MOV.L @(disp, PC), Rn
    if (hi == 0xDu) {
        instr.id = OpcodeId::MOV_L_PC_REL;
        instr.rn = rn;
        instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        instr.mem_access = MemoryAccessType::READ_U32;
        return instr;
    }

    // 0xAddd: BRA label (12-bit signed displacement)
    if (hi == 0xAu) {
        instr.id = OpcodeId::BRA;
        instr.disp = static_cast<uint32_t>(opcode & 0x0FFFu);
        instr.flow = ControlFlowType::BRANCH;
        instr.has_delay_slot = true;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x4n0B: JSR @Rn
    if ((opcode & 0xF0FFu) == 0x400Bu) {
        instr.id = OpcodeId::JSR;
        instr.rn = rn;
        instr.flow = ControlFlowType::CALL;
        instr.has_delay_slot = true;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x0009: NOP
    if (opcode == 0x0009u) {
        instr.id = OpcodeId::NOP;
        instr.flow = ControlFlowType::SEQUENTIAL;
        instr.has_delay_slot = false;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x2nm6: MOV.L Rm, @-Rn
    if (hi == 0x2u && lo == 0x6u) {
        instr.id = OpcodeId::MOV_L_WRITE_PREDEC;
        instr.rn = rn;
        instr.rm = rm;
        instr.flow = ControlFlowType::SEQUENTIAL;
        instr.has_delay_slot = false;
        instr.mem_access = MemoryAccessType::WRITE_U32;
        return instr;
    }

    // 0x000B: RTS
    if (opcode == 0x000Bu) {
        instr.id = OpcodeId::RTS;
        instr.flow = ControlFlowType::RETURN;
        instr.has_delay_slot = true;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x9ndd: MOV.W @(disp, PC), Rn
    if (hi == 0x9u) {
        instr.id = OpcodeId::MOV_W_PC_REL;
        instr.rn = rn;
        instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        instr.mem_access = MemoryAccessType::READ_S16;
        return instr;
    }

    // 0x6nm6: MOV.L @Rm+, Rn
    if (hi == 0x6u && lo == 0x6u) {
        instr.id = OpcodeId::MOV_L_READ_POSTINC;
        instr.rn = rn;
        instr.rm = rm;
        instr.mem_access = MemoryAccessType::READ_U32;
        return instr;
    }

    // 0x4n22: STS.L PR, @-Rn
    if ((opcode & 0xF0FFu) == 0x4022u) {
        instr.id = OpcodeId::STS_L_PR_PREDEC;
        instr.rn = rn;
        instr.mem_access = MemoryAccessType::WRITE_U32;
        return instr;
    }

    // 0x4m26: LDS.L @Rm+, PR
    if ((opcode & 0xF0FFu) == 0x4026u) {
        instr.id = OpcodeId::LDS_L_PR_POSTINC;
        instr.rm = rn; // In 0x4m26, Rm is in bits 11..8
        instr.mem_access = MemoryAccessType::READ_U32;
        return instr;
    }

    // 0xEnii: MOV #imm, Rn
    if (hi == 0xEu) {
        instr.id = OpcodeId::MOV_IMM;
        instr.rn = rn;
        instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x7nii: ADD #imm, Rn
    if (hi == 0x7u) {
        instr.id = OpcodeId::ADD_IMM;
        instr.rn = rn;
        instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x2nm1: MOV.W Rm, @Rn
    if (hi == 0x2u && lo == 0x1u) {
        instr.id = OpcodeId::MOV_W_WRITE_MEM;
        instr.rn = rn;
        instr.rm = rm;
        instr.mem_access = MemoryAccessType::WRITE_U16;
        return instr;
    }

    // 0x2nm2: MOV.L Rm, @Rn
    if (hi == 0x2u && lo == 0x2u) {
        instr.id = OpcodeId::MOV_L_WRITE_MEM;
        instr.rn = rn;
        instr.rm = rm;
        instr.mem_access = MemoryAccessType::WRITE_U32;
        return instr;
    }

    // 0x2nm8: TST Rm, Rn
    if (hi == 0x2u && lo == 0x8u) {
        instr.id = OpcodeId::TST_REG;
        instr.rn = rn;
        instr.rm = rm;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x88ii: CMP/EQ #imm, R0
    if ((opcode & 0xFF00u) == 0x8800u) {
        instr.id = OpcodeId::CMP_EQ_IMM;
        instr.rn = 0;
        instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x3nm0: CMP/EQ Rm, Rn
    if (hi == 0x3u && lo == 0x0u) {
        instr.id = OpcodeId::CMP_EQ_REG;
        instr.rn = rn;
        instr.rm = rm;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x8Bdd: BF disp
    if ((opcode & 0xFF00u) == 0x8B00u) {
        instr.id = OpcodeId::BF;
        instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        instr.flow = ControlFlowType::BRANCH_CONDITIONAL;
        instr.has_delay_slot = false;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x89dd: BT disp
    if ((opcode & 0xFF00u) == 0x8900u) {
        instr.id = OpcodeId::BT;
        instr.disp = static_cast<uint32_t>(opcode & 0xFFu);
        instr.flow = ControlFlowType::BRANCH_CONDITIONAL;
        instr.has_delay_slot = false;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0xBddd: BSR disp
    if (hi == 0xBu) {
        instr.id = OpcodeId::BSR;
        instr.disp = static_cast<uint32_t>(opcode & 0x0FFFu);
        instr.flow = ControlFlowType::CALL;
        instr.has_delay_slot = true;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x4n2B: JMP @Rn
    if ((opcode & 0xF0FFu) == 0x402Bu) {
        instr.id = OpcodeId::JMP;
        instr.rn = rn;
        instr.flow = ControlFlowType::JUMP;
        instr.has_delay_slot = true;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x5nmd: MOV.L @(disp, Rm), Rn
    if (hi == 0x5u) {
        instr.id = OpcodeId::MOV_L_DISP_READ;
        instr.rn = rn;
        instr.rm = rm;
        instr.disp = static_cast<uint32_t>(lo);
        instr.mem_access = MemoryAccessType::READ_U32;
        return instr;
    }

    // 0x1nmd: MOV.L Rm, @(disp, Rn)
    if (hi == 0x1u) {
        instr.id = OpcodeId::MOV_L_DISP_WRITE;
        instr.rn = rn;
        instr.rm = rm;
        instr.disp = static_cast<uint32_t>(lo);
        instr.mem_access = MemoryAccessType::WRITE_U32;
        return instr;
    }

    // 0x81nd: MOV.W R0, @(disp, Rn)
    if ((opcode & 0xFF00u) == 0x8100u) {
        instr.id = OpcodeId::MOV_W_DISP_WRITE;
        instr.rn = static_cast<uint8_t>((opcode >> 4) & 0x0Fu);
        instr.rm = 0;
        instr.disp = static_cast<uint32_t>(lo);
        instr.mem_access = MemoryAccessType::WRITE_U16;
        return instr;
    }

    // 0x85md: MOV.W @(disp, Rm), R0
    if ((opcode & 0xFF00u) == 0x8500u) {
        instr.id = OpcodeId::MOV_W_DISP_READ;
        instr.rn = 0;
        instr.rm = static_cast<uint8_t>((opcode >> 4) & 0x0Fu);
        instr.disp = static_cast<uint32_t>(lo);
        instr.mem_access = MemoryAccessType::READ_S16;
        return instr;
    }

    // 0x6nm0: MOV.B @Rm, Rn
    if (hi == 0x6u && lo == 0x0u) {
        instr.id = OpcodeId::MOV_B_READ_MEM;
        instr.rn = rn;
        instr.rm = rm;
        instr.mem_access = MemoryAccessType::READ_S8;
        return instr;
    }

    // 0x2nm0: MOV.B Rm, @Rn
    if (hi == 0x2u && lo == 0x0u) {
        instr.id = OpcodeId::MOV_B_WRITE_MEM;
        instr.rn = rn;
        instr.rm = rm;
        instr.mem_access = MemoryAccessType::WRITE_U8;
        return instr;
    }

    // 0x3nmC: ADD Rm, Rn
    if (hi == 0x3u && lo == 0xCu) {
        instr.id = OpcodeId::ADD_REG;
        instr.rn = rn;
        instr.rm = rm;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x3nm8: SUB Rm, Rn
    if (hi == 0x3u && lo == 0x8u) {
        instr.id = OpcodeId::SUB_REG;
        instr.rn = rn;
        instr.rm = rm;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x4n00: SHLL Rn
    if ((opcode & 0xF0FFu) == 0x4000u) {
        instr.id = OpcodeId::SHLL;
        instr.rn = rn;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x4n01: SHLR Rn
    if ((opcode & 0xF0FFu) == 0x4001u) {
        instr.id = OpcodeId::SHLR;
        instr.rn = rn;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x4n08: SHLL2 Rn
    if ((opcode & 0xF0FFu) == 0x4008u) {
        instr.id = OpcodeId::SHLL2;
        instr.rn = rn;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x4n09: SHLR2 Rn
    if ((opcode & 0xF0FFu) == 0x4009u) {
        instr.id = OpcodeId::SHLR2;
        instr.rn = rn;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x0028: CLRMAC
    if (opcode == 0x0028u) {
        instr.id = OpcodeId::CLRMAC;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x0008: CLRT
    if (opcode == 0x0008u) {
        instr.id = OpcodeId::CLRT;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // 0x0018: SETT
    if (opcode == 0x0018u) {
        instr.id = OpcodeId::SETT;
        instr.mem_access = MemoryAccessType::NONE;
        return instr;
    }

    // Delegate extended arithmetic, logic, shifts, and indexed operations
    if (decode_sh2_ext(opcode, pc, instr)) {
        return instr;
    }

    // Delegate system, transfer, and ALU operations
    if (decode_sh2_ops(opcode, pc, instr)) {
        return instr;
    }

    // Fail closed for any unmodeled opcode
    instr.id = OpcodeId::UNKNOWN;
    instr.flow = ControlFlowType::ILLEGAL;
    instr.mem_access = MemoryAccessType::NONE;
    return instr;
}

} // namespace thor::sh2
