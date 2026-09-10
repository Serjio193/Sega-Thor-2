#include "thor/recomp/block_exit.hpp"

namespace thor::recomp {

std::optional<BlockExitDescriptor> derive_block_exit_descriptor(
    const thor::sh2::Sh2BasicBlock& block
) noexcept {
    if (block.instructions.empty()) {
        return std::nullopt;
    }

    // Delay slot consistency check: terminator has_delay_slot must match block.delay_slot presence
    const bool has_delay_slot = block.terminator.has_delay_slot;
    if (has_delay_slot != block.delay_slot.has_value()) {
        return std::nullopt; // Inconsistent delay-slot metadata fails closed
    }

    BlockExitDescriptor desc{};
    desc.terminator_pc = block.terminator.pc;
    desc.has_delay_slot = has_delay_slot;

    switch (block.terminator.id) {
    case thor::sh2::OpcodeId::BRA:
        desc.kind = BlockExitKind::DIRECT;
        desc.writes_pr = false;
        if (block.direct_exits.size() != 1 || block.fallthrough.has_value()) {
            return std::nullopt;
        }
        if (block.dynamic_taken_exit.has_value() && *block.dynamic_taken_exit != block.direct_exits[0]) {
            return std::nullopt;
        }
        desc.static_target_pc = block.direct_exits[0];
        desc.fallthrough_pc = std::nullopt;
        return desc;

    case thor::sh2::OpcodeId::JSR:
        desc.kind = BlockExitKind::INDIRECT_CALL;
        desc.writes_pr = true;
        // Static descriptor MUST NOT contain static_target_pc or observed target
        desc.static_target_pc = std::nullopt;
        desc.fallthrough_pc = std::nullopt;
        if (!block.direct_exits.empty() || block.fallthrough.has_value() || block.dynamic_taken_exit.has_value()) {
            return std::nullopt;
        }
        return desc;

    default:
        // Any unknown or unsupported terminator fails closed
        return std::nullopt;
    }
}

std::optional<ResolvedBlockExit> resolve_block_exit(
    const BlockExitDescriptor& desc,
    const thor::sh2::Sh2CpuState& post_state
) noexcept {
    switch (desc.kind) {
    case BlockExitKind::DIRECT: {
        if (!desc.static_target_pc.has_value()) {
            return std::nullopt;
        }
        // Direct branch runtime PC must agree with static target
        if (post_state.pc != *desc.static_target_pc) {
            return std::nullopt; // Direct post-PC mismatch fails closed
        }
        ResolvedBlockExit res{};
        res.kind = BlockExitKind::DIRECT;
        res.target_pc = post_state.pc;
        res.pr_value = desc.writes_pr ? std::make_optional(post_state.pr) : std::nullopt;
        res.delay_slot_completed = desc.has_delay_slot;
        return res;
    }

    case BlockExitKind::INDIRECT_CALL: {
        // Static target PC must be absent for indirect call
        if (desc.static_target_pc.has_value()) {
            return std::nullopt;
        }
        ResolvedBlockExit res{};
        res.kind = BlockExitKind::INDIRECT_CALL;
        // Runtime target MUST come directly from post_state.pc
        res.target_pc = post_state.pc;
        res.pr_value = post_state.pr;
        res.delay_slot_completed = desc.has_delay_slot;
        return res;
    }

    case BlockExitKind::INDIRECT_JUMP: {
        if (desc.static_target_pc.has_value()) {
            return std::nullopt;
        }
        ResolvedBlockExit res{};
        res.kind = BlockExitKind::INDIRECT_JUMP;
        res.target_pc = post_state.pc;
        res.pr_value = std::nullopt;
        res.delay_slot_completed = desc.has_delay_slot;
        return res;
    }

    case BlockExitKind::RETURN: {
        ResolvedBlockExit res{};
        res.kind = BlockExitKind::RETURN;
        res.target_pc = post_state.pc;
        res.pr_value = std::nullopt;
        res.delay_slot_completed = desc.has_delay_slot;
        return res;
    }

    case BlockExitKind::CONDITIONAL: {
        const bool match_target = desc.static_target_pc && (post_state.pc == *desc.static_target_pc);
        const bool match_fall = desc.fallthrough_pc && (post_state.pc == *desc.fallthrough_pc);
        if (!match_target && !match_fall) {
            return std::nullopt;
        }
        ResolvedBlockExit res{};
        res.kind = BlockExitKind::CONDITIONAL;
        res.target_pc = post_state.pc;
        res.pr_value = std::nullopt;
        res.delay_slot_completed = desc.has_delay_slot;
        return res;
    }

    default:
        return std::nullopt;
    }
}

} // namespace thor::recomp
