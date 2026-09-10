#include "thor/recomp/shadow_checker.hpp"
#include <algorithm>

namespace thor::recomp {

const char* shadow_status_to_string(ShadowStatus status) noexcept {
    switch (status) {
    case ShadowStatus::MATCH:
        return "MATCH";
    case ShadowStatus::DIVERGENCE:
        return "DIVERGENCE";
    case ShadowStatus::INELIGIBLE:
        return "INELIGIBLE";
    case ShadowStatus::EXECUTION_ERROR:
        return "EXECUTION_ERROR";
    default:
        return "UNKNOWN_STATUS";
    }
}

const char* divergence_category_to_string(DivergenceCategory cat) noexcept {
    switch (cat) {
    case DivergenceCategory::REGISTER:
        return "REGISTER";
    case DivergenceCategory::PROGRAM_COUNTER:
        return "PROGRAM_COUNTER";
    case DivergenceCategory::STATUS_REGISTER:
        return "STATUS_REGISTER";
    case DivergenceCategory::CONTROL_REGISTER:
        return "CONTROL_REGISTER";
    case DivergenceCategory::MEMORY_EFFECT_COUNT:
        return "MEMORY_EFFECT_COUNT";
    case DivergenceCategory::MEMORY_EFFECT_KIND:
        return "MEMORY_EFFECT_KIND";
    case DivergenceCategory::MEMORY_EFFECT_ADDRESS:
        return "MEMORY_EFFECT_ADDRESS";
    case DivergenceCategory::MEMORY_EFFECT_VALUE:
        return "MEMORY_EFFECT_VALUE";
    case DivergenceCategory::MEMORY_EFFECT_SIZE:
        return "MEMORY_EFFECT_SIZE";
    case DivergenceCategory::EVENT_SAFETY_METADATA:
        return "EVENT_SAFETY_METADATA";
    case DivergenceCategory::DELAYED_CONTROL_STATE:
        return "DELAYED_CONTROL_STATE";
    default:
        return "UNKNOWN_CATEGORY";
    }
}

ShadowComparisonResult ShadowChecker::compare_outcomes(
    const thor::sh2::Sh2CpuState& oracle_cpu,
    const std::vector<thor::sh2::MemoryLogEntry>& oracle_log,
    const BoundedEventMetadata& oracle_meta,
    const thor::sh2::Sh2CpuState& candidate_cpu,
    const std::vector<thor::sh2::MemoryLogEntry>& candidate_log,
    const BoundedEventMetadata& candidate_meta) {

    std::vector<DivergenceRecord> diffs;

    // 1. Compare General Registers R0..R15
    for (uint32_t i = 0; i < 16; ++i) {
        if (oracle_cpu.r[i] != candidate_cpu.r[i]) {
            diffs.push_back(DivergenceRecord{
                .category = DivergenceCategory::REGISTER,
                .index = i,
                .field_name = "R" + std::to_string(i),
                .oracle_value = oracle_cpu.r[i],
                .candidate_value = candidate_cpu.r[i],
                .details = "General register value mismatch"
            });
        }
    }

    // 2. Compare PC
    if (oracle_cpu.pc != candidate_cpu.pc) {
        diffs.push_back(DivergenceRecord{
            .category = DivergenceCategory::PROGRAM_COUNTER,
            .index = 0,
            .field_name = "PC",
            .oracle_value = oracle_cpu.pc,
            .candidate_value = candidate_cpu.pc,
            .details = "Program counter mismatch"
        });
    }

    // 3. Compare SR
    if (oracle_cpu.sr != candidate_cpu.sr) {
        diffs.push_back(DivergenceRecord{
            .category = DivergenceCategory::STATUS_REGISTER,
            .index = 0,
            .field_name = "SR",
            .oracle_value = oracle_cpu.sr,
            .candidate_value = candidate_cpu.sr,
            .details = "Status register mismatch"
        });
    }

    // 4. Compare PR, GBR, VBR, MACH, MACL
    if (oracle_cpu.pr != candidate_cpu.pr) {
        diffs.push_back({DivergenceCategory::CONTROL_REGISTER, 0, "PR", oracle_cpu.pr, candidate_cpu.pr, "PR mismatch"});
    }
    if (oracle_cpu.gbr != candidate_cpu.gbr) {
        diffs.push_back({DivergenceCategory::CONTROL_REGISTER, 1, "GBR", oracle_cpu.gbr, candidate_cpu.gbr, "GBR mismatch"});
    }
    if (oracle_cpu.vbr != candidate_cpu.vbr) {
        diffs.push_back({DivergenceCategory::CONTROL_REGISTER, 2, "VBR", oracle_cpu.vbr, candidate_cpu.vbr, "VBR mismatch"});
    }
    if (oracle_cpu.mach != candidate_cpu.mach) {
        diffs.push_back({DivergenceCategory::CONTROL_REGISTER, 3, "MACH", oracle_cpu.mach, candidate_cpu.mach, "MACH mismatch"});
    }
    if (oracle_cpu.macl != candidate_cpu.macl) {
        diffs.push_back({DivergenceCategory::CONTROL_REGISTER, 4, "MACL", oracle_cpu.macl, candidate_cpu.macl, "MACL mismatch"});
    }

    // 5. Compare Ordered Memory Effects
    const size_t o_size = oracle_log.size();
    const size_t c_size = candidate_log.size();
    if (o_size != c_size) {
        diffs.push_back(DivergenceRecord{
            .category = DivergenceCategory::MEMORY_EFFECT_COUNT,
            .index = 0,
            .field_name = "memory_log_size",
            .oracle_value = static_cast<uint32_t>(o_size),
            .candidate_value = static_cast<uint32_t>(c_size),
            .details = "Memory access log entry count mismatch"
        });
    }

    const size_t min_size = std::min(o_size, c_size);
    for (size_t i = 0; i < min_size; ++i) {
        const auto& o_entry = oracle_log[i];
        const auto& c_entry = candidate_log[i];
        const std::string entry_name = "MEM[" + std::to_string(i) + "]";

        if (o_entry.kind != c_entry.kind) {
            diffs.push_back(DivergenceRecord{
                .category = DivergenceCategory::MEMORY_EFFECT_KIND,
                .index = static_cast<uint32_t>(i),
                .field_name = entry_name + ".kind",
                .oracle_value = static_cast<uint32_t>(o_entry.kind),
                .candidate_value = static_cast<uint32_t>(c_entry.kind),
                .details = "Memory access kind mismatch (READ vs WRITE)"
            });
        }
        if (o_entry.address != c_entry.address) {
            diffs.push_back(DivergenceRecord{
                .category = DivergenceCategory::MEMORY_EFFECT_ADDRESS,
                .index = static_cast<uint32_t>(i),
                .field_name = entry_name + ".address",
                .oracle_value = o_entry.address,
                .candidate_value = c_entry.address,
                .details = "Memory access address/order mismatch"
            });
        }
        if (o_entry.value != c_entry.value) {
            diffs.push_back(DivergenceRecord{
                .category = DivergenceCategory::MEMORY_EFFECT_VALUE,
                .index = static_cast<uint32_t>(i),
                .field_name = entry_name + ".value",
                .oracle_value = o_entry.value,
                .candidate_value = c_entry.value,
                .details = "Memory access value mismatch"
            });
        }
        if (o_entry.size_bytes != c_entry.size_bytes) {
            diffs.push_back(DivergenceRecord{
                .category = DivergenceCategory::MEMORY_EFFECT_SIZE,
                .index = static_cast<uint32_t>(i),
                .field_name = entry_name + ".size_bytes",
                .oracle_value = o_entry.size_bytes,
                .candidate_value = c_entry.size_bytes,
                .details = "Memory access width mismatch"
            });
        }
    }

    // 6. Compare Bounded Event Safety Metadata
    if (oracle_meta.mmio_accessed != candidate_meta.mmio_accessed) {
        diffs.push_back({DivergenceCategory::EVENT_SAFETY_METADATA, 0, "mmio_accessed",
            oracle_meta.mmio_accessed, candidate_meta.mmio_accessed, "MMIO access mismatch"});
    }
    if (oracle_meta.irq_accepted != candidate_meta.irq_accepted) {
        diffs.push_back({DivergenceCategory::EVENT_SAFETY_METADATA, 1, "irq_accepted",
            oracle_meta.irq_accepted, candidate_meta.irq_accepted, "IRQ accepted mismatch"});
    }
    if (oracle_meta.scu_dma_crossing != candidate_meta.scu_dma_crossing) {
        diffs.push_back({DivergenceCategory::EVENT_SAFETY_METADATA, 2, "scu_dma_crossing",
            oracle_meta.scu_dma_crossing, candidate_meta.scu_dma_crossing, "SCU DMA crossing mismatch"});
    }
    if (oracle_meta.slave_sh2_active != candidate_meta.slave_sh2_active) {
        diffs.push_back({DivergenceCategory::EVENT_SAFETY_METADATA, 3, "slave_sh2_active",
            oracle_meta.slave_sh2_active, candidate_meta.slave_sh2_active, "Slave SH-2 activity mismatch"});
    }
    if (oracle_meta.delay_slot_atomic != candidate_meta.delay_slot_atomic) {
        diffs.push_back({DivergenceCategory::EVENT_SAFETY_METADATA, 4, "delay_slot_atomic",
            oracle_meta.delay_slot_atomic, candidate_meta.delay_slot_atomic, "Delay slot atomicity mismatch"});
    }

    // 7. Compare Delayed Control State (delayed_pc / pending delayed transfer)
    if (oracle_cpu.has_delayed_branch() != candidate_cpu.has_delayed_branch()) {
        diffs.push_back(DivergenceRecord{
            .category = DivergenceCategory::DELAYED_CONTROL_STATE,
            .index = 0,
            .field_name = "delayed_pc.has_value",
            .oracle_value = oracle_cpu.has_delayed_branch() ? 1u : 0u,
            .candidate_value = candidate_cpu.has_delayed_branch() ? 1u : 0u,
            .details = "Delayed branch presence mismatch"
        });
    } else if (oracle_cpu.has_delayed_branch()) {
        if (oracle_cpu.delayed_pc != candidate_cpu.delayed_pc) {
            diffs.push_back(DivergenceRecord{
                .category = DivergenceCategory::DELAYED_CONTROL_STATE,
                .index = 1,
                .field_name = "delayed_pc.target",
                .oracle_value = *oracle_cpu.delayed_pc,
                .candidate_value = *candidate_cpu.delayed_pc,
                .details = "Delayed branch target address mismatch"
            });
        }
    }

    return ShadowComparisonResult{
        .status = diffs.empty() ? ShadowStatus::MATCH : ShadowStatus::DIVERGENCE,
        .divergences = std::move(diffs),
        .eligibility_reason = EligibilityResult::ELIGIBLE,
        .error_message = ""
    };
}

ShadowComparisonResult ShadowChecker::run_and_compare(
    const BlockIdentityDescriptor& proven_identity,
    const BlockIdentityDescriptor& candidate_identity,
    const thor::sh2::Sh2BasicBlock& block,
    CandidateBlockFn candidate_fn,
    const BlockPreState& immutable_pre_state,
    const BoundedEventMetadata& candidate_event_meta) {

    // 1. Fail-closed eligibility check against pre-state memory
    const auto elig = check_block_eligibility(proven_identity, candidate_identity, immutable_pre_state.memory);
    if (elig != EligibilityResult::ELIGIBLE) {
        return ShadowComparisonResult{
            .status = ShadowStatus::INELIGIBLE,
            .divergences = {},
            .eligibility_reason = elig,
            .error_message = eligibility_result_to_string(elig)
        };
    }

    // 2. Validate block
    if (block.instructions.empty()) {
        return ShadowComparisonResult{
            .status = ShadowStatus::EXECUTION_ERROR,
            .divergences = {},
            .eligibility_reason = EligibilityResult::ELIGIBLE,
            .error_message = "Block contains no instructions"
        };
    }

    // 3. Create independent cloned execution environments
    thor::sh2::Sh2CpuState oracle_cpu = immutable_pre_state.cpu_state;
    thor::sh2::Sh2FlatMemory oracle_mem = immutable_pre_state.memory;
    oracle_mem.clear_log();

    thor::sh2::Sh2CpuState candidate_cpu = immutable_pre_state.cpu_state;
    thor::sh2::Sh2FlatMemory candidate_mem = immutable_pre_state.memory;
    candidate_mem.clear_log();

    // 4. Assert memory and state isolation (never alias mutable state)
    if (&oracle_mem == &candidate_mem || &oracle_cpu == &candidate_cpu ||
        &oracle_mem == &immutable_pre_state.memory || &oracle_cpu == &immutable_pre_state.cpu_state) {
        return ShadowComparisonResult{
            .status = ShadowStatus::EXECUTION_ERROR,
            .divergences = {},
            .eligibility_reason = EligibilityResult::ELIGIBLE,
            .error_message = "Aliased execution context detected; isolation violated"
        };
    }

    // 5. Execute Oracle (verified D3/L0 interpreter)
    const auto exec_res = thor::sh2::execute_basic_block(block, oracle_cpu, oracle_mem);
    if (exec_res != thor::sh2::ExecutionResult::SUCCESS) {
        return ShadowComparisonResult{
            .status = ShadowStatus::EXECUTION_ERROR,
            .divergences = {},
            .eligibility_reason = EligibilityResult::ELIGIBLE,
            .error_message = "Oracle execution failed"
        };
    }

    // 6. Execute Candidate (generated code)
    candidate_fn(candidate_cpu, candidate_mem);

    // 7. Perform differential comparison
    return compare_outcomes(
        oracle_cpu, oracle_mem.log(), immutable_pre_state.event_metadata,
        candidate_cpu, candidate_mem.log(), candidate_event_meta);
}

} // namespace thor::recomp
