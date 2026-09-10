#pragma once

#include <cstdint>
#include <optional>
#include "thor/sh2/sh2_block.hpp"
#include "thor/sh2/sh2_state.hpp"

namespace thor::recomp {

/// Static classification of basic block exit terminator.
enum class BlockExitKind : uint8_t {
    DIRECT = 0,
    CONDITIONAL,
    INDIRECT_JUMP,
    INDIRECT_CALL,
    RETURN,
    FALLBACK_UNSUPPORTED
};

/// Static descriptor of basic block exit control-flow properties.
/// Represents what the instruction/block structure proves statically.
/// Timing and event safety are deliberately separated from this structure.
struct BlockExitDescriptor {
    BlockExitKind kind = BlockExitKind::FALLBACK_UNSUPPORTED;
    uint32_t terminator_pc = 0;
    bool has_delay_slot = false;
    std::optional<uint32_t> static_target_pc = std::nullopt;
    std::optional<uint32_t> fallthrough_pc = std::nullopt;
    bool writes_pr = false;

    bool operator==(const BlockExitDescriptor& other) const = default;
};

/// Dynamic resolution of block exit from verified post-execution CPU state.
/// Represents what a concrete execution produced.
struct ResolvedBlockExit {
    BlockExitKind kind = BlockExitKind::FALLBACK_UNSUPPORTED;
    uint32_t target_pc = 0;
    std::optional<uint32_t> pr_value = std::nullopt;
    bool delay_slot_completed = false;

    bool operator==(const ResolvedBlockExit& other) const = default;
};

/// Deterministically derives a static BlockExitDescriptor from an Sh2BasicBlock.
/// Fails closed (std::nullopt) on malformed, unsupported, or contradictory metadata.
[[nodiscard]] std::optional<BlockExitDescriptor> derive_block_exit_descriptor(
    const thor::sh2::Sh2BasicBlock& block
) noexcept;

/// Resolves runtime exit target and procedure register from verified post-state.
/// For DIRECT branches, verifies post_state.pc matches static_target_pc.
/// For INDIRECT_CALL, resolves target_pc strictly from post_state.pc and pr from post_state.pr.
/// Fails closed (std::nullopt) if post_state violates static constraints.
[[nodiscard]] std::optional<ResolvedBlockExit> resolve_block_exit(
    const BlockExitDescriptor& desc,
    const thor::sh2::Sh2CpuState& post_state
) noexcept;

} // namespace thor::recomp
