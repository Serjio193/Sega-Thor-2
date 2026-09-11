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
    MOVT,               // MOVT Rn             (0000 nnnn 0010 1001)
    STS_MACL,           // STS MACL, Rn        (0000 nnnn 0001 1010)
    STS_MACH,           // STS MACH, Rn        (0000 nnnn 0000 1010)
    STS_PR,             // STS PR, Rn          (0000 nnnn 0010 1010)
    LDS_MACL,           // LDS Rm, MACL        (0100 mmmm 0001 1010)
    LDS_MACH,           // LDS Rm, MACH        (0100 mmmm 0000 1010)
    LDS_PR,             // LDS Rm, PR          (0100 mmmm 0010 1010)
    STS_L_MACL_PREDEC,  // STS.L MACL, @-Rn    (0100 nnnn 0001 0010)
    STS_L_MACH_PREDEC,  // STS.L MACH, @-Rn    (0100 nnnn 0000 0010)
    LDS_L_MACL_POSTINC, // LDS.L @Rm+, MACL    (0100 mmmm 0001 0110)
    LDS_L_MACH_POSTINC, // LDS.L @Rm+, MACH    (0100 mmmm 0000 0110)
    MOV_B_READ_POSTINC, // MOV.B @Rm+, Rn      (0110 nnnn mmmm 0100)
    MOV_B_WRITE_PREDEC, // MOV.B Rm, @-Rn      (0010 nnnn mmmm 0100)
    MOV_W_WRITE_PREDEC, // MOV.W Rm, @-Rn      (0010 nnnn mmmm 0101)
    MOVA,               // MOVA @(disp, PC), R0 (1100 0111 dddddddd)
    NOT_REG,            // NOT Rm, Rn          (0110 nnnn mmmm 0111)
    SWAP_B,             // SWAP.B Rm, Rn       (0110 nnnn mmmm 1000)
    SWAP_W,             // SWAP.W Rm, Rn       (0110 nnnn mmmm 1001)
    NEGC,               // NEGC Rm, Rn         (0110 nnnn mmmm 1010)
    NEG,                // NEG Rm, Rn          (0110 nnnn mmmm 1011)
    XOR_REG,            // XOR Rm, Rn          (0010 nnnn mmmm 1010)
    XOR_IMM,            // XOR #imm, R0        (1100 1010 iiii iiii)
    OR_IMM,             // OR #imm, R0         (1100 1011 iiii iiii)
    DIV0U,              // DIV0U               (0000 0000 0001 1001)
    DIV0S,              // DIV0S Rm, Rn        (0010 nnnn mmmm 0111)
    DIV1,               // DIV1 Rm, Rn         (0011 nnnn mmmm 0100)
    ROTL,               // ROTL Rn             (0100 nnnn 0000 0100)
    ROTR,               // ROTR Rn             (0100 nnnn 0000 0101)
    ROTCR,              // ROTCR Rn            (0100 nnnn 0010 0101)
    SHAL,               // SHAL Rn             (0100 nnnn 0010 0000)
    SUBC,               // SUBC Rm, Rn         (0011 nnnn mmmm 1010)
    SUBV,               // SUBV Rm, Rn         (0011 nnnn mmmm 1011)
    ADDC,               // ADDC Rm, Rn         (0011 nnnn mmmm 1110)
    ADDV,               // ADDV Rm, Rn         (0011 nnnn mmmm 1111)
    MULU_W,             // MULU.W Rm, Rn       (0010 nnnn mmmm 1110)
    MULS_W,             // MULS.W Rm, Rn       (0010 nnnn mmmm 1111)
    DMULU_L,            // DMULU.L Rm, Rn      (0011 nnnn mmmm 0101)
    DMULS_L,            // DMULS.L Rm, Rn      (0011 nnnn mmmm 1101)
    CMP_STR,            // CMP/STR Rm, Rn      (0010 nnnn mmmm 1100)
    STC_SR,             // STC SR, Rn          (0000 nnnn 0000 0010)
    STC_GBR,            // STC GBR, Rn         (0000 nnnn 0001 0010)
    STC_VBR,            // STC VBR, Rn         (0000 nnnn 0010 0010)
    LDC_SR,             // LDC Rm, SR          (0100 mmmm 0000 1110)
    LDC_GBR,            // LDC Rm, GBR         (0100 mmmm 0001 1110)
    LDC_VBR,            // LDC Rm, VBR         (0100 mmmm 0010 1110)
    STC_L_SR_PREDEC,    // STC.L SR, @-Rn      (0100 nnnn 0000 0011)
    STC_L_GBR_PREDEC,   // STC.L GBR, @-Rn     (0100 nnnn 0001 0011)
    STC_L_VBR_PREDEC,   // STC.L VBR, @-Rn     (0100 nnnn 0010 0011)
    LDC_L_SR_POSTINC,   // LDC.L @Rm+, SR      (0100 mmmm 0000 0111)
    LDC_L_GBR_POSTINC,  // LDC.L @Rm+, GBR     (0100 mmmm 0001 0111)
    LDC_L_VBR_POSTINC,  // LDC.L @Rm+, VBR     (0100 mmmm 0010 0111)
    SLEEP,              // SLEEP               (0000 0000 0001 1011)
    RTE,                // RTE                 (0000 0000 0010 1011)
    TRAPA,              // TRAPA #imm          (1100 0011 iiii iiii)
    MUL_L,              // MUL.L Rm, Rn        (0000 nnnn mmmm 0111)
    MAC_L,              // MAC.L @Rm+, @Rn+    (0000 nnnn mmmm 1111)
    MAC_W,              // MAC.W @Rm+, @Rn+    (0100 nnnn mmmm 1111)
    BSRF,               // BSRF Rn             (0000 nnnn 0000 0011)
    BRAF,               // BRAF Rn             (0000 nnnn 0010 0011)
    XTRCT,              // XTRCT Rm, Rn        (0010 nnnn mmmm 1101)
    TAS_B,              // TAS.B @Rn           (0100 nnnn 0001 1011)
    MOV_B_GBR_WRITE,    // MOV.B R0, @(disp, GBR) (1100 0000 dddddddd)
    MOV_W_GBR_WRITE,    // MOV.W R0, @(disp, GBR) (1100 0001 dddddddd)
    MOV_L_GBR_WRITE,    // MOV.L R0, @(disp, GBR) (1100 0010 dddddddd)
    MOV_B_GBR_READ,     // MOV.B @(disp, GBR), R0 (1100 0100 dddddddd)
    MOV_W_GBR_READ,     // MOV.W @(disp, GBR), R0 (1100 0101 dddddddd)
    MOV_L_GBR_READ,     // MOV.L @(disp, GBR), R0 (1100 0110 dddddddd)
    TST_B_GBR,          // TST.B #imm, @(R0, GBR) (1100 1100 iiii iiii)
    AND_B_GBR,          // AND.B #imm, @(R0, GBR) (1100 1101 iiii iiii)
    XOR_B_GBR,          // XOR.B #imm, @(R0, GBR) (1100 1110 iiii iiii)
    OR_B_GBR            // OR.B #imm, @(R0, GBR)  (1100 1111 iiii iiii)
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
            case OpcodeId::MOVA:
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
            case OpcodeId::MOV_B_READ_POSTINC:
            case OpcodeId::LDS_L_PR_POSTINC:
            case OpcodeId::LDS_L_MACL_POSTINC:
            case OpcodeId::LDS_L_MACH_POSTINC:
            case OpcodeId::LDC_L_SR_POSTINC:
            case OpcodeId::LDC_L_GBR_POSTINC:
            case OpcodeId::LDC_L_VBR_POSTINC:
                return base_reg_val;
            case OpcodeId::MOV_W_R0_READ:
            case OpcodeId::MOV_L_R0_READ:
            case OpcodeId::MOV_B_R0_READ:
            case OpcodeId::MOV_L_R0_WRITE:
            case OpcodeId::MOV_W_R0_WRITE:
            case OpcodeId::MOV_B_R0_WRITE:
                return base_reg_val; // base register is (Rm or Rn) + R0, caller supplies evaluated sum
            case OpcodeId::MOV_B_WRITE_PREDEC:
                return base_reg_val - 1u;
            case OpcodeId::MOV_W_WRITE_PREDEC:
                return base_reg_val - 2u;
            case OpcodeId::MOV_L_WRITE_PREDEC:
            case OpcodeId::STS_L_PR_PREDEC:
            case OpcodeId::STS_L_MACL_PREDEC:
            case OpcodeId::STS_L_MACH_PREDEC:
            case OpcodeId::STC_L_SR_PREDEC:
            case OpcodeId::STC_L_GBR_PREDEC:
            case OpcodeId::STC_L_VBR_PREDEC:
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
