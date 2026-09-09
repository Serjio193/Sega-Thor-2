#include "thor/sh2/sh2_block.hpp"

namespace thor::sh2 {

Sh2BasicBlock discover_basic_block(
    uint32_t start_pc,
    ISh2Memory& mem,
    const std::string& module_id,
    const std::string& cpu_id,
    const std::string& evidence_link) {

    Sh2BasicBlock block;
    block.start_address = start_pc;
    block.module_id = module_id;
    block.cpu_id = cpu_id;
    block.evidence_link = evidence_link;

    uint32_t curr_pc = start_pc;
    while (true) {
        const uint16_t raw_op = mem.read16(curr_pc);
        const Sh2Instruction ins = decode_sh2(raw_op, curr_pc);
        block.instructions.push_back(ins);

        if (ins.flow != ControlFlowType::SEQUENTIAL) {
            block.terminator = ins;
            if (ins.has_delay_slot) {
                curr_pc += 2;
                const uint16_t slot_op = mem.read16(curr_pc);
                const Sh2Instruction slot_ins = decode_sh2(slot_op, curr_pc);
                block.instructions.push_back(slot_ins);
                block.delay_slot = slot_ins;
            }

            if (ins.id == OpcodeId::BRA) {
                const uint32_t target = ins.compute_branch_target();
                block.direct_exits.push_back(target);
                block.fallthrough = std::nullopt; // Unconditional branch has no fallthrough
                block.dynamic_taken_exit = target;
            }
            break;
        }
        curr_pc += 2;
    }

    block.end_address = block.instructions.back().pc;
    block.instruction_count = static_cast<uint32_t>(block.instructions.size());
    block.byte_length = (block.end_address - block.start_address) + 2u;
    return block;
}

ExecutionResult execute_basic_block(
    const Sh2BasicBlock& block,
    Sh2CpuState& state,
    ISh2Memory& mem) {

    for (const auto& ins : block.instructions) {
        const ExecutionResult res = execute_sh2_instruction(ins, state, mem);
        if (res != ExecutionResult::SUCCESS) {
            return res;
        }
    }
    return ExecutionResult::SUCCESS;
}

} // namespace thor::sh2
