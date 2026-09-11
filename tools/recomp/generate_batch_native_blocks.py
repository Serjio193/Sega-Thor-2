#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description="Batch generate native C++ blocks")
    parser.add_argument("--census", default="out/native_block_census.json")
    parser.add_argument("--generator-bin", default="build/generate_sh2_block.exe")
    parser.add_argument("--bin-0th2", default="scratch/0TH2.BIN")
    parser.add_argument("--bin-th2-low", default="scratch/th2_low_rebuilt.bin")
    parser.add_argument("--out-dir", default="build/generated/native_blocks")
    parser.add_argument("--shard-size", type=int, default=50)
    args = parser.parse_args()

    with open(args.census, "r") as f:
        census = json.load(f)

    eligible = [b for b in census["blocks"] if b["state"] in ("CODEGEN_ELIGIBLE", "GENERATED", "COMPILES", "PROMOTED")]
    print(f"Total eligible blocks to generate: {len(eligible)}")

    os.makedirs(args.out_dir, exist_ok=True)

    module_bins = {
        "0TH2.BIN": args.bin_0th2,
        "TH2.LOW": args.bin_th2_low
    }

    generated_blocks = []
    for b in eligible:
        bid = b["block_id"]
        mod = b["module"]
        bin_path = module_bins[mod]
        rt_start = b["runtime_start"]
        length = b["byte_length"]
        off = b["offset_start"]

        hdr_path = os.path.join(args.out_dir, f"{bid}.hpp")
        src_path = os.path.join(args.out_dir, f"{bid}.cpp")

        cmd = [
            args.generator_bin,
            "--block-name", bid,
            "--module", bin_path,
            "--start-pc", rt_start,
            "--length", str(length),
            "--offset", str(off),
            "--out-header", hdr_path,
            "--out-source", src_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"FAIL_CLOSED: Generation failed for {bid}: {res.stderr}")
            sys.exit(1)
        generated_blocks.append(b)

    print(f"Successfully generated {len(generated_blocks)} block headers and sources.")

    shards = []
    for i in range(0, len(generated_blocks), args.shard_size):
        shard_blocks = generated_blocks[i:i + args.shard_size]
        shard_idx = i // args.shard_size
        shard_src = os.path.join(args.out_dir, f"native_blocks_shard_{shard_idx:02d}.cpp")
        with open(shard_src, "w") as sf:
            sf.write("// GENERATED FILE - DO NOT EDIT MANUALLY\n")
            sf.write("// Sharded translation unit for native blocks\n\n")
            for b in shard_blocks:
                bid = b['block_id']
                sf.write('#include "' + bid + '.cpp"\n')
        shards.append(shard_src)

    catalog_hdr = os.path.join(args.out_dir, "native_block_catalog.hpp")
    with open(catalog_hdr, "w") as ch:
        ch.write("#pragma once\n\n")
        ch.write("// GENERATED FILE - DO NOT EDIT MANUALLY\n")
        ch.write("// Catalog of all mechanically recompiled native candidate blocks\n\n")
        ch.write("#include <cstdint>\n")
        ch.write("#include <cstddef>\n\n")
        ch.write("namespace thor::generated {\n\n")
        ch.write("constexpr size_t TOTAL_NATIVE_CANDIDATE_BLOCKS = " + str(len(generated_blocks)) + ";\n\n")
        ch.write("struct CandidateBlockEntry {\n")
        ch.write("    const char* block_id;\n")
        ch.write("    uint32_t start_pc;\n")
        ch.write("    uint32_t byte_length;\n")
        ch.write("    uint32_t instruction_count;\n")
        ch.write("    const char* sha256;\n")
        ch.write("    const char* module_name;\n")
        ch.write("};\n\n")
        ch.write("extern const CandidateBlockEntry NATIVE_CANDIDATE_CATALOG[TOTAL_NATIVE_CANDIDATE_BLOCKS];\n\n")
        ch.write("} // namespace thor::generated\n")

    catalog_src = os.path.join(args.out_dir, "native_block_catalog.cpp")
    with open(catalog_src, "w") as cs:
        cs.write("// GENERATED FILE - DO NOT EDIT MANUALLY\n")
        cs.write('#include "native_block_catalog.hpp"\n\n')
        cs.write("namespace thor::generated {\n\n")
        cs.write("const CandidateBlockEntry NATIVE_CANDIDATE_CATALOG[TOTAL_NATIVE_CANDIDATE_BLOCKS] = {\n")
        for b in generated_blocks:
            cs.write('    {"' + b['block_id'] + '", ' + b['runtime_start'] + ', ' + str(b['byte_length']) + ', ' + str(b['instruction_count']) + ', "' + b['sha256'] + '", "' + b['module'] + '"},\n')
        cs.write("};\n\n")
        cs.write("} // namespace thor::generated\n")

    all_hdr = os.path.join(args.out_dir, "native_blocks_all.hpp")
    with open(all_hdr, "w") as ah:
        ah.write("#pragma once\n\n")
        ah.write("// GENERATED FILE - DO NOT EDIT MANUALLY\n")
        ah.write("// Forward declarations of all mechanically recompiled candidate blocks\n\n")
        ah.write("#include <cstdint>\n")
        ah.write('#include "thor/sh2/sh2_state.hpp"\n')
        ah.write('#include "thor/sh2/sh2_memory.hpp"\n')
        ah.write('#include "native_block_catalog.hpp"\n\n')
        ah.write("namespace thor::generated {\n\n")
        for b in generated_blocks:
            ah.write("void " + b['block_id'] + "(thor::sh2::Sh2CpuState& state, thor::sh2::ISh2Memory& mem);\n")
        ah.write("\n} // namespace thor::generated\n")

    print(f"Created {len(shards)} shards, catalog header, catalog source, and native_blocks_all.hpp.")

if __name__ == "__main__":
    main()
