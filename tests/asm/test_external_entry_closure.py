#!/usr/bin/env python3
"""tests/asm/test_external_entry_closure.py — Integration Tests for T2-ASM-12.

Verifies:
  1. Threat rebase audit integrity against module byte ownership V3.
  2. Targeted data certificates consumer chain proof (0 open consumers).
  3. Canonical entry graph V2 hygiene (100% CODE or root sources).
  4. RTS completeness V5 soundness audit (INVALID_RESOLVED_CERTIFICATES == 0).
  5. Byte ownership partition V4 and caller threat frontier accounting.
"""

import bisect
from pathlib import Path
import json
import pytest

_repo_root = Path(__file__).resolve().parent.parent.parent


def test_threat_rebase_integrity():
    p = _repo_root / "workstreams/T2-ASM-12/threat_rebase_audit.json"
    assert p.exists(), f"Missing {p}"
    audit = json.loads(p.read_text(encoding="utf-8"))
    assert audit["historical_reference_sources_total"] == 99
    assert audit["current_ownership_distribution"].get("DATA") == 99
    assert audit["current_subtype_distribution"].get("DATA_LITERAL_POOL") == 99


def test_targeted_data_certificates_consumer_chains():
    p = _repo_root / "workstreams/T2-ASM-12/targeted_data_certificates.json"
    assert p.exists(), f"Missing {p}"
    data = json.loads(p.read_text(encoding="utf-8"))
    certs = data["certificates"]
    assert len(certs) == 99
    # Every single literal pool reference must have a verified consumer chain
    open_consumers = [c for c in certs if c["primary_classification"] == "DATA_LITERAL_CONSUMER_OPEN"]
    assert len(open_consumers) == 0, f"Found open consumers: {open_consumers}"


def test_canonical_entry_graph_v2_code_only():
    p = _repo_root / "workstreams/T2-ASM-12/canonical_entry_graph_v2.json"
    assert p.exists(), f"Missing {p}"
    ceg = json.loads(p.read_text(encoding="utf-8"))
    edges = ceg["edges"]
    assert len(edges) >= 9500
    # Verify no source PC is in DATA or UNKNOWN
    own = json.loads((_repo_root / "workstreams/T2-ASM-10/module_byte_ownership_v3.json").read_text(encoding="utf-8"))
    starts = {
        m: [int(iv["runtime_start"], 16) for iv in own["modules"][m]["intervals"]]
        for m in own["modules"]
    }
    for e in edges:
        src = e.get("source_pc", "")
        if src.startswith("0x"):
            src_pc = int(src, 16)
            mod = e.get("module", "0TH2.BIN")
            idx = bisect.bisect_right(starts.get(mod, []), src_pc) - 1
            iv = own["modules"][mod]["intervals"][idx] if idx >= 0 else None
            assert iv is not None and iv["ownership_class"] == "CODE", f"Edge source {src} in {mod} is not in confirmed CODE!"


def test_rts_v5_soundness_audit_clean():
    p = _repo_root / "workstreams/T2-ASM-12/rts_v5_soundness_audit.json"
    assert p.exists(), f"Missing {p}"
    audit = json.loads(p.read_text(encoding="utf-8"))
    assert audit["total_sites_audited"] == 638
    assert audit["resolved_sites_count"] == 510
    assert audit["unresolved_sites_count"] == 128
    assert audit["invalid_resolved_certificates_count"] == 0
    assert audit["audit_passed"] is True


def test_byte_partition_v4_and_frontier():
    p = _repo_root / "workstreams/T2-ASM-12/executable_byte_partition_v4.json"
    assert p.exists(), f"Missing {p}"
    part = json.loads(p.read_text(encoding="utf-8"))
    assert part["processor_breakdown"]["SH2_UNKNOWN_BYTES"] == 498392
    assert part["processor_breakdown"]["SH2_UNKNOWN_BYTES_STILL_ON_CALLER_THREAT_FRONTIER"] == 202
    assert part["processor_breakdown"]["SH2_UNKNOWN_BYTES_REACHABILITY_EXCLUDED"] == 498392 - 202
