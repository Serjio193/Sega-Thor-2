#!/usr/bin/env python3
"""tools/carver/interval_db.py — Canonical Central Interval Database.

Manages legal-safe non-overlapping interval partitions across all Saturn
executable modules, enforcing the execution conflict invariant fail-closed.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import bisect
import json


class IntervalConflictError(Exception):
    """Raised when an interval transition violates verification contracts."""
    pass


@dataclass
class MemoryInterval:
    module: str
    generation: str
    cpu: str
    offset_start: int
    offset_end_exclusive: int
    runtime_start: Optional[int]
    runtime_end_exclusive: Optional[int]
    classification: str  # CONFIRMED_CODE, DATA, UNKNOWN, PADDING
    representation: str  # MNEMONIC_PROVEN, RAW_CODE_PENDING, RAW_DATA, RAW_UNKNOWN
    subclass: Optional[str] = None
    evidence_refs: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    parent_provenance: Optional[str] = None
    consumer_refs: List[str] = field(default_factory=list)
    discovered_by: str = "INITIAL_IMPORT"
    discovery_pass: int = 0
    block_id: Optional[str] = None
    instruction_count: Optional[int] = None
    instructions: Optional[List[str]] = None

    @property
    def byte_length(self) -> int:
        return self.offset_end_exclusive - self.offset_start

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "module": self.module,
            "generation": self.generation,
            "cpu": self.cpu,
            "offset_start": self.offset_start,
            "offset_end_exclusive": self.offset_end_exclusive,
            "runtime_start": f"0x{self.runtime_start:08X}" if self.runtime_start is not None else None,
            "runtime_end_exclusive": f"0x{self.runtime_end_exclusive:08X}" if self.runtime_end_exclusive is not None else None,
            "byte_length": self.byte_length,
            "evidence_classification": self.classification,
            "assembly_representation": self.representation,
            "subclass": self.subclass,
            "evidence_refs": list(self.evidence_refs),
            "conflicts": list(self.conflicts),
            "parent_provenance": self.parent_provenance,
            "consumer_refs": list(self.consumer_refs),
            "discovered_by": self.discovered_by,
            "discovery_pass": self.discovery_pass,
        }
        if self.block_id:
            d["block_id"] = self.block_id
        if self.instruction_count is not None:
            d["instruction_count"] = self.instruction_count
        if self.instructions:
            d["instructions"] = list(self.instructions)
        return d


class IntervalDatabase:
    """Orchestrates interval partitions and conflict detection for all modules."""

    def __init__(self) -> None:
        self.modules: Dict[str, Dict[str, Any]] = {}
        self.intervals: Dict[str, List[MemoryInterval]] = {}
        self.conflicts_detected: List[str] = []

    def register_module(
        self,
        name: str,
        size: int,
        vma_base: int,
        cpu: str,
        generation: str = "gen_0",
        iso_sector_start: int = 0,
        expected_sha: str = "",
    ) -> None:
        self.modules[name] = {
            "name": name,
            "size": size,
            "vma_base": vma_base,
            "cpu": cpu,
            "generation": generation,
            "iso_sector_start": iso_sector_start,
            "expected_sha": expected_sha,
        }
        self.intervals[name] = []

    def import_manifest(self, manifest_path: Path) -> None:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        name = data["module"]
        size = data["module_size"]
        vma_str = data.get("module_runtime_base", "0x00000000")
        vma_base = int(vma_str, 16)
        cpu = data.get("processor", "MASTER_SH2")
        gen = data.get("generation", "gen_0")
        sector = data.get("iso_sector_start", 0)
        sha = data.get("expected_output_sha256", "")

        self.register_module(name, size, vma_base, cpu, gen, sector, sha)
        parsed_intervals: List[MemoryInterval] = []

        for r in data.get("ranges", []):
            o_start = r["offset_start"]
            o_end = r["offset_end_exclusive"]
            r_start = int(r["runtime_start"], 16) if r.get("runtime_start") else vma_base + o_start
            r_end = int(r["runtime_end_exclusive"], 16) if r.get("runtime_end_exclusive") else vma_base + o_end
            c = r.get("evidence_classification", "UNKNOWN")
            rep = r.get("assembly_representation", "RAW_UNKNOWN")
            sub = r.get("subclass")
            ev = list(r.get("evidence_refs", []))
            if "original_manifest" not in ev:
                ev.append("original_manifest")

            iv = MemoryInterval(
                module=name,
                generation=gen,
                cpu=cpu,
                offset_start=o_start,
                offset_end_exclusive=o_end,
                runtime_start=r_start,
                runtime_end_exclusive=r_end,
                classification=c,
                representation=rep,
                subclass=sub,
                evidence_refs=ev,
                parent_provenance=r.get("parent_provenance"),
                consumer_refs=list(r.get("consumer_refs", [])),
                discovered_by=r.get("discovered_by", "MANIFEST_IMPORT"),
                discovery_pass=0,
                block_id=r.get("block_id"),
                instruction_count=r.get("instruction_count"),
                instructions=r.get("instructions"),
            )
            parsed_intervals.append(iv)

        self.intervals[name] = parsed_intervals
        self.validate_module(name)

    def validate_module(self, name: str) -> None:
        """Enforces contiguous non-overlapping coverage over [0..module_size]."""
        ivs = sorted(self.intervals[name], key=lambda x: x.offset_start)
        size = self.modules[name]["size"]
        if not ivs:
            raise IntervalConflictError(f"Module '{name}' has no intervals registered.")

        if ivs[0].offset_start != 0:
            raise IntervalConflictError(f"Module '{name}' does not start at offset 0 (starts at {ivs[0].offset_start}).")

        for i in range(len(ivs) - 1):
            cur, nxt = ivs[i], ivs[i + 1]
            if cur.offset_end_exclusive != nxt.offset_start:
                raise IntervalConflictError(
                    f"Module '{name}' gap/overlap at [{cur.offset_start}..{cur.offset_end_exclusive}) "
                    f"and [{nxt.offset_start}..{nxt.offset_end_exclusive})"
                )

        if ivs[-1].offset_end_exclusive != size:
            raise IntervalConflictError(
                f"Module '{name}' ends at {ivs[-1].offset_end_exclusive}, expected {size}."
            )

    def find_interval(self, module: str, offset: int) -> Optional[MemoryInterval]:
        ivs = self.intervals.get(module)
        if not ivs:
            return None
        idx = bisect.bisect_right(ivs, offset, key=lambda x: x.offset_start) - 1
        if 0 <= idx < len(ivs):
            iv = ivs[idx]
            if iv.offset_start <= offset < iv.offset_end_exclusive:
                return iv
        return None

    def find_intervals_overlapping(self, module: str, start: int, end: int) -> List[MemoryInterval]:
        ivs = self.intervals.get(module)
        if not ivs:
            return []
        s_idx = max(0, bisect.bisect_right(ivs, start, key=lambda x: x.offset_start) - 1)
        e_idx = min(len(ivs), bisect.bisect_left(ivs, end, key=lambda x: x.offset_start) + 1)
        return [
            iv for iv in ivs[s_idx:e_idx]
            if not (iv.offset_end_exclusive <= start or iv.offset_start >= end)
        ]

    def split_and_classify(
        self,
        module: str,
        start: int,
        end: int,
        classification: str,
        representation: str,
        subclass: Optional[str] = None,
        evidence: Optional[List[str]] = None,
        discovered_by: str = "CARVER",
        discovery_pass: int = 1,
        block_id: Optional[str] = None,
        instruction_count: Optional[int] = None,
        instructions: Optional[List[str]] = None,
        validate: bool = False,
    ) -> MemoryInterval:
        """Carves [start..end) out of existing interval(s), enforcing conflict rules."""
        if start >= end:
            raise ValueError(f"Invalid range [{start}..{end})")

        mod_meta = self.modules[module]
        vma_base = mod_meta["vma_base"]
        cpu = mod_meta["cpu"]
        gen = mod_meta["generation"]
        overlapping = self.find_intervals_overlapping(module, start, end)

        # Enforce Execution Conflict Rule (Rule 4)
        for old in overlapping:
            if classification == "CONFIRMED_CODE":
                if old.classification == "DATA" and "PROVEN_DATA" in old.evidence_refs:
                    err = f"CONFLICT: Attempt to decode proven DATA as code at {module}:[{start}..{end})"
                    self.conflicts_detected.append(err)
                    raise IntervalConflictError(err)
            elif classification == "DATA":
                if old.classification == "CONFIRMED_CODE":
                    err = f"CONFLICT: Attempt to mark CONFIRMED_CODE as DATA at {module}:[{start}..{end})"
                    self.conflicts_detected.append(err)
                    raise IntervalConflictError(err)

        new_intervals: List[MemoryInterval] = []
        new_iv = MemoryInterval(
            module=module,
            generation=gen,
            cpu=cpu,
            offset_start=start,
            offset_end_exclusive=end,
            runtime_start=vma_base + start,
            runtime_end_exclusive=vma_base + end,
            classification=classification,
            representation=representation,
            subclass=subclass,
            evidence_refs=list(evidence or []),
            discovered_by=discovered_by,
            discovery_pass=discovery_pass,
            block_id=block_id,
            instruction_count=instruction_count,
            instructions=instructions,
        )

        for iv in self.intervals[module]:
            if iv.offset_end_exclusive <= start or iv.offset_start >= end:
                new_intervals.append(iv)
            else:
                # iv overlaps with [start..end)
                if iv.offset_start < start:
                    left = MemoryInterval(
                        module=module,
                        generation=iv.generation,
                        cpu=iv.cpu,
                        offset_start=iv.offset_start,
                        offset_end_exclusive=start,
                        runtime_start=iv.runtime_start,
                        runtime_end_exclusive=vma_base + start,
                        classification=iv.classification,
                        representation=iv.representation,
                        subclass=iv.subclass,
                        evidence_refs=list(iv.evidence_refs),
                        parent_provenance=iv.parent_provenance,
                        consumer_refs=list(iv.consumer_refs),
                        discovered_by=iv.discovered_by,
                        discovery_pass=iv.discovery_pass,
                    )
                    new_intervals.append(left)

                if iv.offset_end_exclusive > end:
                    right = MemoryInterval(
                        module=module,
                        generation=iv.generation,
                        cpu=iv.cpu,
                        offset_start=end,
                        offset_end_exclusive=iv.offset_end_exclusive,
                        runtime_start=vma_base + end,
                        runtime_end_exclusive=iv.runtime_end_exclusive,
                        classification=iv.classification,
                        representation=iv.representation,
                        subclass=iv.subclass,
                        evidence_refs=list(iv.evidence_refs),
                        parent_provenance=iv.parent_provenance,
                        consumer_refs=list(iv.consumer_refs),
                        discovered_by=iv.discovered_by,
                        discovery_pass=iv.discovery_pass,
                    )
                    new_intervals.append(right)

        new_intervals.append(new_iv)
        self.intervals[module] = sorted(new_intervals, key=lambda x: x.offset_start)
        if validate:
            self.validate_module(module)
        return new_iv

    def export_summary(self) -> Dict[str, Any]:
        """Generates legal-safe summary metrics across all registered modules."""
        res: Dict[str, Any] = {
            "modules": {},
            "aggregate": {
                "total_bytes": 0,
                "confirmed_code_bytes": 0,
                "data_bytes": 0,
                "unknown_bytes": 0,
                "padding_bytes": 0,
                "mnemonic_proven_bytes": 0,
                "total_ranges": 0,
                "conflicts_count": len(self.conflicts_detected),
            },
            "conflicts": list(self.conflicts_detected),
        }
        for name, meta in self.modules.items():
            ivs = self.intervals[name]
            stats = {
                "size": meta["size"],
                "cpu": meta["cpu"],
                "vma_base": f"0x{meta['vma_base']:08X}",
                "ranges_count": len(ivs),
                "confirmed_code_bytes": 0,
                "data_bytes": 0,
                "unknown_bytes": 0,
                "padding_bytes": 0,
                "mnemonic_proven_bytes": 0,
                "subclasses": {},
            }
            for iv in ivs:
                bl = iv.byte_length
                if iv.classification == "CONFIRMED_CODE":
                    stats["confirmed_code_bytes"] += bl
                    if iv.representation == "MNEMONIC_PROVEN":
                        stats["mnemonic_proven_bytes"] += bl
                elif iv.classification == "DATA":
                    stats["data_bytes"] += bl
                elif iv.classification == "PADDING":
                    stats["padding_bytes"] += bl
                elif iv.classification == "UNKNOWN":
                    stats["unknown_bytes"] += bl

                if iv.subclass:
                    stats["subclasses"][iv.subclass] = stats["subclasses"].get(iv.subclass, 0) + bl

            res["modules"][name] = stats
            res["aggregate"]["total_bytes"] += meta["size"]
            res["aggregate"]["confirmed_code_bytes"] += stats["confirmed_code_bytes"]
            res["aggregate"]["data_bytes"] += stats["data_bytes"]
            res["aggregate"]["unknown_bytes"] += stats["unknown_bytes"]
            res["aggregate"]["padding_bytes"] += stats["padding_bytes"]
            res["aggregate"]["mnemonic_proven_bytes"] += stats["mnemonic_proven_bytes"]
            res["aggregate"]["total_ranges"] += len(ivs)

        return res
