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

int main() {
    std::cout << "Running test_sh2_block_compiler...\n";
    test_compile_bb_06004000();
    test_determinism();
    test_fail_closed_unsupported_opcode();
    test_fail_closed_empty_block();
    test_fail_closed_malformed_branch();
    std::cout << "All test_sh2_block_compiler cases passed!\n";
    return 0;
}
