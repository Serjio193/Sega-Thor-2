#include "thor/sh2/sh2_executor.hpp"

namespace thor::sh2 {

ExecutionResult execute_sh2_instruction(
    const Sh2Instruction& instr,
    Sh2CpuState& state,
    ISh2Memory& mem) noexcept {

    if (!instr.is_valid()) {
        return ExecutionResult::UNSUPPORTED_INSTRUCTION;
    }

    switch (instr.id) {
        case OpcodeId::MOV_W_READ_MEM: {
            const uint32_t addr = state.r[instr.rm];
            const uint16_t raw_val = mem.read16(addr);
            // Sign-extend 16-bit to 32-bit:
            const int16_t s16 = static_cast<int16_t>(raw_val);
            state.r[instr.rn] = static_cast<uint32_t>(static_cast<int32_t>(s16));
            state.pc += 2;
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_REG: {
            state.r[instr.rn] = state.r[instr.rm];
            state.pc += 2;
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_L_PC_REL: {
            // Hitachi SH-2 rule: ((PC & ~3) + 4) + (disp * 4)
            const uint32_t ea = ((instr.pc & ~3u) + 4u) + (instr.disp * 4u);
            const uint32_t val32 = mem.read32(ea);
            state.r[instr.rn] = val32;
            state.pc += 2;
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_L_READ_MEM: {
            // Source address captured before writeback even when Rm == Rn:
            const uint32_t addr = state.r[instr.rm];
            const uint32_t val32 = mem.read32(addr);
            state.r[instr.rn] = val32;
            state.pc += 2;
            return ExecutionResult::SUCCESS;
        }

        default:
            return ExecutionResult::UNSUPPORTED_INSTRUCTION;
    }
}

StepResult step_sh2(Sh2CpuState& state, ISh2Memory& mem) noexcept {
    StepResult res{};
    res.pre_pc = state.pc;
    const uint16_t raw_opcode = mem.read16(state.pc);
    res.instruction = decode_sh2(raw_opcode, state.pc);
    res.status = execute_sh2_instruction(res.instruction, state, mem);
    res.post_pc = state.pc;
    return res;
}

} // namespace thor::sh2
