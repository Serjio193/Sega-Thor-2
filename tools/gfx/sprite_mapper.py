#!/usr/bin/env python3
"""Sprite mapper and runtime provenance recovery tool for Thor 2.

Correlates visible VDP1 sprites -> VDP1 commands -> character addresses ->
VRAM byte ranges -> RAM source ranges -> source files -> file offsets ->
SpriteArchive records -> animation/frame references.
"""
from __future__ import annotations

import json
import os
import struct
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CANONICAL_HEADER_SIZE = 12


@dataclass
class SpriteRecord:
    archive_name: str
    record_idx: int
    descriptor_offset: int
    x_min: int
    x_max: int
    y_min: int
    y_max: int
    z: int
    flags: int
    pixel_width: int
    pixel_height: int
    pixel_bytes: int
    pixel_data_offset: int
    referenced_by_frames: List[int]


@dataclass
class AnimFrame:
    frame_idx: int
    frame_offset: int
    dx: int
    dy: int
    duration: int
    flags: int
    sprite_ref: int


@dataclass
class AnimSequence:
    archive_name: str
    seq_idx: int
    anim_offset: int
    frames: List[AnimFrame]


@dataclass
class Vdp1Cmd:
    cmd_idx: int
    vram_offset: int
    cmd_type: int
    type_name: str
    char_addr: int
    colr: int
    width: int
    height: int
    xa: int
    ya: int


def decode_vdp1_commands(vram: bytes, max_cmds: int = 250) -> List[Vdp1Cmd]:
    """Parse live VDP1 command display list from VRAM dump."""
    cmds: List[Vdp1Cmd] = []
    off = 0
    type_names = {
        0: "NORMAL_SPRITE", 1: "SCALED_SPRITE", 2: "DISTORTED_SPRITE",
        4: "POLYGON", 5: "POLYLINE", 6: "LINE",
        8: "USER_CLIP", 9: "SYS_CLIP", 10: "LOCAL_COORD"
    }
    while off + 32 <= len(vram) and len(cmds) < max_cmds:
        chunk = vram[off:off + 32]
        cmdctrl, cmdlink, _, cmdcolr, cmdsrca, cmdsize = struct.unpack(
            ">HHHHHH", chunk[:12]
        )
        xa, ya = struct.unpack(">hh", chunk[12:16])
        cmd_type = cmdctrl & 0xF
        is_end = bool(cmdctrl & 0x8000)
        jp_mode = (cmdctrl >> 8) & 0x7
        w = ((cmdsize >> 8) & 0x3F) * 8
        h = cmdsize & 0xFF
        char_addr = (cmdsrca << 3) & 0x7FFFF
        tname = type_names.get(cmd_type, f"UNKNOWN_{cmd_type}")

        if cmd_type in (0, 1, 2) and w > 0 and h > 0:
            cmds.append(
                Vdp1Cmd(
                    cmd_idx=len(cmds),
                    vram_offset=off,
                    cmd_type=cmd_type,
                    type_name=tname,
                    char_addr=char_addr,
                    colr=cmdcolr,
                    width=w,
                    height=h,
                    xa=xa,
                    ya=ya,
                )
            )

        if is_end or jp_mode == 4:
            break
        if jp_mode == 1:
            off = (cmdlink << 3) & 0x7FFFF
        else:
            off = (off + 32) & 0x7FFFF
    return cmds


def parse_sprite_archive(
    data: bytes, archive_name: str, base_file_offset: int = 0
) -> Tuple[List[SpriteRecord], List[AnimSequence], Dict[str, Any]]:
    """Extract all sprite records and animation sequences from an archive."""
    if len(data) < CANONICAL_HEADER_SIZE:
        return [], [], {"status": "TOO_SMALL", "size": len(data)}

    hdr_sz, a_off, s_off = struct.unpack_from(">III", data, 0)
    if hdr_sz != CANONICAL_HEADER_SIZE:
        return [], [], {"status": "INVALID_HEADER_SIZE", "hdr_sz": hdr_sz}

    max_offsets = max(0, (len(data) - 12) // 2)
    num_anim = min((a_off - 12) // 2, max_offsets) if a_off >= 12 else 0
    anim_offsets = [
        struct.unpack_from(">H", data, 12 + i * 2)[0] for i in range(num_anim)
    ]

    script_start = min(a_off, len(data))
    script_end = min(s_off, len(data)) if s_off >= a_off else len(data)
    script = data[script_start:script_end]

    anim_sequences: List[AnimSequence] = []
    frame_ref_map: Dict[int, List[int]] = {}

    if len(script) >= 2:
        cnt = struct.unpack_from(">H", script, 0)[0]
        max_cnt = max(0, (len(script) - 2) // 2)
        cnt = min(cnt, max_cnt)
        seq_offsets = [
            struct.unpack_from(">H", script, 2 + i * 2)[0] for i in range(cnt)
        ]
        seq_frames: List[AnimFrame] = []
        for s_idx, f_off in enumerate(seq_offsets):
            if 0 < f_off and f_off + 6 <= len(script):
                dx, dy, dur, flg, s_ref = struct.unpack_from(">4bH", script, f_off)
                af = AnimFrame(s_idx, f_off, dx, dy, dur, flg, s_ref)
                seq_frames.append(af)
                frame_ref_map.setdefault(s_ref, []).append(s_idx)
        if seq_frames:
            anim_sequences.append(
                AnimSequence(
                    archive_name=archive_name,
                    seq_idx=0,
                    anim_offset=script_start,
                    frames=seq_frames,
                )
            )

    sprite_records: List[SpriteRecord] = []
    if s_off + 2 <= len(data):
        spr_cnt = struct.unpack_from(">H", data, s_off)[0]
        max_spr = max(0, (len(data) - s_off - 2) // 2)
        spr_cnt = min(spr_cnt, max_spr)
        if spr_cnt > 0:
            spr_offsets = [
                struct.unpack_from(">H", data, s_off + 2 + i * 2)[0]
                for i in range(spr_cnt)
            ]
            valid_offs = [
                (i, o) for i, o in enumerate(spr_offsets) if 0 < o <= len(data) - s_off - 14
            ]
            first_pixel_off = (
                max(o for _, o in valid_offs) + 14 if valid_offs else 0
            )

            current_pix_off = s_off + first_pixel_off
            for r_idx, r_off in valid_offs:
                f = struct.unpack_from(">7h", data, s_off + r_off)
                if f[6] == 0x7FFF:
                    w = f[1] - f[0] + 1
                    h = f[3] - f[2] + 1
                    w_align = ((w + 7) // 8) * 8
                    sz = (w_align // 2) * h
                    sr = SpriteRecord(
                        archive_name=archive_name,
                        record_idx=r_idx,
                        descriptor_offset=base_file_offset + s_off + r_off,
                        x_min=f[0],
                        x_max=f[1],
                        y_min=f[2],
                        y_max=f[3],
                        z=f[4],
                        flags=f[5],
                        pixel_width=w_align,
                        pixel_height=h,
                        pixel_bytes=sz,
                        pixel_data_offset=base_file_offset + current_pix_off,
                        referenced_by_frames=frame_ref_map.get(r_idx, []),
                    )
                    sprite_records.append(sr)
                    current_pix_off += sz

    meta = {
        "status": "PARSED",
        "size": len(data),
        "anim_script_offset": a_off,
        "sprite_data_offset": s_off,
        "anim_offsets_count": len(anim_offsets),
        "frames_count": sum(len(s.frames) for s in anim_sequences),
        "records_count": len(sprite_records),
    }
    return sprite_records, anim_sequences, meta


def parse_dma_trace(trace_path: Path) -> List[Dict[str, Any]]:
    """Parse SCU DMA level 0/1/2 transfer logs."""
    if not trace_path.exists():
        return []
    records: List[Dict[str, Any]] = []
    for line in trace_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        entry: Dict[str, Any] = {}
        for p in parts:
            if "=" in p:
                k, v = p.split("=", 1)
                entry[k] = int(v, 16) if v.startswith("0x") else (
                    int(v) if v.isdigit() else v
                )
            else:
                entry["type"] = p
        records.append(entry)
    return records


def correlate_sprite_provenance(
    vdp1_cmds: List[Vdp1Cmd],
    dma_events: List[Dict[str, Any]],
    records: List[SpriteRecord],
    frame_id: int,
    scene_name: str,
) -> List[Dict[str, Any]]:
    """Link visible VDP1 sprites to DMA anchors and source file records."""
    provenance_list: List[Dict[str, Any]] = []
    leon_records = [r for r in records if r.archive_name == "P0.BIN"]

    for cmd in vdp1_cmds:
        # Match DMA transfer for this character address
        matching_dma = None
        for ev in dma_events:
            dst = ev.get("dst", 0) - 0x05C00000
            length = ev.get("len", 0)
            if dst <= cmd.char_addr < dst + length:
                matching_dma = ev
                break

        # Match source file and record
        source_file = "UNKNOWN"
        source_record_idx = None
        source_file_offset = None
        bounds = None
        anim_ref = None

        if cmd.colr in (0x2300, 0x0800):
            source_file = "P0.BIN"
            # Find best match by dimensions
            for lr in leon_records:
                if lr.pixel_width == cmd.width and abs(lr.pixel_height - cmd.height) <= 8:
                    source_record_idx = lr.record_idx
                    source_file_offset = lr.descriptor_offset
                    bounds = {
                        "x_min": lr.x_min, "x_max": lr.x_max,
                        "y_min": lr.y_min, "y_max": lr.y_max
                    }
                    anim_ref = lr.referenced_by_frames[:3]
                    break
        elif cmd.colr == 0x2200:
            source_file = "MONS.BIN"
            source_record_idx = 23  # Subarchive 23 (Ordan in bedroom)
        elif (cmd.colr & 0xF000) == 0x7000:
            source_file = "CHR.BIN"  # HUD fonts and icons

        vram_sz = (cmd.width * cmd.height) // 2
        prov_entry = {
            "frame_id": frame_id,
            "scene_name": scene_name,
            "vdp1_command_idx": cmd.cmd_idx,
            "vdp1_vram_offset": f"0x{cmd.vram_offset:05X}",
            "command_type": cmd.type_name,
            "character_address": f"0x{cmd.char_addr:05X}",
            "vram_byte_range": {
                "start": f"0x{cmd.char_addr:05X}",
                "end": f"0x{cmd.char_addr + vram_sz:05X}",
                "size_bytes": vram_sz,
            },
            "dimensions": {"width": cmd.width, "height": cmd.height},
            "screen_position": {"x": cmd.xa, "y": cmd.ya},
            "color_bank": f"0x{cmd.colr:04X}",
            "cram_offset": f"0x{cmd.colr & 0x07F0:04X}",
            "source_file": source_file,
            "source_record_idx": source_record_idx,
            "source_file_offset": (
                f"0x{source_file_offset:06X}" if source_file_offset else None
            ),
            "source_record_bounds": bounds,
            "animation_frame_refs": anim_ref,
            "dma_event": (
                {
                    "src": f"0x{matching_dma.get('src', 0):08X}",
                    "dst": f"0x{matching_dma.get('dst', 0):08X}",
                    "len": f"0x{matching_dma.get('len', 0):04X}",
                    "pc": f"0x{matching_dma.get('pc', 0):08X}",
                    "cycle": matching_dma.get("cycle", 0),
                }
                if matching_dma
                else None
            ),
        }
        provenance_list.append(prov_entry)
    return provenance_list


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    usa_dir = root / ".private" / "usa"
    cap_dir = root / ".private" / "vdp1_captures"
    out_dir = root / "workstreams" / "T2-GFX-01.5"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== T2-GFX-01.5 Sprite Mapper & Provenance Recovery ===")
    all_records: List[SpriteRecord] = []
    all_anim: List[AnimSequence] = []

    # 1. Parse player archives P0..P3
    for p_name in ["P0.BIN", "P1.BIN", "P2.BIN", "P3.BIN"]:
        p_path = usa_dir / p_name
        if p_path.exists():
            recs, seqs, _ = parse_sprite_archive(p_path.read_bytes(), p_name)
            all_records.extend(recs)
            all_anim.extend(seqs)
            print(f"  {p_name:<12}: {len(recs):3d} records, {sum(len(s.frames) for s in seqs):4d} frames")

    # 2. Parse spirits
    for s_name in ["ARELE.BIN", "BAW.BIN", "BRAS.BIN", "DIT.BIN", "EFREET.BIN", "SHADE.BIN"]:
        s_path = usa_dir / s_name
        if s_path.exists():
            recs, seqs, _ = parse_sprite_archive(s_path.read_bytes(), s_name)
            all_records.extend(recs)
            all_anim.extend(seqs)
            print(f"  {s_name:<12}: {len(recs):3d} records, {sum(len(s.frames) for s in seqs):4d} frames")

    # 3. Parse MONS.BIN subarchives (50 subarchives)
    mons_path = usa_dir / "MONS.BIN"
    mons_count = 0
    if mons_path.exists():
        mons_data = mons_path.read_bytes()
        starts = [
            i for i in range(0, len(mons_data), 2048)
            if i + 16 <= len(mons_data) and mons_data[i + 4:i + 8] == b"\x00\x00\x00\x0C"
        ]
        for idx, s in enumerate(starts):
            nxt = starts[idx + 1] if idx + 1 < len(starts) else len(mons_data)
            sub_name = f"MONS_{idx:02d}"
            recs, seqs, _ = parse_sprite_archive(mons_data[s + 4:nxt], sub_name, base_file_offset=s + 4)
            all_records.extend(recs)
            all_anim.extend(seqs)
            mons_count += 1
        print(f"  MONS.BIN    : {mons_count} subarchives parsed ({len(starts)} packages)")

    # 4. Save sprite records database
    records_json = [asdict(r) for r in all_records]
    (out_dir / "sprite_records.json").write_text(json.dumps(records_json, indent=2), encoding="utf-8")
    print(f"\nSaved {len(records_json)} sprite records to sprite_records.json")

    # 5. Save animation map database
    anim_json = [
        {
            "archive_name": a.archive_name,
            "seq_idx": a.seq_idx,
            "anim_offset": f"0x{a.anim_offset:05X}",
            "frames_count": len(a.frames),
            "frames": [asdict(f) for f in a.frames],
        }
        for a in all_anim
    ]
    (out_dir / "animation_map.json").write_text(json.dumps(anim_json, indent=2), encoding="utf-8")
    print(f"Saved {len(anim_json)} animation sequences to animation_map.json")

    # 6. Parse DMA trace and correlate live VDP1 frames
    dma_events = parse_dma_trace(cap_dir / "dma_trace.txt")
    scenes = [
        (1480, "frame_1480_menu", "HUD / Menu / Cursor"),
        (2200, "frame_2200_idle", "Leon Idle with Ordan"),
        (2300, "frame_2300_walk", "Leon Walk Downward"),
        (2480, "frame_2480_attack", "Leon Attack Swing"),
        (2580, "frame_2580_combat", "Courtyard Combat"),
    ]
    all_provenance: List[Dict[str, Any]] = []
    vdp1_summary: Dict[str, Any] = {"dma_events_count": len(dma_events), "scenes": {}}

    for fid, dname, sdesc in scenes:
        vram_file = cap_dir / dname / "vdp1_vram.bin"
        if vram_file.exists():
            vram_bytes = vram_file.read_bytes()
            cmds = decode_vdp1_commands(vram_bytes)
            prov = correlate_sprite_provenance(cmds, dma_events, all_records, fid, sdesc)
            all_provenance.extend(prov)
            vdp1_summary["scenes"][dname] = {
                "frame": fid,
                "description": sdesc,
                "total_commands": len(cmds),
                "commands": [asdict(c) for c in cmds],
            }
            print(f"  Correlated {len(cmds):2d} VDP1 commands for {dname} ({sdesc})")

    (out_dir / "sprite_provenance.json").write_text(json.dumps(all_provenance, indent=2), encoding="utf-8")
    (out_dir / "vdp1_trace_summary.json").write_text(json.dumps(vdp1_summary, indent=2), encoding="utf-8")
    print(f"Saved {len(all_provenance)} provenance mappings to sprite_provenance.json")
    print(f"Saved trace summary to vdp1_trace_summary.json")


if __name__ == "__main__":
    main()
