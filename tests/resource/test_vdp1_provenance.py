#!/usr/bin/env python3
"""Deterministic regression tests and negative controls for Thor 2 VDP1 sprite provenance.

Verifies:
- VDP1 command display list parsing (normal sprite, scaled, coordinate math);
- Character address to VRAM offset mapping (cmdsrca << 3);
- Sprite descriptor extraction and 14-byte record validation;
- 6-byte animation frame record parsing;
- Reverse index queries (sprite_record -> animation_frames);
- Negative controls: invalid header sizes, truncated buffers, bad sentinels.
"""
from __future__ import annotations

import struct
import unittest
from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tools.gfx.sprite_mapper import (
    CANONICAL_HEADER_SIZE,
    AnimFrame,
    SpriteRecord,
    Vdp1Cmd,
    decode_vdp1_commands,
    parse_dma_trace,
    parse_sprite_archive,
)


class TestVdp1Provenance(unittest.TestCase):
    def test_vdp1_command_decoding(self) -> None:
        """Verify VDP1 command list decoding with synthetic binary packet."""
        # 1. Normal sprite (type 0), 24x32, char_addr = 0x43520 (srca = 0x86A4)
        # 2. End command (0x8000)
        vram = bytearray(64)
        cmdctrl_0 = 0x0000  # Normal sprite, jump mode 0
        cmdlink_0 = 0x0000
        cmdpmod_0 = 0x0008  # 4bpp color bank mode
        cmdcolr_0 = 0x2300  # Palette bank 3
        cmdsrca_0 = 0x43520 >> 3  # 0x86A4
        cmdsize_0 = (3 << 8) | 32  # width = 3 * 8 = 24, height = 32
        xa_0, ya_0 = 117, 97

        struct.pack_into(
            ">HHHHHHhh",
            vram,
            0,
            cmdctrl_0,
            cmdlink_0,
            cmdpmod_0,
            cmdcolr_0,
            cmdsrca_0,
            cmdsize_0,
            xa_0,
            ya_0,
        )

        # End command
        struct.pack_into(">H", vram, 32, 0x8000)

        cmds = decode_vdp1_commands(bytes(vram))
        self.assertEqual(len(cmds), 1)
        c0 = cmds[0]
        self.assertEqual(c0.cmd_type, 0)
        self.assertEqual(c0.type_name, "NORMAL_SPRITE")
        self.assertEqual(c0.width, 24)
        self.assertEqual(c0.height, 32)
        self.assertEqual(c0.char_addr, 0x43520)
        self.assertEqual(c0.colr, 0x2300)
        self.assertEqual(c0.xa, 117)
        self.assertEqual(c0.ya, 97)

    def test_sprite_descriptor_validation(self) -> None:
        """Verify 14-byte sprite descriptor parsing and dimension alignment."""
        # Build synthetic archive: 12-byte header + 0 anim offsets + 0 anim script + 1 sprite record
        pkg = bytearray()
        hdr_sz = CANONICAL_HEADER_SIZE
        anim_off = hdr_sz
        spr_off = hdr_sz

        pkg.extend(struct.pack(">III", hdr_sz, anim_off, spr_off))
        # spr_off: count = 1, offset = 4 (points to spr_off + 4)
        pkg.extend(struct.pack(">HH", 1, 4))
        # 14-byte descriptor: x_min=-8, x_max=47 (w=56), y_min=-8, y_max=7 (h=16), z=-4, flg=24, delim=0x7FFF
        pkg.extend(struct.pack(">7h", -8, 47, -8, 7, -4, 24, 0x7FFF))

        recs, _, meta = parse_sprite_archive(bytes(pkg), "TEST.BIN")
        self.assertEqual(meta["status"], "PARSED")
        self.assertEqual(len(recs), 1)
        r0 = recs[0]
        self.assertEqual(r0.pixel_width, 56)
        self.assertEqual(r0.pixel_height, 16)
        self.assertEqual(r0.pixel_bytes, (56 // 2) * 16)
        self.assertEqual(r0.x_min, -8)
        self.assertEqual(r0.x_max, 47)

    def test_animation_frame_decoding(self) -> None:
        """Verify 6-byte animation frame record parsing and reverse linking."""
        pkg = bytearray()
        hdr_sz = CANONICAL_HEADER_SIZE
        anim_off = hdr_sz
        spr_off = hdr_sz + 16  # room for anim script

        pkg.extend(struct.pack(">III", hdr_sz, anim_off, spr_off))
        # Anim script at anim_off: count = 1, offset to frame = 4
        pkg.extend(struct.pack(">HH", 1, 4))
        # 6-byte frame: dx=-4, dy=4, duration=8, flags=1, sprite_ref=0
        pkg.extend(struct.pack(">4bH", -4, 4, 8, 1, 0))
        # Pad to spr_off
        while len(pkg) < spr_off:
            pkg.append(0)

        # spr_off: count = 1, offset = 4
        pkg.extend(struct.pack(">HH", 1, 4))
        # 14-byte descriptor with sentinel 0x7FFF
        pkg.extend(struct.pack(">7h", -10, 9, -20, 19, 0, 0, 0x7FFF))

        recs, seqs, meta = parse_sprite_archive(bytes(pkg), "ANIM_TEST.BIN")
        self.assertEqual(len(seqs), 1)
        self.assertEqual(len(seqs[0].frames), 1)
        f0 = seqs[0].frames[0]
        self.assertEqual(f0.dx, -4)
        self.assertEqual(f0.dy, 4)
        self.assertEqual(f0.duration, 8)
        self.assertEqual(f0.flags, 1)
        self.assertEqual(f0.sprite_ref, 0)

        # Verify reverse index linking
        self.assertEqual(len(recs), 1)
        self.assertIn(0, recs[0].referenced_by_frames)

    def test_dma_trace_parser(self) -> None:
        """Verify SCU DMA log parser."""
        import tempfile

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tf:
            tf.write("# Test trace\n")
            tf.write("L0 src=0x060D3D18 dst=0x05C43400 len=0x7680 pc=0x060809B2 cycle=752823158\n")
            tf_path = Path(tf.name)

        try:
            records = parse_dma_trace(tf_path)
            self.assertEqual(len(records), 1)
            r0 = records[0]
            self.assertEqual(r0["src"], 0x060D3D18)
            self.assertEqual(r0["dst"], 0x05C43400)
            self.assertEqual(r0["len"], 0x7680)
            self.assertEqual(r0["pc"], 0x060809B2)
            self.assertEqual(r0["cycle"], 752823158)
        finally:
            tf_path.unlink(missing_ok=True)

    def test_negative_controls(self) -> None:
        """Ensure malformed packages fail closed."""
        # 1. Too small (< 12 bytes)
        recs, seqs, meta = parse_sprite_archive(b"\x00" * 8, "TINY.BIN")
        self.assertEqual(meta["status"], "TOO_SMALL")
        self.assertEqual(len(recs), 0)

        # 2. Invalid header size
        bad_hdr = struct.pack(">III", 16, 32, 64)
        recs, seqs, meta = parse_sprite_archive(bad_hdr, "BAD_HDR.BIN")
        self.assertEqual(meta["status"], "INVALID_HEADER_SIZE")
        self.assertEqual(len(recs), 0)

        # 3. Invalid sentinel in descriptor (should be ignored, not crash)
        bad_desc_pkg = bytearray()
        bad_desc_pkg.extend(struct.pack(">III", 12, 12, 12))
        bad_desc_pkg.extend(struct.pack(">HH", 1, 4))
        bad_desc_pkg.extend(struct.pack(">7h", 0, 10, 0, 10, 0, 0, 0x1234))  # Bad sentinel != 0x7FFF
        recs, _, meta = parse_sprite_archive(bytes(bad_desc_pkg), "BAD_SENTINEL.BIN")
        self.assertEqual(len(recs), 0)


if __name__ == "__main__":
    unittest.main()
