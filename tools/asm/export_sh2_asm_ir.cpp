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
#include "sh2_opcode_names.hpp"

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

struct FormattedInstruction {
    std::string asm_line;
    std::string comment;
    uint32_t target_vma = 0;
};

FormattedInstruction format_instruction(
    const thor::sh2::Sh2Instruction& instr,
    uint32_t base_vma,
    std::vector<LabelRef>* labels
) {
    FormattedInstruction fi;
    auto record_label = [&](const std::string& name, uint32_t vma, const std::string& type) {
        if (!labels) return;
        for (const auto& l : *labels) {
            if (l.vma == vma && l.name == name) return;
        }
        labels->push_back({name, vma, vma - base_vma, type});
    };

    switch (instr.id) {
        case thor::sh2::OpcodeId::MOV_W_READ_MEM: {
            fi.asm_line = "mov.w   @r" + std::to_string(instr.rm) + ", r" + std::to_string(instr.rn);
            fi.comment = "MOV.W @R" + std::to_string(instr.rm) + ", R" + std::to_string(instr.rn);
            break;
        }
        case thor::sh2::OpcodeId::MOV_REG: {
            fi.asm_line = "mov     r" + std::to_string(instr.rm) + ", r" + std::to_string(instr.rn);
            fi.comment = "MOV R" + std::to_string(instr.rm) + ", R" + std::to_string(instr.rn);
            break;
        }
        case thor::sh2::OpcodeId::MOV_L_PC_REL: {
            fi.target_vma = instr.compute_effective_address();
            std::string sym = "lit_" + hex_str(fi.target_vma).substr(2);
            record_label(sym, fi.target_vma, "literal_pool");
            fi.asm_line = "mov.l   " + sym + ", r" + std::to_string(instr.rn);
            fi.comment = "MOV.L @(0x" + hex_str(instr.disp * 4, 2).substr(2) + ", PC), R"
                      + std::to_string(instr.rn) + " -> " + hex_str(fi.target_vma);
            break;
        }
        case thor::sh2::OpcodeId::MOV_W_PC_REL: {
            fi.target_vma = instr.compute_effective_address();
            std::string sym = "lit_" + hex_str(fi.target_vma).substr(2);
            record_label(sym, fi.target_vma, "literal_pool");
            fi.asm_line = "mov.w   " + sym + ", r" + std::to_string(instr.rn);
            fi.comment = "MOV.W @(0x" + hex_str(instr.disp * 2, 2).substr(2) + ", PC), R"
                      + std::to_string(instr.rn) + " -> " + hex_str(fi.target_vma);
            break;
        }
        case thor::sh2::OpcodeId::MOVA: {
            fi.target_vma = instr.compute_effective_address();
            std::string sym = "lit_" + hex_str(fi.target_vma).substr(2);
            record_label(sym, fi.target_vma, "literal_pool");
            fi.asm_line = "mova    " + sym + ", r0";
            fi.comment = "MOVA @(0x" + hex_str(instr.disp * 4, 2).substr(2) + ", PC), R0 -> " + hex_str(fi.target_vma);
            break;
        }
        case thor::sh2::OpcodeId::MOV_L_READ_MEM: {
            fi.asm_line = "mov.l   @r" + std::to_string(instr.rm) + ", r" + std::to_string(instr.rn);
            fi.comment = "MOV.L @R" + std::to_string(instr.rm) + ", R" + std::to_string(instr.rn);
            break;
        }
        case thor::sh2::OpcodeId::BRA: {
            fi.target_vma = instr.compute_branch_target();
            std::string sym = "loc_" + hex_str(fi.target_vma).substr(2);
            record_label(sym, fi.target_vma, "branch_target");
            fi.asm_line = "bra     " + sym;
            fi.comment = "BRA " + hex_str(fi.target_vma);
            break;
        }
        case thor::sh2::OpcodeId::BSR: {
            fi.target_vma = instr.compute_branch_target();
            std::string sym = "loc_" + hex_str(fi.target_vma).substr(2);
            record_label(sym, fi.target_vma, "branch_target");
            fi.asm_line = "bsr     " + sym;
            fi.comment = "BSR " + hex_str(fi.target_vma);
            break;
        }
        case thor::sh2::OpcodeId::BF: {
            fi.target_vma = instr.compute_branch_target();
            std::string sym = "loc_" + hex_str(fi.target_vma).substr(2);
            record_label(sym, fi.target_vma, "branch_target");
            fi.asm_line = "bf      " + sym;
            fi.comment = "BF " + hex_str(fi.target_vma);
            break;
        }
        case thor::sh2::OpcodeId::BT: {
            fi.target_vma = instr.compute_branch_target();
            std::string sym = "loc_" + hex_str(fi.target_vma).substr(2);
            record_label(sym, fi.target_vma, "branch_target");
            fi.asm_line = "bt      " + sym;
            fi.comment = "BT " + hex_str(fi.target_vma);
            break;
        }
        case thor::sh2::OpcodeId::BT_S: {
            fi.target_vma = instr.compute_branch_target();
            std::string sym = "loc_" + hex_str(fi.target_vma).substr(2);
            record_label(sym, fi.target_vma, "branch_target");
            fi.asm_line = "bt/s    " + sym;
            fi.comment = "BT/S " + hex_str(fi.target_vma);
            break;
        }
        case thor::sh2::OpcodeId::BF_S: {
            fi.target_vma = instr.compute_branch_target();
            std::string sym = "loc_" + hex_str(fi.target_vma).substr(2);
            record_label(sym, fi.target_vma, "branch_target");
            fi.asm_line = "bf/s    " + sym;
            fi.comment = "BF/S " + hex_str(fi.target_vma);
            break;
        }
        case thor::sh2::OpcodeId::JSR: {
            fi.asm_line = "jsr     @r" + std::to_string(instr.rn);
            fi.comment = "JSR @R" + std::to_string(instr.rn);
            break;
        }
        case thor::sh2::OpcodeId::JMP: {
            fi.asm_line = "jmp     @r" + std::to_string(instr.rn);
            fi.comment = "JMP @R" + std::to_string(instr.rn);
            break;
        }
        case thor::sh2::OpcodeId::NOP: {
            fi.asm_line = "nop";
            fi.comment = "NOP";
            break;
        }
        case thor::sh2::OpcodeId::MOV_L_WRITE_PREDEC: {
            fi.asm_line = "mov.l   r" + std::to_string(instr.rm) + ", @-r" + std::to_string(instr.rn);
            fi.comment = "MOV.L R" + std::to_string(instr.rm) + ", @-R" + std::to_string(instr.rn);
            break;
        }
        case thor::sh2::OpcodeId::RTS: {
            fi.asm_line = "rts";
            fi.comment = "RTS";
            break;
        }
        default: {
            fi.asm_line = instr.mnemonic();
            fi.comment = instr.mnemonic();
            break;
        }
    }
    return fi;
}

void emit_instruction_json(
    std::ostringstream& json,
    const thor::sh2::Sh2Instruction& instr,
    uint32_t pc,
    uint32_t offset,
    uint16_t opcode,
    const FormattedInstruction& fi,
    const std::string& indent
) {
    json << indent << "{\n";
    json << indent << "  \"pc\": \"" << hex_str(pc) << "\",\n";
    json << indent << "  \"offset\": " << offset << ",\n";
    json << indent << "  \"opcode\": \"" << hex_str(opcode, 4) << "\",\n";
    json << indent << "  \"opcode_id\": \"" << thor::sh2::opcode_id_name(instr.id) << "\",\n";
    json << indent << "  \"asm_line\": \"" << fi.asm_line << "\",\n";
    json << indent << "  \"comment\": \"" << fi.comment << "\",\n";
    json << indent << "  \"rn\": " << static_cast<int>(instr.rn) << ",\n";
    json << indent << "  \"rm\": " << static_cast<int>(instr.rm) << ",\n";
    json << indent << "  \"disp\": " << instr.disp << ",\n";
    json << indent << "  \"target_vma\": \"" << hex_str(fi.target_vma) << "\",\n";
    json << indent << "  \"flow\": \"" << flow_type_name(instr.flow) << "\",\n";
    json << indent << "  \"has_delay_slot\": " << (instr.has_delay_slot ? "true" : "false") << "\n";
    json << indent << "}";
}

} // namespace

int main(int argc, char* argv[]) {
    if (argc > 4 && std::string(argv[1]) == "--dump-all-valid") {
        const std::string bin_path = argv[2];
        uint32_t base_vma = 0;
        try {
            base_vma = static_cast<uint32_t>(std::stoul(argv[3], nullptr, 0));
        } catch (...) {
            std::cerr << "Invalid base VMA: " << argv[3] << "\n";
            return 1;
        }
        const std::string out_json_path = argv[4];

        std::ifstream bin_file(bin_path, std::ios::binary);
        if (!bin_file.is_open()) {
            std::cerr << "Cannot open binary: " << bin_path << "\n";
            return 1;
        }
        bin_file.seekg(0, std::ios::end);
        const size_t file_size = static_cast<size_t>(bin_file.tellg());
        bin_file.seekg(0, std::ios::beg);
        std::vector<uint8_t> bytes(file_size);
        bin_file.read(reinterpret_cast<char*>(bytes.data()), file_size);

        std::ostringstream json;
        json << "{\n";
        json << "  \"mode\": \"dump_all_valid\",\n";
        json << "  \"base_vma\": \"" << hex_str(base_vma) << "\",\n";
        json << "  \"file_size\": " << file_size << ",\n";
        json << "  \"instructions\": [\n";

        bool first = true;
        for (size_t offset = 0; offset + 1 < file_size; offset += 2) {
            uint32_t pc = base_vma + static_cast<uint32_t>(offset);
            uint16_t opcode = static_cast<uint16_t>((bytes[offset] << 8) | bytes[offset + 1]);
            auto instr = thor::sh2::decode_sh2(opcode, pc);
            if (!instr.is_valid()) continue;

            if (!first) {
                json << ",\n";
            }
            first = false;

            FormattedInstruction fi = format_instruction(instr, base_vma, nullptr);
            emit_instruction_json(json, instr, pc, static_cast<uint32_t>(offset), opcode, fi, "    ");
        }
        json << "\n  ]\n";
        json << "}\n";

        std::ofstream out_file(out_json_path, std::ios::out | std::ios::trunc);
        if (!out_file.is_open()) {
            std::cerr << "Cannot write output json: " << out_json_path << "\n";
            return 1;
        }
        out_file << json.str();
        std::cout << "Successfully exported all valid SH-2 IR to " << out_json_path << "\n";
        return 0;
    }

    if (argc < 4) {
        std::cerr << "Usage: " << argv[0]
                  << " <binary_path> <base_vma_hex> <output_json_path> [start:end:block_id ...]\n"
                  << "   or: " << argv[0]
                  << " --dump-all-valid <binary_path> <base_vma_hex> <output_json_path>\n";
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
            std::string arg = argv[i];
            if (!arg.empty() && arg[0] == '@') {
                std::ifstream rf(arg.substr(1));
                if (!rf.is_open()) {
                    std::cerr << "Cannot open response file: " << arg.substr(1) << "\n";
                    return 1;
                }
                std::string line;
                while (std::getline(rf, line)) {
                    if (line.empty() || line[0] == '#') continue;
                    RangeSpec r;
                    if (!parse_range(line, r)) {
                        std::cerr << "Invalid range in response file: " << line << "\n";
                        return 1;
                    }
                    ranges.push_back(r);
                }
            } else {
                RangeSpec r;
                if (!parse_range(arg, r)) {
                    std::cerr << "Invalid range specification: " << arg << "\n";
                    return 1;
                }
                ranges.push_back(r);
            }
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

            FormattedInstruction fi = format_instruction(instr, base_vma, &labels);
            emit_instruction_json(json, instr, pc, static_cast<uint32_t>(offset), opcode, fi, "        ");
            if (pc + 2 < r.end_vma) {
                json << ",\n";
            } else {
                json << "\n";
            }
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

    std::ofstream out_file(out_json_path, std::ios::out | std::ios::trunc);
    if (!out_file.is_open()) {
        std::cerr << "Cannot write output json: " << out_json_path << "\n";
        return 1;
    }
    out_file << json.str();
    std::cout << "Successfully exported SH-2 Assembly IR to " << out_json_path << "\n";
    return 0;
}
