cmake_minimum_required(VERSION 3.20)
project(Thor2 CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Enable strict warning flags
if(MSVC)
    add_compile_options(/W4 /WX /permissive-)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

# Core SH-2 decoder & L0 semantic library
add_library(thor_sh2 STATIC
    src/sh2/sh2_decoder.cpp
    src/sh2/sh2_executor.cpp
)

target_include_directories(thor_sh2 PUBLIC
    include
)

# Test executables
enable_testing()

add_executable(test_sh2_decoder
    tests/sh2/test_sh2_decoder.cpp
)
target_link_libraries(test_sh2_decoder PRIVATE thor_sh2)
target_include_directories(test_sh2_decoder PRIVATE tests/sh2)
add_test(NAME test_sh2_decoder COMMAND test_sh2_decoder)

add_executable(test_sh2_l0_semantics
    tests/sh2/test_sh2_l0_semantics.cpp
)
target_link_libraries(test_sh2_l0_semantics PRIVATE thor_sh2)
target_include_directories(test_sh2_l0_semantics PRIVATE tests/sh2)
add_test(NAME test_sh2_l0_semantics COMMAND test_sh2_l0_semantics)

add_executable(test_sh2_oracle_vector
    tests/sh2/test_sh2_oracle_vector.cpp
)
target_link_libraries(test_sh2_oracle_vector PRIVATE thor_sh2)
target_include_directories(test_sh2_oracle_vector PRIVATE tests/sh2)
add_test(NAME test_sh2_oracle_vector COMMAND test_sh2_oracle_vector)
