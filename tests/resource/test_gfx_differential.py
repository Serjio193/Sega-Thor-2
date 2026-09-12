#!/usr/bin/env python3
"""Regression tests and negative controls for Thor 2 graphics differential tools."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.sprite_archive_analyzer import analyze_archive
from tools.gfx.carver import score_sprite_archive, score_cram_palette, score_1bpp_font
from tools.gfx.inspect_palettes import decode_rgb555

class TestGraphicsDifferential(unittest.TestCase):

    def test_negative_controls_archive(self):
        # 1. Truncated archive (< 12 bytes)
        res = analyze_archive(b"\x00\x00\x00\x0C\x00\x00", "tiny.bin")
        self.assertEqual(res["status"], "SPRITE_ARCHIVE_REJECTED")

        # 2. Header size != 12
        bad_hdr = struct.pack(">III", 16, 20, 30) + b"\x00" * 20
        res = analyze_archive(bad_hdr, "bad_hdr.bin")
        self.assertEqual(res["status"], "SPRITE_ARCHIVE_REJECTED")

        # 3. anim_script_offset < header_size
        bad_off1 = struct.pack(">III", 12, 8, 30) + b"\x00" * 20
        res = analyze_archive(bad_off1, "bad_off1.bin")
        self.assertEqual(res["status"], "SPRITE_ARCHIVE_REJECTED")

        # 4. sprite_data_offset < anim_script_offset
        bad_off2 = struct.pack(">III", 12, 30, 20) + b"\x00" * 20
        res = analyze_archive(bad_off2, "bad_off2.bin")
        self.assertEqual(res["status"], "SPRITE_ARCHIVE_REJECTED")

        # 5. sprite_data_offset > file_size
        bad_off3 = struct.pack(">III", 12, 20, 100) + b"\x00" * 20
        res = analyze_archive(bad_off3, "bad_off3.bin")
        self.assertEqual(res["status"], "SPRITE_ARCHIVE_REJECTED")

        # 6. Odd offset table size
        bad_odd = struct.pack(">III", 12, 13, 20) + b"\x00" * 20
        res = analyze_archive(bad_odd, "bad_odd.bin")
        self.assertEqual(res["status"], "SPRITE_ARCHIVE_REJECTED")

    def test_synthetic_roundtrip_analyzer(self):
        hdr = struct.pack(">III", 12, 16, 24)
        offsets = struct.pack(">HH", 0x10, 0x20)
        script = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        sprites = b"\xAA\xBB\xCC\xDD"
        payload = hdr + offsets + script + sprites
        res = analyze_archive(payload, "synth.bin")
        self.assertEqual(res["status"], "SPRITE_ARCHIVE_CONFIRMED")
        self.assertTrue(res["roundtrip_exact"])
        self.assertEqual(res["num_anim_offsets"], 2)
        self.assertEqual(res["anim_script_bytes"], 8)
        self.assertEqual(res["sprite_bytes"], 4)

    def test_carver_negative_controls(self):
        # Corrupted palette
        bad_pal = b"\xFF" * 10 # wrong length
        self.assertIsNone(score_cram_palette(bad_pal, 0, len(bad_pal)))

        # All zero font
        zero_font = b"\x00" * 64
        self.assertIsNone(score_1bpp_font(zero_font, 0, len(zero_font)))

        # All ones font (excessive density)
        one_font = b"\xFF" * 64
        self.assertIsNone(score_1bpp_font(one_font, 0, len(one_font)))

    def test_rgb555_decoder(self):
        # 0x7C00 is Pure Blue (B=31, G=0, R=0)
        r, g, b = decode_rgb555(0x7C00)
        self.assertEqual((r, g, b), (0, 0, 255))

        # 0x001F is Pure Red (B=0, G=0, R=31)
        r, g, b = decode_rgb555(0x001F)
        self.assertEqual((r, g, b), (255, 0, 0))

        # 0x03E0 is Pure Green (B=0, G=31, R=0)
        r, g, b = decode_rgb555(0x03E0)
        self.assertEqual((r, g, b), (0, 255, 0))

        # 0x7FFF is White (B=31, G=31, R=31)
        r, g, b = decode_rgb555(0x7FFF)
        self.assertEqual((r, g, b), (255, 255, 255))

        # 0x0000 is Black (B=0, G=0, R=0)
        r, g, b = decode_rgb555(0x0000)
        self.assertEqual((r, g, b), (0, 0, 0))

    def test_live_p0_roundtrip(self):
        p0_path = Path(".private/rus/P0.BIN")
        if not p0_path.exists():
            self.skipTest("Private P0.BIN not extracted")
        data = p0_path.read_bytes()
        res = analyze_archive(data, "P0.BIN")
        self.assertEqual(res["status"], "SPRITE_ARCHIVE_CONFIRMED")
        self.assertTrue(res["roundtrip_exact"])

if __name__ == "__main__":
    unittest.main()
