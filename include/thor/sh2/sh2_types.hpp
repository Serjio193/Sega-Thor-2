#pragma once

#include <cstdint>
#include <string>

namespace thor::sh2 {

/// Supported opcode categories for the bounded target subset.
enum class OpcodeId : uint16_t {
    UNKNOWN = 0,
    MOV_W_READ_MEM,  // MOV.W @Rm, Rn (0110 nnnn mmmm 0001)
    MOV_REG,         // MOV Rm, Rn    (0110 nnnn mmmm 0011)
    MOV_L_PC_REL,    // MOV.L @(disp, PC), Rn (1101 nnnn dddddddd)
    MOV_L_READ_MEM,  // MOV.L @Rm, Rn (0110 nnnn mmmm 0010)
    BRA,             // BRA label     (1010 dddddddddddd)
    JSR,             // JSR @Rn       (0100 nnnn 0000 1011)
    NOP,             // NOP           (0000 0000 0000 1001)
    MOV_L_WRITE_PREDEC, // MOV.L Rm, @-Rn (0010 nnnn mmmm 0110)
    RTS              // RTS           (0000 0000 0000 1011)
};


/// Control flow behavior.
enum class ControlFlowType : uint8_t {
    SEQUENTIAL = 0,
    BRANCH,
    BRANCH_CONDITIONAL,
    JUMP,
    CALL,
    RETURN,
    ILLEGAL
};

/// Memory access width/sign for memory operations.
enum class MemoryAccessType : uint8_t {
    NONE = 0,
    READ_U8,
    READ_S8,
    READ_U16,
    READ_S16,
    READ_U32,
    WRITE_U8,
    WRITE_U16,
    WRITE_U32
};

/// Decoded representation of a 16-bit SH-2 instruction.
struct Sh2Instruction {
    uint16_t raw_opcode = 0;
    uint32_t pc = 0;
    OpcodeId id = OpcodeId::UNKNOWN;
    uint8_t rn = 0;          // Destination / target register (0..15)
    uint8_t rm = 0;          // Source register (0..15)
    uint32_t disp = 0;       // Displacement / immediate value
    uint8_t length = 2;      // Length in bytes (always 2 on SH-2)
    ControlFlowType flow = ControlFlowType::SEQUENTIAL;
    bool has_delay_slot = false;
    MemoryAccessType mem_access = MemoryAccessType::NONE;

    [[nodiscard]] constexpr bool is_valid() const noexcept {
        return id != OpcodeId::UNKNOWN;
    }

    /// Computes the effective memory address for load/store instructions.
    /// For PC-relative instructions, implements the SH-2 architectural PC-base rule:
    /// ((PC & ~3) + 4) + (disp * 4).
    [[nodiscard]] uint32_t compute_effective_address(uint32_t base_reg_val = 0) const noexcept {
        switch (id) {
            case OpcodeId::MOV_L_PC_REL:
                return ((pc & ~3u) + 4u) + (disp * 4u);
            case OpcodeId::MOV_W_READ_MEM:
            case OpcodeId::MOV_L_READ_MEM:
                return base_reg_val;
            default:
                return 0;
        }
    }

    /// Computes the branch destination address for control transfer instructions.
    /// For BRA: PC + 4 + (sign_extend_12(disp) * 2).
    [[nodiscard]] uint32_t compute_branch_target() const noexcept {
        if (id == OpcodeId::BRA) {
            const int32_t s_disp = (disp & 0x800u)
                ? static_cast<int32_t>(disp | 0xFFFFF000u)
                : static_cast<int32_t>(disp);
            return static_cast<uint32_t>(static_cast<int64_t>(pc) + 4 + (static_cast<int64_t>(s_disp) * 2));
        }
        return 0;
    }

    [[nodiscard]] std::string mnemonic() const;
};

} // namespace thor::sh2
