#pragma once

#include <optional>
#include <string>
#include "thor/sh2/sh2_block.hpp"

namespace thor::recomp {

struct GeneratedBlockCode {
    std::string header_filename;
    std::string source_filename;
    std::string header_content;
    std::string source_content;
};

/// Mechanically translates a validated Sh2BasicBlock into explicit-state C++20.
/// Fails closed (returns std::nullopt) if any instruction is unknown or unsupported.
[[nodiscard]] std::optional<GeneratedBlockCode> compile_block_to_cpp(
    const thor::sh2::Sh2BasicBlock& block,
    const std::string& function_name) noexcept;

} // namespace thor::recomp
