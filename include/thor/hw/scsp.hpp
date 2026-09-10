#pragma once

#include <cstdint>
#include <array>
#include <optional>
#include <span>
#include "thor/hw/scsp_types.hpp"

namespace thor::hw {

inline constexpr uint32_t SCSP_SOUND_RAM_SIZE = 0x80000; // 512 KB
inline constexpr size_t SCSP_NUM_SLOTS = 32;
inline constexpr size_t SCSP_RING_BUFFER_CAPACITY = 16;

class ScspEngine {
public:
    ScspEngine() noexcept;

    void reset() noexcept;

    [[nodiscard]] bool enqueue_command(const ScspCommandPacket& cmd) noexcept;
    [[nodiscard]] std::optional<ScspCommandPacket> dequeue_command() noexcept;
    bool process_next_command() noexcept;
    void process_all_pending() noexcept;

    void configure_slot(size_t slot_idx, const ScspSlotConfig& cfg) noexcept;
    [[nodiscard]] const ScspSlotConfig& slot(size_t slot_idx) const noexcept;

    [[nodiscard]] ScspDriverStatus driver_status() const noexcept { return driver_status_; }
    [[nodiscard]] uint8_t current_bgm() const noexcept { return current_bgm_; }
    [[nodiscard]] uint8_t master_volume() const noexcept { return master_volume_; }
    [[nodiscard]] size_t pending_command_count() const noexcept { return count_; }

private:
    std::array<ScspSlotConfig, SCSP_NUM_SLOTS> slots_{};
    std::array<ScspCommandPacket, SCSP_RING_BUFFER_CAPACITY> ring_buffer_{};
    size_t head_ = 0;
    size_t tail_ = 0;
    size_t count_ = 0;

    uint8_t master_volume_ = 127;
    uint8_t current_bgm_ = 0;
    ScspDriverStatus driver_status_ = ScspDriverStatus::READY;
};

} // namespace thor::hw
