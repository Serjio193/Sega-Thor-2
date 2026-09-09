#pragma once

#include <cstdlib>
#include <iostream>

#define THOR_ASSERT(expr) \
    do { \
        if (!(expr)) { \
            std::cerr << "[FAIL] Assertion failed: (" #expr ") at " << __FILE__ << ":" << __LINE__ << std::endl; \
            std::abort(); \
        } \
    } while (false)
