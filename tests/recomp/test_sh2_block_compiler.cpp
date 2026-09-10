#include <iostream>
#include "thor/recomp/block_compiler.hpp"
#include "thor/sh2/sh2_block.hpp"
#include "thor/sh2/sh2_memory.hpp"
#include "tests/sh2/test_framework.hpp"

using namespace thor::recomp;
using namespace thor::sh2;

static Sh2BasicBlock make_canonical_block() {
    Sh2FlatMemory mem;
    const uint8_t bytes[] = {
        0x66, 0x11, // 0x06004000: MOV.W @R1, R6
        0x6F, 0x03, // 0x06004002: MOV R0, R15
        0xD4, 0x17, // 0x06004004: MOV.L @(0x5C, PC), R4
        0x64, 0x42, // 0x06004006: MOV.L @R4, R4
        0xA0, 0x03, // 0x06004008: BRA 0x06004012
        0x00, 0x09  // 0x0600400A: NOP
    };
    for (size_t i = 0; i < sizeof(bytes); ++i) {
        mem.write8(0x06004000u + static_cast<uint32_t>(i), bytes[i]);
    }
    const auto block = discover_basic_block(0x06004000u, mem);
    THOR_ASSERT(!block.instructions.empty());
    return block;
}

static void test_compile_bb_06004000() {
    const auto block = make_canonical_block();
    const auto res = compile_block_to_cpp(block, "bb_06004000");
    THOR_ASSERT(res.has_value());

    THOR_ASSERT(res->header_filename == "bb_06004000.hpp");
    THOR_ASSERT(res->source_filename == "bb_06004000.cpp");

    // Verify key mechanical patterns in header and source
    THOR_ASSERT(res->header_content.find("void bb_06004000(") != std::string::npos);
    THOR_ASSERT(res->source_content.find("state.r[6] = static_cast<uint32_t>") != std::string::npos);
    THOR_ASSERT(res->source_content.find("state.r[15] = state.r[0];") != std::string::npos);
    THOR_ASSERT(res->source_content.find("state.r[4] = mem.read32(0x06004064u);") != std::string::npos);
    THOR_ASSERT(res->source_content.find("state.r[4] = mem.read32(state.r[4]);") != std::string::npos);
    THOR_ASSERT(res->source_content.find("state.pc = 0x06004012u;") != std::string::npos);

    // Verify prohibition of runtime interpreter wrappers
    THOR_ASSERT(res->source_content.find("decode_sh2") == std::string::npos);
    THOR_ASSERT(res->source_content.find("execute_sh2_instruction") == std::string::npos);
    THOR_ASSERT(res->source_content.find("step_sh2") == std::string::npos);
    THOR_ASSERT(res->source_content.find("execute_basic_block") == std::string::npos);
}

static void test_determinism() {
    const auto block = make_canonical_block();
    const auto res1 = compile_block_to_cpp(block, "bb_06004000");
    const auto res2 = compile_block_to_cpp(block, "bb_06004000");
    THOR_ASSERT(res1.has_value() && res2.has_value());
    THOR_ASSERT(res1->header_content == res2->header_content);
    THOR_ASSERT(res1->source_content == res2->source_content);
}

static void test_fail_closed_unsupported_opcode() {
    auto block = make_canonical_block();
    // Inject an unsupported / unknown opcode
    block.instructions[0].id = OpcodeId::UNKNOWN;
    const auto res = compile_block_to_cpp(block, "bb_fail");
    THOR_ASSERT(!res.has_value());
}

static void test_fail_closed_empty_block() {
    Sh2BasicBlock empty_block{};
    const auto res = compile_block_to_cpp(empty_block, "bb_empty");
    THOR_ASSERT(!res.has_value());
}

static void test_fail_closed_malformed_branch() {
    auto block = make_canonical_block();
    block.direct_exits.clear(); // corrupt exit target
    const auto res = compile_block_to_cpp(block, "bb_corrupt");
    THOR_ASSERT(!res.has_value());
}

static Sh2BasicBlock make_candidate_block() {
    Sh2FlatMemory mem;
    const uint8_t bytes[] = {
        0xD5, 0x36, // 0x06004280: MOV.L @(0xD8, PC), R5
        0xD4, 0x37, // 0x06004282: MOV.L @(0xDC, PC), R4
        0xD3, 0x37, // 0x06004284: MOV.L @(0xDC, PC), R3
        0x43, 0x0B, // 0x06004286: JSR @R3
        0x00, 0x09  // 0x06004288: NOP
    };
    for (size_t i = 0; i < sizeof(bytes); ++i) {
        mem.write8(0x06004280u + static_cast<uint32_t>(i), bytes[i]);
    }
    const auto block = discover_basic_block(0x06004280u, mem);
    THOR_ASSERT(!block.instructions.empty());
    return block;
}

static void test_compile_bb_06004280() {
    const auto block = make_candidate_block();
    const auto res = compile_block_to_cpp(block, "bb_06004280");
    THOR_ASSERT(res.has_value());

    THOR_ASSERT(res->header_filename == "bb_06004280.hpp");
    THOR_ASSERT(res->source_filename == "bb_06004280.cpp");

    // Static literals are proven PC-relative addresses
    THOR_ASSERT(res->source_content.find("state.r[5] = mem.read32(0x0600435Cu);") != std::string::npos);
    THOR_ASSERT(res->source_content.find("state.r[4] = mem.read32(0x06004360u);") != std::string::npos);
    THOR_ASSERT(res->source_content.find("state.r[3] = mem.read32(0x06004364u);") != std::string::npos);

    // Call mechanics: target captured before delay slot, PR set, delay slot executed, PC updated, delayed_pc cleared
    THOR_ASSERT(res->source_content.find("const uint32_t target_temp = state.r[3];") != std::string::npos);
    THOR_ASSERT(res->source_content.find("state.pr = 0x0600428Au;") != std::string::npos);
    THOR_ASSERT(res->source_content.find("/* NOP */") != std::string::npos);
    THOR_ASSERT(res->source_content.find("state.pc = target_temp;") != std::string::npos);
    THOR_ASSERT(res->source_content.find("state.delayed_pc = std::nullopt;") != std::string::npos);

    // Negative control: must NOT hardcode observed target 0x0600A0F8 in generated code!
    THOR_ASSERT(res->source_content.find("0x0600A0F8") == std::string::npos);

    // Prohibition of interpreter wrappers
    THOR_ASSERT(res->source_content.find("decode_sh2") == std::string::npos);
    THOR_ASSERT(res->source_content.find("execute_basic_block") == std::string::npos);
}

static void test_compile_synthetic_jsr_delay_slot_rn_mutation() {
    Sh2FlatMemory mem;
    // 0x06005000: 43 0B -> JSR @R3
    // 0x06005002: 63 03 -> MOV R0, R3 (mutates R3 in delay slot)
    mem.write16(0x06005000u, 0x430Bu);
    mem.write16(0x06005002u, 0x6303u);
    const auto block = discover_basic_block(0x06005000u, mem);
    THOR_ASSERT(!block.instructions.empty());

    const auto res = compile_block_to_cpp(block, "bb_synthetic_jsr");
    THOR_ASSERT(res.has_value());

    const std::string& src = res->source_content;
    const size_t pos_target_capture = src.find("const uint32_t target_temp = state.r[3];");
    const size_t pos_pr_set = src.find("state.pr = 0x06005004u;");
    const size_t pos_delay_slot_mov = src.find("state.r[3] = state.r[0];");
    const size_t pos_pc_update = src.find("state.pc = target_temp;");
    const size_t pos_delayed_pc = src.find("state.delayed_pc = std::nullopt;");

    THOR_ASSERT(pos_target_capture != std::string::npos);
    THOR_ASSERT(pos_pr_set != std::string::npos);
    THOR_ASSERT(pos_delay_slot_mov != std::string::npos);
    THOR_ASSERT(pos_pc_update != std::string::npos);
    THOR_ASSERT(pos_delayed_pc != std::string::npos);

    // Strict order: target_capture < pr_set < delay_slot_mov < pc_update < delayed_pc
    THOR_ASSERT(pos_target_capture < pos_pr_set);
    THOR_ASSERT(pos_pr_set < pos_delay_slot_mov);
    THOR_ASSERT(pos_delay_slot_mov < pos_pc_update);
    THOR_ASSERT(pos_pc_update < pos_delayed_pc);
}

static void test_fail_closed_illegal_delay_slots() {
    // 1. JSR @R3 followed by JSR @R4
    {
        Sh2FlatMemory mem;
        mem.write16(0x06005100u, 0x430Bu); // JSR @R3
        mem.write16(0x06005102u, 0x440Bu); // JSR @R4
        const auto block = discover_basic_block(0x06005100u, mem);
        THOR_ASSERT(!block.instructions.empty());
        const auto res = compile_block_to_cpp(block, "bb_illegal_jsr_jsr");
        THOR_ASSERT(!res.has_value());
    }
    // 2. JSR @R3 followed by BRA
    {
        Sh2FlatMemory mem;
        mem.write16(0x06005100u, 0x430Bu); // JSR @R3
        mem.write16(0x06005102u, 0xA002u); // BRA +4
        const auto block = discover_basic_block(0x06005100u, mem);
        THOR_ASSERT(!block.instructions.empty());
        const auto res = compile_block_to_cpp(block, "bb_illegal_jsr_bra");
        THOR_ASSERT(!res.has_value());
    }
    // 3. BRA followed by JSR @R3
    {
        Sh2FlatMemory mem;
        mem.write16(0x06005100u, 0xA002u); // BRA +4
        mem.write16(0x06005102u, 0x430Bu); // JSR @R3
        const auto block = discover_basic_block(0x06005100u, mem);
        THOR_ASSERT(!block.instructions.empty());
        const auto res = compile_block_to_cpp(block, "bb_illegal_bra_jsr");
        THOR_ASSERT(!res.has_value());
    }
}

int main() {
    std::cout << "Running test_sh2_block_compiler...\n";
    test_compile_bb_06004000();
    test_compile_bb_06004280();
    test_compile_synthetic_jsr_delay_slot_rn_mutation();
    test_determinism();
    test_fail_closed_unsupported_opcode();
    test_fail_closed_empty_block();
    test_fail_closed_malformed_branch();
    test_fail_closed_illegal_delay_slots();
    std::cout << "All test_sh2_block_compiler cases passed!\n";
    return 0;
}
