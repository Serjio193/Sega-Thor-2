#include "thor/recomp/native_dispatcher.hpp"
#include "thor/recomp/native_bridge.h"
#include "bb_06004000.hpp"

#include <cstring>

namespace thor::recomp {

uint8_t HardwareCallbackMemory::read8(uint32_t addr) {
    uint8_t v = m_cb.read8 ? m_cb.read8(addr, m_cb.user_data) : 0;
    if (m_record_log) {
        m_log.push_back({thor::sh2::MemoryAccessKind::READ, addr, v, 1});
    }
    return v;
}

uint16_t HardwareCallbackMemory::read16(uint32_t addr) {
    uint16_t v = m_cb.read16 ? m_cb.read16(addr, m_cb.user_data) : 0;
    if (m_record_log) {
        m_log.push_back({thor::sh2::MemoryAccessKind::READ, addr, v, 2});
    }
    return v;
}

uint32_t HardwareCallbackMemory::read32(uint32_t addr) {
    uint32_t v = m_cb.read32 ? m_cb.read32(addr, m_cb.user_data) : 0;
    if (m_record_log) {
        m_log.push_back({thor::sh2::MemoryAccessKind::READ, addr, v, 4});
    }
    return v;
}

uint8_t HardwareCallbackMemory::peek8(uint32_t addr) const {
    return m_cb.read8 ? m_cb.read8(addr, m_cb.user_data) : 0;
}

uint16_t HardwareCallbackMemory::peek16(uint32_t addr) const {
    if (m_cb.read16) {
        return m_cb.read16(addr, m_cb.user_data);
    }
    return static_cast<uint16_t>((static_cast<uint16_t>(peek8(addr)) << 8) | peek8(addr + 1));
}

uint32_t HardwareCallbackMemory::peek32(uint32_t addr) const {
    if (m_cb.read32) {
        return m_cb.read32(addr, m_cb.user_data);
    }
    return (static_cast<uint32_t>(peek16(addr)) << 16) | peek16(addr + 2);
}

void HardwareCallbackMemory::write8(uint32_t addr, uint8_t val) {
    if (m_cb.write8) m_cb.write8(addr, val, m_cb.user_data);
    if (m_record_log) {
        m_log.push_back({thor::sh2::MemoryAccessKind::WRITE, addr, val, 1});
    }
}

void HardwareCallbackMemory::write16(uint32_t addr, uint16_t val) {
    if (m_cb.write16) m_cb.write16(addr, val, m_cb.user_data);
    if (m_record_log) {
        m_log.push_back({thor::sh2::MemoryAccessKind::WRITE, addr, val, 2});
    }
}

void HardwareCallbackMemory::write32(uint32_t addr, uint32_t val) {
    if (m_cb.write32) m_cb.write32(addr, val, m_cb.user_data);
    if (m_record_log) {
        m_log.push_back({thor::sh2::MemoryAccessKind::WRITE, addr, val, 4});
    }
}

NativeDispatcher::NativeDispatcher() {
    // Register canonical bb_06004000
    RegisteredNativeBlock bb0{};
    bb0.proven_identity = make_bb_06004000_descriptor();

    bb0.target_pc = 0x06004012u;
    // Cycle cost breakdown (27 cycles total for bb_06004000: 305462360..305462387):
    // - 0x06004000 MOV.W @R1, R6: 1 cycle (305462360 -> 305462361)
    // - 0x06004002 MOV R0, R15: 1 cycle (305462361 -> 305462362)
    // - 0x06004004 MOV.L @(disp,PC), R4: 1 cycle (305462362 -> 305462363)
    // - 0x06004006 MOV.L @R4, R4: 8 cycles (305462363 -> 305462371, SDRAM bus wait)
    // - 0x06004008 BRA 0x06004012: 1 cycle (305462371 -> 305462372)
    // - 0x0600400A NOP (delay slot): 15 cycles (305462372 -> 305462387, target fetch & pipeline refill)
    // Entry at exit target 0x06004012 occurs at cycle 305462387. Cycle 305462388 is post-completion of 0x06004012.
    bb0.cycle_cost = 27u;
    bb0.expected_event_meta = BoundedEventMetadata{
        .mmio_accessed = false,
        .irq_accepted = false,
        .scu_dma_crossing = false,
        .slave_sh2_active = false,
        .delay_slot_atomic = true
    };

    // Construct oracle basic block representation
    thor::sh2::Sh2FlatMemory dummy_mem;
    for (size_t i = 0; i < bb0.proven_identity.expected_bytes.size(); ++i) {
        dummy_mem.write8(0x06004000u + static_cast<uint32_t>(i), bb0.proven_identity.expected_bytes[i]);
    }
    bb0.oracle_block = thor::sh2::discover_basic_block(0x06004000u, dummy_mem);
    bb0.candidate_fn = thor::generated::bb_06004000;

    register_block(std::move(bb0));
}

void NativeDispatcher::register_block(RegisteredNativeBlock block) {
    m_blocks[block.proven_identity.start_pc] = std::move(block);
}

NativeDispatcher& NativeDispatcher::instance() {
    static NativeDispatcher s_instance;
    return s_instance;
}

bool NativeDispatcher::dispatch_step(
    uint32_t pc,
    ThorCpuRegs& live_regs,
    uint32_t& out_target_pc,
    uint32_t& out_cycles_advanced,
    const ThorHardwareCallbacks& hw_cb
) {
    auto it = m_blocks.find(pc);
    if (it == m_blocks.end()) {
        return false;
    }

    m_stats.dispatch_attempts++;
    const auto& block = it->second;

    // Fail closed if mode is INTERPRETER_AUTHORITATIVE
    if (m_mode == THOR_NATIVE_MODE_INTERPRETER) {
        m_stats.fallback_count++;
        return false;
    }

    // Event safety check
    if (hw_cb.is_slave_active && hw_cb.is_slave_active(hw_cb.user_data)) {
        m_stats.fallback_count++;
        return false;
    }
    if (hw_cb.is_dma_active && hw_cb.is_dma_active(hw_cb.user_data)) {
        m_stats.fallback_count++;
        return false;
    }
    if (hw_cb.is_irq_pending && hw_cb.is_irq_pending(hw_cb.user_data)) {
        m_stats.fallback_count++;
        return false;
    }

    // Executable identity eligibility check
    BlockIdentityDescriptor candidate_identity = block.proven_identity;
    if (m_inject_ineligible_rev) {
        candidate_identity.revision_id = "0000000000000000000000000000000000000000000000000000000000000000";
    }

    HardwareCallbackMemory live_mem(hw_cb, false);
    EligibilityResult elig = check_block_eligibility(
        block.proven_identity, candidate_identity, live_mem);
    
    if (m_inject_ineligible_content || elig != EligibilityResult::ELIGIBLE) {
        m_stats.ineligible_count++;
        m_stats.fallback_count++;
        return false;
    }

    // Shadow qualification before native commit
    BlockPreState pre_state{};
    for (size_t i = 0; i < 16; ++i) pre_state.cpu_state.r[i] = live_regs.r[i];
    pre_state.cpu_state.pc = pc;
    pre_state.cpu_state.sr = live_regs.sr;
    pre_state.cpu_state.pr = live_regs.pr;
    pre_state.cpu_state.gbr = live_regs.gbr;
    pre_state.cpu_state.vbr = live_regs.vbr;
    pre_state.cpu_state.mach = live_regs.mach;
    pre_state.cpu_state.macl = live_regs.macl;
    pre_state.event_metadata = block.expected_event_meta;

    // Snapshot necessary memory addresses into pre_state flat memory
    for (size_t i = 0; i < block.proven_identity.expected_bytes.size(); ++i) {
        pre_state.memory.write8(pc + static_cast<uint32_t>(i), live_mem.peek8(pc + static_cast<uint32_t>(i)));
    }
    // Setup literal pool and indirect pointers accessed by bb_06004000
    uint32_t lit_addr = 0x06004064u;
    uint32_t ptr_val = live_mem.peek32(lit_addr);
    pre_state.memory.write32(lit_addr, ptr_val);
    pre_state.memory.write32(ptr_val, live_mem.peek32(ptr_val));
    pre_state.memory.write16(live_regs.r[1], live_mem.peek16(live_regs.r[1]));

    CandidateBlockFn cand_fn = block.candidate_fn;
    if (m_inject_divergence) {
        cand_fn = [](thor::sh2::Sh2CpuState& s, thor::sh2::ISh2Memory&) {
            s.r[6] = 0xDEADBEEFu;
            s.pc = 0x06004012u;
        };
    }

    ShadowComparisonResult shadow_res = ShadowChecker::run_and_compare(
        block.proven_identity, candidate_identity, block.oracle_block, cand_fn, pre_state, block.expected_event_meta);

    if (!shadow_res.is_match()) {
        m_stats.shadow_divergence_count++;
        m_stats.fallback_count++;
        return false;
    }

    m_stats.shadow_match_count++;

    // In SHADOW_VERIFY mode, parity is proven but no live override is applied
    if (m_mode == THOR_NATIVE_MODE_SHADOW_VERIFY) {
        m_stats.fallback_count++;
        return false;
    }

    // Authoritative Native Override Commit
    thor::sh2::Sh2CpuState live_cpu = pre_state.cpu_state;
    cand_fn(live_cpu, live_mem);

    for (size_t i = 0; i < 16; ++i) live_regs.r[i] = live_cpu.r[i];
    live_regs.pc = live_cpu.pc;
    live_regs.sr = live_cpu.sr;
    live_regs.pr = live_cpu.pr;
    live_regs.gbr = live_cpu.gbr;
    live_regs.vbr = live_cpu.vbr;
    live_regs.mach = live_cpu.mach;
    live_regs.macl = live_cpu.macl;

    out_target_pc = block.target_pc;
    out_cycles_advanced = block.cycle_cost;
    m_stats.native_executed_count++;
    return true;
}

} // namespace thor::recomp

// C ABI implementations
extern "C" {

void thor_native_init(void) {
    thor::recomp::NativeDispatcher::instance();
}

void thor_native_set_mode(ThorNativeMode mode) {
    thor::recomp::NativeDispatcher::instance().set_mode(mode);
}

ThorNativeMode thor_native_get_mode(void) {
    return thor::recomp::NativeDispatcher::instance().get_mode();
}

void thor_native_get_stats(ThorNativeStats* out_stats) {
    if (out_stats) {
        *out_stats = thor::recomp::NativeDispatcher::instance().get_stats();
    }
}

void thor_native_reset_stats(void) {
    thor::recomp::NativeDispatcher::instance().reset_stats();
}

bool thor_native_dispatch_step(
    uint32_t pc,
    ThorCpuRegs* live_regs,
    uint32_t* out_target_pc,
    uint32_t* out_cycles_advanced,
    const ThorHardwareCallbacks* hw_cb
) {
    if (!live_regs || !out_target_pc || !out_cycles_advanced || !hw_cb) {
        return false;
    }
    return thor::recomp::NativeDispatcher::instance().dispatch_step(
        pc, *live_regs, *out_target_pc, *out_cycles_advanced, *hw_cb);
}

} // extern "C"
