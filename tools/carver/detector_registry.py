#!/usr/bin/env python3
"""tools/carver/detector_registry.py — Prioritized Saturn Detector Registry."""

from typing import Dict, List, Optional
from .detector_base import CarverDetector, CandidateRange, CarverContext
from .interval_db import IntervalDatabase
from .provenance_dag import ProvenanceDAG


class DetectorRegistry:
    """Manages detector ordering and candidate acquisition."""

    def __init__(self) -> None:
        self.detectors: List[CarverDetector] = []
        self._by_name: Dict[str, CarverDetector] = {}

    def register(self, detector: CarverDetector) -> None:
        if detector.name in self._by_name:
            raise ValueError(f"Detector '{detector.name}' already registered")
        self.detectors.append(detector)
        self._by_name[detector.name] = detector

    def get(self, name: str) -> Optional[CarverDetector]:
        return self._by_name.get(name)

    def run_all(
        self,
        db: IntervalDatabase,
        dag: ProvenanceDAG,
        ctx: CarverContext,
    ) -> List[CandidateRange]:
        """Runs registered detectors in priority order, accumulating candidate ranges."""
        all_candidates: List[CandidateRange] = []
        for det in self.detectors:
            cands = det.detect(db, dag, ctx)
            all_candidates.extend(cands)
        return all_candidates
