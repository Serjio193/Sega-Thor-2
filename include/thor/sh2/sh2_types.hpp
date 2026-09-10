#pragma once

#include <cstdint>
#include <string>

namespace thor::sh2 {

/// Supported opcode categories for the bounded target subset.
enum class OpcodeId : uint16_t {
    UNKNOWN = 0,
    MOV_W_READ_MEM,     // MOV.W @Rm, Rn       (0110 nnnn mmmm 0001)
    MOV_REG,            // MOV Rm, Rn          (0110 nnnn mmmm 0011)
    MOV_L_PC_REL,       // MOV.L @(disp, PC), Rn (1101 nnnn dddddddd)
    MOV_L_READ_MEM,     // MOV.L @Rm, Rn       (0110 nnnn mmmm 0010)
    BRA,                // BRA label           (1010 dddddddddddd)
    JSR,                // JSR @Rn             (0100 nnnn 0000 1011)
    NOP,                // NOP                 (0000 0000 0000 1001)
    MOV_L_WRITE_PREDEC, // MOV.L Rm, @-Rn      (0010 nnnn mmmm 0110)
    RTS,                // RTS                 (0000 0000 0000 1011)
    MOV_W_PC_REL,       // MOV.W @(disp, PC), Rn (1001 nnnn dddddddd)
    MOV_L_READ_POSTINC, // MOV.L @Rm+, Rn      (0110 nnnn mmmm 0110)
    STS_L_PR_PREDEC,    // STS.L PR, @-Rn      (0100 nnnn 0010 0010)
    LDS_L_PR_POSTINC,   // LDS.L @Rm+, PR      (0100 mmmm 0010 0110)
    MOV_IMM,            // MOV #imm, Rn        (1110 nnnn iiiiiiii)
    ADD_IMM,            // ADD #imm, Rn        (0111 nnnn iiiiiiii)
    MOV_W_WRITE_MEM,    // MOV.W Rm, @Rn       (0010 nnnn mmmm 0001)
    MOV_L_WRITE_MEM,    // MOV.L Rm, @Rn       (0010 nnnn mmmm 0010)
    TST_REG,            // TST Rm, Rn          (0010 nnnn mmmm 1000)
    CMP_EQ_IMM,         // CMP/EQ #imm, R0     (1000 1000 iiiiiiii)
    CMP_EQ_REG,         // CMP/EQ Rm, Rn       (0011 nnnn mmmm 0000)
    BF,                 // BF label            (1000 1011 dddddddd)
    BT,                 // BT label            (1000 1001 dddddddd)
    BSR,                // BSR label           (1011 dddddddddddd)
    JMP,                // JMP @Rn             (0100 nnnn 0010 1011)
    MOV_L_DISP_READ,    // MOV.L @(disp,Rm), Rn (0101 nnnn mmmm dddd)
    MOV_L_DISP_WRITE,   // MOV.L Rm, @(disp,Rn) (0001 nnnn mmmm dddd)
    MOV_W_DISP_READ,    // MOV.W @(disp,Rm), R0 (1000 0101 mmmm dddd)
    MOV_W_DISP_WRITE,   // MOV.W R0, @(disp,Rn) (1000 0001 nnnn dddd)
    MOV_B_READ_MEM,     // MOV.B @Rm, Rn       (0110 nnnn mmmm 0000)
    MOV_B_WRITE_MEM,    // MOV.B Rm, @Rn       (0010 nnnn mmmm 0000)
    ADD_REG,            // ADD Rm, Rn          (0011 nnnn mmmm 1100)
    SUB_REG,            // SUB Rm, Rn          (0011 nnnn mmmm 1000)
    SHLL,               // SHLL Rn             (0100 nnnn 0000 0000)
    SHLR,               // SHLR Rn             (0100 nnnn 0000 0001)
    SHLL2,              // SHLL2 Rn            (0100 nnnn 0000 1000)
    SHLR2,              // SHLR2 Rn            (0100 nnnn 0000 1001)
    CLRMAC,             // CLRMAC              (0000 0000 0010 1000)
    CLRT,               // CLRT                (0000 0000 0000 1000)
    SETT,               // SETT                (0000 0000 0001 1000)
    SHAR,               // SHAR Rn             (0100 nnnn 0010 0001)
    BT_S,               // BT/S label          (1000 1101 dddddddd)
    BF_S,               // BF/S label          (1000 1111 dddddddd)
    EXTU_B,             // EXTU.B Rm, Rn       (0110 nnnn mmmm 1100)
    EXTU_W,             // EXTU.W Rm, Rn       (0110 nnnn mmmm 1101)
    EXTS_B,             // EXTS.B Rm, Rn       (0110 nnnn mmmm 1110)
    EXTS_W,             // EXTS.W Rm, Rn       (0110 nnnn mmmm 1111)
    CMP_PZ,             // CMP/PZ Rn           (0100 nnnn 0001 0001)
    CMP_PL,             // CMP/PL Rn           (0100 nnnn 0001 0101)
    MOV_W_READ_POSTINC, // MOV.W @Rm+, Rn      (0110 nnnn mmmm 0101)
    AND_REG,            // AND Rm, Rn          (0010 nnnn mmmm 1001)
    OR_REG,             // OR Rm, Rn           (0010 nnnn mmmm 1011)
    CMP_HS,             // CMP/HS Rm, Rn       (0011 nnnn mmmm 0010)
    CMP_GE,             // CMP/GE Rm, Rn       (0011 nnnn mmmm 0011)
    CMP_HI,             // CMP/HI Rm, Rn       (0011 nnnn mmmm 0110)
    CMP_GT,             // CMP/GT Rm, Rn       (0011 nnnn mmmm 0111)
    ROTCL,              // ROTCL Rn            (0100 nnnn 0010 0100)
    AND_IMM,            // AND #imm, R0        (1100 1001 iiii iiii)
    TST_IMM,            // TST #imm, R0        (1100 1000 iiii iiii)
    MOV_B_DISP_READ,    // MOV.B @(disp, Rm), R0 (1000 0100 mmmm dddd)
    MOV_B_DISP_WRITE,   // MOV.B R0, @(disp, Rn) (1000 0000 nnnn dddd)
    MOV_W_R0_READ,      // MOV.W @(R0, Rm), Rn (0000 nnnn mmmm 1101)
    MOV_L_R0_READ,      // MOV.L @(R0, Rm), Rn (0000 nnnn mmmm 1110)
    MOV_B_R0_READ,      // MOV.B @(R0, Rm), Rn (0000 nnnn mmmm 1100)
    MOV_L_R0_WRITE,     // MOV.L Rm, @(R0, Rn) (0000 nnnn mmmm 0110)
    MOV_W_R0_WRITE,     // MOV.W Rm, @(R0, Rn) (0000 nnnn mmmm 0101)
    MOV_B_R0_WRITE,     // MOV.B Rm, @(R0, Rn) (0000 nnnn mmmm 0100)
    SHLL8,              // SHLL8 Rn            (0100 nnnn 0001 1000)
    SHLL16,             // SHLL16 Rn           (0100 nnnn 0010 1000)
    SHLR8,              // SHLR8 Rn            (0100 nnnn 0001 1001)
    SHLR16,             // SHLR16 Rn           (0100 nnnn 0010 1001)
    DT,                 // DT Rn               (0100 nnnn 0001 0000)
    MOVT                // MOVT Rn             (0000 nnnn 0010 1001)
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
            case OpcodeId::MOV_W_PC_REL:
                return (pc + 4u) + (disp * 2u);
            case OpcodeId::MOV_L_DISP_READ:
            case OpcodeId::MOV_L_DISP_WRITE:
                return base_reg_val + (disp * 4u);
            case OpcodeId::MOV_W_DISP_READ:
            case OpcodeId::MOV_W_DISP_WRITE:
                return base_reg_val + (disp * 2u);
            case OpcodeId::MOV_B_DISP_READ:
            case OpcodeId::MOV_B_DISP_WRITE:
                return base_reg_val + disp;
            case OpcodeId::MOV_W_READ_MEM:
            case OpcodeId::MOV_L_READ_MEM:
            case OpcodeId::MOV_B_READ_MEM:
            case OpcodeId::MOV_W_WRITE_MEM:
            case OpcodeId::MOV_L_WRITE_MEM:
            case OpcodeId::MOV_B_WRITE_MEM:
            case OpcodeId::MOV_L_READ_POSTINC:
            case OpcodeId::MOV_W_READ_POSTINC:
            case OpcodeId::LDS_L_PR_POSTINC:
                return base_reg_val;
            case OpcodeId::MOV_W_R0_READ:
            case OpcodeId::MOV_L_R0_READ:
            case OpcodeId::MOV_B_R0_READ:
            case OpcodeId::MOV_L_R0_WRITE:
            case OpcodeId::MOV_W_R0_WRITE:
            case OpcodeId::MOV_B_R0_WRITE:
                return base_reg_val; // base register is (Rm or Rn) + R0, caller supplies evaluated sum
            case OpcodeId::MOV_L_WRITE_PREDEC:
            case OpcodeId::STS_L_PR_PREDEC:
                return base_reg_val - 4u;
            default:
                return 0;
        }
    }

    /// Computes the branch destination address for control transfer instructions.
    [[nodiscard]] uint32_t compute_branch_target() const noexcept {
        if (id == OpcodeId::BRA || id == OpcodeId::BSR) {
            const int32_t s_disp = (disp & 0x800u)
                ? static_cast<int32_t>(disp | 0xFFFFF000u)
                : static_cast<int32_t>(disp);
            return static_cast<uint32_t>(static_cast<int64_t>(pc) + 4 + (static_cast<int64_t>(s_disp) * 2));
        }
        if (id == OpcodeId::BF || id == OpcodeId::BT || id == OpcodeId::BF_S || id == OpcodeId::BT_S) {
            const int32_t s_disp = (disp & 0x80u)
                ? static_cast<int32_t>(disp | 0xFFFFFF00u)
                : static_cast<int32_t>(disp);
            return static_cast<uint32_t>(static_cast<int64_t>(pc) + 4 + (static_cast<int64_t>(s_disp) * 2));
        }
        return 0;
    }

    [[nodiscard]] std::string mnemonic() const;
};

} // namespace thor::sh2
