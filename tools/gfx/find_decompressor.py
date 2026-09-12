#!/usr/bin/env python3
"""Scan 0TH2.BIN and TH2.LOW for SH-2 decompression routines."""
import struct
import sys
from pathlib import Path

def scan_file_for_decompressor(bin_path: Path, base_vma: int):
    data = bin_path.read_bytes()
    print(f"\n=== Scanning {bin_path.name} (base 0x{base_vma:08X}, size {len(data)}) ===")
    
    candidates = []
    
    for i in range(0, len(data) - 16, 2):
        pc = base_vma + i
        w0 = struct.unpack_from(">H", data, i)[0]
        w1 = struct.unpack_from(">H", data, i+2)[0]
        w2 = struct.unpack_from(">H", data, i+4)[0]
        
        # 1. Look for bit extraction: SHLR/SHLL followed by BT/BF
        # SHLR Rn: 0100nnnn 00000001 (0x4n01)
        # SHLL Rn: 0100nnnn 00000000 (0x4n00)
        # ROTCR Rn: 0100nnnn 00100101 (0x4n25)
        # ROTCL Rn: 0100nnnn 00100100 (0x4n24)
        is_shift = (w0 & 0xF0FF) in (0x4001, 0x4000, 0x4025, 0x4024)
        is_cbranch = (w1 & 0xFC00) in (0x8800, 0x8900, 0x8A00, 0x8B00, 0x8E00, 0x8F00)
        
        # 2. Look for window masking: AND with 0xFFF or 0x7FF or 0x1FFF or 0x3FF
        # Check if immediate or register AND
        is_win_mask = False
        if (w0 & 0xF000) == 0xD000: # MOV.L @(disp, PC), Rm
            disp = w0 & 0xFF
            ref_off = (i & ~3) + 4 + (disp * 4)
            if ref_off + 4 <= len(data):
                const_val = struct.unpack_from(">I", data, ref_off)[0]
                if const_val in (0xFFF, 0x7FF, 0x1FFF, 0x3FF, 0x0FFF, 0x07FF):
                    is_win_mask = True
                    
        if (is_shift and is_cbranch) or is_win_mask:
            candidates.append((pc, i, w0, w1, is_win_mask))
            
    print(f"Found {len(candidates)} shift/branch/mask sites.")
    
    # Filter for clusters of decompression instructions
    clusters = []
    if candidates:
        cluster = [candidates[0]]
        for c in candidates[1:]:
            if c[1] - cluster[-1][1] <= 64:
                cluster.append(c)
            else:
                if len(cluster) >= 3 or any(x[4] for x in cluster):
                    clusters.append(cluster)
                cluster = [c]
        if len(cluster) >= 3 or any(x[4] for x in cluster):
            clusters.append(cluster)
            
    print(f"Identified {len(clusters)} candidate decompression clusters:")
    for cl in clusters:
        start_pc = cl[0][0]
        end_pc = cl[-1][0]
        has_mask = any(x[4] for x in cl)
        print(f"  Cluster at 0x{start_pc:08X} - 0x{end_pc:08X} (span {end_pc - start_pc + 2} bytes, {len(cl)} events, window_mask={has_mask})")

if __name__ == "__main__":
    scan_file_for_decompressor(Path(".private/rus/0TH2.BIN"), 0x06004000)
    scan_file_for_decompressor(Path(".private/rus/TH2.LOW"), 0x002DA000)
