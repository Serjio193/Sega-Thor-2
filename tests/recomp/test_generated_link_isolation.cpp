#include <iostream>
#include "bb_06004000.hpp"

// This test target links EXCLUSIVELY against thor_generated_bb_06004000.
// It explicitly DOES NOT link against thor_sh2 (decoder/executor/interpreter).
// If the generated code referenced decode_sh2, execute_sh2_instruction, step_sh2,
// or execute_basic_block, linking this binary would fail with undefined symbol errors.

int main() {
    thor::sh2::Sh2CpuState state{};
    thor::sh2::Sh2FlatMemory mem;

    // Call mechanically recompiled function
    thor::generated::bb_06004000(state, mem);

    // Verify expected architectural jump target
    if (state.pc != 0x06004012u) {
        std::cerr << "Unexpected exit PC: 0x" << std::hex << state.pc << "\n";
        return 1;
    }

    std::cout << "PASS: thor_generated_bb_06004000 linked with 0 interpreter dependencies.\n";
    return 0;
}
