cmake_minimum_required(VERSION 3.20)
project(thor_sh2 CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if (CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

include_directories(include .)

add_library(thor_sh2 STATIC
    src/sh2/sh2_decoder.cpp
    src/sh2/sh2_executor.cpp
    src/sh2/sh2_block.cpp
)

add_library(thor_recomp STATIC
    src/recomp/block_identity.cpp
    src/recomp/block_compiler.cpp
    src/recomp/shadow_checker.cpp
    src/recomp/mutation_harness.cpp
    src/recomp/block_exit.cpp
    src/recomp/block_memory.cpp
)
target_link_libraries(thor_recomp PUBLIC thor_sh2)

# Tool to mechanically compile a basic block to C++20
add_executable(generate_sh2_block tools/recomp/generate_sh2_block.cpp)
target_link_libraries(generate_sh2_block PRIVATE thor_recomp thor_sh2)

# Tool to export generic Thor-decoder-backed SH-2 Assembly IR
add_executable(export_sh2_asm_ir tools/asm/export_sh2_asm_ir.cpp)
target_link_libraries(export_sh2_asm_ir PRIVATE thor_sh2)

# Build-time mechanical C++20 generation for bb_06004000
set(GENERATED_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated")
file(MAKE_DIRECTORY "${GENERATED_DIR}")
set(GEN_BB0_HEADER "${GENERATED_DIR}/bb_06004000.hpp")
set(GEN_BB0_SOURCE "${GENERATED_DIR}/bb_06004000.cpp")

add_custom_command(
    OUTPUT "${GEN_BB0_HEADER}" "${GEN_BB0_SOURCE}"
    COMMAND generate_sh2_block "bb_06004000" "${GEN_BB0_HEADER}" "${GEN_BB0_SOURCE}"
    DEPENDS generate_sh2_block
    COMMENT "Mechanically generating C++20 for bb_06004000"
    VERBATIM
)

# Generated native candidate library - STRICT LINK-TIME ISOLATION:
# Does NOT link against thor_sh2 (decoder/executor/interpreter).
add_library(thor_generated_bb_06004000 STATIC
    "${GEN_BB0_SOURCE}"
    "${GEN_BB0_HEADER}"
)
target_include_directories(thor_generated_bb_06004000 PUBLIC include "${GENERATED_DIR}")

# Build-time mechanical C++20 generation for bb_06004280
set(GEN_BB4280_HEADER "${GENERATED_DIR}/bb_06004280.hpp")
set(GEN_BB4280_SOURCE "${GENERATED_DIR}/bb_06004280.cpp")

add_custom_command(
    OUTPUT "${GEN_BB4280_HEADER}" "${GEN_BB4280_SOURCE}"
    COMMAND generate_sh2_block "bb_06004280" "${GEN_BB4280_HEADER}" "${GEN_BB4280_SOURCE}"
    DEPENDS generate_sh2_block
    COMMENT "Mechanically generating C++20 for bb_06004280"
    VERBATIM
)

add_library(thor_generated_bb_06004280 STATIC
    "${GEN_BB4280_SOURCE}"
    "${GEN_BB4280_HEADER}"
)
target_include_directories(thor_generated_bb_06004280 PUBLIC include "${GENERATED_DIR}")

enable_testing()

add_executable(test_sh2_decoder tests/sh2/test_sh2_decoder.cpp)
target_link_libraries(test_sh2_decoder PRIVATE thor_sh2)
add_test(NAME test_sh2_decoder COMMAND test_sh2_decoder)

add_executable(test_sh2_l0_semantics tests/sh2/test_sh2_l0_semantics.cpp)
target_link_libraries(test_sh2_l0_semantics PRIVATE thor_sh2)
add_test(NAME test_sh2_l0_semantics COMMAND test_sh2_l0_semantics)

add_executable(test_sh2_oracle_vector tests/sh2/test_sh2_oracle_vector.cpp)
target_link_libraries(test_sh2_oracle_vector PRIVATE thor_sh2)
add_test(NAME test_sh2_oracle_vector COMMAND test_sh2_oracle_vector)

add_executable(test_sh2_block tests/sh2/test_sh2_block.cpp)
target_link_libraries(test_sh2_block PRIVATE thor_sh2)
add_test(NAME test_sh2_block COMMAND test_sh2_block)

# Executable identity guard test suite
add_executable(test_executable_identity tests/recomp/test_executable_identity.cpp)
target_link_libraries(test_executable_identity PRIVATE thor_recomp)
add_test(NAME test_executable_identity COMMAND test_executable_identity)

# Mechanical block compiler test suite
add_executable(test_sh2_block_compiler tests/recomp/test_sh2_block_compiler.cpp)
target_link_libraries(test_sh2_block_compiler PRIVATE thor_recomp thor_sh2)
add_test(NAME test_sh2_block_compiler COMMAND test_sh2_block_compiler)

# Link isolation verification: links ONLY against generated library
add_executable(test_generated_link_isolation tests/recomp/test_generated_link_isolation.cpp)
target_link_libraries(test_generated_link_isolation PRIVATE thor_generated_bb_06004000 thor_generated_bb_06004280)
target_include_directories(test_generated_link_isolation PRIVATE "${GENERATED_DIR}")
add_test(NAME test_generated_link_isolation COMMAND test_generated_link_isolation)

# V-07A transition proof test suite
add_executable(test_v07a_transition tests/recomp/test_v07a_transition.cpp)
target_link_libraries(test_v07a_transition PRIVATE thor_generated_bb_06004000 thor_recomp thor_sh2)
target_include_directories(test_v07a_transition PRIVATE "${GENERATED_DIR}")
add_test(NAME test_v07a_transition COMMAND test_v07a_transition)

# V-07B positive shadow comparison test suite
add_executable(test_shadow_positive tests/recomp/test_shadow_positive.cpp)
target_link_libraries(test_shadow_positive PRIVATE thor_generated_bb_06004000 thor_generated_bb_06004280 thor_recomp thor_sh2)
target_include_directories(test_shadow_positive PRIVATE "${GENERATED_DIR}")
add_test(NAME test_shadow_positive COMMAND test_shadow_positive)

# V-07B negative controls test suite (100% fault classes detected)
add_executable(test_shadow_negative tests/recomp/test_shadow_negative.cpp)
target_link_libraries(test_shadow_negative PRIVATE thor_recomp thor_sh2)
add_test(NAME test_shadow_negative COMMAND test_shadow_negative)

# Pre-state isolation and anti-aliasing proof test suite
add_executable(test_shadow_isolation tests/recomp/test_shadow_isolation.cpp)
target_link_libraries(test_shadow_isolation PRIVATE thor_generated_bb_06004000 thor_recomp thor_sh2)
target_include_directories(test_shadow_isolation PRIVATE "${GENERATED_DIR}")
add_test(NAME test_shadow_isolation COMMAND test_shadow_isolation)

# Authoritative native execution & dispatch library
add_library(thor_native STATIC
    src/recomp/native_dispatcher.cpp
)
target_link_libraries(thor_native PUBLIC thor_recomp thor_generated_bb_06004000 thor_generated_bb_06004280)
target_include_directories(thor_native PUBLIC include "${GENERATED_DIR}")

# Shared plugin for emulator oracle dynamic integration
add_library(thor_native_plugin SHARED
    src/recomp/native_dispatcher.cpp
)
target_link_libraries(thor_native_plugin PUBLIC thor_recomp thor_generated_bb_06004000 thor_generated_bb_06004280)
target_include_directories(thor_native_plugin PUBLIC include "${GENERATED_DIR}")
set_target_properties(thor_native_plugin PROPERTIES OUTPUT_NAME "thor_native")

# V-07C native dispatcher and fail-closed fallback test suite
add_executable(test_native_dispatcher tests/recomp/test_native_dispatcher.cpp)
target_link_libraries(test_native_dispatcher PRIVATE thor_native)
target_include_directories(test_native_dispatcher PRIVATE "${GENERATED_DIR}")
add_test(NAME test_native_dispatcher COMMAND test_native_dispatcher)

# D9.4 native indirect dispatcher, dynamic continuation, and block mask test suite
add_executable(test_native_indirect tests/recomp/test_native_indirect.cpp)
target_link_libraries(test_native_indirect PRIVATE thor_native)
target_include_directories(test_native_indirect PRIVATE "${GENERATED_DIR}")
add_test(NAME test_native_indirect COMMAND test_native_indirect)

# M-02 guest mutation harness and fault injection test suite
add_executable(test_mutation_harness tests/recomp/test_mutation_harness.cpp)
target_link_libraries(test_mutation_harness PRIVATE thor_native thor_recomp thor_sh2)
target_include_directories(test_mutation_harness PRIVATE "${GENERATED_DIR}")
add_test(NAME test_mutation_harness COMMAND test_mutation_harness)

# D9.2 block exit descriptor and runtime exit resolution test suite
add_executable(test_block_exit tests/recomp/test_block_exit.cpp)
target_link_libraries(test_block_exit PRIVATE thor_recomp thor_sh2)
add_test(NAME test_block_exit COMMAND test_block_exit)

# D9.2 declarative memory dependency contract test suite
add_executable(test_block_memory tests/recomp/test_block_memory.cpp)
target_link_libraries(test_block_memory PRIVATE thor_recomp thor_sh2)
add_test(NAME test_block_memory COMMAND test_block_memory)

# M-07 SaturnRecomp reference corpus and negative controls test suite
find_package(Python3 COMPONENTS Interpreter)
if (Python3_Interpreter_FOUND)
    add_test(NAME test_m07_reference COMMAND Python3::Interpreter "${CMAKE_CURRENT_SOURCE_DIR}/tests/recomp/test_m07_reference.py")
    add_test(NAME test_post_d8_closure COMMAND Python3::Interpreter "${CMAKE_CURRENT_SOURCE_DIR}/tests/recomp/test_post_d8_closure.py")
    add_test(NAME test_d9_plan COMMAND Python3::Interpreter "${CMAKE_CURRENT_SOURCE_DIR}/tests/recomp/test_d9_plan.py")
    add_test(NAME test_asm_roundtrip COMMAND Python3::Interpreter "${CMAKE_CURRENT_SOURCE_DIR}/tests/asm/test_asm_roundtrip.py")
    add_test(NAME test_full_module_asm COMMAND Python3::Interpreter "${CMAKE_CURRENT_SOURCE_DIR}/tests/asm/test_full_module_asm.py")
endif()
