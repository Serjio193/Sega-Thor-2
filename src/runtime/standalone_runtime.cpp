#include "thor/runtime/standalone_runtime.hpp"
#include "thor/sh2/sh2_decoder.hpp"
#include "thor/sh2/sh2_executor.hpp"

#include <cstring>
#include <algorithm>

namespace thor::runtime {

namespace {

uint8_t cb_read8(uint32_t addr, void* user_data) {
    return static_cast<StandaloneRuntime*>(user_data)->read8(addr);
}

uint16_t cb_read16(uint32_t addr, void* user_data) {
    return static_cast<StandaloneRuntime*>(user_data)->read16(addr);
}

uint32_t cb_read32(uint32_t addr, void* user_data) {
    return static_cast<StandaloneRuntime*>(user_data)->read32(addr);
}

void cb_write8(uint32_t addr, uint8_t val, void* user_data) {
    static_cast<StandaloneRuntime*>(user_data)->write8(addr, val);
}

void cb_write16(uint32_t addr, uint16_t val, void* user_data) {
    static_cast<StandaloneRuntime*>(user_data)->write16(addr, val);
}

void cb_write32(uint32_t addr, uint32_t val, void* user_data) {
    static_cast<StandaloneRuntime*>(user_data)->write32(addr, val);
}

bool cb_is_slave_active(void* /*user_data*/) { return false; }
bool cb_is_dma_active(void* /*user_data*/) { return false; }
bool cb_is_irq_pending(void* /*user_data*/) { return false; }

} // anonymous namespace

StandaloneRuntime::StandaloneRuntime() {
    high_work_ram_.resize(0x100000, 0);
    low_work_ram_.resize(0x100000, 0);
    framebuffer_.resize(320 * 224, 0);
    audio_buffer_.resize(735 * 2, 0);
    native_dispatcher_.set_mode(THOR_NATIVE_MODE_NATIVE_OVERRIDE);
}

void StandaloneRuntime::boot() {
    master_cpu_ = {};
    master_cpu_.pc = 0x06004000u;
    master_cpu_.r[0] = 0x06002EDCu;
    master_cpu_.r[1] = 0x06004000u;
    master_cpu_.r[4] = 0x00002650u;
    master_cpu_.r[15] = 0x06001000u;
    master_cpu_.sr = 0x00000001u;
    master_cpu_.vbr = 0x06000000u;
    master_cpu_.pr = 0x06002244u;

    native_system_.reset();
    metrics_ = {};
}

bool StandaloneRuntime::load_module(uint32_t vma, const uint8_t* data, size_t size) {
    if (!data || size == 0) return false;

    if (is_high_work_ram(vma)) {
        uint32_t offset = vma & 0x000FFFFFu;
        if (offset + size > high_work_ram_.size()) return false;
        std::memcpy(high_work_ram_.data() + offset, data, size);
        return true;
    }
    if (is_low_work_ram(vma)) {
        uint32_t offset = vma & 0x000FFFFFu;
        if (offset + size > low_work_ram_.size()) return false;
        std::memcpy(low_work_ram_.data() + offset, data, size);
        return true;
    }
    return false;
}

bool StandaloneRuntime::is_high_work_ram(uint32_t addr) const noexcept {
    uint32_t masked = addr & 0x1FFFFFFFu;
    return (masked >= 0x06000000u && masked < 0x06100000u);
}

bool StandaloneRuntime::is_low_work_ram(uint32_t addr) const noexcept {
    uint32_t masked = addr & 0x1FFFFFFFu;
    return (masked >= 0x00200000u && masked < 0x00300000u);
}

bool StandaloneRuntime::is_hardware_mmio(uint32_t addr) const noexcept {
    uint32_t masked = addr & 0x1FFFFFFFu;
    return (masked >= 0x05A00000u && masked < 0x06000000u);
}

uint8_t StandaloneRuntime::read8(uint32_t addr) {
    if (is_high_work_ram(addr)) {
        return high_work_ram_[addr & 0x000FFFFFu];
    }
    if (is_low_work_ram(addr)) {
        return low_work_ram_[addr & 0x000FFFFFu];
    }
    if (is_hardware_mmio(addr)) {
        uint16_t w = native_system_.read_mmio_u16(addr & ~1u);
        return (addr & 1u) ? static_cast<uint8_t>(w & 0xFF) : static_cast<uint8_t>(w >> 8);
    }
    return 0;
}

uint16_t StandaloneRuntime::read16(uint32_t addr) {
    if (is_high_work_ram(addr)) {
        uint32_t off = addr & 0x000FFFFEu;
        return static_cast<uint16_t>((static_cast<uint16_t>(high_work_ram_[off]) << 8) | high_work_ram_[off + 1]);
    }
    if (is_low_work_ram(addr)) {
        uint32_t off = addr & 0x000FFFFEu;
        return static_cast<uint16_t>((static_cast<uint16_t>(low_work_ram_[off]) << 8) | low_work_ram_[off + 1]);
    }
    if (is_hardware_mmio(addr)) {
        return native_system_.read_mmio_u16(addr);
    }
    return 0;
}

uint32_t StandaloneRuntime::read32(uint32_t addr) {
    if (is_high_work_ram(addr)) {
        uint32_t off = addr & 0x000FFFFCu;
        return (static_cast<uint32_t>(high_work_ram_[off]) << 24) |
               (static_cast<uint32_t>(high_work_ram_[off + 1]) << 16) |
               (static_cast<uint32_t>(high_work_ram_[off + 2]) << 8) |
               static_cast<uint32_t>(high_work_ram_[off + 3]);
    }
    if (is_low_work_ram(addr)) {
        uint32_t off = addr & 0x000FFFFCu;
        return (static_cast<uint32_t>(low_work_ram_[off]) << 24) |
               (static_cast<uint32_t>(low_work_ram_[off + 1]) << 16) |
               (static_cast<uint32_t>(low_work_ram_[off + 2]) << 8) |
               static_cast<uint32_t>(low_work_ram_[off + 3]);
    }
    if (is_hardware_mmio(addr)) {
        return native_system_.read_mmio_u32(addr);
    }
    return 0;
}

uint8_t StandaloneRuntime::peek8(uint32_t addr) const {
    if (is_high_work_ram(addr)) return high_work_ram_[addr & 0x000FFFFFu];
    if (is_low_work_ram(addr)) return low_work_ram_[addr & 0x000FFFFFu];
    return 0;
}

void StandaloneRuntime::write8(uint32_t addr, uint8_t val) {
    if (is_high_work_ram(addr)) {
        high_work_ram_[addr & 0x000FFFFFu] = val;
    } else if (is_low_work_ram(addr)) {
        low_work_ram_[addr & 0x000FFFFFu] = val;
    } else if (is_hardware_mmio(addr)) {
        uint16_t old_w = native_system_.read_mmio_u16(addr & ~1u);
        uint16_t new_w = (addr & 1u) ? ((old_w & 0xFF00u) | val) : ((old_w & 0x00FFu) | (static_cast<uint16_t>(val) << 8));
        (void)native_system_.write_mmio_u16(addr & ~1u, new_w);
    }
}

void StandaloneRuntime::write16(uint32_t addr, uint16_t val) {
    if (is_high_work_ram(addr)) {
        uint32_t off = addr & 0x000FFFFEu;
        high_work_ram_[off] = static_cast<uint8_t>(val >> 8);
        high_work_ram_[off + 1] = static_cast<uint8_t>(val);
    } else if (is_low_work_ram(addr)) {
        uint32_t off = addr & 0x000FFFFEu;
        low_work_ram_[off] = static_cast<uint8_t>(val >> 8);
        low_work_ram_[off + 1] = static_cast<uint8_t>(val);
    } else if (is_hardware_mmio(addr)) {
        (void)native_system_.write_mmio_u16(addr, val);
    }
}

void StandaloneRuntime::write32(uint32_t addr, uint32_t val) {
    if (is_high_work_ram(addr)) {
        uint32_t off = addr & 0x000FFFFCu;
        high_work_ram_[off] = static_cast<uint8_t>(val >> 24);
        high_work_ram_[off + 1] = static_cast<uint8_t>(val >> 16);
        high_work_ram_[off + 2] = static_cast<uint8_t>(val >> 8);
        high_work_ram_[off + 3] = static_cast<uint8_t>(val);
    } else if (is_low_work_ram(addr)) {
        uint32_t off = addr & 0x000FFFFCu;
        low_work_ram_[off] = static_cast<uint8_t>(val >> 24);
        low_work_ram_[off + 1] = static_cast<uint8_t>(val >> 16);
        low_work_ram_[off + 2] = static_cast<uint8_t>(val >> 8);
        low_work_ram_[off + 3] = static_cast<uint8_t>(val);
    } else if (is_hardware_mmio(addr)) {
        (void)native_system_.write_mmio_u32(addr, val);
    }
}

bool StandaloneRuntime::step() {
    ThorHardwareCallbacks cb{
        .read8 = cb_read8,
        .read16 = cb_read16,
        .read32 = cb_read32,
        .write8 = cb_write8,
        .write16 = cb_write16,
        .write32 = cb_write32,
        .is_slave_active = cb_is_slave_active,
        .is_dma_active = cb_is_dma_active,
        .is_irq_pending = cb_is_irq_pending,
        .user_data = this
    };

    ThorCpuRegs live_regs{};
    for (int i = 0; i < 16; ++i) live_regs.r[i] = master_cpu_.r[i];
    live_regs.pc = master_cpu_.pc;
    live_regs.sr = master_cpu_.sr;
    live_regs.pr = master_cpu_.pr;
    live_regs.gbr = master_cpu_.gbr;
    live_regs.vbr = master_cpu_.vbr;
    live_regs.mach = master_cpu_.mach;
    live_regs.macl = master_cpu_.macl;

    uint32_t target_pc = 0;
    uint32_t cycles_adv = 0;
    uint32_t instrs_adv = 0;
    bool handled = native_dispatcher_.dispatch_step(master_cpu_.pc, live_regs, target_pc, cycles_adv, instrs_adv, cb);
    if (handled) {
        for (int i = 0; i < 16; ++i) master_cpu_.r[i] = live_regs.r[i];
        master_cpu_.pc = target_pc;
        master_cpu_.sr = live_regs.sr;
        master_cpu_.pr = live_regs.pr;
        master_cpu_.gbr = live_regs.gbr;
        master_cpu_.vbr = live_regs.vbr;
        master_cpu_.mach = live_regs.mach;
        master_cpu_.macl = live_regs.macl;

        metrics_.native_instructions += instrs_adv;
        metrics_.native_cycles += cycles_adv;
        metrics_.total_cycles += cycles_adv;
        return true;
    }

    // Fallback: decode and execute instruction
    auto step_res = thor::sh2::step_sh2(master_cpu_, *this);
    if (step_res.status != thor::sh2::ExecutionResult::SUCCESS) {
        return false;
    }

    uint32_t cost = 1u;
    metrics_.fallback_instructions++;
    metrics_.fallback_cycles += cost;
    metrics_.total_cycles += cost;
    return true;
}

uint32_t StandaloneRuntime::run_cycles(uint32_t max_cycles) {
    uint32_t start = static_cast<uint32_t>(metrics_.total_cycles);
    while (static_cast<uint32_t>(metrics_.total_cycles - start) < max_cycles) {
        if (!step()) break;
    }
    return static_cast<uint32_t>(metrics_.total_cycles - start);
}

void StandaloneRuntime::run_frame() {
    run_cycles(100);
    native_system_.render_frame(framebuffer_, 320, 224);
    native_system_.render_audio(audio_buffer_, 735);
    metrics_.frames_rendered++;
    metrics_.audio_buffers_rendered++;
}

} // namespace thor::runtime
