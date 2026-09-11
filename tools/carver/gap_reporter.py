#!/usr/bin/env python3
"""tools/carver/gap_reporter.py — UNKNOWN Gap Audit & Campaign Prioritization.

Analyzes every residual UNKNOWN interval across all modules, evaluates boundary
context, reference density, and CDL activity, and clusters gaps into campaigns.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import struct

from .interval_db import IntervalDatabase, MemoryInterval
from .detector_base import CarverContext


@dataclass
class GapReportItem:
    module: str
    generation: str
    offset_start: int
    offset_end_exclusive: int
    byte_length: int
    runtime_start: Optional[str]
    runtime_end_exclusive: Optional[str]
    left_neighbor: Optional[Dict[str, Any]]
    right_neighbor: Optional[Dict[str, Any]]
    pointers_into_gap: int = 0
    runtime_reads: int = 0
    runtime_executions: int = 0
    literal_references: int = 0
    candidate_subclasses: List[str] = field(default_factory=list)
    priority: str = "P5_HEURISTIC"  # P1_EXECUTION, P2_PROVENANCE, P3_CONTROL_FLOW, P4_DATA_CONSUMER, P5_HEURISTIC
    campaign_id: str = "campaign_misc"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "generation": self.generation,
            "offset_start": self.offset_start,
            "offset_end_exclusive": self.offset_end_exclusive,
            "byte_length": self.byte_length,
            "runtime_start": self.runtime_start,
            "runtime_end_exclusive": self.runtime_end_exclusive,
            "left_neighbor": self.left_neighbor,
            "right_neighbor": self.right_neighbor,
            "pointers_into_gap": self.pointers_into_gap,
            "runtime_reads": self.runtime_reads,
            "runtime_executions": self.runtime_executions,
            "literal_references": self.literal_references,
            "candidate_subclasses": self.candidate_subclasses,
            "priority": self.priority,
            "campaign_id": self.campaign_id,
        }


class GapReporter:
    """Audits UNKNOWN gaps and groups them into prioritized recovery campaigns."""

    def __init__(self, db: IntervalDatabase) -> None:
        self.db = db

    def audit_gaps(self, ctx: CarverContext) -> Dict[str, Any]:
        gap_items: List[GapReportItem] = []
        campaign_map: Dict[str, List[Dict[str, Any]]] = {}

        for mod_name, meta in self.db.modules.items():
            ivs = self.db.intervals[mod_name]
            vma_base = meta["vma_base"]
            raw = ctx.module_bytes.get(mod_name)
            cdl = ctx.cdl_hwr if (0x06000000 <= vma_base < 0x06100000) else (ctx.cdl_lwr if (0x00200000 <= vma_base < 0x00300000) else None)
            cdl_offset = (vma_base - 0x06000000) if (0x06000000 <= vma_base < 0x06100000) else ((vma_base - 0x00200000) if (0x00200000 <= vma_base < 0x00300000) else 0)

            for i, iv in enumerate(ivs):
                if iv.classification != "UNKNOWN":
                    continue

                left_info = ivs[i - 1].to_dict() if i > 0 else None
                right_info = ivs[i + 1].to_dict() if i < len(ivs) - 1 else None

                # Count runtime reads and executions in gap
                reads = 0
                execs = 0
                if cdl:
                    for off in range(iv.offset_start, iv.offset_end_exclusive):
                        r_idx = cdl_offset + off
                        if 0 <= r_idx < len(cdl):
                            b = cdl[r_idx]
                            if b & 1:
                                execs += 1
                            if b & 2:
                                reads += 1

                # Priority assignment per Section 9 hierarchy
                if execs > 0:
                    priority = "P1_EXECUTION"
                elif iv.parent_provenance:
                    priority = "P2_PROVENANCE"
                elif left_info and left_info.get("evidence_classification") == "CONFIRMED_CODE":
                    priority = "P3_CONTROL_FLOW"
                elif reads > 0:
                    priority = "P4_DATA_CONSUMER"
                else:
                    priority = "P5_HEURISTIC"

                # Assign campaign by size and address locality
                camp_idx = iv.offset_start // 0x10000
                campaign_id = f"{mod_name}_block_{camp_idx:02X}"

                item = GapReportItem(
                    module=mod_name,
                    generation=iv.generation,
                    offset_start=iv.offset_start,
                    offset_end_exclusive=iv.offset_end_exclusive,
                    byte_length=iv.byte_length,
                    runtime_start=f"0x{iv.runtime_start:08X}" if iv.runtime_start is not None else None,
                    runtime_end_exclusive=f"0x{iv.runtime_end_exclusive:08X}" if iv.runtime_end_exclusive is not None else None,
                    left_neighbor={"class": left_info["evidence_classification"], "subclass": left_info.get("subclass"), "bytes": left_info["byte_length"]} if left_info else None,
                    right_neighbor={"class": right_info["evidence_classification"], "subclass": right_info.get("subclass"), "bytes": right_info["byte_length"]} if right_info else None,
                    runtime_reads=reads,
                    runtime_executions=execs,
                    priority=priority,
                    campaign_id=campaign_id,
                )
                gap_items.append(item)
                campaign_map.setdefault(campaign_id, []).append(item.to_dict())

        # Sort gaps by priority then size
        p_order = {"P1_EXECUTION": 0, "P2_PROVENANCE": 1, "P3_CONTROL_FLOW": 2, "P4_DATA_CONSUMER": 3, "P5_HEURISTIC": 4}
        gap_items.sort(key=lambda x: (p_order.get(x.priority, 5), -x.byte_length))

        summary = {
            "total_unknown_gaps": len(gap_items),
            "total_unknown_bytes": sum(g.byte_length for g in gap_items),
            "gaps_by_priority": {
                "P1_EXECUTION": sum(1 for g in gap_items if g.priority == "P1_EXECUTION"),
                "P2_PROVENANCE": sum(1 for g in gap_items if g.priority == "P2_PROVENANCE"),
                "P3_CONTROL_FLOW": sum(1 for g in gap_items if g.priority == "P3_CONTROL_FLOW"),
                "P4_DATA_CONSUMER": sum(1 for g in gap_items if g.priority == "P4_DATA_CONSUMER"),
                "P5_HEURISTIC": sum(1 for g in gap_items if g.priority == "P5_HEURISTIC"),
            },
            "total_campaigns": len(campaign_map),
            "campaigns": {k: {"count": len(v), "bytes": sum(x["byte_length"] for x in v)} for k, v in campaign_map.items()},
            "top_gaps": [g.to_dict() for g in gap_items[:50]],
        }
        return summary
