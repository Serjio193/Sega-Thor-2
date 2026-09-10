#pragma once

#include <cstdint>
#include <functional>
#include <string>
#include <vector>

#include "thor/recomp/block_identity.hpp"
#include "thor/sh2/sh2_block.hpp"
#include "thor/sh2/sh2_memory.hpp"
#include "thor/sh2/sh2_state.hpp"

namespace thor::recomp {

enum class ShadowStatus : uint8_t {
    MATCH = 0,
    DIVERGENCE,
    INELIGIBLE,
    EXECUTION_ERROR
};

[[nodiscard]] const char* shadow_status_to_string(ShadowStatus status) noexcept;

enum class DivergenceCategory : uint8_t {
    REGISTER = 0,
    PROGRAM_COUNTER,
    STATUS_REGISTER,
    CONTROL_REGISTER,
    MEMORY_EFFECT_COUNT,
    MEMORY_EFFECT_KIND,
    MEMORY_EFFECT_ADDRESS,
    MEMORY_EFFECT_VALUE,
    MEMORY_EFFECT_SIZE,
    EVENT_SAFETY_METADATA,
    DELAYED_CONTROL_STATE
};

[[nodiscard]] const char* divergence_category_to_string(DivergenceCategory cat) noexcept;

struct DivergenceRecord {
    DivergenceCategory category = DivergenceCategory::REGISTER;
    uint32_t index = 0;
    std::string field_name;
    uint32_t oracle_value = 0;
    uint32_t candidate_value = 0;
    std::string details;
};

/// Bounded event safety metadata for a block execution window.
struct BoundedEventMetadata {
    bool mmio_accessed = false;
    bool irq_accepted = false;
    bool scu_dma_crossing = false;
    bool slave_sh2_active = false;
    bool delay_slot_atomic = true;

    bool operator==(const BoundedEventMetadata& other) const noexcept = default;
};

/// An immutable captured pre-state for a basic block.
struct BlockPreState {
    thor::sh2::Sh2CpuState cpu_state{};
    thor::sh2::Sh2FlatMemory memory{};
    BoundedEventMetadata event_metadata{};
};

/// Result of a shadow execution comparison.
struct ShadowComparisonResult {
    ShadowStatus status = ShadowStatus::MATCH;
    std::vector<DivergenceRecord> divergences{};
    EligibilityResult eligibility_reason = EligibilityResult::ELIGIBLE;
    std::string error_message;

    [[nodiscard]] bool is_match() const noexcept {
        return status == ShadowStatus::MATCH && divergences.empty();
    }
};

using CandidateBlockFn = std::function<void(thor::sh2::Sh2CpuState&, thor::sh2::ISh2Memory&)>;

class ShadowChecker {
public:
    /// Executes both oracle and candidate from independently cloned pre-states and compares results.
    /// Fails closed if candidate is ineligible or if mutable state aliasing is detected.
    [[nodiscard]] static ShadowComparisonResult run_and_compare(
        const BlockIdentityDescriptor& proven_identity,
        const BlockIdentityDescriptor& candidate_identity,
        const thor::sh2::Sh2BasicBlock& block,
        CandidateBlockFn candidate_fn,
        const BlockPreState& immutable_pre_state,
        const BoundedEventMetadata& candidate_event_meta = BoundedEventMetadata{});

    /// Direct comparator of two execution outcomes.
    [[nodiscard]] static ShadowComparisonResult compare_outcomes(
        const thor::sh2::Sh2CpuState& oracle_cpu,
        const std::vector<thor::sh2::MemoryLogEntry>& oracle_log,
        const BoundedEventMetadata& oracle_meta,
        const thor::sh2::Sh2CpuState& candidate_cpu,
        const std::vector<thor::sh2::MemoryLogEntry>& candidate_log,
        const BoundedEventMetadata& candidate_meta);
};

} // namespace thor::recomp
