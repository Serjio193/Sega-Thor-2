#!/usr/bin/env python3
"""tools/carver/provenance_dag.py — Provenance DAG & Graph Expansion Engine.

Tracks object discovery lineage and enforces fail-closed parent qualification:
only CONFIRMED nodes may generate authoritative child candidates.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
import json


@dataclass
class ProvenanceNode:
    node_id: str
    node_type: str  # CODE_BLOCK, LITERAL_POOL, POINTER_TABLE, JUMP_TARGET, MODULE, RESOURCE
    status: str     # CONFIRMED, PROBABLE, HYPOTHESIS
    module: str
    offset_start: int
    offset_end_exclusive: int
    runtime_address: Optional[int] = None
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProvenanceEdge:
    source_id: str
    target_id: str
    relation: str   # LITERAL_REF, BRANCH_TARGET, CALL_TARGET, TABLE_ENTRY, LOADER_MAPPING, CONSUMER_REF
    confidence: str # CONFIRMED, PROBABLE, HYPOTHESIS
    evidence_ref: str


class ProvenanceDAG:
    """Directed Acyclic Graph modeling Saturn recovery evidence and provenance."""

    def __init__(self) -> None:
        self.nodes: Dict[str, ProvenanceNode] = {}
        self.edges: List[ProvenanceEdge] = []
        self.children_by_parent: Dict[str, List[ProvenanceEdge]] = {}
        self.parents_by_child: Dict[str, List[ProvenanceEdge]] = {}

    def add_node(
        self,
        node_id: str,
        node_type: str,
        status: str,
        module: str,
        offset_start: int,
        offset_end_exclusive: int,
        runtime_address: Optional[int] = None,
        evidence_refs: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProvenanceNode:
        if node_id in self.nodes:
            node = self.nodes[node_id]
            # Update status if new status is stronger
            if status == "CONFIRMED" and node.status != "CONFIRMED":
                node.status = "CONFIRMED"
            for ev in (evidence_refs or []):
                if ev not in node.evidence_refs:
                    node.evidence_refs.append(ev)
            return node

        node = ProvenanceNode(
            node_id=node_id,
            node_type=node_type,
            status=status,
            module=module,
            offset_start=offset_start,
            offset_end_exclusive=offset_end_exclusive,
            runtime_address=runtime_address,
            evidence_refs=list(evidence_refs or []),
            metadata=dict(metadata or {}),
        )
        self.nodes[node_id] = node
        self.children_by_parent[node_id] = []
        self.parents_by_child[node_id] = []
        return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        confidence: str,
        evidence_ref: str,
    ) -> None:
        if source_id not in self.nodes or target_id not in self.nodes:
            raise KeyError(f"Source '{source_id}' or Target '{target_id}' not in DAG")

        edge = ProvenanceEdge(
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            confidence=confidence,
            evidence_ref=evidence_ref,
        )
        self.edges.append(edge)
        self.children_by_parent[source_id].append(edge)
        self.parents_by_child[target_id].append(edge)

    def can_authoritatively_expand(self, parent_id: str) -> bool:
        """Rule 5: Only CONFIRMED nodes may generate authoritative child candidates."""
        node = self.nodes.get(parent_id)
        if not node:
            return False
        return node.status == "CONFIRMED"

    def get_ancestor_lineage(self, node_id: str) -> List[Dict[str, Any]]:
        """Rule 6: Every node tracks why it is known back to canonical roots."""
        lineage: List[Dict[str, Any]] = []
        visited: Set[str] = set()

        def dfs(cur_id: str, depth: int) -> None:
            if cur_id in visited:
                return
            visited.add(cur_id)
            node = self.nodes.get(cur_id)
            if not node:
                return
            lineage.append({
                "node_id": cur_id,
                "type": node.node_type,
                "status": node.status,
                "depth": depth,
                "evidence_refs": node.evidence_refs,
            })
            for edge in self.parents_by_child.get(cur_id, []):
                dfs(edge.source_id, depth + 1)

        dfs(node_id, 0)
        return lineage

    def export_summary(self) -> Dict[str, Any]:
        """Produces provenance_graph_summary.json metrics."""
        type_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}
        for n in self.nodes.values():
            type_counts[n.node_type] = type_counts.get(n.node_type, 0) + 1
            status_counts[n.status] = status_counts.get(n.status, 0) + 1

        rel_counts: Dict[str, int] = {}
        for e in self.edges:
            rel_counts[e.relation] = rel_counts.get(e.relation, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "nodes_by_type": type_counts,
            "nodes_by_status": status_counts,
            "edges_by_relation": rel_counts,
            "confirmed_nodes": status_counts.get("CONFIRMED", 0),
            "probable_nodes": status_counts.get("PROBABLE", 0),
            "hypothesis_nodes": status_counts.get("HYPOTHESIS", 0),
        }
