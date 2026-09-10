#include "thor/sh2/sh2_executor.hpp"

namespace thor::sh2 {

namespace {

/// Advances PC to next sequential instruction (+2) or to pending delayed branch target.
inline void advance_pc(Sh2CpuState& state) noexcept {
    if (state.has_delayed_branch()) {
        state.pc = *state.delayed_pc;
        state.delayed_pc = std::nullopt;
    } else {
        state.pc += 2;
    }
}

} // namespace

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
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_REG: {
            state.r[instr.rn] = state.r[instr.rm];
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_L_PC_REL: {
            // Hitachi SH-2 rule: ((PC & ~3) + 4) + (disp * 4)
            const uint32_t ea = ((instr.pc & ~3u) + 4u) + (instr.disp * 4u);
            const uint32_t val32 = mem.read32(ea);
            state.r[instr.rn] = val32;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_L_READ_MEM: {
            // Source address captured before writeback even when Rm == Rn:
            const uint32_t addr = state.r[instr.rm];
            const uint32_t val32 = mem.read32(addr);
            state.r[instr.rn] = val32;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::BRA: {
            // Hitachi SH-2: branch instructions in a delay slot trigger an illegal slot instruction exception
            if (state.has_delayed_branch()) {
                return ExecutionResult::ILLEGAL_SLOT_INSTRUCTION;
            }
            const uint32_t target = instr.compute_branch_target();
            state.delayed_pc = target;
            state.pc += 2; // Advance to delay slot instruction
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::JSR: {
            // Hitachi SH-2: branch instructions in a delay slot trigger an illegal slot instruction exception
            if (state.has_delayed_branch()) {
                return ExecutionResult::ILLEGAL_SLOT_INSTRUCTION;
            }
            const uint32_t target = state.r[instr.rn];
            state.pr = instr.pc + 4u;
            state.delayed_pc = target;
            state.pc += 2; // Advance to delay slot instruction
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::NOP: {
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_L_WRITE_PREDEC: {
            state.r[instr.rn] -= 4;
            const uint32_t val = (instr.rn == instr.rm) ? state.r[instr.rn] : state.r[instr.rm];
            mem.write32(state.r[instr.rn], val);
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::RTS: {
            if (state.has_delayed_branch()) {
                return ExecutionResult::ILLEGAL_SLOT_INSTRUCTION;
            }
            state.delayed_pc = state.pr;
            state.pc += 2;
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_W_PC_REL: {
            const uint32_t ea = instr.compute_effective_address();
            const int16_t s16 = static_cast<int16_t>(mem.read16(ea));
            state.r[instr.rn] = static_cast<uint32_t>(static_cast<int32_t>(s16));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_L_READ_POSTINC: {
            const uint32_t val = mem.read32(state.r[instr.rm]);
            if (instr.rn != instr.rm) {
                state.r[instr.rm] += 4;
            }
            state.r[instr.rn] = val;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::STS_L_PR_PREDEC: {
            state.r[instr.rn] -= 4;
            mem.write32(state.r[instr.rn], state.pr);
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::LDS_L_PR_POSTINC: {
            state.pr = mem.read32(state.r[instr.rm]);
            state.r[instr.rm] += 4;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_IMM: {
            state.r[instr.rn] = static_cast<uint32_t>(static_cast<int32_t>(static_cast<int8_t>(instr.disp)));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::ADD_IMM: {
            state.r[instr.rn] += static_cast<uint32_t>(static_cast<int32_t>(static_cast<int8_t>(instr.disp)));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_W_WRITE_MEM: {
            mem.write16(state.r[instr.rn], static_cast<uint16_t>(state.r[instr.rm]));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_L_WRITE_MEM: {
            mem.write32(state.r[instr.rn], state.r[instr.rm]);
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::TST_REG: {
            if ((state.r[instr.rn] & state.r[instr.rm]) == 0) {
                state.sr |= 1u;
            } else {
                state.sr &= ~1u;
            }
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::CMP_EQ_IMM: {
            const int32_t imm = static_cast<int32_t>(static_cast<int8_t>(instr.disp));
            if (static_cast<int32_t>(state.r[0]) == imm) {
                state.sr |= 1u;
            } else {
                state.sr &= ~1u;
            }
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::CMP_EQ_REG: {
            if (state.r[instr.rn] == state.r[instr.rm]) {
                state.sr |= 1u;
            } else {
                state.sr &= ~1u;
            }
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::BF: {
            if ((state.sr & 1u) == 0) {
                state.pc = instr.compute_branch_target();
            } else {
                state.pc += 2;
            }
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::BT: {
            if ((state.sr & 1u) != 0) {
                state.pc = instr.compute_branch_target();
            } else {
                state.pc += 2;
            }
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::BSR: {
            if (state.has_delayed_branch()) {
                return ExecutionResult::ILLEGAL_SLOT_INSTRUCTION;
            }
            state.pr = instr.pc + 4u;
            state.delayed_pc = instr.compute_branch_target();
            state.pc += 2;
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::JMP: {
            if (state.has_delayed_branch()) {
                return ExecutionResult::ILLEGAL_SLOT_INSTRUCTION;
            }
            state.delayed_pc = state.r[instr.rn];
            state.pc += 2;
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_L_DISP_READ: {
            const uint32_t ea = state.r[instr.rm] + (instr.disp * 4u);
            state.r[instr.rn] = mem.read32(ea);
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_L_DISP_WRITE: {
            const uint32_t ea = state.r[instr.rn] + (instr.disp * 4u);
            mem.write32(ea, state.r[instr.rm]);
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_W_DISP_READ: {
            const uint32_t ea = state.r[instr.rm] + (instr.disp * 2u);
            const int16_t s16 = static_cast<int16_t>(mem.read16(ea));
            state.r[0] = static_cast<uint32_t>(static_cast<int32_t>(s16));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_W_DISP_WRITE: {
            const uint32_t ea = state.r[instr.rn] + (instr.disp * 2u);
            mem.write16(ea, static_cast<uint16_t>(state.r[0]));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_B_READ_MEM: {
            const int8_t s8 = static_cast<int8_t>(mem.read8(state.r[instr.rm]));
            state.r[instr.rn] = static_cast<uint32_t>(static_cast<int32_t>(s8));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_B_WRITE_MEM: {
            mem.write8(state.r[instr.rn], static_cast<uint8_t>(state.r[instr.rm]));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::ADD_REG: {
            state.r[instr.rn] += state.r[instr.rm];
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::SUB_REG: {
            state.r[instr.rn] -= state.r[instr.rm];
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::SHLL: {
            state.sr = (state.sr & ~1u) | ((state.r[instr.rn] >> 31) & 1u);
            state.r[instr.rn] <<= 1;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::SHLR: {
            state.sr = (state.sr & ~1u) | (state.r[instr.rn] & 1u);
            state.r[instr.rn] >>= 1;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::SHLL2: {
            state.r[instr.rn] <<= 2;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::SHLR2: {
            state.r[instr.rn] >>= 2;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::CLRMAC: {
            state.mach = 0;
            state.macl = 0;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::CLRT: {
            state.sr &= ~1u;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::SETT: {
            state.sr |= 1u;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        default:
            return execute_sh2_instruction_ext(instr, state, mem);
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
