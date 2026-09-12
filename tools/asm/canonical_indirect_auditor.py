#!/usr/bin/env python3
"""tools/asm/canonical_indirect_auditor.py — Re-Audit of Entire Canonical Indirect Inventory.

Verifies that every canonical indirect site (1,465 JSR, 121 JMP, 2 BRAF, 638 RTS)
is located in proven CODE, correctly decoded from raw binary bytes, and free of
any DATA or PADDING overlap. Re-confirms the 7 false BSRF sites as non-code data.
Derives the canonical indirect site count (expected: 2,226).
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import struct
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


@dataclass
class IndirectSiteAuditRecord:
    site_pc: str
    site_id: str
    module: str
    opcode_id: str
    raw_bytes_hex: str
    instruction_decode: str
    byte_ownership: str  # CONFIRMED_CODE, DATA, PADDING, UNKNOWN
    cfg_ownership: bool
    data_padding_overlap: bool
    overlap_details: Optional[str]
    function_or_block_ownership: str
    is_legitimate_canonical_site: bool


class CanonicalIndirectAuditor:
    """Audits every canonical indirect site against raw bytes, manifests, and tables."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.b0 = (repo_root / ".private/rus/0TH2.BIN").read_bytes()
        self.blow = (repo_root / ".private/rus/TH2.LOW").read_bytes()
        self.vma_0 = 0x06004000
        self.vma_low = 0x002DA000

        sc_path = repo_root / "workstreams/T2-ASM-08/final_indirect_scorecard.json"
        self.scorecard = json.loads(sc_path.read_text(encoding="utf-8"))
        self.canonical_sites = self.scorecard.get("sites", [])

        ft_path = repo_root / "workstreams/T2-ASM-08/false_decode_pointer_tables.json"
        self.false_tables = json.loads(ft_path.read_text(encoding="utf-8"))

        fb_path = repo_root / "workstreams/T2-ASM-06/function_boundaries.json"
        self.fb = json.loads(fb_path.read_text(encoding="utf-8"))
        self.functions = self.fb.get("functions", [])

        # Load manifests
        mf0_path = repo_root / "asm/manifests/0TH2.BIN.json"
        mflow_path = repo_root / "asm/manifests/TH2.LOW.json"
        self.mf0 = json.loads(mf0_path.read_text(encoding="utf-8"))
        self.mflow = json.loads(mflow_path.read_text(encoding="utf-8"))

        self._build_manifest_maps()
        self._build_carved_code_set()

    def _build_carved_code_set(self):
        """Builds confirmed code set including manifest code and carved CFG closure."""
        self.carved_code: Dict[str, Set[int]] = {"0TH2.BIN": set(), "TH2.LOW": set()}
        for mod, mf in [("0TH2.BIN", self.mf0), ("TH2.LOW", self.mflow)]:
            for r in mf.get("ranges", []):
                if r.get("evidence_classification") == "CONFIRMED_CODE":
                    st = int(r["runtime_start"], 16)
                    en = int(r["runtime_end_exclusive"], 16)
                    self.carved_code[mod].update(range(st, en))

        # Also add CFG worklist closure
        from tools.carver.thor_decoder import dump_all_valid_with_thor_sh2
        from collections import deque

        for mod, raw, base in [("0TH2.BIN", self.b0, self.vma_0), ("TH2.LOW", self.blow, self.vma_low)]:
            insts = dump_all_valid_with_thor_sh2(self.repo_root, mod, base, raw)
            seeds = set(self.carved_code[mod])
            seeds.add(base)
            worklist = deque(sorted(list(seeds)))
            visited = set(self.carved_code[mod])
            terminals = {"RTS", "RTE", "BRA", "JMP", "BRAF"}

            # Exclude pointer tables
            for t_mod, t_st, t_en in self.pointer_table_intervals:
                if mod == t_mod:
                    seeds = {s for s in seeds if not (t_st <= s < t_en)}

            while worklist:
                pc = worklist.popleft()
                curr = pc
                while curr < base + len(raw):
                    ins = insts.get(curr)
                    if not ins:
                        break
                    visited.add(curr)
                    visited.add(curr + 1)
                    if ins.target_vma and (ins.is_branch or ins.is_call):
                        t = ins.target_vma
                        if base <= t < base + len(raw) and t not in visited:
                            visited.add(t)
                            worklist.append(t)
                    if ins.has_delay_slot:
                        d_pc = curr + 2
                        d_ins = insts.get(d_pc)
                        if d_ins:
                            visited.add(d_pc)
                            visited.add(d_pc + 1)
                        if ins.opcode_id in terminals:
                            break
                        curr += 4
                    else:
                        if ins.opcode_id in terminals:
                            break
                        curr += 2
            self.carved_code[mod] = visited

    def _build_manifest_maps(self):
        self.manifest_ranges: Dict[str, List[Dict[str, Any]]] = {
            "0TH2.BIN": self.mf0.get("ranges", []),
            "TH2.LOW": self.mflow.get("ranges", []),
        }

        # Pointer table intervals
        self.pointer_table_intervals: List[Tuple[str, int, int]] = []
        for tbl in self.false_tables.get("tables", []):
            self.pointer_table_intervals.append(
                (tbl.get("module", "0TH2.BIN"), int(tbl["table_start"], 16), int(tbl["table_end"], 16))
            )

    def read_word(self, module: str, pc: int) -> Optional[int]:
        raw = self.b0 if module == "0TH2.BIN" else self.blow
        base = self.vma_0 if module == "0TH2.BIN" else self.vma_low
        off = pc - base
        if 0 <= off + 2 <= len(raw):
            return struct.unpack(">H", raw[off:off + 2])[0]
        return None

    def find_function_ownership(self, module: str, pc: int) -> str:
        matching = [
            f for f in self.functions
            if f["module"] == module and int(f["entry_pc"], 16) <= pc
        ]
        if matching:
            best = max(matching, key=lambda x: int(x["entry_pc"], 16))
            return best.get("function_id", f"entry_{best['entry_pc']}")
        return "UNKNOWN_FUNCTION"

    def audit_site(self, site: Dict[str, Any]) -> IndirectSiteAuditRecord:
        pc_s = site["runtime_pc"]
        pc = int(pc_s, 16)
        mod = site["module"]
        op = site["opcode_id"]
        site_id = site.get("site_id", f"{mod}_{pc_s}")

        w = self.read_word(mod, pc)
        raw_hex = f"0x{w:04X}" if w is not None else "NONE"

        decode_valid = False
        decoded_mnemonic = "UNKNOWN"
        if w is not None:
            if op == "RTS" and w == 0x000B:
                decode_valid = True
                decoded_mnemonic = "RTS"
            elif op == "BRAF" and (w & 0xF0FF) == 0x0023:
                rn = (w >> 8) & 0x0F
                decode_valid = True
                decoded_mnemonic = f"BRAF R{rn}"
            elif op == "JSR" and (w & 0xF0FF) == 0x400B:
                rn = (w >> 8) & 0x0F
                decode_valid = True
                decoded_mnemonic = f"JSR @R{rn}"
            elif op == "JMP" and (w & 0xF0FF) == 0x402B:
                rn = (w >> 8) & 0x0F
                decode_valid = True
                decoded_mnemonic = f"JMP @R{rn}"

        byte_ownership = "UNKNOWN"
        data_pad_overlap = False
        overlap_details = None

        ranges = self.manifest_ranges.get(mod, [])
        for r in ranges:
            st = int(r["runtime_start"], 16)
            en = int(r["runtime_end_exclusive"], 16)
            if st <= pc < en:
                cls = r.get("evidence_classification", "UNKNOWN")
                byte_ownership = cls
                if cls in ("DATA", "PADDING"):
                    data_pad_overlap = True
                    overlap_details = f"Manifest {cls} [{r['runtime_start']}..{r['runtime_end_exclusive']})"
                break

        for t_mod, t_st, t_en in self.pointer_table_intervals:
            if mod == t_mod and t_st <= pc < t_en:
                data_pad_overlap = True
                overlap_details = f"Pointer table [{hex(t_st)}..{hex(t_en)})"
                byte_ownership = "DATA"

        if not data_pad_overlap and pc in self.carved_code.get(mod, set()):
            byte_ownership = "CONFIRMED_CODE"

        func_owner = self.find_function_ownership(mod, pc)
        cfg_ownership = (pc in self.carved_code.get(mod, set()))
        is_legitimate = (decode_valid and not data_pad_overlap and byte_ownership == "CONFIRMED_CODE")

        return IndirectSiteAuditRecord(
            site_pc=pc_s,
            site_id=site_id,
            module=mod,
            opcode_id=op,
            raw_bytes_hex=raw_hex,
            instruction_decode=decoded_mnemonic,
            byte_ownership=byte_ownership,
            cfg_ownership=cfg_ownership,
            data_padding_overlap=data_pad_overlap,
            overlap_details=overlap_details,
            function_or_block_ownership=func_owner,
            is_legitimate_canonical_site=is_legitimate,
        )

    def audit_all(self) -> Dict[str, Any]:
        records: List[IndirectSiteAuditRecord] = []
        op_counts: Dict[str, int] = {}
        legit_counts: Dict[str, int] = {}

        for s in self.canonical_sites:
            rec = self.audit_site(s)
            records.append(rec)
            op = rec.opcode_id
            op_counts[op] = op_counts.get(op, 0) + 1
            if rec.is_legitimate_canonical_site:
                legit_counts[op] = legit_counts.get(op, 0) + 1

        total_checked = len(records)
        total_legit = sum(1 for r in records if r.is_legitimate_canonical_site)
        total_invalid = total_checked - total_legit

        false_bsrf_audits = []
        for s in self.false_tables.get("false_instruction_pcs", []):
            rec = self.audit_site({
                "runtime_pc": s,
                "module": "0TH2.BIN",
                "opcode_id": "BSRF",
                "site_id": f"0TH2.BIN_{s}",
            })
            false_bsrf_audits.append(asdict(rec))

        payload = {
            "historical_indirect_site_count": 2233,
            "false_positive_bsrf_count": len(false_bsrf_audits),
            "canonical_indirect_sites_checked": total_checked,
            "canonical_indirect_sites_legitimate": total_legit,
            "canonical_indirect_sites_invalid": total_invalid,
            "opcode_distribution": op_counts,
            "legitimate_distribution": legit_counts,
            "all_sites_in_confirmed_code": (total_invalid == 0),
            "zero_data_padding_overlap": all(not r.data_padding_overlap for r in records),
            "false_bsrf_confirmed_data": all(r["data_padding_overlap"] for r in false_bsrf_audits),
            "audited_records": [asdict(r) for r in records],
            "false_bsrf_records": false_bsrf_audits,
        }

        return payload


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    auditor = CanonicalIndirectAuditor(repo_root)
    result = auditor.audit_all()

    out_path = repo_root / "workstreams/T2-ASM-09/canonical_indirect_site_audit.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"Audited {result['canonical_indirect_sites_checked']} canonical indirect sites:")
    print(f"  Legitimate in CODE: {result['canonical_indirect_sites_legitimate']}")
    print(f"  Invalid / Overlap:  {result['canonical_indirect_sites_invalid']}")
    print(f"  Opcode breakdown:   {result['opcode_distribution']}")
    print(f"  All in confirmed code: {result['all_sites_in_confirmed_code']}")
    print(f"  Zero data/padding overlap: {result['zero_data_padding_overlap']}")
    print(f"Wrote audit to {out_path}")


if __name__ == '__main__':
    main()
