#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "thor/sh2/sh2_decoder.hpp"
#include "thor/sh2/sh2_types.hpp"

namespace {

struct RangeRecord {
    size_t offset_start = 0;
    size_t offset_end_exclusive = 0;
    uint32_t runtime_start = 0;
    uint32_t runtime_end_exclusive = 0;
    std::string evidence_classification;
    std::string assembly_representation;
};

std::string hex_str(uint32_t val, int width = 8) {
    std::ostringstream ss;
    ss << "0x" << std::uppercase << std::hex << std::setw(width) << std::setfill('0') << val;
    return ss.str();
}

std::vector<uint8_t> read_file(const std::string& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "FAIL_CLOSED: Cannot open file: " << path << "\n";
        return {};
    }
    file.seekg(0, std::ios::end);
    const size_t sz = static_cast<size_t>(file.tellg());
    file.seekg(0, std::ios::beg);
    std::vector<uint8_t> buf(sz);
    file.read(reinterpret_cast<char*>(buf.data()), sz);
    return buf;
}

std::string extract_json_string(const std::string& src, const std::string& key) {
    auto pos = src.find("\"" + key + "\"");
    if (pos == std::string::npos) return "";
    auto colon = src.find(':', pos);
    if (colon == std::string::npos) return "";
    auto first_quote = src.find('"', colon);
    if (first_quote == std::string::npos) return "";
    auto second_quote = src.find('"', first_quote + 1);
    if (second_quote == std::string::npos) return "";
    return src.substr(first_quote + 1, second_quote - first_quote - 1);
}

int64_t extract_json_int(const std::string& src, const std::string& key) {
    auto pos = src.find("\"" + key + "\"");
    if (pos == std::string::npos) return -1;
    auto colon = src.find(':', pos);
    if (colon == std::string::npos) return -1;
    size_t start = colon + 1;
    while (start < src.size() && (src[start] == ' ' || src[start] == '\t' || src[start] == '\n' || src[start] == '\r')) {
        start++;
    }
    size_t end = start;
    while (end < src.size() && ((src[end] >= '0' && src[end] <= '9') || src[end] == '-')) {
        end++;
    }
    if (start == end) return -1;
    try {
        return std::stoll(src.substr(start, end - start));
    } catch (...) {
        return -1;
    }
}

bool parse_manifest_ranges(const std::string& json_text, std::vector<RangeRecord>& out_ranges) {
    auto ranges_pos = json_text.find("\"ranges\"");
    if (ranges_pos == std::string::npos) {
        std::cerr << "FAIL_CLOSED: \"ranges\" key missing in manifest\n";
        return false;
    }
    auto open_bracket = json_text.find('[', ranges_pos);
    if (open_bracket == std::string::npos) return false;
    auto close_bracket = json_text.find(']', open_bracket);
    if (close_bracket == std::string::npos) return false;

    size_t cur = open_bracket;
    while (cur < close_bracket) {
        auto obj_start = json_text.find('{', cur);
        if (obj_start == std::string::npos || obj_start > close_bracket) break;
        auto obj_end = json_text.find('}', obj_start);
        if (obj_end == std::string::npos || obj_end > close_bracket) break;

        std::string block = json_text.substr(obj_start, obj_end - obj_start + 1);
        RangeRecord rec;
        rec.offset_start = static_cast<size_t>(extract_json_int(block, "offset_start"));
        rec.offset_end_exclusive = static_cast<size_t>(extract_json_int(block, "offset_end_exclusive"));

        std::string r_start_str = extract_json_string(block, "runtime_start");
        std::string r_end_str = extract_json_string(block, "runtime_end_exclusive");
        if (!r_start_str.empty()) {
            rec.runtime_start = static_cast<uint32_t>(std::stoul(r_start_str, nullptr, 0));
        }
        if (!r_end_str.empty()) {
            rec.runtime_end_exclusive = static_cast<uint32_t>(std::stoul(r_end_str, nullptr, 0));
        }

        rec.evidence_classification = extract_json_string(block, "evidence_classification");
        rec.assembly_representation = extract_json_string(block, "assembly_representation");

        out_ranges.push_back(rec);
        cur = obj_end + 1;
    }
    return !out_ranges.empty();
}

} // namespace

int main(int argc, char* argv[]) {
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0] << " <canonical_bin> <rebuilt_bin> <manifest_json>\n";
        return 1;
    }

    const std::string canonical_path = argv[1];
    const std::string rebuilt_path = argv[2];
    const std::string manifest_path = argv[3];

    const auto canonical_bytes = read_file(canonical_path);
    const auto rebuilt_bytes = read_file(rebuilt_path);

    if (canonical_bytes.empty() || rebuilt_bytes.empty()) {
        std::cerr << "FAIL_CLOSED: Empty or unreadable input binary\n";
        return 1;
    }

    if (canonical_bytes.size() != rebuilt_bytes.size()) {
        std::cerr << "FAIL_CLOSED: Binary size mismatch: canonical="
                  << canonical_bytes.size() << " rebuilt=" << rebuilt_bytes.size() << "\n";
        return 1;
    }

    // Byte-exact check across all bytes
    for (size_t i = 0; i < canonical_bytes.size(); ++i) {
        if (canonical_bytes[i] != rebuilt_bytes[i]) {
            std::cerr << "FAIL_CLOSED: Byte mismatch at offset 0x" << std::hex << i
                      << ": canonical=0x" << static_cast<int>(canonical_bytes[i])
                      << " rebuilt=0x" << static_cast<int>(rebuilt_bytes[i]) << "\n";
            return 1;
        }
    }

    // Read manifest
    std::ifstream mfile(manifest_path);
    if (!mfile.is_open()) {
        std::cerr << "FAIL_CLOSED: Cannot open manifest: " << manifest_path << "\n";
        return 1;
    }
    std::stringstream buffer;
    buffer << mfile.rdbuf();
    const std::string manifest_text = buffer.str();

    std::vector<RangeRecord> ranges;
    if (!parse_manifest_ranges(manifest_text, ranges)) {
        std::cerr << "FAIL_CLOSED: Failed to parse ranges from manifest: " << manifest_path << "\n";
        return 1;
    }

    // Partition integrity check
    size_t expected_offset = 0;
    for (size_t i = 0; i < ranges.size(); ++i) {
        const auto& r = ranges[i];
        if (r.offset_start != expected_offset) {
            std::cerr << "FAIL_CLOSED: Range gap/overlap at index " << i
                      << ": expected offset " << expected_offset << ", got " << r.offset_start << "\n";
            return 1;
        }
        if (r.offset_end_exclusive <= r.offset_start) {
            std::cerr << "FAIL_CLOSED: Inverted range at index " << i << "\n";
            return 1;
        }
        expected_offset = r.offset_end_exclusive;
    }
    if (expected_offset != canonical_bytes.size()) {
        std::cerr << "FAIL_CLOSED: Ranges do not span entire file: spanned="
                  << expected_offset << " file=" << canonical_bytes.size() << "\n";
        return 1;
    }

    // Instruction verification using thor::sh2::decode_sh2
    size_t proven_insns = 0;
    size_t pending_insns = 0;
    size_t raw_unknown_bytes = 0;

    for (const auto& r : ranges) {
        if (r.assembly_representation == "MNEMONIC_PROVEN") {
            for (size_t off = r.offset_start; off < r.offset_end_exclusive; off += 2) {
                const uint32_t pc = r.runtime_start + static_cast<uint32_t>(off - r.offset_start);
                const uint16_t op_orig = static_cast<uint16_t>((canonical_bytes[off] << 8) | canonical_bytes[off + 1]);
                const uint16_t op_rebuilt = static_cast<uint16_t>((rebuilt_bytes[off] << 8) | rebuilt_bytes[off + 1]);

                if (op_orig != op_rebuilt) {
                    std::cerr << "FAIL_CLOSED: Opcode mismatch at PC " << hex_str(pc) << "\n";
                    return 1;
                }

                const auto insn_orig = thor::sh2::decode_sh2(op_orig, pc);
                const auto insn_rebuilt = thor::sh2::decode_sh2(op_rebuilt, pc);

                if (!insn_orig.is_valid() || !insn_rebuilt.is_valid()) {
                    std::cerr << "FAIL_CLOSED: MNEMONIC_PROVEN opcode invalid in thor::sh2 decoder at PC "
                              << hex_str(pc) << " (opcode 0x" << std::hex << op_orig << ")\n";
                    return 1;
                }

                if (insn_orig.id != insn_rebuilt.id ||
                    insn_orig.rn != insn_rebuilt.rn ||
                    insn_orig.rm != insn_rebuilt.rm ||
                    insn_orig.disp != insn_rebuilt.disp ||
                    insn_orig.flow != insn_rebuilt.flow ||
                    insn_orig.has_delay_slot != insn_rebuilt.has_delay_slot) {
                    std::cerr << "FAIL_CLOSED: Instruction semantic mismatch at PC " << hex_str(pc) << "\n";
                    return 1;
                }
                proven_insns++;
            }
        } else if (r.assembly_representation == "RAW_CODE_PENDING_DECODE") {
            pending_insns += (r.offset_end_exclusive - r.offset_start) / 2;
        } else {
            raw_unknown_bytes += (r.offset_end_exclusive - r.offset_start);
        }
    }

    std::cout << "=== THOR SH-2 REBUILT MODULE VERIFICATION: PASS ===\n";
    std::cout << "  Canonical bytes:  " << canonical_bytes.size() << "\n";
    std::cout << "  Rebuilt bytes:    " << rebuilt_bytes.size() << "\n";
    std::cout << "  Ranges verified:  " << ranges.size() << " (exhaustive partition)\n";
    std::cout << "  Proven insns:     " << proven_insns << " (decoded with thor::sh2::decode_sh2)\n";
    std::cout << "  Pending insns:    " << pending_insns << " (raw code pending decode)\n";
    std::cout << "  Raw unknown:      " << raw_unknown_bytes << " bytes\n";
    return 0;
}
