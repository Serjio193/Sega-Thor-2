cmake_minimum_required(VERSION 3.20)
project(thor_sh2 CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if (CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

include_directories(include)

add_library(thor_sh2 STATIC
    src/sh2/sh2_decoder.cpp
    src/sh2/sh2_executor.cpp
    src/sh2/sh2_block.cpp
)

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
