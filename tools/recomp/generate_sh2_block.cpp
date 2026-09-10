#include <fstream>
#include <iostream>
#include <string>
#include "thor/sh2/sh2_block.hpp"
#include "thor/sh2/sh2_memory.hpp"
#include "thor/recomp/block_compiler.hpp"

int main(int argc, char* argv[]) {
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0] << " <block_name> <out_header> <out_source>\n";
        return 1;
    }

    const std::string block_name = argv[1];
    const std::string out_header = argv[2];
    const std::string out_source = argv[3];

    uint32_t start_addr = 0;
    thor::sh2::Sh2FlatMemory mem;

    if (block_name == "bb_06004000") {
        start_addr = 0x06004000u;
        const uint8_t bytes[] = {
            0x66, 0x11, // 0x06004000: MOV.W @R1, R6
            0x6F, 0x03, // 0x06004002: MOV R0, R15
            0xD4, 0x17, // 0x06004004: MOV.L @(0x5C, PC), R4
            0x64, 0x42, // 0x06004006: MOV.L @R4, R4
            0xA0, 0x03, // 0x06004008: BRA 0x06004012
            0x00, 0x09  // 0x0600400A: NOP (delay slot)
        };
        for (size_t i = 0; i < sizeof(bytes); ++i) {
            mem.write8(start_addr + static_cast<uint32_t>(i), bytes[i]);
        }
    } else if (block_name == "bb_06004280") {
        start_addr = 0x06004280u;
        const uint8_t bytes[] = {
            0xD5, 0x36, // 0x06004280: MOV.L @(0xD8, PC), R5
            0xD4, 0x37, // 0x06004282: MOV.L @(0xDC, PC), R4
            0xD3, 0x37, // 0x06004284: MOV.L @(0xDC, PC), R3
            0x43, 0x0B, // 0x06004286: JSR @R3
            0x00, 0x09  // 0x06004288: NOP (delay slot)
        };
        for (size_t i = 0; i < sizeof(bytes); ++i) {
            mem.write8(start_addr + static_cast<uint32_t>(i), bytes[i]);
        }
    } else {
        std::cerr << "Unknown block: " << block_name << "\n";
        return 1;
    }

    // Discover basic block representation
    const auto block = thor::sh2::discover_basic_block(start_addr, mem);
    if (block.instructions.empty()) {
        std::cerr << "Failed to discover basic block\n";
        return 1;
    }

    // Mechanically compile block to C++
    auto code_opt = thor::recomp::compile_block_to_cpp(block, block_name);
    if (!code_opt.has_value()) {
        std::cerr << "Failed to mechanically compile basic block\n";
        return 1;
    }

    // Write header
    std::ofstream h_file(out_header, std::ios::binary);
    if (!h_file.is_open()) {
        std::cerr << "Cannot open " << out_header << " for writing\n";
        return 1;
    }
    h_file << code_opt->header_content;

    // Write source
    std::ofstream s_file(out_source, std::ios::binary);
    if (!s_file.is_open()) {
        std::cerr << "Cannot open " << out_source << " for writing\n";
        return 1;
    }
    s_file << code_opt->source_content;

    std::cout << "Successfully generated " << block_name << " -> " << out_source << "\n";
    return 0;
}
