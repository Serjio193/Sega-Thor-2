#include "thor/sh2/sh2_decoder.hpp"

#include <iomanip>
#include <sstream>

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

    // Fail closed for any unmodeled opcode
    instr.id = OpcodeId::UNKNOWN;
    instr.flow = ControlFlowType::ILLEGAL;
    instr.mem_access = MemoryAccessType::NONE;
    return instr;
}

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
        case OpcodeId::MOV_L_READ_MEM:
            ss << "mov.l @r" << static_cast<int>(rm) << ", r" << static_cast<int>(rn);
            return ss.str();
        default:
            ss << ".word 0x" << std::hex << std::setw(4) << std::setfill('0') << raw_opcode;
            return ss.str();
    }
}

} // namespace thor::sh2
