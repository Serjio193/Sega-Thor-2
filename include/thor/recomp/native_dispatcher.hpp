#pragma once

#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

#include "thor/recomp/block_exit.hpp"
#include "thor/recomp/block_identity.hpp"
#include "thor/recomp/block_memory.hpp"
#include "thor/recomp/native_bridge.h"
#include "thor/recomp/shadow_checker.hpp"
#include "thor/sh2/sh2_block.hpp"
#include "thor/sh2/sh2_memory.hpp"
#include "thor/sh2/sh2_state.hpp"

namespace thor::recomp {

/// Memory adapter wrapping external hardware callbacks into ISh2Memory.
class HardwareCallbackMemory final : public thor::sh2::ISh2Memory {
public:
    HardwareCallbackMemory(const ThorHardwareCallbacks& cb, bool record_log = false)
        : m_cb(cb), m_record_log(record_log) {}

    uint8_t read8(uint32_t addr) override;
    uint16_t read16(uint32_t addr) override;
    uint32_t read32(uint32_t addr) override;

    [[nodiscard]] uint8_t peek8(uint32_t addr) const override;
    [[nodiscard]] uint16_t peek16(uint32_t addr) const;
    [[nodiscard]] uint32_t peek32(uint32_t addr) const;

    void write8(uint32_t addr, uint8_t val) override;
    void write16(uint32_t addr, uint16_t val) override;
    void write32(uint32_t addr, uint32_t val) override;

    [[nodiscard]] const std::vector<thor::sh2::MemoryLogEntry>& log() const noexcept {
        return m_log;
    }

private:
    ThorHardwareCallbacks m_cb{};
    bool m_record_log = false;
    std::vector<thor::sh2::MemoryLogEntry> m_log{};
};

/// Registered native recompiled basic block entry.
struct RegisteredNativeBlock {
    BlockIdentityDescriptor proven_identity{};
    thor::sh2::Sh2BasicBlock oracle_block{};
    CandidateBlockFn candidate_fn{};
    BlockExitDescriptor exit_descriptor{};
    BlockMemoryContract memory_contract{};
    uint32_t cycle_cost = 0;
    BoundedEventMetadata expected_event_meta{};
};

/// Authoritative native dispatcher with fail-closed shadow qualification.
class NativeDispatcher {
public:
    NativeDispatcher();

    void set_mode(ThorNativeMode mode) noexcept { m_mode = mode; }
    [[nodiscard]] ThorNativeMode get_mode() const noexcept { return m_mode; }

    [[nodiscard]] ThorNativeStats get_stats() const noexcept { return m_stats; }
    void reset_stats() noexcept { m_stats = {}; }

    /// Register a native recompiled block. Returns true if valid, false if validation failed.
    bool register_block(RegisteredNativeBlock block);

    /// Attempt to dispatch and execute recompiled block at live PC.
    /// Returns true if native override was executed and committed.
    /// Returns false if skipped/failed, requiring interpreter fallback.
    bool dispatch_step(
        uint32_t pc,
        ThorCpuRegs& live_regs,
        uint32_t& out_target_pc,
        uint32_t& out_cycles_advanced,
        const ThorHardwareCallbacks& hw_cb
    );

    /// Testing injection hooks
    void inject_forced_divergence(bool enable) noexcept { m_inject_divergence = enable; }
    void inject_ineligible_revision(bool enable) noexcept { m_inject_ineligible_rev = enable; }
    void inject_ineligible_content(bool enable) noexcept { m_inject_ineligible_content = enable; }

    static NativeDispatcher& instance();

private:
    ThorNativeMode m_mode = THOR_NATIVE_MODE_INTERPRETER;
    ThorNativeStats m_stats{};
    std::unordered_map<uint32_t, RegisteredNativeBlock> m_blocks{};

    bool m_inject_divergence = false;
    bool m_inject_ineligible_rev = false;
    bool m_inject_ineligible_content = false;
};

} // namespace thor::recomp
