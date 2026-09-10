#include <iostream>
#include <string>
#include "thor/hw/scsp.hpp"

using namespace thor::hw;

int main() {
    std::cout << "[TEST] Running SCSP Subsystem Contract Tests...\n";

    ScspEngine engine;
    if (engine.driver_status() != ScspDriverStatus::READY ||
        engine.master_volume() != 127 ||
        engine.current_bgm() != 0 ||
        engine.pending_command_count() != 0) {
        std::cerr << "Engine initial state failure\n";
        return 1;
    }

    // 1. Enqueue commands up to capacity
    for (uint16_t i = 0; i < SCSP_RING_BUFFER_CAPACITY; ++i) {
        ScspCommandPacket cmd{};
        cmd.sequence_id = static_cast<uint16_t>(i + 1);
        cmd.command_type = ScspCommandType::BGM_PLAY;
        cmd.target_id = static_cast<uint8_t>(i + 1);
        if (!engine.enqueue_command(cmd)) {
            std::cerr << "Enqueue failed at index " << i << "\n";
            return 2;
        }
    }
    if (engine.pending_command_count() != SCSP_RING_BUFFER_CAPACITY) {
        std::cerr << "Pending count mismatch\n";
        return 3;
    }

    // Queue is full, next enqueue must fail fail-closed
    ScspCommandPacket overflow_cmd{};
    overflow_cmd.command_type = ScspCommandType::BGM_PLAY;
    if (engine.enqueue_command(overflow_cmd)) {
        std::cerr << "Overflow enqueue should have failed\n";
        return 4;
    }

    // 2. Process next command: BGM_PLAY track 1
    if (!engine.process_next_command() ||
        engine.current_bgm() != 1 ||
        engine.driver_status() != ScspDriverStatus::PLAYING ||
        engine.pending_command_count() != SCSP_RING_BUFFER_CAPACITY - 1) {
        std::cerr << "process_next_command failure\n";
        return 5;
    }

    // Drain remaining
    engine.process_all_pending();
    if (engine.pending_command_count() != 0 || engine.current_bgm() != 16) {
        std::cerr << "process_all_pending failure\n";
        return 6;
    }

    // 3. Command transitions: Pause, Resume, Stop
    ScspCommandPacket pause_cmd{};
    pause_cmd.command_type = ScspCommandType::BGM_PAUSE;
    if (!engine.enqueue_command(pause_cmd)) return 7;
    engine.process_next_command();
    if (engine.driver_status() != ScspDriverStatus::PAUSED) {
        std::cerr << "Pause failure\n";
        return 7;
    }

    ScspCommandPacket resume_cmd{};
    resume_cmd.command_type = ScspCommandType::BGM_RESUME;
    if (!engine.enqueue_command(resume_cmd)) return 8;
    engine.process_next_command();
    if (engine.driver_status() != ScspDriverStatus::PLAYING) {
        std::cerr << "Resume failure\n";
        return 8;
    }

    ScspCommandPacket stop_cmd{};
    stop_cmd.command_type = ScspCommandType::BGM_STOP;
    if (!engine.enqueue_command(stop_cmd)) return 9;
    engine.process_next_command();
    if (engine.driver_status() != ScspDriverStatus::STOPPED || engine.current_bgm() != 0) {
        std::cerr << "Stop failure\n";
        return 9;
    }

    // 4. SFX allocation
    ScspCommandPacket sfx_cmd{};
    sfx_cmd.command_type = ScspCommandType::SFX_PLAY;
    sfx_cmd.target_id = 42;
    sfx_cmd.volume = 90;
    sfx_cmd.pan = -20;
    if (!engine.enqueue_command(sfx_cmd)) return 10;
    engine.process_next_command();
    if (!engine.slot(16).enabled ||
        engine.slot(16).volume != 90 ||
        engine.slot(16).pan != -20) {
        std::cerr << "SFX allocation failure\n";
        return 10;
    }

    // SFX Stop clears slots
    ScspCommandPacket sfx_stop{};
    sfx_stop.command_type = ScspCommandType::SFX_STOP;
    if (!engine.enqueue_command(sfx_stop)) return 11;
    engine.process_next_command();
    if (engine.slot(16).enabled) {
        std::cerr << "SFX stop failure\n";
        return 11;
    }

    // 5. Master volume clamping
    ScspCommandPacket vol_cmd{};
    vol_cmd.command_type = ScspCommandType::MASTER_VOLUME;
    vol_cmd.volume = 200;
    if (!engine.enqueue_command(vol_cmd)) return 12;
    engine.process_next_command();
    if (engine.master_volume() != 127) {
        std::cerr << "Volume clamp failure\n";
        return 12;
    }

    vol_cmd.volume = 80;
    if (!engine.enqueue_command(vol_cmd)) return 13;
    engine.process_next_command();
    if (engine.master_volume() != 80) {
        std::cerr << "Volume set failure\n";
        return 13;
    }

    // 6. Reset Driver
    ScspCommandPacket reset_cmd{};
    reset_cmd.command_type = ScspCommandType::RESET_DRIVER;
    if (!engine.enqueue_command(reset_cmd)) return 14;
    engine.process_next_command();
    if (engine.driver_status() != ScspDriverStatus::READY || engine.master_volume() != 127) {
        std::cerr << "Reset failure\n";
        return 14;
    }

    // 7. String representations
    if (std::string(scsp_command_type_to_string(ScspCommandType::BGM_PLAY)) != "BGM_PLAY" ||
        std::string(scsp_driver_status_to_string(ScspDriverStatus::PLAYING)) != "PLAYING") {
        std::cerr << "string conversion failure\n";
        return 15;
    }

    std::cout << "[TEST] SCSP Subsystem Contract Tests PASSED.\n";
    return 0;
}
