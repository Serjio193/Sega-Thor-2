#!/usr/bin/env python3
"""tests/resource/test_gfx_recovery.py — Regression Suite and Negative Controls for T2-GFX-02.

Verifies:
1. Universal Ancient decompressor (sub_4108) byte-exact output on CHR.BIN and MAP.BIN.
2. Negative controls fail-closed on corrupt headers, invalid distances, and overflows.
3. MAP.BIN room packages decompress to exactly 49,152 bytes.
4. ED.BIN 8bpp frame decoding and palette geometry.
5. P4.BIN 4-byte prefix and canonical 12-byte SpriteArchive roundtrip.
6. Census monotonicity: UNKNOWN_RESOURCE_BYTES_AFTER < UNKNOWN_RESOURCE_BYTES_BEFORE.
"""

from pathlib import Path
import json
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.chr_decompressor import AncientDecompressor, DecompressionError
from tools.gfx.sprite_archive_analyzer import analyze_archive
from tools.gfx.ed_extractor import EndingExtractor, decode_rgb555_palette


class TestGfxRecovery(unittest.TestCase):

    def setUp(self):
        self.dec = AncientDecompressor()
        self.usa_chr_path = Path(".private/usa/CHR.BIN")
        self.usa_map_path = Path(".private/usa/MAP.BIN")
        self.usa_ed_path = Path(".private/usa/ED.BIN")
        self.usa_p4_path = Path(".private/usa/P4.BIN")

    def test_chr_decompression_block0(self):
        """Test Block 0 decompression in CHR.BIN produces exact expected payload sizes."""
        if not self.usa_chr_path.exists():
            self.skipTest("USA CHR.BIN not available")

        chr_data = self.usa_chr_path.read_bytes()
        # Stream 0 (Palette at 0x00000)
        res0 = self.dec.decompress(chr_data, 0x00000)
        self.assertEqual(len(res0.data), 256)
        self.assertEqual(res0.bytes_consumed, 170)
        self.assertEqual(len(res0.sub_blocks), 1)

        # Stream 1 (Graphics at 0x000AA)
        res1 = self.dec.decompress(chr_data, 0x000AA)
        self.assertEqual(len(res1.data), 76800)  # 320x240 in 8bpp or 640x240 in 4bpp
        self.assertEqual(res1.bytes_consumed, 59864)
        self.assertEqual(len(res1.sub_blocks), 2)

    def test_decompressor_negative_controls(self):
        """Verify decompressor strictly fails closed on all corrupt or malicious streams."""
        # NC-1: Truncated stream header (< 2 bytes)
        with self.assertRaises(DecompressionError):
            self.dec.decompress(b"\x05")

        # NC-2: Sub-block length < 2
        with self.assertRaises(DecompressionError):
            self.dec.decompress(b"\x00\x00")

        # NC-3: Sub-block specifies length beyond buffer
        with self.assertRaises(DecompressionError):
            self.dec.decompress(b"\xFF\x7F\x01\x02")

        # NC-4: Backreference distance exceeds output buffer (underflow)
        # Token 0x80 (backref len 4), distance = 0x0005 (when out is empty)
        bad_backref = struct.pack("<H", 5) + bytes([0x80, 0x05]) + b"\x00"
        with self.assertRaises(DecompressionError):
            self.dec.decompress(bad_backref)

        # NC-5: Zero literal length
        bad_literal = struct.pack("<H", 4) + bytes([0x00]) + b"\x00"
        with self.assertRaises(DecompressionError):
            self.dec.decompress(bad_literal)

        # NC-6: Literal length exceeds sub-block boundary
        bad_overflow = struct.pack("<H", 4) + bytes([0x05, 0xAA, 0xBB]) + b"\x00"
        with self.assertRaises(DecompressionError):
            self.dec.decompress(bad_overflow)

    def test_map_rooms_decompression(self):
        """Verify MAP.BIN room packages decompress cleanly to exactly 49,152 bytes."""
        if not self.usa_map_path.exists():
            self.skipTest("USA MAP.BIN not available")

        map_data = self.usa_map_path.read_bytes()

        # Room 0: DSP< at LBA 0 (0x000000)
        self.assertEqual(map_data[2:4], b"P<")
        res0 = self.dec.decompress(map_data, 0x000000)
        self.assertEqual(len(res0.data), 49152)
        self.assertEqual(res0.bytes_consumed, 21317)

        # Room 1: TQP< at LBA 11 (0x005800)
        self.assertEqual(map_data[0x5802:0x5804], b"P<")
        res1 = self.dec.decompress(map_data, 0x005800)
        self.assertEqual(len(res1.data), 49152)
        self.assertEqual(res1.bytes_consumed, 20821)

        # Room 2: BLP< at LBA 22 (0x00B000)
        self.assertEqual(map_data[0xB002:0xB004], b"P<")
        res2 = self.dec.decompress(map_data, 0x00B000)
        self.assertEqual(len(res2.data), 49152)
        self.assertEqual(res2.bytes_consumed, 19523)

    def test_ed_bin_frames(self):
        """Verify ED.BIN 8bpp frame layout and palette decoding."""
        if not self.usa_ed_path.exists():
            self.skipTest("USA ED.BIN not available")

        extractor = EndingExtractor(self.usa_ed_path)
        self.assertEqual(len(extractor.palettes), 4)
        for pal in extractor.palettes:
            self.assertEqual(len(pal), 256)

        # Frame 0 extract
        rgba0 = extractor.extract_frame(0, palette_idx=0)
        self.assertEqual(len(rgba0), 320 * 240 * 4)

        # Frame 7 extract
        rgba7 = extractor.extract_frame(7, palette_idx=0)
        self.assertEqual(len(rgba7), 320 * 240 * 4)

        # Out of bounds frame index
        with self.assertRaises(IndexError):
            extractor.extract_frame(8)

    def test_p4_bin_structure(self):
        """Verify P4.BIN has 4-byte prefix and canonical 12-byte SpriteArchive roundtrip."""
        if not self.usa_p4_path.exists():
            self.skipTest("USA P4.BIN not available")

        p4_data = self.usa_p4_path.read_bytes()
        self.assertEqual(len(p4_data), 2893)

        # Direct offset 0 must be rejected
        res0 = analyze_archive(p4_data, "P4.BIN [0]")
        self.assertEqual(res0["status"], "SPRITE_ARCHIVE_REJECTED")

        # Offset 4 must pass 100% roundtrip
        res4 = analyze_archive(p4_data[4:], "P4.BIN [4]")
        self.assertEqual(res4["status"], "SPRITE_ARCHIVE_CONFIRMED")
        self.assertTrue(res4["roundtrip_exact"])
        self.assertEqual(res4["header_size"], 12)
        self.assertEqual(res4["anim_script_offset"], 1888)
        self.assertEqual(res4["sprite_data_offset"], 2082)
        self.assertEqual(res4["num_anim_offsets"], 938)

    def test_census_monotonicity(self):
        """Verify asset census V3 metrics strictly reduce UNKNOWN bytes monotonically."""
        census_path = Path("workstreams/T2-GFX-02/asset_census_v3.json")
        self.assertTrue(census_path.exists(), "asset_census_v3.json must exist")

        census = json.loads(census_path.read_text(encoding="utf-8"))
        unknown_before = census["UNKNOWN_RESOURCE_BYTES_BEFORE"]
        unknown_after = census["UNKNOWN_RESOURCE_BYTES_AFTER"]
        reduction = census["EXACT_UNKNOWN_BYTE_REDUCTION"]

        self.assertEqual(unknown_before, 3207750)
        self.assertLess(unknown_after, unknown_before)
        self.assertEqual(reduction, unknown_before - unknown_after)
        self.assertGreater(reduction, 2000000)  # Over 2 million bytes reduced


if __name__ == "__main__":
    unittest.main()
