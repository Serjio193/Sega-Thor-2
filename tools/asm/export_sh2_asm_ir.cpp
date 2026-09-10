#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "thor/sh2/sh2_decoder.hpp"
#include "thor/sh2/sh2_types.hpp"

namespace {

struct RangeSpec {
    uint32_t start_vma = 0;
    uint32_t end_vma = 0;
    std::string block_id;
};

struct LabelRef {
    std::string name;
    uint32_t vma = 0;
    uint32_t offset = 0;
    std::string type;
};

std::string hex_str(uint32_t val, int width = 8) {
    std::ostringstream ss;
    ss << "0x" << std::uppercase << std::hex << std::setw(width) << std::setfill('0') << val;
    return ss.str();
}

std::string opcode_id_name(thor::sh2::OpcodeId id) {
    switch (id) {
        case thor::sh2::OpcodeId::MOV_W_READ_MEM: return "MOV_W_READ_MEM";
        case thor::sh2::OpcodeId::MOV_REG: return "MOV_REG";
        case thor::sh2::OpcodeId::MOV_L_PC_REL: return "MOV_L_PC_REL";
        case thor::sh2::OpcodeId::MOV_L_READ_MEM: return "MOV_L_READ_MEM";
        case thor::sh2::OpcodeId::BRA: return "BRA";
        case thor::sh2::OpcodeId::JSR: return "JSR";
        case thor::sh2::OpcodeId::NOP: return "NOP";
        case thor::sh2::OpcodeId::MOV_L_WRITE_PREDEC: return "MOV_L_WRITE_PREDEC";
        case thor::sh2::OpcodeId::RTS: return "RTS";
        default: return "UNKNOWN";
    }
}


std::string flow_type_name(thor::sh2::ControlFlowType flow) {
    switch (flow) {
        case thor::sh2::ControlFlowType::SEQUENTIAL: return "SEQUENTIAL";
        case thor::sh2::ControlFlowType::BRANCH: return "BRANCH";
        case thor::sh2::ControlFlowType::BRANCH_CONDITIONAL: return "BRANCH_CONDITIONAL";
        case thor::sh2::ControlFlowType::JUMP: return "JUMP";
        case thor::sh2::ControlFlowType::CALL: return "CALL";
        case thor::sh2::ControlFlowType::RETURN: return "RETURN";
        default: return "ILLEGAL";
    }
}

bool parse_range(const std::string& str, RangeSpec& out) {
    auto first_colon = str.find(':');
    auto second_colon = str.rfind(':');
    if (first_colon == std::string::npos || second_colon == std::string::npos || first_colon == second_colon) {
        return false;
    }
    std::string s_start = str.substr(0, first_colon);
    std::string s_end = str.substr(first_colon + 1, second_colon - first_colon - 1);
    out.block_id = str.substr(second_colon + 1);
    try {
        out.start_vma = static_cast<uint32_t>(std::stoul(s_start, nullptr, 0));
        out.end_vma = static_cast<uint32_t>(std::stoul(s_end, nullptr, 0));
    } catch (...) {
        return false;
    }
    return out.start_vma < out.end_vma;
}

} // namespace

int main(int argc, char* argv[]) {
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0]
                  << " <binary_path> <base_vma_hex> <output_json_path> [start:end:block_id ...]\n";
        return 1;
    }

    const std::string bin_path = argv[1];
    uint32_t base_vma = 0;
    try {
        base_vma = static_cast<uint32_t>(std::stoul(argv[2], nullptr, 0));
    } catch (...) {
        std::cerr << "Invalid base VMA: " << argv[2] << "\n";
        return 1;
    }
    const std::string out_json_path = argv[3];

    std::vector<RangeSpec> ranges;
    if (argc > 4) {
        for (int i = 4; i < argc; ++i) {
            RangeSpec r;
            if (!parse_range(argv[i], r)) {
                std::cerr << "Invalid range specification: " << argv[i] << "\n";
                return 1;
            }
            ranges.push_back(r);
        }
    } else {
        // Default proven ranges for 0TH2.BIN
        ranges.push_back({0x06004000u, 0x0600400Cu, "bb_06004000"});
        ranges.push_back({0x06004280u, 0x0600428Au, "bb_06004280"});
    }

    std::ifstream bin_file(bin_path, std::ios::binary);
    if (!bin_file.is_open()) {
        std::cerr << "Cannot open binary file: " << bin_path << "\n";
        return 1;
    }
    bin_file.seekg(0, std::ios::end);
    const size_t file_size = static_cast<size_t>(bin_file.tellg());
    bin_file.seekg(0, std::ios::beg);
    std::vector<uint8_t> bytes(file_size);
    bin_file.read(reinterpret_cast<char*>(bytes.data()), file_size);

    std::vector<LabelRef> labels;
    auto record_label = [&](const std::string& name, uint32_t vma, const std::string& type) {
        for (const auto& l : labels) {
            if (l.vma == vma && l.name == name) return;
        }
        labels.push_back({name, vma, vma - base_vma, type});
    };

    std::string clean_bin_path = bin_path;
    for (char& c : clean_bin_path) {
        if (c == '\\') c = '/';
    }

    std::ostringstream json;
    json << "{\n";
    json << "  \"module_binary\": \"" << clean_bin_path << "\",\n";
    json << "  \"base_vma\": \"" << hex_str(base_vma) << "\",\n";
    json << "  \"file_size\": " << file_size << ",\n";
    json << "  \"decoder_identity\": \"thor::sh2::decode_sh2\",\n";
    json << "  \"blocks\": [\n";

    for (size_t b_idx = 0; b_idx < ranges.size(); ++b_idx) {
        const auto& r = ranges[b_idx];
        if (r.start_vma < base_vma || r.end_vma > (base_vma + file_size) || (r.end_vma - r.start_vma) % 2 != 0) {
            std::cerr << "Range out of bounds or unaligned: " << r.block_id << "\n";
            return 1;
        }

        const uint32_t byte_len = r.end_vma - r.start_vma;
        const uint32_t insn_count = byte_len / 2;

        json << "    {\n";
        json << "      \"block_id\": \"" << r.block_id << "\",\n";
        json << "      \"start_vma\": \"" << hex_str(r.start_vma) << "\",\n";
        json << "      \"end_vma\": \"" << hex_str(r.end_vma) << "\",\n";
        json << "      \"byte_length\": " << byte_len << ",\n";
        json << "      \"instruction_count\": " << insn_count << ",\n";
        json << "      \"instructions\": [\n";

        for (uint32_t pc = r.start_vma; pc < r.end_vma; pc += 2) {
            const size_t offset = pc - base_vma;
            const uint16_t opcode = static_cast<uint16_t>((bytes[offset] << 8) | bytes[offset + 1]);
            const auto instr = thor::sh2::decode_sh2(opcode, pc);

            if (!instr.is_valid()) {
                std::cerr << "FAIL_CLOSED: Unknown or unmodeled opcode 0x" << std::hex << opcode
                          << " at PC 0x" << pc << " in block " << r.block_id << "\n";
                return 1;
            }

            std::string asm_line;
            std::string comment;
            uint32_t target_vma = 0;

            switch (instr.id) {
                case thor::sh2::OpcodeId::MOV_W_READ_MEM: {
                    asm_line = "mov.w   @r" + std::to_string(instr.rm) + ", r" + std::to_string(instr.rn);
                    comment = "MOV.W @R" + std::to_string(instr.rm) + ", R" + std::to_string(instr.rn);
                    break;
                }
                case thor::sh2::OpcodeId::MOV_REG: {
                    asm_line = "mov     r" + std::to_string(instr.rm) + ", r" + std::to_string(instr.rn);
                    comment = "MOV R" + std::to_string(instr.rm) + ", R" + std::to_string(instr.rn);
                    break;
                }
                case thor::sh2::OpcodeId::MOV_L_PC_REL: {
                    target_vma = instr.compute_effective_address();
                    std::string sym = "lit_" + hex_str(target_vma).substr(2);
                    record_label(sym, target_vma, "literal_pool");
                    asm_line = "mov.l   " + sym + ", r" + std::to_string(instr.rn);
                    comment = "MOV.L @(0x" + hex_str(instr.disp * 4, 2).substr(2) + ", PC), R"
                              + std::to_string(instr.rn) + " -> " + hex_str(target_vma);
                    break;
                }
                case thor::sh2::OpcodeId::MOV_L_READ_MEM: {
                    asm_line = "mov.l   @r" + std::to_string(instr.rm) + ", r" + std::to_string(instr.rn);
                    comment = "MOV.L @R" + std::to_string(instr.rm) + ", R" + std::to_string(instr.rn);
                    break;
                }
                case thor::sh2::OpcodeId::BRA: {
                    target_vma = instr.compute_branch_target();
                    std::string sym = "loc_" + hex_str(target_vma).substr(2);
                    record_label(sym, target_vma, "branch_target");
                    asm_line = "bra     " + sym;
                    comment = "BRA " + hex_str(target_vma);
                    break;
                }
                case thor::sh2::OpcodeId::JSR: {
                    asm_line = "jsr     @r" + std::to_string(instr.rn);
                    comment = "JSR @R" + std::to_string(instr.rn);
                    break;
                }
                case thor::sh2::OpcodeId::NOP: {
                    asm_line = "nop";
                    comment = "NOP";
                    break;
                }
                case thor::sh2::OpcodeId::MOV_L_WRITE_PREDEC: {
                    asm_line = "mov.l   r" + std::to_string(instr.rm) + ", @-r" + std::to_string(instr.rn);
                    comment = "MOV.L R" + std::to_string(instr.rm) + ", @-R" + std::to_string(instr.rn);
                    break;
                }
                case thor::sh2::OpcodeId::RTS: {
                    asm_line = "rts";
                    comment = "RTS";
                    break;
                }
                default:
                    return 1;
            }


            json << "        {\n";
            json << "          \"pc\": \"" << hex_str(pc) << "\",\n";
            json << "          \"offset\": " << offset << ",\n";
            json << "          \"opcode\": \"" << hex_str(opcode, 4) << "\",\n";
            json << "          \"opcode_id\": \"" << opcode_id_name(instr.id) << "\",\n";
            json << "          \"asm_line\": \"" << asm_line << "\",\n";
            json << "          \"comment\": \"" << comment << "\",\n";
            json << "          \"rn\": " << static_cast<int>(instr.rn) << ",\n";
            json << "          \"rm\": " << static_cast<int>(instr.rm) << ",\n";
            json << "          \"disp\": " << instr.disp << ",\n";
            json << "          \"target_vma\": \"" << hex_str(target_vma) << "\",\n";
            json << "          \"flow\": \"" << flow_type_name(instr.flow) << "\",\n";
            json << "          \"has_delay_slot\": " << (instr.has_delay_slot ? "true" : "false") << "\n";
            json << "        }" << (pc + 2 < r.end_vma ? ",\n" : "\n");
        }

        json << "      ]\n";
        json << "    }" << (b_idx + 1 < ranges.size() ? ",\n" : "\n");
    }

    json << "  ],\n";
    json << "  \"labels\": [\n";
    for (size_t i = 0; i < labels.size(); ++i) {
        const auto& l = labels[i];
        json << "    {\n";
        json << "      \"name\": \"" << l.name << "\",\n";
        json << "      \"vma\": \"" << hex_str(l.vma) << "\",\n";
        json << "      \"offset\": " << l.offset << ",\n";
        json << "      \"type\": \"" << l.type << "\"\n";
        json << "    }" << (i + 1 < labels.size() ? ",\n" : "\n");
    }
    json << "  ]\n";
    json << "}\n";

    std::ofstream out_file(out_json_path);
    if (!out_file.is_open()) {
        std::cerr << "Cannot write output json: " << out_json_path << "\n";
        return 1;
    }
    out_file << json.str();
    std::cout << "Successfully exported SH-2 Assembly IR to " << out_json_path << "\n";
    return 0;
}
