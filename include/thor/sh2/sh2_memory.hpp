#pragma once

#include <cstdint>
#include <map>
#include <vector>

namespace thor::sh2 {

enum class MemoryAccessKind : uint8_t {
    READ = 0,
    WRITE
};

struct MemoryLogEntry {
    MemoryAccessKind kind = MemoryAccessKind::READ;
    uint32_t address = 0;
    uint32_t value = 0;
    uint8_t size_bytes = 0; // 1, 2, or 4

    bool operator==(const MemoryLogEntry& other) const noexcept = default;
};

/// Abstract interface for explicit SH-2 big-endian memory access.
class ISh2Memory {
public:
    virtual ~ISh2Memory() = default;

    virtual uint8_t read8(uint32_t addr) = 0;
    virtual uint16_t read16(uint32_t addr) = 0;
    virtual uint32_t read32(uint32_t addr) = 0;

    virtual void write8(uint32_t addr, uint8_t val) = 0;
    virtual void write16(uint32_t addr, uint16_t val) = 0;
    virtual void write32(uint32_t addr, uint32_t val) = 0;
};

/// Sparse test memory harness with explicit big-endian order and access logging.
class Sh2FlatMemory : public ISh2Memory {
public:
    uint8_t read8(uint32_t addr) override {
        const uint8_t val = data_.contains(addr) ? data_[addr] : 0u;
        log_.push_back({MemoryAccessKind::READ, addr, val, 1});
        return val;
    }

    uint16_t read16(uint32_t addr) override {
        const uint8_t b0 = data_.contains(addr) ? data_[addr] : 0u;
        const uint8_t b1 = data_.contains(addr + 1) ? data_[addr + 1] : 0u;
        const uint16_t val = static_cast<uint16_t>((static_cast<uint16_t>(b0) << 8) | b1);
        log_.push_back({MemoryAccessKind::READ, addr, val, 2});
        return val;
    }

    uint32_t read32(uint32_t addr) override {
        const uint8_t b0 = data_.contains(addr) ? data_[addr] : 0u;
        const uint8_t b1 = data_.contains(addr + 1) ? data_[addr + 1] : 0u;
        const uint8_t b2 = data_.contains(addr + 2) ? data_[addr + 2] : 0u;
        const uint8_t b3 = data_.contains(addr + 3) ? data_[addr + 3] : 0u;
        const uint32_t val = (static_cast<uint32_t>(b0) << 24) |
                             (static_cast<uint32_t>(b1) << 16) |
                             (static_cast<uint32_t>(b2) << 8) |
                             static_cast<uint32_t>(b3);
        log_.push_back({MemoryAccessKind::READ, addr, val, 4});
        return val;
    }

    void write8(uint32_t addr, uint8_t val) override {
        data_[addr] = val;
        log_.push_back({MemoryAccessKind::WRITE, addr, val, 1});
    }

    void write16(uint32_t addr, uint16_t val) override {
        data_[addr] = static_cast<uint8_t>((val >> 8) & 0xFF);
        data_[addr + 1] = static_cast<uint8_t>(val & 0xFF);
        log_.push_back({MemoryAccessKind::WRITE, addr, val, 2});
    }

    void write32(uint32_t addr, uint32_t val) override {
        data_[addr] = static_cast<uint8_t>((val >> 24) & 0xFF);
        data_[addr + 1] = static_cast<uint8_t>((val >> 16) & 0xFF);
        data_[addr + 2] = static_cast<uint8_t>((val >> 8) & 0xFF);
        data_[addr + 3] = static_cast<uint8_t>(val & 0xFF);
        log_.push_back({MemoryAccessKind::WRITE, addr, val, 4});
    }

    void clear_log() noexcept {
        log_.clear();
    }

    [[nodiscard]] const std::vector<MemoryLogEntry>& log() const noexcept {
        return log_;
    }

private:
    std::map<uint32_t, uint8_t> data_;
    std::vector<MemoryLogEntry> log_;
};

} // namespace thor::sh2
