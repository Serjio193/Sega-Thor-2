#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include "thor/sh2/sh2_block.hpp"
#include "thor/sh2/sh2_memory.hpp"
#include "thor/recomp/block_compiler.hpp"

namespace {

std::vector<uint8_t> read_binary_file(const std::string& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file.is_open()) {
        return {};
    }
    file.seekg(0, std::ios::end);
    const size_t sz = static_cast<size_t>(file.tellg());
    file.seekg(0, std::ios::beg);
    std::vector<uint8_t> buf(sz);
    file.read(reinterpret_cast<char*>(buf.data()), sz);
    return buf;
}

} // namespace

int main(int argc, char* argv[]) {
    std::string block_name;
    std::string out_header;
    std::string out_source;
    std::string module_path;
    uint32_t start_pc = 0;
    size_t byte_length = 0;
    size_t file_offset = 0;
    bool has_file_offset = false;

    if (argc == 4) {
        block_name = argv[1];
        out_header = argv[2];
        out_source = argv[3];
    } else {
        for (int i = 1; i < argc; ++i) {
            std::string arg = argv[i];
            if (arg == "--block-name" && i + 1 < argc) {
                block_name = argv[++i];
            } else if (arg == "--out-header" && i + 1 < argc) {
                out_header = argv[++i];
            } else if (arg == "--out-source" && i + 1 < argc) {
                out_source = argv[++i];
            } else if (arg == "--module" && i + 1 < argc) {
                module_path = argv[++i];
            } else if (arg == "--start-pc" && i + 1 < argc) {
                start_pc = static_cast<uint32_t>(std::stoul(argv[++i], nullptr, 0));
            } else if (arg == "--length" && i + 1 < argc) {
                byte_length = static_cast<size_t>(std::stoul(argv[++i], nullptr, 0));
            } else if (arg == "--offset" && i + 1 < argc) {
                file_offset = static_cast<size_t>(std::stoul(argv[++i], nullptr, 0));
                has_file_offset = true;
            } else {
                std::cerr << "Unknown argument: " << arg << "\n";
                return 1;
            }
        }
    }

    if (block_name.empty() || out_header.empty() || out_source.empty()) {
        std::cerr << "Usage: generate_sh2_block <block_name> <out_header> <out_source>\n"
                  << "   or: generate_sh2_block --block-name <name> --out-header <h> --out-source <s>\n"
                  << "                          [--module <bin>] [--start-pc <pc>] [--length <len>] [--offset <off>]\n";
        return 1;
    }

    thor::sh2::Sh2FlatMemory mem;

    if (!module_path.empty()) {
        auto bin = read_binary_file(module_path);
        if (bin.empty()) {
            std::cerr << "Failed to read module file: " << module_path << "\n";
            return 1;
        }
        if (!has_file_offset) {
            if (start_pc >= 0x06004000u && start_pc < 0x06004000u + bin.size()) {
                file_offset = start_pc - 0x06004000u;
            } else if (start_pc >= 0x002DA000u && start_pc < 0x002DA000u + bin.size()) {
                file_offset = start_pc - 0x002DA000u;
            } else {
                file_offset = 0;
            }
        }
        if (file_offset + byte_length > bin.size()) {
            std::cerr << "Requested range exceeds binary size\n";
            return 1;
        }
        for (size_t i = 0; i < byte_length; ++i) {
            mem.write8(start_pc + static_cast<uint32_t>(i), bin[file_offset + i]);
        }
    } else if (block_name == "bb_06004000") {
        start_pc = 0x06004000u;
        const uint8_t bytes[] = {
            0x66, 0x11, // MOV.W @R1, R6
            0x6F, 0x03, // MOV R0, R15
            0xD4, 0x17, // MOV.L @(0x5C, PC), R4
            0x64, 0x42, // MOV.L @R4, R4
            0xA0, 0x03, // BRA 0x06004012
            0x00, 0x09  // NOP (delay slot)
        };
        for (size_t i = 0; i < sizeof(bytes); ++i) {
            mem.write8(start_pc + static_cast<uint32_t>(i), bytes[i]);
        }
    } else if (block_name == "bb_06004280") {
        start_pc = 0x06004280u;
        const uint8_t bytes[] = {
            0xD5, 0x36, // MOV.L @(0xD8, PC), R5
            0xD4, 0x37, // MOV.L @(0xDC, PC), R4
            0xD3, 0x37, // MOV.L @(0xDC, PC), R3
            0x43, 0x0B, // JSR @R3
            0x00, 0x09  // NOP (delay slot)
        };
        for (size_t i = 0; i < sizeof(bytes); ++i) {
            mem.write8(start_pc + static_cast<uint32_t>(i), bytes[i]);
        }
    } else {
        std::cerr << "Unknown block: " << block_name << " (module required for generic blocks)\n";
        return 1;
    }

    const auto block = thor::sh2::discover_basic_block(
        start_pc, mem,
        module_path.empty() ? "0TH2.BIN" : module_path,
        "MASTER_SH2",
        "workstreams/T2-D17-native-scaling/batch_codegen_evidence.md",
        static_cast<uint32_t>(byte_length)
    );
    if (block.instructions.empty()) {
        std::cerr << "Failed to discover basic block\n";
        return 1;
    }

    auto code_opt = thor::recomp::compile_block_to_cpp(block, block_name);
    if (!code_opt.has_value()) {
        std::cerr << "Failed to mechanically compile basic block\n";
        return 1;
    }

    std::ofstream h_file(out_header, std::ios::binary);
    if (!h_file.is_open()) {
        std::cerr << "Cannot open " << out_header << " for writing\n";
        return 1;
    }
    h_file << code_opt->header_content;

    std::ofstream s_file(out_source, std::ios::binary);
    if (!s_file.is_open()) {
        std::cerr << "Cannot open " << out_source << " for writing\n";
        return 1;
    }
    s_file << code_opt->source_content;

    std::cout << "Successfully generated " << block_name << " -> " << out_source << "\n";
    return 0;
}
