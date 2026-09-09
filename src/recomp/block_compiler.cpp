#include "thor/recomp/block_compiler.hpp"
#include <iomanip>
#include <sstream>

namespace thor::recomp {

std::optional<GeneratedBlockCode> compile_block_to_cpp(
    const thor::sh2::Sh2BasicBlock& block,
    const std::string& function_name) noexcept {

    if (block.instructions.empty()) {
        return std::nullopt;
    }

    // Fail-closed validation of all instructions in the block
    for (const auto& ins : block.instructions) {
        switch (ins.id) {
        case thor::sh2::OpcodeId::MOV_W_READ_MEM:
        case thor::sh2::OpcodeId::MOV_REG:
        case thor::sh2::OpcodeId::MOV_L_PC_REL:
        case thor::sh2::OpcodeId::MOV_L_READ_MEM:
        case thor::sh2::OpcodeId::BRA:
        case thor::sh2::OpcodeId::NOP:
            break;
        default:
            return std::nullopt; // Unsupported instruction fails closed
        }
    }

    const bool has_delay_slot = block.delay_slot.has_value();
    if (has_delay_slot) {
        if (block.instructions.size() < 2 || block.direct_exits.empty()) {
            return std::nullopt;
        }
        if (block.terminator.id != thor::sh2::OpcodeId::BRA) {
            return std::nullopt;
        }
    }

    // Deterministic header generation
    std::ostringstream hdr;
    hdr << "#pragma once\n\n"
        << "#include <cstdint>\n"
        << "#include \"thor/sh2/sh2_state.hpp\"\n"
        << "#include \"thor/sh2/sh2_memory.hpp\"\n\n"
        << "namespace thor::generated {\n\n"
        << "void " << function_name << "(thor::sh2::Sh2CpuState& state, thor::sh2::ISh2Memory& mem);\n\n"
        << "} // namespace thor::generated\n";

    // Deterministic source generation
    std::ostringstream src;
    src << "// GENERATED FILE - DO NOT EDIT MANUALLY\n"
        << "// Mechanically recompiled from Sh2BasicBlock [0x"
        << std::hex << std::uppercase << std::setfill('0') << std::setw(8) << block.start_address
        << "..0x" << std::setw(8) << block.end_address << "]\n"
        << std::dec
        << "#include \"" << function_name << ".hpp\"\n\n"
        << "namespace thor::generated {\n\n"
        << "void " << function_name << "(thor::sh2::Sh2CpuState& state, thor::sh2::ISh2Memory& mem) {\n";

    const size_t total_ins = block.instructions.size();
    const size_t straight_ins_count = has_delay_slot ? (total_ins - 2) : total_ins;

    auto emit_instruction = [&](const thor::sh2::Sh2Instruction& ins) {
        switch (ins.id) {
        case thor::sh2::OpcodeId::MOV_W_READ_MEM:
            src << "    state.r[" << std::dec << static_cast<int>(ins.rn)
                << "] = static_cast<uint32_t>(static_cast<int32_t>(static_cast<int16_t>(mem.read16(state.r["
                << std::dec << static_cast<int>(ins.rm) << "]))));\n";
            break;
        case thor::sh2::OpcodeId::MOV_REG:
            src << "    state.r[" << std::dec << static_cast<int>(ins.rn)
                << "] = state.r[" << std::dec << static_cast<int>(ins.rm) << "];\n";
            break;
        case thor::sh2::OpcodeId::MOV_L_PC_REL: {
            const uint32_t ea = ((ins.pc + 4u) & ~3u) + (ins.disp * 4u);
            src << "    state.r[" << std::dec << static_cast<int>(ins.rn)
                << "] = mem.read32(0x" << std::hex << std::uppercase << std::setfill('0') << std::setw(8)
                << ea << std::dec << "u);\n";
            break;
        }
        case thor::sh2::OpcodeId::MOV_L_READ_MEM:
            src << "    state.r[" << std::dec << static_cast<int>(ins.rn)
                << "] = mem.read32(state.r[" << std::dec << static_cast<int>(ins.rm) << "]);\n";
            break;
        case thor::sh2::OpcodeId::NOP:
            src << "    /* NOP */\n";
            break;
        default:
            break;
        }
    };

    for (size_t i = 0; i < straight_ins_count; ++i) {
        emit_instruction(block.instructions[i]);
    }

    if (has_delay_slot) {
        emit_instruction(*block.delay_slot);
        src << "    state.pc = 0x" << std::hex << std::uppercase << std::setfill('0') << std::setw(8)
            << block.direct_exits[0] << std::dec << "u;\n";
    } else if (block.fallthrough.has_value()) {
        src << "    state.pc = 0x" << std::hex << std::uppercase << std::setfill('0') << std::setw(8)
            << *block.fallthrough << std::dec << "u;\n";
    }

    src << "}\n\n"
        << "} // namespace thor::generated\n";

    return GeneratedBlockCode{
        .header_filename = function_name + ".hpp",
        .source_filename = function_name + ".cpp",
        .header_content = hdr.str(),
        .source_content = src.str()
    };
}

} // namespace thor::recomp
