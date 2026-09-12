import hashlib
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from typing import Dict, List, Optional
from tools.disc.census_saturn_cd import Mode1RawImage, parse_saturn_header, parse_iso9660, sha256_path

class SaturnDisc:
    def __init__(self, bin_path: Path, cue_path: Optional[Path] = None):
        self.bin_path = bin_path
        self.cue_path = cue_path
        self.image = Mode1RawImage(bin_path)
        self.header = parse_saturn_header(self.image.read_user_sector(0))
        self.volume_id, self.raw_entries = parse_iso9660(self.image)
        self.track2_path: Optional[Path] = None
        if cue_path and cue_path.exists():
            t2_cand = bin_path.parent / bin_path.name.replace("Track 1", "Track 2")
            if t2_cand.exists() and t2_cand != bin_path:
                self.track2_path = t2_cand

        self.files: Dict[str, dict] = {}
        for entry in self.raw_entries:
            if not entry['is_dir']:
                # Normalize filename (remove trailing dot if ISO9660 produced it)
                norm_name = entry['path'].rstrip('.')
                self.files[norm_name] = entry

    def close(self):
        self.image.close()

    def read_extent(self, lba: int, size: int) -> bytes:
        if lba < self.image.sector_count:
            # Check if extent spans beyond track 1
            sectors = (size + 2047) // 2048
            if lba + sectors <= self.image.sector_count:
                return self.image.read_extent(lba, size)
            # Partially in track 1
            part1_sectors = self.image.sector_count - lba
            part1_bytes = self.image.read_extent(lba, part1_sectors * 2048)
            remaining = size - len(part1_bytes)
            return part1_bytes + (b'\x00' * remaining)
        # In track 2 / audio
        if self.track2_path and self.track2_path.exists():
            with open(self.track2_path, "rb") as f:
                # Track 2 starts at LBA 35008 (standard index 01 with 150 pregap)
                track2_lba = max(0, lba - (self.image.sector_count + 150))
                f.seek(track2_lba * 2352)
                return f.read(size)
        return b'\x00' * size

    def hash_extent(self, lba: int, size: int) -> str:
        data = self.read_extent(lba, size)
        return hashlib.sha256(data).hexdigest()

    def read_file(self, path: str) -> bytes:
        norm = path.rstrip('.')
        if norm not in self.files:
            raise KeyError(f"File not found on disc: {path}")
        entry = self.files[norm]
        return self.read_extent(entry['lba'], entry['size'])

    def hash_file(self, path: str) -> str:
        norm = path.rstrip('.')
        if norm not in self.files:
            raise KeyError(f"File not found on disc: {path}")
        entry = self.files[norm]
        return self.hash_extent(entry['lba'], entry['size'])

    def get_file_list(self) -> List[str]:
        return sorted(list(self.files.keys()))

    def get_summary(self) -> dict:
        return {
            "bin_path": str(self.bin_path),
            "image_size": self.bin_path.stat().st_size,
            "image_sha256": sha256_path(self.bin_path),
            "sector_format": "MODE1/2352",
            "sector_count": self.image.sector_count,
            "cue_path": str(self.cue_path) if self.cue_path else None,
            "cue_sha256": sha256_path(self.cue_path) if self.cue_path and self.cue_path.exists() else None,
            "volume_id": self.volume_id,
            "product_code": self.header.get("product_code", ""),
            "version": self.header.get("version", ""),
            "date": self.header.get("date", ""),
            "regions": self.header.get("regions", ""),
            "title": self.header.get("title", ""),
            "file_count": len(self.files),
            "files": {
                name: {
                    "lba": entry["lba"],
                    "size": entry["size"],
                    "sha256": self.hash_extent(entry["lba"], entry["size"])
                }
                for name, entry in sorted(self.files.items())
            }
        }
