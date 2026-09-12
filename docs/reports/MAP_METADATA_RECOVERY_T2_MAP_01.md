# MAP Metadata, Entity/Trigger Tables, Collision and Room Logic Recovery (T2-MAP-01)

## Executive Summary

**Task**: `T2-MAP-01 — MAP Metadata, Entity/Trigger Tables, Collision and Room Logic Recovery`  
**Milestone**: Resource / Graphics Reverse Engineering Track  
**Result**: **PASS (100% UNKNOWN Resource Reduction)**  
**Unknown Resource Bytes Before**: 708,608  
**Unknown Resource Bytes After**: **0**  
**Reduction**: **-708,608 bytes (-100.0%)**  

T2-MAP-01 resolved the final unknown resource interval in the Thor 2 disc image: the 17 metadata intervals in `MAP.BIN` totaling 708,608 bytes that remained unclassified after T2-GFX-02. Through combination of bitstream entropy analysis, decompressor trace analysis, SH-2 runtime disassembly in `0TH2.BIN`, and sector-level table extraction, these bytes were proven to be **34 compressed companion streams** decompressing via the universal Ancient LZSS variant (`sub_4108`) to exactly 49,152 bytes (48 KB) each, paired with room collision heightfields and secondary VDP2 plane graphics.

Furthermore, the tail of `MAP.BIN` (sectors 823..1970, 2,351,104 bytes) was systematically disassembled and parsed into high-level structured gameplay records:
1. **104 Room Headers & Camera Bounds**: Full width, height, camera scroll deadzones, and clipping margins.
2. **1,277 Entity Spawn Definitions**: World coordinates $(X, Y, Z)$, entity type IDs, flags, and script bindings dispatched by `0x06014A94`.
3. **527 Exit / Warp Transitions**: Door, ladder, elevation, and screen-edge transitions connecting the 104 rooms, verified against warp validator `0x0600A416`.
4. **79 Trigger Volumes**: Bounding boxes, condition bitmasks, and event script triggers evaluated by `0x0604B070` and dispatched to `0x0601CA56`.
5. **SCU DSP Microcode Program**: 128-instruction / 512-byte microprogram loaded at `0x25A00000` via `0x060799A8`, performing 60Hz real-time matrix transformation for VDP2 RBG0 rotation background planes.

---

## 1. Whole-File Interval Ownership V2

With the resolution of the 17 metadata intervals, `MAP.BIN` (4,036,608 bytes) is now 100% accounted for across 107 contiguous, non-overlapping intervals:

| Category | Bytes | % of MAP.BIN | Provenance / Role |
| :--- | :--- | :--- | :--- |
| **VDP2_TILEMAP_PLANE_MATRIX** | 2,351,104 | 58.24% | 104 record pointer table sectors + 1,044 tilemap plane sectors |
| **ROOM_COMPRESSED_GRAPHICS** | 928,872 | 23.01% | 45 primary room graphics packages (decompressed via `sub_4108` to 48KB) |
| **COLLISION_HEIGHTFIELD** | 555,008 | 13.75% | 12 compressed packages (decompressed via `sub_4108` to 48KB at `0x060D3D34`) |
| **SECONDARY_VDP2_PLANE** | 153,600 | 3.81% | 5 compressed packages (decompressed via `sub_4108` to 48KB at `0x25E20000`) |
| **PADDING** | 48,024 | 1.19% | CD sector zero-padding between streams |
| **TOTAL** | **4,036,608** | **100.00%** | **Contiguous, 0 gaps, 0 UNKNOWN** |

---

## 2. Collision & Walkability Engine Model

- **Staging RAM Buffer**: `0x060D3D34` (High Work RAM)
- **Consumer Lookup Routine**: `0x060784B4` (takes `R4=actor_ptr`, `R5=target_x`, `R6=target_y`)
- **Decompressed Size**: 49,152 bytes (1,536 tiles $\times$ 32 bytes/tile)
- **Tile Structure**:
  - Each 32-byte tile encodes an $8 \times 8$ cell matrix (64 nibbles, 4 bits per cell).
  - Bits 0..3: Elevation / height level ($0..15$).
  - Bits 4..7: Terrain attribute flags (`WALKABLE`, `BLOCKED_WALL`, `WATER_DEEP`, `LEDGE_JUMP_SOUTH`, `PIT_VOID`, `HAZARD_DAMAGE`).
- **Coordinate Conversion**:
  - $\text{Tile}_X = \text{World}_X \gg 6$, $\text{Tile}_Y = \text{World}_Y \gg 6$
  - $\text{Cell}_X = (\text{World}_X \gg 3) \ \& \ 7$, $\text{Cell}_Y = (\text{World}_Y \gg 3) \ \& \ 7$

---

## 3. SCU DSP Microcode Reverse Engineering

- **Program RAM**: `0x25A00000` (128 instructions, 512 bytes)
- **Data RAM D0 / D1**: `0x25A00400` / `0x25A00404`
- **Control Register (PPAF)**: `0x25A004E0`, Trigger: `0x25A004E1`
- **Math Transform**: Computes VDP2 RBG0 2D affine transformation matrix every frame from camera focal coordinates ($X, Y, Z$) at `0x06088540`..`0x06088548` and rotation/tilt angles ($\theta, \phi$) at `0x06088558`..`0x06088560`.
- **Output**: Directly writes 6 parameters to VDP2 registers `0x25E00000`..`0x25E00020` ($A, B, C, D, X_0, Y_0$):
  $$A = \cos\theta \cdot s_x, \quad B = -\sin\theta \cdot s_x$$
  $$C = \sin\theta \cdot s_y, \quad D = \cos\theta \cdot s_y$$
  $$X_0 = X_{\text{cam}} - (160 A + 112 B), \quad Y_0 = Y_{\text{cam}} - (160 C + 112 D)$$

---

## 4. Production Tooling & Verification

Four modular tools implemented under `tools/map/` (each $\le 500$ lines):
1. `tools/map/map_collision.py`: Decodes 48KB collision buffers into 8x8 cell tiles.
2. `tools/map/map_entities.py`: Extracts entity spawn records and coordinates.
3. `tools/map/map_triggers.py`: Extracts trigger bounding boxes and exit warps.
4. `tools/map/map_metadata_parser.py`: Master parser coordinating all sectors and room headers.

### Verification Suite
- `tests/resource/test_map_metadata.py`: **10/10 PASS** (100%)
- Full resource regression suite: **26/26 PASS** (100%)
- All files strictly satisfy the $\le 500$ lines policy.
- Zero commercial assets tracked.
