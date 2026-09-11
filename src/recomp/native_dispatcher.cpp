#include "thor/recomp/native_dispatcher.hpp"
#include "thor/recomp/native_bridge.h"
#include "bb_06004000.hpp"
#include "bb_06004280.hpp"

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

    // Construct oracle basic block representation
    thor::sh2::Sh2FlatMemory dummy_mem;
    for (size_t i = 0; i < bb0.proven_identity.expected_bytes.size(); ++i) {
        dummy_mem.write8(0x06004000u + static_cast<uint32_t>(i), bb0.proven_identity.expected_bytes[i]);
    }
    bb0.oracle_block = thor::sh2::discover_basic_block(0x06004000u, dummy_mem);
    bb0.candidate_fn = thor::generated::bb_06004000;

    auto exit_desc = derive_block_exit_descriptor(bb0.oracle_block);
    if (exit_desc.has_value()) {
        bb0.exit_descriptor = *exit_desc;
    }
    auto mem_contract = derive_block_memory_contract(bb0.oracle_block);
    if (mem_contract.has_value()) {
        bb0.memory_contract = *mem_contract;
    }

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

    bool ok = register_block(std::move(bb0));
    (void)ok;

    // Register canonical bb_06004280
    RegisteredNativeBlock bb1{};
    bb1.proven_identity = make_bb_06004280_descriptor();

    thor::sh2::Sh2FlatMemory dummy_mem1;
    for (size_t i = 0; i < bb1.proven_identity.expected_bytes.size(); ++i) {
        dummy_mem1.write8(0x06004280u + static_cast<uint32_t>(i), bb1.proven_identity.expected_bytes[i]);
    }
    bb1.oracle_block = thor::sh2::discover_basic_block(0x06004280u, dummy_mem1);
    bb1.candidate_fn = thor::generated::bb_06004280;

    auto exit_desc1 = derive_block_exit_descriptor(bb1.oracle_block);
    if (exit_desc1.has_value()) {
        bb1.exit_descriptor = *exit_desc1;
    }
    auto mem_contract1 = derive_block_memory_contract(bb1.oracle_block);
    if (mem_contract1.has_value()) {
        bb1.memory_contract = *mem_contract1;
    }

    // Hit 2 arrival at 316309169 -> target 0x0600A0F8 entry at 316309189 (delta 20 cycles)
    bb1.cycle_cost = 20u;
    bb1.expected_event_meta = BoundedEventMetadata{
        .mmio_accessed = false,
        .irq_accepted = false,
        .scu_dma_crossing = false,
        .slave_sh2_active = false,
        .delay_slot_atomic = true
    };

    bool ok1 = register_block(std::move(bb1));
    (void)ok1;
}

bool NativeDispatcher::register_block(RegisteredNativeBlock block) {
    if (!block.candidate_fn || block.oracle_block.instructions.empty()) {
        return false;
    }
    if (block.proven_identity.start_pc != block.oracle_block.start_address ||
        block.proven_identity.end_pc != block.oracle_block.end_address) {
        return false;
    }
    auto derived_exit = derive_block_exit_descriptor(block.oracle_block);
    if (!derived_exit.has_value() || *derived_exit != block.exit_descriptor) {
        return false;
    }
    auto derived_mem = derive_block_memory_contract(block.oracle_block);
    if (!derived_mem.has_value() || *derived_mem != block.memory_contract) {
        return false;
    }
    if (block.cycle_cost == 0) {
        return false;
    }
    for (const auto& dep : block.memory_contract.dependencies) {
        if (dep.access_kind == thor::sh2::MemoryAccessKind::WRITE) {
            return false;
        }
    }

    m_blocks[block.proven_identity.start_pc] = std::move(block);
    return true;
}

NativeDispatcher& NativeDispatcher::instance() {
    static NativeDispatcher s_instance;
    return s_instance;
}

static uint32_t get_block_mask_bit(uint32_t pc) noexcept {
    if (pc == 0x06004000u) return THOR_BLOCK_MASK_BB_06004000;
    if (pc == 0x06004280u) return THOR_BLOCK_MASK_BB_06004280;
    return 0;
}

bool NativeDispatcher::dispatch_step(
    uint32_t pc,
    ThorCpuRegs& live_regs,
    uint32_t& out_target_pc,
    uint32_t& out_cycles_advanced,
    const ThorHardwareCallbacks& hw_cb
) {
    uint32_t dummy_instrs = 0;
    return dispatch_step(pc, live_regs, out_target_pc, out_cycles_advanced, dummy_instrs, hw_cb);
}

bool NativeDispatcher::dispatch_step(
    uint32_t pc,
    ThorCpuRegs& live_regs,
    uint32_t& out_target_pc,
    uint32_t& out_cycles_advanced,
    uint32_t& out_instructions_executed,
    const ThorHardwareCallbacks& hw_cb
) {
    out_instructions_executed = 0;
    auto it = m_blocks.find(pc);
    if (it == m_blocks.end()) {
        return false;
    }

    m_stats.dispatch_attempts++;
    m_block_stats[pc].dispatch_attempts++;
    const auto& block = it->second;

    auto record_fallback = [&]() {
        m_stats.fallback_count++;
        m_block_stats[pc].fallback_count++;
    };

    // Mask gating
    uint32_t mask_bit = get_block_mask_bit(pc);
    if (mask_bit != 0 && (m_block_mask & mask_bit) == 0) {
        record_fallback();
        return false;
    }

    // Fail closed if mode is INTERPRETER_AUTHORITATIVE
    if (m_mode == THOR_NATIVE_MODE_INTERPRETER) {
        record_fallback();
        return false;
    }

    // Event safety check
    if (hw_cb.is_slave_active && hw_cb.is_slave_active(hw_cb.user_data)) {
        record_fallback();
        return false;
    }
    if (hw_cb.is_dma_active && hw_cb.is_dma_active(hw_cb.user_data)) {
        record_fallback();
        return false;
    }
    if (hw_cb.is_irq_pending && hw_cb.is_irq_pending(hw_cb.user_data)) {
        record_fallback();
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
        record_fallback();
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

    // Snapshot code bytes
    for (size_t i = 0; i < block.proven_identity.expected_bytes.size(); ++i) {
        pre_state.memory.write8(pc + static_cast<uint32_t>(i), live_mem.peek8(pc + static_cast<uint32_t>(i)));
    }

    // Setup memory dependencies
    if (pc == 0x06004000u) {
        // Documented legacy compatibility debt for bb_06004000
        uint32_t lit_addr = 0x06004064u;
        uint32_t ptr_val = live_mem.peek32(lit_addr);
        pre_state.memory.write32(lit_addr, ptr_val);
        pre_state.memory.write32(ptr_val, live_mem.peek32(ptr_val));
        pre_state.memory.write16(live_regs.r[1], live_mem.peek16(live_regs.r[1]));
    } else {
        // Generic declarative memory contract materializer
        for (const auto& dep : block.memory_contract.dependencies) {
            uint32_t addr = 0;
            if (dep.address_source == AddressSourceKind::STATIC_ADDRESS && dep.static_address.has_value()) {
                addr = *dep.static_address;
            } else if (dep.address_source == AddressSourceKind::REGISTER_AT_EXECUTION && dep.source_register.has_value()) {
                addr = live_regs.r[*dep.source_register];
            } else {
                record_fallback();
                return false;
            }

            if (!validate_runtime_memory_dependency(dep, addr)) {
                record_fallback();
                return false;
            }

            uint32_t width_bytes = memory_access_width_bytes(dep.width);
            if (width_bytes == 1) {
                pre_state.memory.write8(addr, live_mem.peek8(addr));
            } else if (width_bytes == 2) {
                pre_state.memory.write16(addr, live_mem.peek16(addr));
            } else if (width_bytes == 4) {
                pre_state.memory.write32(addr, live_mem.peek32(addr));
            } else {
                record_fallback();
                return false;
            }
        }
    }

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
        record_fallback();
        return false;
    }

    m_stats.shadow_match_count++;

    // In SHADOW_VERIFY mode, parity is proven but no live override is applied
    if (m_mode == THOR_NATIVE_MODE_SHADOW_VERIFY) {
        record_fallback();
        return false;
    }

    // Write safety check: candidate blocks with WRITE dependencies are not yet supported for native commit
    for (const auto& dep : block.memory_contract.dependencies) {
        if (dep.access_kind == thor::sh2::MemoryAccessKind::WRITE) {
            record_fallback();
            return false;
        }
    }

    // Authoritative Native Override Commit
    thor::sh2::Sh2CpuState live_cpu = pre_state.cpu_state;
    cand_fn(live_cpu, live_mem);

    // Resolve exit target dynamically from executed live_cpu post-state
    auto resolved_exit = resolve_block_exit(block.exit_descriptor, live_cpu);
    if (!resolved_exit.has_value()) {
        record_fallback();
        return false;
    }

    for (size_t i = 0; i < 16; ++i) live_regs.r[i] = live_cpu.r[i];
    live_regs.pc = live_cpu.pc;
    live_regs.sr = live_cpu.sr;
    live_regs.pr = live_cpu.pr;
    live_regs.gbr = live_cpu.gbr;
    live_regs.vbr = live_cpu.vbr;
    live_regs.mach = live_cpu.mach;
    live_regs.macl = live_cpu.macl;

    out_target_pc = resolved_exit->target_pc;
    out_cycles_advanced = block.cycle_cost;
    out_instructions_executed = static_cast<uint32_t>(block.oracle_block.instructions.size());
    m_stats.native_executed_count++;
    m_block_stats[pc].native_executed_count++;
    return true;
}

size_t NativeDispatcher::get_block_instruction_count(uint32_t pc) const noexcept {
    auto it = m_blocks.find(pc);
    if (it == m_blocks.end()) return 0;
    return it->second.oracle_block.instructions.size();
}

bool NativeDispatcher::get_block_stats(uint32_t pc, uint64_t* out_executed, uint64_t* out_fallback) const noexcept {
    auto it = m_block_stats.find(pc);
    if (it == m_block_stats.end()) {
        if (out_executed) *out_executed = 0;
        if (out_fallback) *out_fallback = 0;
        return false;
    }
    if (out_executed) *out_executed = it->second.native_executed_count;
    if (out_fallback) *out_fallback = it->second.fallback_count;
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

void thor_native_set_block_mask(uint32_t mask) {
    thor::recomp::NativeDispatcher::instance().set_block_mask(mask);
}

uint32_t thor_native_get_block_mask(void) {
    return thor::recomp::NativeDispatcher::instance().get_block_mask();
}

void thor_native_get_stats(ThorNativeStats* out_stats) {
    if (out_stats) {
        *out_stats = thor::recomp::NativeDispatcher::instance().get_stats();
    }
}

void thor_native_reset_stats(void) {
    thor::recomp::NativeDispatcher::instance().reset_stats();
}

bool thor_native_get_block_stats(uint32_t pc, uint64_t* out_executed, uint64_t* out_fallback) {
    return thor::recomp::NativeDispatcher::instance().get_block_stats(pc, out_executed, out_fallback);
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
