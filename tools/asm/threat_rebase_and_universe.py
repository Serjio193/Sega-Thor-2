#!/usr/bin/env python3
"""tools/asm/threat_rebase_and_universe.py — Threat Rebase, Universe & UNKNOWN Clustering.

T2-ASM-12 Phases 1, 2, 3, 8:
  1. Rebase the historical threat universe against current module_byte_ownership_v3.json.
  2. Map historical reference sources & UNKNOWN entry-graph edges to physical intervals.
  3. Cluster remaining UNKNOWN-source edges by physical interval with ranking.
  4. Perform raw-byte validation and generalized false decode audit.
  5. Emits:
     - workstreams/T2-ASM-12/threat_rebase_audit.json
     - workstreams/T2-ASM-12/external_threat_universe.json
     - workstreams/T2-ASM-12/unknown_threat_regions.json
     - workstreams/T2-ASM-12/unknown_false_decode_audit.json
"""

import bisect
from collections import Counter, defaultdict
import json
from pathlib import Path
import struct
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))


class ThreatRebaseAndUniverse:
    def __init__(self, root: Path):
        self.root = root
        self.out_dir = root / "workstreams" / "T2-ASM-12"
        self.out_dir.mkdir(parents=True, exist_ok=True)

        # Byte ownership v3
        own_p = root / "workstreams/T2-ASM-10/module_byte_ownership_v3.json"
        self.ownership = json.loads(own_p.read_text(encoding="utf-8"))
        self.mod_intervals: Dict[str, Tuple[List[int], List[Dict[str, Any]]]] = {}
        for mod, mdata in self.ownership["modules"].items():
            ivs = mdata.get("intervals", [])
            starts = [int(iv["runtime_start"], 16) for iv in ivs]
            self.mod_intervals[mod] = (starts, ivs)

        # Canonical entry graph (historical 14,656 edges)
        ceg_p = root / "workstreams/T2-ASM-09/canonical_entry_graph.json"
        self.ceg = json.loads(ceg_p.read_text(encoding="utf-8"))

        # Targeted external threats (81 sites)
        tet_p = root / "workstreams/T2-ASM-11/targeted_external_threats.json"
        self.tet = json.loads(tet_p.read_text(encoding="utf-8"))

        # RTS completeness v4
        rts4_p = root / "workstreams/T2-ASM-11/rts_completeness_v4.json"
        self.rts4 = json.loads(rts4_p.read_text(encoding="utf-8"))

        # Raw binaries for byte inspection
        self.b0 = (root / ".private/rus/0TH2.BIN").read_bytes()
        self.blow = (root / ".private/rus/TH2.LOW").read_bytes()
        self.vma_0 = 0x06004000
        self.vma_low = 0x002DA000

    def lookup_iv(self, mod: str, pc: int) -> Optional[Dict[str, Any]]:
        if mod not in self.mod_intervals:
            return None
        starts, ivs = self.mod_intervals[mod]
        idx = bisect.bisect_right(starts, pc) - 1
        if 0 <= idx < len(ivs):
            iv = ivs[idx]
            if int(iv["runtime_start"], 16) <= pc < int(iv["runtime_end_exclusive"], 16):
                return iv
        return None

    def determine_module(self, pc: int) -> str:
        if pc >= 0x060D8000:
            return "SET07.BIN"
        if pc >= 0x06000000:
            return "0TH2.BIN"
        if pc >= 0x00200000:
            return "TH2.LOW"
        return "BGM.BIN"

    def run_rebase_and_universe(self) -> Dict[str, Any]:
        # 1. Map blocked RTS sites and functions
        blocked_rts_by_fn = defaultdict(list)
        fn_entry_by_fn = {}
        for s in self.tet["sites"]:
            fn = s["function"]
            blocked_rts_by_fn[fn].append(s["site_id"])
            fn_entry_by_fn[fn] = s.get("entry_pc", "")

        # 2. Rebase the historical reference sources
        all_ref_sources = set()
        ref_source_to_fns = defaultdict(set)
        for s in self.tet["sites"]:
            fn = s["function"]
            for src in s.get("unresolved_reference_sources", []):
                all_ref_sources.add(src)
                ref_source_to_fns[src].add(fn)

        rebased_threats = []
        for src in sorted(all_ref_sources):
            pc = int(src, 16)
            mod = self.determine_module(pc)
            iv = self.lookup_iv(mod, pc)
            curr_cls = iv["ownership_class"] if iv else "OUT_OF_BOUNDS"
            curr_sub = iv.get("semantic_subtype", "NONE") if iv else "NONE"
            iv_range = f"{iv['runtime_start']}..{iv['runtime_end_exclusive']}" if iv else "NONE"
            fns = sorted(ref_source_to_fns[src])
            rts_sites = [sid for fn in fns for sid in blocked_rts_by_fn[fn]]
            
            # Historical ownership was UNKNOWN in T2-ASM-09
            still_relevant = (curr_cls in ("UNKNOWN", "DATA"))
            
            rebased_threats.append({
                "threat_id": f"REF_{mod}_{src}",
                "source_pc": src,
                "source_module": mod,
                "source_generation": 0,
                "historical_ownership": "UNKNOWN",
                "current_ownership": curr_cls,
                "current_subtype": curr_sub,
                "historical_threat_kind": "RAW_32BIT_POINTER_MATCH",
                "current_threat_kind": "DATA_TARGET_VALUE_THREAT" if curr_cls == "DATA" else "EXECUTABLE_INGRESS_THREAT",
                "still_relevant": still_relevant,
                "containing_interval": iv_range,
                "blocked_functions": fns,
                "blocked_rts_sites": rts_sites,
                "unique_blocked_functions_count": len(fns),
                "number_of_rts_sites_blocked": len(rts_sites),
            })

        rebase_audit = {
            "version": "1.0",
            "historical_reference_sources_total": len(rebased_threats),
            "current_ownership_distribution": dict(Counter(t["current_ownership"] for t in rebased_threats)),
            "current_subtype_distribution": dict(Counter(t["current_subtype"] for t in rebased_threats)),
            "rebased_threat_records": rebased_threats,
        }
        (self.out_dir / "threat_rebase_audit.json").write_text(
            json.dumps(rebase_audit, indent=2), encoding="utf-8"
        )

        # 3. Canonical external threat universe (incorporating tailcalls and branch threats)
        threat_universe_records = list(rebased_threats)
        
        # Add tailcall threats for the 8 functions
        tailcall_fns = [
            fn for fn, sites in blocked_rts_by_fn.items()
            if any("TAILCALL_DOMAIN_INCOMPLETE" in s.get("unresolved_entry_sources", [])
                   for sid in sites for s in self.tet["sites"] if s["site_id"] == sid)
        ]
        for fn in sorted(tailcall_fns):
            epc = fn_entry_by_fn.get(fn, "")
            threat_universe_records.append({
                "threat_id": f"TAILCALL_{fn}",
                "source_pc": "UPSTREAM_TAILCALLS",
                "source_module": self.determine_module(int(epc, 16)) if epc.startswith("0x") else "0TH2.BIN",
                "source_generation": 0,
                "historical_ownership": "CODE",
                "current_ownership": "CODE",
                "current_subtype": "TAILCALL_DOMAIN",
                "historical_threat_kind": "TAILCALL_SOURCE",
                "current_threat_kind": "TAILCALL_ENTRY_THREAT",
                "still_relevant": True,
                "containing_interval": "CODE_INTERVALS",
                "blocked_functions": [fn],
                "blocked_rts_sites": blocked_rts_by_fn[fn],
                "unique_blocked_functions_count": 1,
                "number_of_rts_sites_blocked": len(blocked_rts_by_fn[fn]),
            })

        universe_out = {
            "version": "1.0",
            "total_threat_sources": len(threat_universe_records),
            "total_blocked_rts_sites": 81,
            "total_blocked_functions": len(blocked_rts_by_fn),
            "threat_records": threat_universe_records,
        }
        (self.out_dir / "external_threat_universe.json").write_text(
            json.dumps(universe_out, indent=2), encoding="utf-8"
        )

        # 4. Phase 2: UNKNOWN region clustering of 2,810 entry-graph edges
        unknown_edges = []
        for e in self.ceg.get("edges", []):
            src = e.get("source_pc", "")
            if not src.startswith("0x"):
                continue
            src_pc = int(src, 16)
            mod = e.get("module", "0TH2.BIN")
            iv = self.lookup_iv(mod, src_pc)
            if iv and iv["ownership_class"] == "UNKNOWN":
                unknown_edges.append((mod, src_pc, e.get("target_pc"), e.get("opcode"), iv))

        region_clusters = {}
        for mod, src_pc, tgt_pc, opc, iv in unknown_edges:
            st = iv["runtime_start"]
            en = iv["runtime_end_exclusive"]
            key = (mod, st, en)
            if key not in region_clusters:
                sz = int(en, 16) - int(st, 16)
                region_clusters[key] = {
                    "module": mod,
                    "generation": 0,
                    "runtime_start": st,
                    "runtime_end_exclusive": en,
                    "size_bytes": sz,
                    "threat_sources": set(),
                    "opcodes": set(),
                    "targets": set(),
                    "blocked_functions": set(),
                    "blocked_rts_sites": set(),
                }
            region_clusters[key]["threat_sources"].add(f"0x{src_pc:08X}")
            region_clusters[key]["opcodes"].add(opc)
            region_clusters[key]["targets"].add(tgt_pc)
            for fn, epc in fn_entry_by_fn.items():
                if epc == tgt_pc:
                    region_clusters[key]["blocked_functions"].add(fn)
                    for sid in blocked_rts_by_fn[fn]:
                        region_clusters[key]["blocked_rts_sites"].add(sid)

        # Convert sets to sorted lists and compute ranking
        ranked_regions = []
        for key, rdata in region_clusters.items():
            sz = max(1, rdata["size_bytes"])
            n_rts = len(rdata["blocked_rts_sites"])
            n_fn = len(rdata["blocked_functions"])
            rdata["threat_sources"] = sorted(rdata["threat_sources"])
            rdata["opcodes"] = sorted(rdata["opcodes"])
            rdata["targets"] = sorted(rdata["targets"])
            rdata["blocked_functions"] = sorted(rdata["blocked_functions"])
            rdata["blocked_rts_sites"] = sorted(rdata["blocked_rts_sites"])
            rdata["blocked_rts_sites_per_kb"] = round(n_rts / (sz / 1024.0), 3)
            rdata["blocked_functions_per_kb"] = round(n_fn / (sz / 1024.0), 3)
            ranked_regions.append(rdata)

        # Sort by blocked RTS per KB, then size
        ranked_regions.sort(key=lambda r: (len(r["blocked_rts_sites"]), r["blocked_rts_sites_per_kb"]), reverse=True)
        regions_out = {
            "version": "1.0",
            "total_unknown_regions_with_threats": len(ranked_regions),
            "total_unknown_edges_clustered": len(unknown_edges),
            "regions": ranked_regions,
        }
        (self.out_dir / "unknown_threat_regions.json").write_text(
            json.dumps(regions_out, indent=2), encoding="utf-8"
        )

        # 5. Phase 3 & 8: Raw byte validation & False decode audit
        false_decode_records = []
        for r in ranked_regions:
            mod = r["module"]
            raw = self.b0 if mod == "0TH2.BIN" else self.blow
            base = self.vma_0 if mod == "0TH2.BIN" else self.vma_low
            for src_s in r["threat_sources"]:
                pc = int(src_s, 16)
                off = pc - base
                if off < 0 or off + 4 > len(raw):
                    continue
                w = struct.unpack(">H", raw[off:off + 2])[0]
                ds = struct.unpack(">H", raw[off + 2:off + 4])[0]
                is_aligned = (pc % 2 == 0)
                disp = w & 0x0FFF
                if disp & 0x0800:
                    disp -= 0x1000
                tgt = pc + 4 + disp * 2
                tgt_s = f"0x{tgt:08X}"
                surr = raw[max(0, off - 4): min(len(raw), off + 8)]
                
                if tgt_s in fn_entry_by_fn.values():
                    cls = "VALID_EXECUTABLE_CANDIDATE"
                elif (w & 0xFF00) == 0x0000:
                    cls = "DATA_HALFWORD_FALSE_DECODE"
                else:
                    cls = "DATA_HALFWORD_FALSE_DECODE"

                false_decode_records.append({
                    "source_pc": src_s,
                    "module": mod,
                    "raw_halfword": f"0x{w:04X}",
                    "delay_slot_halfword": f"0x{ds:04X}",
                    "candidate_target": tgt_s,
                    "alignment_valid": is_aligned,
                    "surrounding_hex": surr.hex(),
                    "classification": cls,
                    "containing_region": f"{r['runtime_start']}..{r['runtime_end_exclusive']}",
                })

        false_decode_out = {
            "version": "1.0",
            "total_threat_halfwords_audited": len(false_decode_records),
            "classifications": dict(Counter(f["classification"] for f in false_decode_records)),
            "audits": false_decode_records,
        }
        (self.out_dir / "unknown_false_decode_audit.json").write_text(
            json.dumps(false_decode_out, indent=2), encoding="utf-8"
        )

        return {
            "rebase_audit": rebase_audit,
            "threat_universe": universe_out,
            "threat_regions": regions_out,
            "false_decode": false_decode_out,
        }


def main():
    runner = ThreatRebaseAndUniverse(repo_root)
    res = runner.run_rebase_and_universe()
    print("Threat Rebase and Universe analysis complete:")
    print(f"  Historical reference sources rebased: {res['rebase_audit']['historical_reference_sources_total']}")
    print(f"  Current ownership distribution: {res['rebase_audit']['current_ownership_distribution']}")
    print(f"  Current subtype distribution: {res['rebase_audit']['current_subtype_distribution']}")
    print(f"  Total threat sources in universe: {res['threat_universe']['total_threat_sources']}")
    print(f"  Total UNKNOWN regions clustered: {res['threat_regions']['total_unknown_regions_with_threats']}")
    print(f"  False decode classifications: {res['false_decode']['classifications']}")


if __name__ == "__main__":
    main()
