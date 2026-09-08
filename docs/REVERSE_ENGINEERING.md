# Reverse engineering record

This file is the human-readable index of confirmed and provisional findings. Detailed machine-readable records may later live under `config/`.

## Revision: current patched NTSC laboratory image

Status: `UNVERIFIED` pending T2-M0 reproducibility gate.

Preliminary observations:

| Item | Observation | Confidence |
|---|---|---|
| Product code | `MK-81302` | HIGH, preliminary parser result |
| Version | `V1.000` | HIGH, preliminary parser result |
| Date field | `19960618` | HIGH, preliminary parser result |
| Header title | `THE STORY OF THOR 2 (patched for NTSC)` | HIGH, preliminary parser result |
| Track | MODE1/2352 | HIGH |
| ISO9660 files | 33 observed | MEDIUM until reproducible manifest |
| Main candidate | `0TH2.BIN` | HIGH |
| `0TH2.BIN` size | `0x82C00` | HIGH, preliminary extraction |
| First-read/load address | `0x06004000` | HIGH, preliminary boot-header parse |

## Known public-research anchors

Public research has reported executable/runtime addresses in both High and Low Work RAM for some Thor 2 revisions. These addresses are **revision-specific hints only** until mapped to the current image.

Examples queued for validation:

- `0x06009CC4` — debug-related routine reported for another analyzed revision;
- `0x002E8A38` — executable Low Work RAM routine reported in public research;
- `0x002E55A4` — executable Low Work RAM routine reported in public research.

Do not treat these addresses as current-revision facts until byte/runtime correspondence is proven.

## Required record template

For each new finding append or link a record containing:

```text
ID:
STATUS:
REVISION/HASH:
DISC FILE:
FILE RANGE:
RUNTIME RANGE:
CPU:
MODULE/GENERATION:
STATIC EVIDENCE:
DYNAMIC EVIDENCE:
READS/WRITES:
CONTROL FLOW:
HARDWARE INTERACTION:
HYPOTHESIS:
CONFIDENCE:
VERIFICATION:
NEGATIVE EVIDENCE:
NEXT ACTION:
```
