#!/usr/bin/env python3
"""RUS vs USA Differential Census and Change Range Analysis for Thor 2."""
import csv
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from typing import Dict, List, Tuple
from tools.gfx.disc_extractor import SaturnDisc

KNOWN_SPRITE_ARCHIVES = {
    "ARELE.BIN", "BAW.BIN", "BRAS.BIN", "DIT.BIN", "EFREET.BIN",
    "SHADE.BIN", "P0.BIN", "P1.BIN", "P2.BIN", "P3.BIN"
}

KNOWN_EXECUTABLES = {"0TH2.BIN", "TH2.LOW", "SET07.BIN", "BGM.BIN"}

def find_changed_ranges(data1: bytes, data2: bytes) -> List[Tuple[int, int, int]]:
    """Return list of (start_offset, len_rus, len_usa) contiguous difference regions."""
    min_len = min(len(data1), len(data2))
    diff_mask = [i for i in range(min_len) if data1[i] != data2[i]]
    ranges = []
    if diff_mask:
        start = diff_mask[0]
        prev = start
        for idx in diff_mask[1:]:
            if idx > prev + 16:  # group differences within 16 bytes
                ranges.append((start, prev - start + 1))
                start = idx
            prev = idx
        ranges.append((start, prev - start + 1))
    
    # Handle length tail difference
    if len(data1) != len(data2):
        ranges.append((min_len, abs(len(data1) - len(data2))))
    return ranges

def classify_file_diff(filename: str, identical: bool, size_rus: int, size_usa: int,
                       diff_bytes: int, diff_ranges: list) -> str:
    if identical:
        return "IDENTICAL"
    if filename in KNOWN_EXECUTABLES or filename.startswith("SET"):
        return "EXECUTABLE_CHANGED"
    if filename in KNOWN_SPRITE_ARCHIVES:
        return "GRAPHICS_CHANGED_LIKELY"
    if filename in {"CHR.BIN", "MONS.BIN", "MAP.BIN"}:
        return "CONTAINER_STRUCTURE_CHANGED"
    if filename.endswith(".TXT") or filename.endswith(".DOC"):
        return "TEXT_ONLY_LIKELY"
    return "REGION_LOCALIZATION_CHANGED"

def run_differential(rus_bin: Path, rus_cue: Path, usa_bin: Path, usa_cue: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    rus_disc = SaturnDisc(rus_bin, rus_cue)
    usa_disc = SaturnDisc(usa_bin, usa_cue)
    
    rus_summary = rus_disc.get_summary()
    usa_summary = usa_disc.get_summary()
    
    # Phase 0: input_revisions.json
    revisions_info = {
        "rus_revision": {
            "identification": "RUS_NTSC_PATCHED_MEDUZA",
            "volume_id": rus_summary["volume_id"],
            "title": rus_summary["title"],
            "product_code": rus_summary["product_code"],
            "version": rus_summary["version"],
            "date": rus_summary["date"],
            "image_size": rus_summary["image_size"],
            "image_sha256": rus_summary["image_sha256"],
            "file_count": rus_summary["file_count"],
        },
        "usa_revision": {
            "identification": "USA_RETAIL_LEGEND_OF_OASIS",
            "volume_id": usa_summary["volume_id"],
            "title": usa_summary["title"],
            "product_code": usa_summary["product_code"],
            "version": usa_summary["version"],
            "date": usa_summary["date"],
            "image_size": usa_summary["image_size"],
            "image_sha256": usa_summary["image_sha256"],
            "file_count": usa_summary["file_count"],
        }
    }
    (out_dir / "input_revisions.json").write_text(json.dumps(revisions_info, indent=2), encoding="utf-8")
    
    # Phase 1: File comparison
    all_files = sorted(list(set(rus_disc.get_file_list()) | set(usa_disc.get_file_list())))
    
    tsv_rows = []
    changed_ranges_data = {}
    
    for filename in all_files:
        in_rus = filename in rus_disc.files
        in_usa = filename in usa_disc.files
        
        if not in_rus or not in_usa:
            classification = "PRESENT_IN_ONE_VERSION_ONLY"
            tsv_rows.append({
                "filename": filename,
                "rus_size": rus_disc.files[filename]["size"] if in_rus else 0,
                "usa_size": usa_disc.files[filename]["size"] if in_usa else 0,
                "rus_sha256": rus_disc.hash_file(filename) if in_rus else "",
                "usa_sha256": usa_disc.hash_file(filename) if in_usa else "",
                "identical": "FALSE",
                "first_diff": -1,
                "last_diff": -1,
                "changed_bytes": -1,
                "similarity_pct": "0.00%",
                "classification": classification
            })
            continue
            
        data_rus = rus_disc.read_file(filename)
        data_usa = usa_disc.read_file(filename)
        size_rus = len(data_rus)
        size_usa = len(data_usa)
        sha_rus = rus_disc.hash_file(filename)
        sha_usa = usa_disc.hash_file(filename)
        
        identical = (sha_rus == sha_usa)
        
        if identical:
            tsv_rows.append({
                "filename": filename,
                "rus_size": size_rus,
                "usa_size": size_usa,
                "rus_sha256": sha_rus,
                "usa_sha256": sha_usa,
                "identical": "TRUE",
                "first_diff": -1,
                "last_diff": -1,
                "changed_bytes": 0,
                "similarity_pct": "100.00%",
                "classification": "IDENTICAL"
            })
        else:
            min_len = min(size_rus, size_usa)
            max_len = max(size_rus, size_usa)
            diff_indices = [i for i in range(min_len) if data_rus[i] != data_usa[i]]
            first_diff = diff_indices[0] if diff_indices else min_len
            last_diff = (max_len - 1) if size_rus != size_usa else (diff_indices[-1] if diff_indices else -1)
            changed_byte_count = len(diff_indices) + abs(size_rus - size_usa)
            similarity = (1.0 - (changed_byte_count / max_len)) * 100.0 if max_len > 0 else 100.0
            
            ranges = find_changed_ranges(data_rus, data_usa)
            classification = classify_file_diff(filename, False, size_rus, size_usa, changed_byte_count, ranges)
            
            tsv_rows.append({
                "filename": filename,
                "rus_size": size_rus,
                "usa_size": size_usa,
                "rus_sha256": sha_rus,
                "usa_sha256": sha_usa,
                "identical": "FALSE",
                "first_diff": first_diff,
                "last_diff": last_diff,
                "changed_bytes": changed_byte_count,
                "similarity_pct": f"{similarity:.2f}%",
                "classification": classification
            })
            changed_ranges_data[filename] = {
                "rus_size": size_rus,
                "usa_size": size_usa,
                "diff_ranges": [{"offset": r[0], "length": r[1]} for r in ranges]
            }

    with open(out_dir / "rus_usa_file_diff.tsv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "filename", "rus_size", "usa_size", "rus_sha256", "usa_sha256",
            "identical", "first_diff", "last_diff", "changed_bytes", "similarity_pct", "classification"
        ], delimiter="\t")
        writer.writeheader()
        writer.writerows(tsv_rows)
        
    (out_dir / "rus_usa_changed_ranges.json").write_text(json.dumps(changed_ranges_data, indent=2), encoding="utf-8")
    
    rus_disc.close()
    usa_disc.close()
    print(f"Differential complete: {len(tsv_rows)} files compared.")

if __name__ == "__main__":
    rus_bin = Path("The_Story_of_Thor_2_[RUS]_(NTSC).bin")
    rus_cue = Path("The_Story_of_Thor_2_[RUS]_(NTSC).cue")
    usa_bin = Path("Legend of Oasis The (USA)/Legend of Oasis, The (USA) (Track 1).bin")
    usa_cue = Path("Legend of Oasis The (USA)/Legend of Oasis, The (USA).cue")
    out = Path("workstreams/T2-GFX-01")
    run_differential(rus_bin, rus_cue, usa_bin, usa_cue, out)
