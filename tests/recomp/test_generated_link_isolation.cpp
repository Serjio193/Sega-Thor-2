#include <iostream>
#include "bb_06004000.hpp"
#include "bb_06004280.hpp"

// This test target links EXCLUSIVELY against generated block libraries.
// It explicitly DOES NOT link against thor_sh2 (decoder/executor/interpreter).
// If the generated code referenced decode_sh2, execute_sh2_instruction, step_sh2,
// or execute_basic_block, linking this binary would fail with undefined symbol errors.

int main() {
    // 1. Direct block bb_06004000
    {
        thor::sh2::Sh2CpuState state{};
        thor::sh2::Sh2FlatMemory mem;
        thor::generated::bb_06004000(state, mem);
        if (state.pc != 0x06004012u) {
            std::cerr << "Unexpected exit PC for bb_06004000: 0x" << std::hex << state.pc << "\n";
            return 1;
        }
    }

    // 2. Indirect block bb_06004280
    {
        thor::sh2::Sh2CpuState state{};
        thor::sh2::Sh2FlatMemory mem;
        mem.write32(0x0600435Cu, 0x002DA000u);
        mem.write32(0x06004360u, 0x06081C20u);
        mem.write32(0x06004364u, 0x0600A0F8u);

        thor::generated::bb_06004280(state, mem);
        if (state.pc != 0x0600A0F8u || state.pr != 0x0600428Au || state.has_delayed_branch()) {
            std::cerr << "Unexpected execution state for bb_06004280: PC=0x"
                      << std::hex << state.pc << " PR=0x" << state.pr << "\n";
            return 1;
        }
    }

    std::cout << "PASS: Generated blocks linked with 0 interpreter dependencies.\n";
    return 0;
}
