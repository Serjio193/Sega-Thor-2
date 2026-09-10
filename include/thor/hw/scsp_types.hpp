#pragma once

#include <cstdint>
#include <string>

namespace thor::hw {

enum class ScspCommandType : uint8_t {
    NONE = 0,
    BGM_PLAY,
    BGM_STOP,
    BGM_PAUSE,
    BGM_RESUME,
    BGM_VOLUME,
    BGM_FADE,
    SFX_PLAY,
    SFX_STOP,
    MASTER_VOLUME,
    RESET_DRIVER,
    COUNT
};

enum class ScspDriverStatus : uint8_t {
    STOPPED = 0,
    READY,
    PLAYING,
    PAUSED,
    ERROR_STATE
};

struct ScspCommandPacket {
    uint16_t sequence_id = 0;
    ScspCommandType command_type = ScspCommandType::NONE;
    uint8_t target_id = 0; // BGM track number or SFX ID
    uint8_t volume = 127;  // 0..127
    int8_t pan = 0;        // -64 (left) .. 0 (center) .. +63 (right)
    uint16_t param1 = 0;
    uint16_t param2 = 0;
};

struct ScspSlotConfig {
    bool enabled = false;
    bool is_pcm16 = true;
    bool loop_enabled = false;
    uint32_t start_address = 0;
    uint32_t loop_start = 0;
    uint32_t loop_end = 0;
    uint32_t sample_rate = 44100;
    uint8_t volume = 127;
    int8_t pan = 0;
};

[[nodiscard]] const char* scsp_command_type_to_string(ScspCommandType type) noexcept;
[[nodiscard]] const char* scsp_driver_status_to_string(ScspDriverStatus status) noexcept;

} // namespace thor::hw
