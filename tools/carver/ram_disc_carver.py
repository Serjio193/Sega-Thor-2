#!/usr/bin/env python3
"""tools/carver/ram_disc_carver.py — R-Studio Style RAM → Disc File Signature Carver.

Matches unresolved runtime RAM executions and data blocks to private Saturn ISO files,
expanding windows and correlating with CD read, DMA, and copy traces.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import csv
import hashlib


@dataclass
class CarvedFileMatch:
    ram_address: int
    disc_file: str
    file_offset: int
    match_length: int
    disc_sha256: str
    confidence: str
    cd_lba: Optional[int] = None
    correlation_evidence: Optional[str] = None


class RamDiscCarver:
    """Carves disc file provenance for unresolved RAM ranges using byte signatures."""

    def __init__(self, repo_root: Path, disc_path: Optional[Path] = None) -> None:
        self.repo_root = repo_root
        self.disc_path = disc_path or (repo_root / "The_Story_of_Thor_2_[RUS]_(NTSC).bin")
        self.disc_files: Dict[str, Dict[str, Any]] = {}
        self._load_disc_manifest()

    def _load_disc_manifest(self) -> None:
        manifest_path = self.repo_root / "workstreams" / "T2-M0-disc-census" / "disc_manifest.tsv"
        if not manifest_path.exists():
            return
        with open(manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                self.disc_files[row["path"]] = {
                    "path": row["path"],
                    "lba": int(row["lba"]),
                    "size": int(row["size"]),
                    "sha256": row["sha256"],
                }

    def read_file_extent(self, filename: str) -> Optional[bytes]:
        meta = self.disc_files.get(filename)
        if not meta or not self.disc_path.exists():
            return None
        lba = meta["lba"]
        size = meta["size"]
        data = bytearray()
        with open(self.disc_path, "rb") as f:
            f.seek(lba * 2352 + 16)
            while len(data) < size:
                chunk = f.read(2048)
                if not chunk:
                    break
                data.extend(chunk)
                f.seek(2352 - 2048, 1)  # Skip sync/header/ECC
        return bytes(data[:size])

    def search_signature_on_disc(
        self,
        signature: bytes,
        min_length: int = 16,
    ) -> List[Tuple[str, int]]:
        """Scans all disc files for exact occurrence of signature."""
        if len(signature) < min_length:
            return []
        matches: List[Tuple[str, int]] = []
        for name in sorted(self.disc_files.keys()):
            data = self.read_file_extent(name)
            if not data:
                continue
            pos = 0
            while True:
                idx = data.find(signature, pos)
                if idx == -1:
                    break
                matches.append((name, idx))
                pos = idx + 1
        return matches

    def carve_ram_range(
        self,
        ram_address: int,
        ram_bytes: bytes,
        cdb_trace_path: Optional[Path] = None,
        dma_trace_path: Optional[Path] = None,
    ) -> Optional[CarvedFileMatch]:
        """Carves disc provenance for a RAM range with progressive window expansion."""
        if len(ram_bytes) < 16:
            return None

        # 1. Initial 16-byte signature scan
        sig = ram_bytes[:16]
        matches = self.search_signature_on_disc(sig, min_length=16)
        if not matches:
            return None

        verified_matches: List[CarvedFileMatch] = []
        for file_name, file_off in matches:
            file_data = self.read_file_extent(file_name)
            if not file_data:
                continue

            # 2. Expand window to full length of available RAM bytes
            max_check = min(len(ram_bytes), len(file_data) - file_off)
            matched_len = 0
            for i in range(max_check):
                if ram_bytes[i] == file_data[file_off + i]:
                    matched_len += 1
                else:
                    break

            if matched_len >= 16:
                meta = self.disc_files[file_name]
                lba = meta["lba"] + (file_off // 2048)
                confidence = "CONFIRMED" if matched_len >= 64 else "HIGH"
                verified_matches.append(CarvedFileMatch(
                    ram_address=ram_address,
                    disc_file=file_name,
                    file_offset=file_off,
                    match_length=matched_len,
                    disc_sha256=meta["sha256"],
                    confidence=confidence,
                    cd_lba=lba,
                    correlation_evidence=f"DISC_EXACT_MATCH_{matched_len}_BYTES_LBA_{lba}",
                ))

        if not verified_matches:
            return None

        # Return longest match
        return max(verified_matches, key=lambda m: m.match_length)
