#!/usr/bin/env python3
"""tools/carver/detector_base.py — Base Interfaces for Saturn Recovery Detectors."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import abc

from .interval_db import IntervalDatabase
from .provenance_dag import ProvenanceDAG


@dataclass
class CandidateRange:
    module: str
    offset_start: int
    offset_end_exclusive: int
    classification: str       # CONFIRMED_CODE, DATA, UNKNOWN, PADDING
    representation: str       # MNEMONIC_PROVEN, RAW_CODE_PENDING, RAW_DATA, RAW_UNKNOWN
    subclass: Optional[str] = None
    confidence: str = "HYPOTHESIS"  # CONFIRMED, HIGH, MEDIUM, HYPOTHESIS
    evidence: List[str] = field(default_factory=list)
    parent_node_id: Optional[str] = None
    detector_name: str = "UNKNOWN_DETECTOR"
    instruction_count: Optional[int] = None
    instructions: Optional[List[str]] = None
    block_id: Optional[str] = None

    @property
    def byte_length(self) -> int:
        return self.offset_end_exclusive - self.offset_start


@dataclass
class CarverContext:
    repo_root: Path
    disc_path: Optional[Path] = None
    cdl_hwr: Optional[bytes] = None
    cdl_lwr: Optional[bytes] = None
    module_bytes: Dict[str, bytes] = field(default_factory=dict)
    pass_number: int = 1
    max_scan_offset: Optional[int] = None


class CarverDetector(abc.ABC):
    """Abstract base detector. Heuristic detectors never directly promote truth."""

    def __init__(self, name: str, category: str, default_confidence: str = "HIGH") -> None:
        self.name = name
        self.category = category
        self.default_confidence = default_confidence

    @abc.abstractmethod
    def detect(
        self,
        db: IntervalDatabase,
        dag: ProvenanceDAG,
        ctx: CarverContext,
    ) -> List[CandidateRange]:
        """Scans intervals, finds candidate ranges, but does not mutate db directly."""
        pass
