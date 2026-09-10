#include "thor/sh2/sh2_executor.hpp"

namespace thor::sh2 {

namespace {

inline void advance_pc(Sh2CpuState& state) noexcept {
    if (state.has_delayed_branch()) {
        state.pc = *state.delayed_pc;
        state.delayed_pc = std::nullopt;
    } else {
        state.pc += 2;
    }
}

} // namespace

ExecutionResult execute_sh2_instruction_ext(
    const Sh2Instruction& instr,
    Sh2CpuState& state,
    ISh2Memory& mem) noexcept {

    switch (instr.id) {
        case OpcodeId::SHAR: {
            const uint32_t msb = state.r[instr.rn] & 0x80000000u;
            state.set_t((state.r[instr.rn] & 1u) != 0);
            state.r[instr.rn] = (state.r[instr.rn] >> 1) | msb;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::BT_S: {
            if (state.get_t()) {
                state.pc = instr.compute_branch_target();
            } else {
                advance_pc(state);
            }
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::BF_S: {
            if (!state.get_t()) {
                state.pc = instr.compute_branch_target();
            } else {
                advance_pc(state);
            }
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::EXTU_B: {
            state.r[instr.rn] = state.r[instr.rm] & 0xFFu;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::EXTU_W: {
            state.r[instr.rn] = state.r[instr.rm] & 0xFFFFu;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::EXTS_B: {
            state.r[instr.rn] = static_cast<uint32_t>(static_cast<int32_t>(static_cast<int8_t>(state.r[instr.rm])));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::EXTS_W: {
            state.r[instr.rn] = static_cast<uint32_t>(static_cast<int32_t>(static_cast<int16_t>(state.r[instr.rm])));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::CMP_PZ: {
            state.set_t(static_cast<int32_t>(state.r[instr.rn]) >= 0);
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::CMP_PL: {
            state.set_t(static_cast<int32_t>(state.r[instr.rn]) > 0);
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_W_READ_POSTINC: {
            const int16_t val = static_cast<int16_t>(mem.read16(state.r[instr.rm]));
            state.r[instr.rm] += 2;
            state.r[instr.rn] = static_cast<uint32_t>(static_cast<int32_t>(val));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::AND_REG: {
            state.r[instr.rn] &= state.r[instr.rm];
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::OR_REG: {
            state.r[instr.rn] |= state.r[instr.rm];
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::CMP_HS: {
            state.set_t(state.r[instr.rn] >= state.r[instr.rm]);
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::CMP_GE: {
            state.set_t(static_cast<int32_t>(state.r[instr.rn]) >= static_cast<int32_t>(state.r[instr.rm]));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::CMP_HI: {
            state.set_t(state.r[instr.rn] > state.r[instr.rm]);
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::CMP_GT: {
            state.set_t(static_cast<int32_t>(state.r[instr.rn]) > static_cast<int32_t>(state.r[instr.rm]));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::ROTCL: {
            const uint32_t t = state.get_t() ? 1u : 0u;
            const uint32_t msb = (state.r[instr.rn] >> 31) & 1u;
            state.r[instr.rn] = (state.r[instr.rn] << 1) | t;
            state.set_t(msb != 0);
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::AND_IMM: {
            state.r[0] &= (instr.disp & 0xFFu);
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::TST_IMM: {
            state.set_t((state.r[0] & (instr.disp & 0xFFu)) == 0);
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_B_DISP_READ: {
            const int8_t s8 = static_cast<int8_t>(mem.read8(state.r[instr.rm] + instr.disp));
            state.r[0] = static_cast<uint32_t>(static_cast<int32_t>(s8));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_B_DISP_WRITE: {
            mem.write8(state.r[instr.rn] + instr.disp, static_cast<uint8_t>(state.r[0]));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_W_R0_READ: {
            const int16_t s16 = static_cast<int16_t>(mem.read16(state.r[instr.rm] + state.r[0]));
            state.r[instr.rn] = static_cast<uint32_t>(static_cast<int32_t>(s16));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_L_R0_READ: {
            state.r[instr.rn] = mem.read32(state.r[instr.rm] + state.r[0]);
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_B_R0_READ: {
            const int8_t s8 = static_cast<int8_t>(mem.read8(state.r[instr.rm] + state.r[0]));
            state.r[instr.rn] = static_cast<uint32_t>(static_cast<int32_t>(s8));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_L_R0_WRITE: {
            mem.write32(state.r[instr.rn] + state.r[0], state.r[instr.rm]);
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_W_R0_WRITE: {
            mem.write16(state.r[instr.rn] + state.r[0], static_cast<uint16_t>(state.r[instr.rm]));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOV_B_R0_WRITE: {
            mem.write8(state.r[instr.rn] + state.r[0], static_cast<uint8_t>(state.r[instr.rm]));
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::SHLL8: {
            state.r[instr.rn] <<= 8;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::SHLL16: {
            state.r[instr.rn] <<= 16;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::SHLR8: {
            state.r[instr.rn] >>= 8;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::SHLR16: {
            state.r[instr.rn] >>= 16;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::DT: {
            state.r[instr.rn] -= 1;
            state.set_t(state.r[instr.rn] == 0);
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        case OpcodeId::MOVT: {
            state.r[instr.rn] = state.get_t() ? 1u : 0u;
            advance_pc(state);
            return ExecutionResult::SUCCESS;
        }

        default:
            return ExecutionResult::UNSUPPORTED_INSTRUCTION;
    }
}

} // namespace thor::sh2
