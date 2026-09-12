# Workstream T2-GFX-01.5 — Dynamic VDP1 Sprite Provenance and Full Sprite Map Recovery

## Overview

This workstream establishes the complete runtime and static provenance chain connecting visible Sega Saturn VDP1 sprites to hardware commands, VRAM extents, SCU DMA transfers, Work RAM buffers, disc files, 14-byte SpriteArchive descriptor records, and 6-byte animation frame scripts.

## Pipeline Architecture

```
VISIBLE SPRITE (Frame / Scene / Coordinates)
  ↓
VDP1 Display List Command (Type, Width, Height, CMDCOLR Bank)
  ↓
VDP1 Character Address (cmdsrca << 3)
  ↓
VRAM Byte Range (0x05C00000 + char_addr .. + width * height / 2)
  ↓
SCU DMA Level 0/1/2 Transfer (pc, src_ram, dst_vram, len, cycle)
  ↓
High/Low Work RAM Staging Buffer (0x060D3D18 / 0x00201D28)
  ↓
Disc File & Extent (P0.BIN..P3.BIN, ARELE..SHADE, MONS.BIN, CHR.BIN)
  ↓
SpriteArchive 14-Byte Descriptor Record ([x_min, x_max, y_min, y_max, z, flags, 0x7FFF])
  ↓
Animation Script 6-Byte Frame Record ([dx, dy, duration, flags, sprite_ref])
```

## Artifact Inventory

- `README.md`: Architectural summary and file map
- `sprite_provenance.json`: 236 complete provenance mappings linking visible sprites in live gameplay scenes to hardware commands, DMA events, and disc files
- `sprite_records.json`: Catalog of 332 recovered 14-byte sprite descriptor records across player banks (P0..P3), spirits (ARELE..SHADE), and monsters (MONS.BIN)
- `animation_map.json`: 43 animation sequences with 6,510 ordered frame records (dx, dy, duration, flags, sprite_ref)
- `vdp1_trace_summary.json`: Multi-scene trace summary covering 5 distinct scenes (Menu, Idle, Walk, Attack, Combat) and 460 SCU DMA transfers
- `coverage_metrics.json`: Audited metrics confirming 100% visible sprite resolution, 332 sprite records, 50 MONS.BIN subarchives, and 312 unique exported sprites
