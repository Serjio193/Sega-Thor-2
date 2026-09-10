#include "thor/sh2/sh2_decoder.hpp"
#include "test_framework.hpp"

#include <iostream>

using namespace thor::sh2;

static void test_extended_mov_w_pc_rel() {
    // 0x9004: mov.w @(4, PC), r0
    // PC = 0x06001000 -> target = 0x06001000 + 4 + 4*2 = 0x0600100C
    const auto ins = decode_sh2(0x9004, 0x06001000);
    THOR_ASSERT(ins.id == OpcodeId::MOV_W_PC_REL);
    THOR_ASSERT(ins.rn == 0);
    THOR_ASSERT(ins.disp == 4);
    THOR_ASSERT(ins.compute_effective_address() == 0x0600100C);
    THOR_ASSERT(ins.mnemonic() == "mov.w @(0x8, pc), r0");
}

static void test_extended_stack_and_reg_moves() {
    // 0x6126: mov.l @r2+, r1
    const auto ins1 = decode_sh2(0x6126, 0x06001000);
    THOR_ASSERT(ins1.id == OpcodeId::MOV_L_READ_POSTINC);
    THOR_ASSERT(ins1.rn == 1 && ins1.rm == 2);
    THOR_ASSERT(ins1.mnemonic() == "mov.l @r2+, r1");

    // 0x4F22: sts.l pr, @-r15
    const auto ins2 = decode_sh2(0x4F22, 0x06001000);
    THOR_ASSERT(ins2.id == OpcodeId::STS_L_PR_PREDEC);
    THOR_ASSERT(ins2.rn == 15);
    THOR_ASSERT(ins2.compute_effective_address(0x06002000) == 0x06001FFC);
    THOR_ASSERT(ins2.mnemonic() == "sts.l pr, @-r15");

    // 0x4F26: lds.l @r15+, pr
    const auto ins3 = decode_sh2(0x4F26, 0x06001000);
    THOR_ASSERT(ins3.id == OpcodeId::LDS_L_PR_POSTINC);
    THOR_ASSERT(ins3.rm == 15);
    THOR_ASSERT(ins3.mnemonic() == "lds.l @r15+, pr");
}

static void test_extended_immediates_and_alu() {
    // 0xE410: mov #16, r4
    const auto ins1 = decode_sh2(0xE410, 0x06001000);
    THOR_ASSERT(ins1.id == OpcodeId::MOV_IMM);
    THOR_ASSERT(ins1.rn == 4 && ins1.disp == 16);
    THOR_ASSERT(ins1.mnemonic() == "mov #16, r4");

    // 0x74FE: add #-2, r4
    const auto ins2 = decode_sh2(0x74FE, 0x06001000);
    THOR_ASSERT(ins2.id == OpcodeId::ADD_IMM);
    THOR_ASSERT(ins2.rn == 4 && ins2.disp == 0xFE);
    THOR_ASSERT(ins2.mnemonic() == "add #-2, r4");

    // 0x312C: add r2, r1
    const auto ins3 = decode_sh2(0x312C, 0x06001000);
    THOR_ASSERT(ins3.id == OpcodeId::ADD_REG);
    THOR_ASSERT(ins3.rn == 1 && ins3.rm == 2);

    // 0x3128: sub r2, r1
    const auto ins4 = decode_sh2(0x3128, 0x06001000);
    THOR_ASSERT(ins4.id == OpcodeId::SUB_REG);
    THOR_ASSERT(ins4.rn == 1 && ins4.rm == 2);
}

static void test_extended_comparisons_and_branches() {
    // 0x2128: tst r2, r1
    const auto ins1 = decode_sh2(0x2128, 0x06001000);
    THOR_ASSERT(ins1.id == OpcodeId::TST_REG);

    // 0x8805: cmp/eq #5, r0
    const auto ins2 = decode_sh2(0x8805, 0x06001000);
    THOR_ASSERT(ins2.id == OpcodeId::CMP_EQ_IMM);
    THOR_ASSERT(ins2.disp == 5);

    // 0x3120: cmp/eq r2, r1
    const auto ins3 = decode_sh2(0x3120, 0x06001000);
    THOR_ASSERT(ins3.id == OpcodeId::CMP_EQ_REG);

    // 0x8904: bt +4 -> 0x06001000 + 4 + 4*2 = 0x0600100C
    const auto ins4 = decode_sh2(0x8904, 0x06001000);
    THOR_ASSERT(ins4.id == OpcodeId::BT);
    THOR_ASSERT(!ins4.has_delay_slot);
    THOR_ASSERT(ins4.compute_branch_target() == 0x0600100C);

    // 0x8B04: bf +4 -> 0x06001000 + 4 + 4*2 = 0x0600100C
    const auto ins5 = decode_sh2(0x8B04, 0x06001000);
    THOR_ASSERT(ins5.id == OpcodeId::BF);
    THOR_ASSERT(!ins5.has_delay_slot);
    THOR_ASSERT(ins5.compute_branch_target() == 0x0600100C);

    // 0xB008: bsr +8 -> 0x06001000 + 4 + 8*2 = 0x06001014
    const auto ins6 = decode_sh2(0xB008, 0x06001000);
    THOR_ASSERT(ins6.id == OpcodeId::BSR);
    THOR_ASSERT(ins6.has_delay_slot);
    THOR_ASSERT(ins6.compute_branch_target() == 0x06001014);

    // 0x442B: jmp @r4
    const auto ins7 = decode_sh2(0x442B, 0x06001000);
    THOR_ASSERT(ins7.id == OpcodeId::JMP);
    THOR_ASSERT(ins7.rn == 4);
    THOR_ASSERT(ins7.has_delay_slot);
}

static void test_extended_disp_and_shifts() {
    // 0x5123: mov.l @(3*4, r2), r1
    const auto ins1 = decode_sh2(0x5123, 0x06001000);
    THOR_ASSERT(ins1.id == OpcodeId::MOV_L_DISP_READ);
    THOR_ASSERT(ins1.rn == 1 && ins1.rm == 2 && ins1.disp == 3);
    THOR_ASSERT(ins1.compute_effective_address(0x100) == 0x10C);

    // 0x1123: mov.l r2, @(3*4, r1)
    const auto ins2 = decode_sh2(0x1123, 0x06001000);
    THOR_ASSERT(ins2.id == OpcodeId::MOV_L_DISP_WRITE);
    THOR_ASSERT(ins2.rn == 1 && ins2.rm == 2 && ins2.disp == 3);

    // 0x8523: mov.w @(3*2, r2), r0
    const auto ins3 = decode_sh2(0x8523, 0x06001000);
    THOR_ASSERT(ins3.id == OpcodeId::MOV_W_DISP_READ);
    THOR_ASSERT(ins3.rm == 2 && ins3.disp == 3);
    THOR_ASSERT(ins3.compute_effective_address(0x100) == 0x106);

    // 0x8113: mov.w r0, @(3*2, r1)
    const auto ins4 = decode_sh2(0x8113, 0x06001000);
    THOR_ASSERT(ins4.id == OpcodeId::MOV_W_DISP_WRITE);
    THOR_ASSERT(ins4.rn == 1 && ins4.disp == 3);

    // 0x4100: shll r1
    const auto ins5 = decode_sh2(0x4100, 0x06001000);
    THOR_ASSERT(ins5.id == OpcodeId::SHLL && ins5.rn == 1);

    // 0x4101: shlr r1
    const auto ins6 = decode_sh2(0x4101, 0x06001000);
    THOR_ASSERT(ins6.id == OpcodeId::SHLR && ins6.rn == 1);

    // 0x4108: shll2 r1
    const auto ins7 = decode_sh2(0x4108, 0x06001000);
    THOR_ASSERT(ins7.id == OpcodeId::SHLL2 && ins7.rn == 1);

    // 0x4109: shlr2 r1
    const auto ins8 = decode_sh2(0x4109, 0x06001000);
    THOR_ASSERT(ins8.id == OpcodeId::SHLR2 && ins8.rn == 1);

    // 0x0028: clrmac, 0x0008: clrt, 0x0018: sett
    THOR_ASSERT(decode_sh2(0x0028, 0).id == OpcodeId::CLRMAC);
    THOR_ASSERT(decode_sh2(0x0008, 0).id == OpcodeId::CLRT);
    THOR_ASSERT(decode_sh2(0x0018, 0).id == OpcodeId::SETT);
}

static void test_extended_batch2() {
    // SHAR
    const auto ins_shar = decode_sh2(0x4321, 0);
    THOR_ASSERT(ins_shar.id == OpcodeId::SHAR && ins_shar.rn == 3);
    THOR_ASSERT(ins_shar.mnemonic() == "shar r3");

    // BT_S / BF_S
    const auto ins_bts = decode_sh2(0x8D04, 0x06001000);
    THOR_ASSERT(ins_bts.id == OpcodeId::BT_S && ins_bts.has_delay_slot);
    THOR_ASSERT(ins_bts.compute_branch_target() == 0x0600100C);
    THOR_ASSERT(ins_bts.mnemonic() == "bt/s 0x600100c");

    const auto ins_bfs = decode_sh2(0x8F04, 0x06001000);
    THOR_ASSERT(ins_bfs.id == OpcodeId::BF_S && ins_bfs.has_delay_slot);
    THOR_ASSERT(ins_bfs.compute_branch_target() == 0x0600100C);
    THOR_ASSERT(ins_bfs.mnemonic() == "bf/s 0x600100c");

    // EXTU.B, EXTU.W, EXTS.B, EXTS.W
    const auto ins_extub = decode_sh2(0x624C, 0);
    THOR_ASSERT(ins_extub.id == OpcodeId::EXTU_B && ins_extub.rn == 2 && ins_extub.rm == 4);
    THOR_ASSERT(ins_extub.mnemonic() == "extu.b r4, r2");

    const auto ins_extuw = decode_sh2(0x624D, 0);
    THOR_ASSERT(ins_extuw.id == OpcodeId::EXTU_W && ins_extuw.rn == 2 && ins_extuw.rm == 4);

    const auto ins_extsb = decode_sh2(0x624E, 0);
    THOR_ASSERT(ins_extsb.id == OpcodeId::EXTS_B && ins_extsb.rn == 2 && ins_extsb.rm == 4);

    const auto ins_extsw = decode_sh2(0x624F, 0);
    THOR_ASSERT(ins_extsw.id == OpcodeId::EXTS_W && ins_extsw.rn == 2 && ins_extsw.rm == 4);
    THOR_ASSERT(ins_extsw.mnemonic() == "exts.w r4, r2");

    // CMP/PZ, CMP/PL
    const auto ins_pz = decode_sh2(0x4311, 0);
    THOR_ASSERT(ins_pz.id == OpcodeId::CMP_PZ && ins_pz.rn == 3);

    const auto ins_pl = decode_sh2(0x4315, 0);
    THOR_ASSERT(ins_pl.id == OpcodeId::CMP_PL && ins_pl.rn == 3);

    // MOV.W @Rm+, Rn
    const auto ins_mwp = decode_sh2(0x6245, 0);
    THOR_ASSERT(ins_mwp.id == OpcodeId::MOV_W_READ_POSTINC && ins_mwp.rn == 2 && ins_mwp.rm == 4);
    THOR_ASSERT(ins_mwp.compute_effective_address(0x1000) == 0x1000);

    // AND, OR
    const auto ins_and = decode_sh2(0x2249, 0);
    THOR_ASSERT(ins_and.id == OpcodeId::AND_REG && ins_and.rn == 2 && ins_and.rm == 4);

    const auto ins_or = decode_sh2(0x224B, 0);
    THOR_ASSERT(ins_or.id == OpcodeId::OR_REG && ins_or.rn == 2 && ins_or.rm == 4);

    // CMP/HS, CMP/GE, CMP/HI, CMP/GT
    THOR_ASSERT(decode_sh2(0x3242, 0).id == OpcodeId::CMP_HS);
    THOR_ASSERT(decode_sh2(0x3243, 0).id == OpcodeId::CMP_GE);
    THOR_ASSERT(decode_sh2(0x3246, 0).id == OpcodeId::CMP_HI);
    THOR_ASSERT(decode_sh2(0x3247, 0).id == OpcodeId::CMP_GT);
}

void test_extended_batch3() {
    // ROTCL, DT, MOVT
    const auto ins_rotcl = decode_sh2(0x4224, 0);
    THOR_ASSERT(ins_rotcl.id == OpcodeId::ROTCL && ins_rotcl.rn == 2);

    const auto ins_dt = decode_sh2(0x4310, 0);
    THOR_ASSERT(ins_dt.id == OpcodeId::DT && ins_dt.rn == 3);

    const auto ins_movt = decode_sh2(0x0229, 0);
    THOR_ASSERT(ins_movt.id == OpcodeId::MOVT && ins_movt.rn == 2);

    // AND #imm, R0 and TST #imm, R0
    const auto ins_and_imm = decode_sh2(0xC90F, 0);
    THOR_ASSERT(ins_and_imm.id == OpcodeId::AND_IMM && ins_and_imm.disp == 0x0F);

    const auto ins_tst_imm = decode_sh2(0xC880, 0);
    THOR_ASSERT(ins_tst_imm.id == OpcodeId::TST_IMM && ins_tst_imm.disp == 0x80);

    // MOV.B @(disp, Rm), R0 and MOV.B R0, @(disp, Rn)
    const auto ins_b_r = decode_sh2(0x84E5, 0);
    THOR_ASSERT(ins_b_r.id == OpcodeId::MOV_B_DISP_READ && ins_b_r.rm == 14 && ins_b_r.disp == 5);

    const auto ins_b_w = decode_sh2(0x80E7, 0);
    THOR_ASSERT(ins_b_w.id == OpcodeId::MOV_B_DISP_WRITE && ins_b_w.rn == 14 && ins_b_w.disp == 7);

    // Indexed moves: @(R0, Rm) / @(R0, Rn)
    THOR_ASSERT(decode_sh2(0x04EC, 0).id == OpcodeId::MOV_B_R0_READ);
    THOR_ASSERT(decode_sh2(0x03ED, 0).id == OpcodeId::MOV_W_R0_READ);
    THOR_ASSERT(decode_sh2(0x03EE, 0).id == OpcodeId::MOV_L_R0_READ);
    THOR_ASSERT(decode_sh2(0x0E46, 0).id == OpcodeId::MOV_L_R0_WRITE);
    THOR_ASSERT(decode_sh2(0x0755, 0).id == OpcodeId::MOV_W_R0_WRITE);
    THOR_ASSERT(decode_sh2(0x0FE4, 0).id == OpcodeId::MOV_B_R0_WRITE);

    // Shifts: SHLL8, SHLL16, SHLR8, SHLR16
    THOR_ASSERT(decode_sh2(0x4418, 0).id == OpcodeId::SHLL8 && decode_sh2(0x4418, 0).rn == 4);
    THOR_ASSERT(decode_sh2(0x4528, 0).id == OpcodeId::SHLL16 && decode_sh2(0x4528, 0).rn == 5);
    THOR_ASSERT(decode_sh2(0x4619, 0).id == OpcodeId::SHLR8 && decode_sh2(0x4619, 0).rn == 6);
    THOR_ASSERT(decode_sh2(0x4729, 0).id == OpcodeId::SHLR16 && decode_sh2(0x4729, 0).rn == 7);
}

int main() {
    std::cout << "[test_sh2_decoder_extended] Testing extended SH-2 opcodes...\n";
    test_extended_mov_w_pc_rel();
    test_extended_stack_and_reg_moves();
    test_extended_immediates_and_alu();
    test_extended_comparisons_and_branches();
    test_extended_disp_and_shifts();
    test_extended_batch2();
    test_extended_batch3();
    std::cout << "[test_sh2_decoder_extended] PASS: All extended decoder checks green.\n";
    return 0;
}
