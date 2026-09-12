#!/usr/bin/env python3
"""tools/asm/struct_site_isolator.py — Isolates struct-derived indirect sites.

Analyzes backward instruction flow across all 855 unresolved indirect sites,
extracting base registers, displacements, and access patterns, and reconciling
with the 551 dynamically active sites.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import struct
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


@dataclass
class StructSiteRecord:
    site_id: str
    runtime_pc: str
    module: str
    opcode_id: str
    category: str
    is_dynamically_active: bool
    target_register: Optional[str]
    access_pattern: str  # STRUCT_FIELD, STRUCT_PTR, STRUCT_INDEXED, CALLEE_SAVED_LITERAL, LEAF_RTS, STACK_RESTORED_RTS, UNKNOWN
    base_register: Optional[str]
    field_displacement: Optional[int]
    base_provenance: str  # ARG_REG, GLOBAL_RAM, LOCAL_STACK, PC_LITERAL, UNKNOWN
    literal_target_candidate: Optional[str]
    defining_pc: Optional[str]


class StructSiteIsolator:
    """Isolates struct-derived and callee-saved function pointer sites."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.scorecard = json.loads((repo_root / "workstreams/T2-ASM-06/indirect_resolution_scorecard.json").read_text(encoding="utf-8"))
        self.dyn_data = json.loads((repo_root / "workstreams/T2-ASM-06/indirect_dynamic_targets.json").read_text(encoding="utf-8"))
        self.b0 = (repo_root / ".private/rus/0TH2.BIN").read_bytes()
        self.blow = (repo_root / ".private/rus/TH2.LOW").read_bytes()
        self.vma_0 = 0x06004000
        self.vma_low = 0x002DA000
        self.dyn_map = {s["site_id"]: s for s in self.dyn_data["sites"]}

    def read_word(self, module: str, pc: int) -> Optional[int]:
        raw = self.b0 if module == "0TH2.BIN" else self.blow
        vma = self.vma_0 if module == "0TH2.BIN" else self.vma_low
        off = pc - vma
        if 0 <= off + 2 <= len(raw):
            return struct.unpack('>H', raw[off:off + 2])[0]
        return None

    def read_long(self, module: str, pc: int) -> Optional[int]:
        raw = self.b0 if module == "0TH2.BIN" else self.blow
        vma = self.vma_0 if module == "0TH2.BIN" else self.vma_low
        off = pc - vma
        if 0 <= off + 4 <= len(raw):
            return struct.unpack('>I', raw[off:off + 4])[0]
        return None

    def _trace_base_provenance(self, module: str, defining_pc: int, base_reg: int) -> Tuple[str, Optional[str]]:
        """Determine origin of base register."""
        if 4 <= base_reg <= 7:
            return "ARG_REG", None
        if base_reg == 14 or base_reg == 15:
            return "LOCAL_STACK", None
        # Check backward from defining_pc
        for step in range(1, 16):
            prev_pc = defining_pc - step * 2
            w = self.read_word(module, prev_pc)
            if w is None:
                break
            op_h = (w >> 12) & 0xF
            wn = (w >> 8) & 0xF
            if wn == base_reg and op_h == 0xD:  # MOV.L @(disp, PC), base_reg
                disp = (w & 0xFF) * 4
                lit_pc = ((prev_pc & ~3) + 4) + disp
                val = self.read_long(module, lit_pc)
                if val is not None:
                    return "GLOBAL_RAM", f"0x{val:08X}"
            elif wn == base_reg and (w & 0xF00F) == 0x6003:  # MOV Rm, Rn
                rm = (w >> 4) & 0xF
                if 4 <= rm <= 7:
                    return "ARG_REG", None
        return "UNKNOWN", None

    def analyze_call_jump_site(self, site: Dict[str, Any], is_dyn: bool) -> StructSiteRecord:
        sid = site["site_id"]
        pc = int(site["runtime_pc"], 16)
        mod = site["module"]
        op = site["opcode_id"]
        cat = site["category"]

        w_site = self.read_word(mod, pc)
        rn = (w_site >> 8) & 0xF if w_site is not None else 0
        cur_reg = rn

        pattern = "UNKNOWN"
        base_reg_name = None
        displacement = None
        base_prov = "UNKNOWN"
        lit_cand = None
        def_pc = None

        for step in range(1, 256):
            prev_pc = pc - step * 2
            w = self.read_word(mod, prev_pc)
            if w is None:
                break
            # Halt if crossing terminal RTS/RTE
            if (w & 0xF0FF) in (0x000B, 0x002B) and step > 2:
                break
            # Calls clobber scratch registers (R0-R7), but preserve R8-R14
            if ((w >> 12) & 0xF) == 0xB or (w & 0xF0FF) == 0x400B:
                if cur_reg <= 7:
                    break
                continue

            op_h = (w >> 12) & 0xF
            wn = (w >> 8) & 0xF
            wm = (w >> 4) & 0xF

            # 1. MOV.L @(disp, Rm), Rn
            if op_h == 0x5 and wn == cur_reg:
                disp = (w & 0xF) * 4
                pattern = "STRUCT_FIELD"
                base_reg_name = f"R{wm}"
                displacement = disp
                def_pc = f"0x{prev_pc:08X}"
                base_prov, lit_cand = self._trace_base_provenance(mod, prev_pc, wm)
                break
            # 2. MOV.L @Rm, Rn
            elif (w & 0xF00F) == 0x6002 and wn == cur_reg:
                pattern = "STRUCT_PTR"
                base_reg_name = f"R{wm}"
                displacement = 0
                def_pc = f"0x{prev_pc:08X}"
                base_prov, lit_cand = self._trace_base_provenance(mod, prev_pc, wm)
                break
            # 3. MOV.L @(R0, Rm), Rn
            elif (w & 0xF00F) == 0x000E and wn == cur_reg:
                pattern = "STRUCT_INDEXED"
                base_reg_name = f"R{wm}"
                displacement = None
                def_pc = f"0x{prev_pc:08X}"
                base_prov, lit_cand = self._trace_base_provenance(mod, prev_pc, wm)
                break
            # 4. MOV.L @R15+, Rn
            elif (w & 0xF0FF) == 0x60F6 and wn == cur_reg:
                pattern = "STACK_RESTORED_REG"
                base_reg_name = "R15"
                displacement = None
                def_pc = f"0x{prev_pc:08X}"
                base_prov = "LOCAL_STACK"
                break
            # 5. MOV.L @(disp, PC), Rn
            elif op_h == 0xD and wn == cur_reg:
                disp = (w & 0xFF) * 4
                lit_pc = ((prev_pc & ~3) + 4) + disp
                val = self.read_long(mod, lit_pc)
                def_pc = f"0x{prev_pc:08X}"
                if val is not None:
                    lit_cand = f"0x{val:08X}"
                    pattern = "CALLEE_SAVED_LITERAL" if cur_reg >= 8 else "SCRATCH_LITERAL"
                break
            # 6. MOV Rm, Rn
            elif (w & 0xF00F) == 0x6003 and wn == cur_reg:
                cur_reg = wm
                continue

        return StructSiteRecord(
            site_id=sid,
            runtime_pc=f"0x{pc:08X}",
            module=mod,
            opcode_id=op,
            category=cat,
            is_dynamically_active=is_dyn,
            target_register=f"R{rn}",
            access_pattern=pattern,
            base_register=base_reg_name,
            field_displacement=displacement,
            base_provenance=base_prov,
            literal_target_candidate=lit_cand,
            defining_pc=def_pc,
        )

    def analyze_rts_site(self, site: Dict[str, Any], is_dyn: bool) -> StructSiteRecord:
        sid = site["site_id"]
        pc = int(site["runtime_pc"], 16)
        mod = site["module"]
        op = site["opcode_id"]
        cat = site["category"]

        # Scan backwards up to 64 instructions to check for PR save/restore
        pattern = "LEAF_RTS"
        for step in range(1, 64):
            prev_pc = pc - step * 2
            w = self.read_word(mod, prev_pc)
            if w is None:
                break
            # Earlier function RTS/RTE marks function boundary
            if (w & 0xF0FF) in (0x000B, 0x002B) and step > 2:
                break
            # LDS.L @R15+, PR (0x4F26)
            if w == 0x4F26:
                pattern = "STACK_RESTORED_RTS"
                break
            # STS.L PR, @-R15 (0x4F22)
            elif w == 0x4F22:
                pattern = "STACK_RESTORED_RTS"
                break

        return StructSiteRecord(
            site_id=sid,
            runtime_pc=f"0x{pc:08X}",
            module=mod,
            opcode_id=op,
            category=cat,
            is_dynamically_active=is_dyn,
            target_register="PR",
            access_pattern=pattern,
            base_register=None,
            field_displacement=None,
            base_provenance="STACK" if pattern == "STACK_RESTORED_RTS" else "CALLER_PR",
            literal_target_candidate=None,
            defining_pc=None,
        )

    def isolate_all(self) -> Dict[str, Any]:
        unresolved_sites = [s for s in self.scorecard["sites"] if s["resolution_status"] == "UNRESOLVED"]
        records: List[StructSiteRecord] = []

        pattern_summary: Dict[str, int] = {}
        dynamic_unresolved = 0
        cold_unresolved = 0

        for site in unresolved_sites:
            sid = site["site_id"]
            dyn_info = self.dyn_map.get(sid, {})
            is_dyn = bool(dyn_info.get("dynamically_executed_in_cdl_or_traces", False))
            if is_dyn:
                dynamic_unresolved += 1
            else:
                cold_unresolved += 1

            if site["opcode_id"] == "RTS":
                rec = self.analyze_rts_site(site, is_dyn)
            else:
                rec = self.analyze_call_jump_site(site, is_dyn)

            records.append(rec)
            pattern_summary[rec.access_pattern] = pattern_summary.get(rec.access_pattern, 0) + 1

        return {
            "summary": {
                "total_unresolved_sites": len(unresolved_sites),
                "dynamic_unresolved_sites": dynamic_unresolved,
                "cold_unresolved_sites": cold_unresolved,
                "pattern_breakdown": pattern_summary,
            },
            "records": [asdict(r) for r in records],
        }


def main():
    repo_root = Path(".")
    isolator = StructSiteIsolator(repo_root)
    result = isolator.isolate_all()

    out_path = repo_root / "workstreams/T2-ASM-07/struct_indirect_sites.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"Isolated struct sites written to {out_path}")
    print(f"  Total analyzed: {result['summary']['total_unresolved_sites']}")
    print(f"  Dynamic: {result['summary']['dynamic_unresolved_sites']}")
    print(f"  Cold: {result['summary']['cold_unresolved_sites']}")
    print("  Pattern breakdown:")
    for pat, count in sorted(result["summary"]["pattern_breakdown"].items()):
        print(f"    {pat}: {count}")


if __name__ == "__main__":
    main()
