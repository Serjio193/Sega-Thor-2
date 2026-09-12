#!/usr/bin/env python3
"""tools/gfx/chr_decompressor.py — Universal Ancient LZSS/RLE Decompressor.

Faithfully implements the SH-2 decompression routine sub_4108 located at
runtime address 0x06004108 (file offset 0x00108) in 0TH2.BIN.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import struct
import sys


class DecompressionError(ValueError):
    """Raised when decompression encounters malformed or out-of-bounds stream data."""
    pass


@dataclass
class SubBlockInfo:
    source_offset: int
    compressed_length: int
    decompressed_bytes: int
    terminator: int


@dataclass
class DecompressionResult:
    data: bytes
    bytes_consumed: int
    sub_blocks: List[SubBlockInfo]


class AncientDecompressor:
    """Universal Ancient Bitstream Decompressor (sub_4108)."""

    def __init__(self, max_output_size: int = 16 * 1024 * 1024):
        self.max_output_size = max_output_size

    def decompress(self, data: bytes, src_offset: int = 0) -> DecompressionResult:
        """Decompress a multi-sub-block stream from `data` starting at `src_offset`.

        Fails closed on any truncation, corrupt token, or out-of-bounds backreference.
        """
        src = src_offset
        out = bytearray()
        sub_blocks: List[SubBlockInfo] = []

        while True:
            if src + 2 > len(data):
                raise DecompressionError(f"Truncated stream header at offset 0x{src:X}")

            sub_start = src
            b0 = data[src]
            b1 = data[src + 1]
            src += 2
            block_len = (b1 << 8) | b0
            block_end = (src - 2) + block_len

            if block_len < 2:
                raise DecompressionError(
                    f"Invalid sub-block length {block_len} at offset 0x{sub_start:X}"
                )
            if block_end > len(data):
                raise DecompressionError(
                    f"Sub-block at 0x{sub_start:X} specifies end 0x{block_end:X}, "
                    f"exceeding data length 0x{len(data):X}"
                )

            prev_out_len = len(out)

            # Process tokens within the sub-block
            while src < block_end:
                token = data[src]
                src += 1

                if (token & 0x80) != 0:
                    # --- BACKREFERENCE BRANCH ---
                    length = ((token & 0x60) >> 5) + 4
                    if src >= block_end:
                        raise DecompressionError(f"Truncated backref distance at 0x{src:X}")
                    dist_hi = token & 0x1F
                    dist_lo = data[src]
                    src += 1
                    distance = (dist_hi << 8) | dist_lo

                    if distance <= 0:
                        raise DecompressionError(f"Zero or negative backref distance {distance}")
                    if distance > len(out):
                        raise DecompressionError(
                            f"Backreference distance {distance} exceeds output length {len(out)} "
                            f"at stream offset 0x{src-2:X}"
                        )

                    ref_pos = len(out) - distance
                    if len(out) + length > self.max_output_size:
                        raise DecompressionError("Output exceeded maximum allowed size")

                    for _ in range(length):
                        out.append(out[ref_pos])
                        ref_pos += 1

                    # Chained copy extension peek
                    while src < block_end:
                        peek = data[src]
                        if (peek & 0xE0) == 0x60:
                            src += 1
                            ext_len = peek & 0x1F
                            if len(out) + ext_len > self.max_output_size:
                                raise DecompressionError("Output exceeded maximum size")
                            for _ in range(ext_len):
                                out.append(out[ref_pos])
                                ref_pos += 1
                        else:
                            break

                elif (token & 0x40) != 0:
                    # --- RLE BRANCH ---
                    if (token & 0x10) != 0:
                        if src >= block_end:
                            raise DecompressionError(f"Truncated extended RLE length at 0x{src:X}")
                        length = ((token & 0x0F) << 8) | data[src]
                        src += 1
                    else:
                        length = token & 0x1F
                    length += 4

                    if src >= block_end:
                        raise DecompressionError(f"Truncated RLE fill byte at 0x{src:X}")
                    fill_val = data[src]
                    src += 1

                    if len(out) + length > self.max_output_size:
                        raise DecompressionError("Output exceeded maximum allowed size")
                    out.extend([fill_val] * length)

                else:
                    # --- LITERAL BRANCH ---
                    if (token & 0x20) != 0:
                        if src >= block_end:
                            raise DecompressionError(f"Truncated extended literal at 0x{src:X}")
                        length = ((token & 0x1F) << 8) | data[src]
                        src += 1
                    else:
                        length = token & 0x1F

                    if length == 0:
                        raise DecompressionError(f"Zero literal length at stream offset 0x{src-1:X}")
                    if src + length > block_end:
                        raise DecompressionError(
                            f"Literal length {length} exceeds sub-block boundary at 0x{src:X}"
                        )
                    if len(out) + length > self.max_output_size:
                        raise DecompressionError("Output exceeded maximum allowed size")

                    out.extend(data[src : src + length])
                    src += length

            if src != block_end:
                raise DecompressionError(
                    f"Sub-block token stream misaligned: ended at 0x{src:X}, expected 0x{block_end:X}"
                )

            # Read terminator byte
            if src >= len(data):
                terminator = 0
            else:
                terminator = data[src]
                src += 1

            sub_blocks.append(
                SubBlockInfo(
                    source_offset=sub_start,
                    compressed_length=block_len,
                    decompressed_bytes=len(out) - prev_out_len,
                    terminator=terminator,
                )
            )

            if terminator == 0:
                # Stream finished
                break

        return DecompressionResult(
            data=bytes(out),
            bytes_consumed=src - src_offset,
            sub_blocks=sub_blocks,
        )


def main():
    if len(sys.argv) < 2:
        print("Usage: python chr_decompressor.py <file.bin> [hex_offset]")
        sys.exit(1)

    bin_path = Path(sys.argv[1])
    offset = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0
    data = bin_path.read_bytes()

    dec = AncientDecompressor()
    try:
        res = dec.decompress(data, offset)
        print(f"Success! Consumed {res.bytes_consumed} bytes across {len(res.sub_blocks)} sub-blocks.")
        print(f"Decompressed size: {len(res.data)} bytes.")
        for i, sb in enumerate(res.sub_blocks):
            print(f"  Sub-block {i}: offset 0x{sb.source_offset:X}, comp={sb.compressed_length}, decomp={sb.decompressed_bytes}")
    except DecompressionError as e:
        print(f"Decompression error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
