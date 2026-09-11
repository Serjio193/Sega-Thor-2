#pragma once

#include "thor/sh2/sh2_types.hpp"

namespace thor::sh2 {

/// Decodes a 16-bit SH-2 opcode at the given program counter.
/// Supported target subset:
/// - 0x6nm1: MOV.W @Rm, Rn
/// - 0x6nm3: MOV Rm, Rn
/// - 0xDndd: MOV.L @(disp, PC), Rn
/// - 0x6nm2: MOV.L @Rm, Rn
///
/// Any unsupported or unrecognized opcode fails closed returning Sh2Instruction
/// with id == OpcodeId::UNKNOWN.
[[nodiscard]] Sh2Instruction decode_sh2(uint16_t opcode, uint32_t pc = 0) noexcept;

/// Decodes extended SH-2 arithmetic, logical, and indexed instructions into instr.
/// Returns true if decoded, false otherwise.
bool decode_sh2_ext(uint16_t opcode, uint32_t pc, Sh2Instruction& instr) noexcept;

/// Decodes system, transfer, and ALU operations into instr.
/// Returns true if decoded, false otherwise.
bool decode_sh2_ops(uint16_t opcode, uint32_t pc, Sh2Instruction& instr) noexcept;

} // namespace thor::sh2
