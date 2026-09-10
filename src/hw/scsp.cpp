#include "thor/hw/scsp.hpp"
#include <algorithm>

namespace thor::hw {

const char* scsp_command_type_to_string(ScspCommandType type) noexcept {
    switch (type) {
    case ScspCommandType::NONE:          return "NONE";
    case ScspCommandType::BGM_PLAY:      return "BGM_PLAY";
    case ScspCommandType::BGM_STOP:      return "BGM_STOP";
    case ScspCommandType::BGM_PAUSE:     return "BGM_PAUSE";
    case ScspCommandType::BGM_RESUME:    return "BGM_RESUME";
    case ScspCommandType::BGM_VOLUME:    return "BGM_VOLUME";
    case ScspCommandType::BGM_FADE:      return "BGM_FADE";
    case ScspCommandType::SFX_PLAY:      return "SFX_PLAY";
    case ScspCommandType::SFX_STOP:      return "SFX_STOP";
    case ScspCommandType::MASTER_VOLUME: return "MASTER_VOLUME";
    case ScspCommandType::RESET_DRIVER:  return "RESET_DRIVER";
    default:                             return "UNKNOWN";
    }
}

const char* scsp_driver_status_to_string(ScspDriverStatus status) noexcept {
    switch (status) {
    case ScspDriverStatus::STOPPED:     return "STOPPED";
    case ScspDriverStatus::READY:       return "READY";
    case ScspDriverStatus::PLAYING:     return "PLAYING";
    case ScspDriverStatus::PAUSED:      return "PAUSED";
    case ScspDriverStatus::ERROR_STATE: return "ERROR_STATE";
    default:                            return "UNKNOWN";
    }
}

ScspEngine::ScspEngine() noexcept {
    reset();
}

void ScspEngine::reset() noexcept {
    for (size_t i = 0; i < slots_.size(); ++i) {
        slots_[i] = ScspSlotConfig{};
    }
    head_ = 0;
    tail_ = 0;
    count_ = 0;
    master_volume_ = 127;
    current_bgm_ = 0;
    driver_status_ = ScspDriverStatus::READY;
}

bool ScspEngine::enqueue_command(const ScspCommandPacket& cmd) noexcept {
    if (count_ >= SCSP_RING_BUFFER_CAPACITY) {
        return false;
    }
    ring_buffer_[tail_] = cmd;
    tail_ = (tail_ + 1) % SCSP_RING_BUFFER_CAPACITY;
    count_++;
    return true;
}

std::optional<ScspCommandPacket> ScspEngine::dequeue_command() noexcept {
    if (count_ == 0) {
        return std::nullopt;
    }
    const ScspCommandPacket cmd = ring_buffer_[head_];
    head_ = (head_ + 1) % SCSP_RING_BUFFER_CAPACITY;
    count_--;
    return cmd;
}

bool ScspEngine::process_next_command() noexcept {
    const auto maybe_cmd = dequeue_command();
    if (!maybe_cmd) {
        return false;
    }

    const ScspCommandPacket& cmd = *maybe_cmd;
    switch (cmd.command_type) {
    case ScspCommandType::BGM_PLAY:
        current_bgm_ = cmd.target_id;
        driver_status_ = ScspDriverStatus::PLAYING;
        break;
    case ScspCommandType::BGM_STOP:
        current_bgm_ = 0;
        driver_status_ = ScspDriverStatus::STOPPED;
        break;
    case ScspCommandType::BGM_PAUSE:
        driver_status_ = ScspDriverStatus::PAUSED;
        break;
    case ScspCommandType::BGM_RESUME:
        if (current_bgm_ != 0) {
            driver_status_ = ScspDriverStatus::PLAYING;
        }
        break;
    case ScspCommandType::MASTER_VOLUME:
        master_volume_ = std::min<uint8_t>(127u, cmd.volume);
        break;
    case ScspCommandType::SFX_PLAY: {
        // Allocate first available SFX slot (slots 16..31)
        for (size_t i = 16; i < SCSP_NUM_SLOTS; ++i) {
            if (!slots_[i].enabled) {
                slots_[i].enabled = true;
                slots_[i].volume = std::min<uint8_t>(127u, cmd.volume);
                slots_[i].pan = cmd.pan;
                break;
            }
        }
        break;
    }
    case ScspCommandType::SFX_STOP: {
        for (size_t i = 16; i < SCSP_NUM_SLOTS; ++i) {
            slots_[i].enabled = false;
        }
        break;
    }
    case ScspCommandType::RESET_DRIVER:
        reset();
        break;
    default:
        break;
    }

    return true;
}

void ScspEngine::process_all_pending() noexcept {
    while (process_next_command()) {
    }
}

void ScspEngine::configure_slot(size_t slot_idx, const ScspSlotConfig& cfg) noexcept {
    if (slot_idx < slots_.size()) {
        slots_[slot_idx] = cfg;
    }
}

const ScspSlotConfig& ScspEngine::slot(size_t slot_idx) const noexcept {
    if (slot_idx < slots_.size()) {
        return slots_[slot_idx];
    }
    static const ScspSlotConfig g_default_slot;
    return g_default_slot;
}

} // namespace thor::hw
