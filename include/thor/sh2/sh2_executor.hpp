#pragma once

#include "thor/sh2/sh2_decoder.hpp"
#include "thor/sh2/sh2_memory.hpp"
#include "thor/sh2/sh2_state.hpp"

namespace thor::sh2 {

enum class ExecutionResult : uint8_t {
    SUCCESS = 0,
    UNSUPPORTED_INSTRUCTION,
    ILLEGAL_ADDRESS,
    ILLEGAL_SLOT_INSTRUCTION
};

struct StepResult {
    ExecutionResult status = ExecutionResult::SUCCESS;
    Sh2Instruction instruction{};
    uint32_t pre_pc = 0;
    uint32_t post_pc = 0;
};

/// Executes a single pre-decoded SH-2 instruction against explicit state and memory.
[[nodiscard]] ExecutionResult execute_sh2_instruction(
    const Sh2Instruction& instr,
    Sh2CpuState& state,
    ISh2Memory& mem) noexcept;

/// Executes extended SH-2 arithmetic, logical, and indexed instructions.
[[nodiscard]] ExecutionResult execute_sh2_instruction_ext(
    const Sh2Instruction& instr,
    Sh2CpuState& state,
    ISh2Memory& mem) noexcept;

/// Fetches, decodes, and executes the instruction at state.pc.
[[nodiscard]] StepResult step_sh2(
    Sh2CpuState& state,
    ISh2Memory& mem) noexcept;

} // namespace thor::sh2
