#pragma once

#include "thor/sh2/sh2_decoder.hpp"
#include "thor/sh2/sh2_executor.hpp"
#include "thor/sh2/sh2_memory.hpp"
#include "thor/sh2/sh2_state.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace thor::sh2 {

/// Evidence-backed CFG record for an SH-2 basic block.
/// Per AGENTS.md, basic blocks are the initial recompilation unit.
/// Function boundaries and semantic names are not asserted without evidence.
struct Sh2BasicBlock {
    uint32_t start_address = 0;
    uint32_t end_address = 0;              // Address of last instruction in block
    uint32_t instruction_count = 0;
    uint32_t byte_length = 0;
    Sh2Instruction terminator{};
    std::optional<Sh2Instruction> delay_slot = std::nullopt;
    std::vector<uint32_t> direct_exits{};
    std::optional<uint32_t> fallthrough = std::nullopt;
    std::optional<uint32_t> dynamic_taken_exit = std::nullopt;
    std::string module_id;
    std::string cpu_id;
    std::string evidence_link;
    std::vector<Sh2Instruction> instructions{};

    [[nodiscard]] bool contains_pc(uint32_t addr) const noexcept {
        return addr >= start_address && addr < start_address + byte_length;
    }
};

/// Discovers and builds an evidence-backed basic block starting at start_pc.
/// Fetches instructions until the first control-flow terminator and its delay slot,
/// or until max_bytes is reached (if max_bytes > 0).
[[nodiscard]] Sh2BasicBlock discover_basic_block(
    uint32_t start_pc,
    ISh2Memory& mem,
    const std::string& module_id = "0TH2.BIN",
    const std::string& cpu_id = "MASTER_SH2",
    const std::string& evidence_link = "workstreams/T2-D4-D5-block0/block_06004000.md",
    uint32_t max_bytes = 0);

/// Executes an entire basic block sequentially against CPU state and memory.
[[nodiscard]] ExecutionResult execute_basic_block(
    const Sh2BasicBlock& block,
    Sh2CpuState& state,
    ISh2Memory& mem);

} // namespace thor::sh2
