# Workstream T2-GFX-01 — RUS/USA Differential Graphics Extraction

## Overview

This workstream contains legal-safe derived metadata, structural diffs, hardware provenance mappings, container verifications, and resource census data produced during task T2-GFX-01.

## Artifact Inventory

- `README.md`: this overview and file guide
- `input_revisions.json`: SHA-256 hashes, volume descriptors, and sector layouts for the Russian and USA disc substrates
- `rus_usa_file_diff.tsv`: Tab-separated 33-file comparison matrix showing bit-for-bit identity across 21 files
- `rus_usa_changed_ranges.json`: Byte-level diff ranges for all modified files
- `sprite_archive_verification.json`: Verification records for all 10 Ancient SpriteArchive packages
- `vram_provenance.json`: Memory and register provenance mapping file extents to Work RAM and VDP1/VDP2/SCU
- `graphics_candidates.json`: 110 candidate graphics segments discovered across the disc
- `extracted_images_manifest.json`: Provenance and geometry manifest for the 50 exported lossless PNG images
- `asset_census.json`: Final audited resource breakdown (5,836,258 structured resource bytes, 64.53%)
