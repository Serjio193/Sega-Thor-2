#!/usr/bin/env python3
"""tools/asm/callback_field_analyzer.py — Callback Field & Table Analyzer.

Discovers store instructions to struct callback fields, identifies static
function pointer arrays (callback tables), and maps state machine transition
domains to bound indirect call site targets.
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
class CallbackFieldWriterRecord:
    writer_pc: str
    module: str
    target_object_type: str
    field_displacement: int
    stored_code_target: str
    writer_function: Optional[str]
    provenance: str


@dataclass
class CallbackTableRecord:
    table_address: str
    module: str
    entry_count: int
    targets: List[str]
    bounding_mechanism: str  # CONSTANT_LITERAL_ARRAY, SWITCH_CASE, MASKED_INDEX
    associated_sites: List[str]


class CallbackFieldAnalyzer:
    """Discovers field writers and callback dispatch tables."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.b0 = (repo_root / ".private/rus/0TH2.BIN").read_bytes()
        self.blow = (repo_root / ".private/rus/TH2.LOW").read_bytes()
        self.fb = json.loads((repo_root / "workstreams/T2-ASM-06/function_boundaries.json").read_text(encoding="utf-8"))
        self.struct_sites = json.loads(
            (repo_root / "workstreams/T2-ASM-07/struct_indirect_sites.json").read_text(encoding="utf-8")
        )

    def is_valid_code_target(self, addr: int) -> bool:
        if (addr & 1) != 0:
            return False
        if 0x06004000 <= addr < 0x06086C00 - 2:
            off = addr - 0x06004000
            w = struct.unpack('>H', self.b0[off:off + 2])[0]
            if w == 0x0000 or w == 0xFFFF:
                return False
            return True
        if 0x002DA000 <= addr < 0x002FE800 - 2:
            off = addr - 0x002DA000
            w = struct.unpack('>H', self.blow[off:off + 2])[0]
            if w == 0x0000 or w == 0xFFFF:
                return False
            return True
        return False

    def find_enclosing_function(self, pc: int) -> Optional[str]:
        for f in self.fb["functions"]:
            entry = int(f["entry_pc"], 16)
            length = f["byte_length"]
            if entry <= pc < entry + length:
                return f["function_id"]
        return None

    def trace_store_literal(self, raw: bytes, vma: int, store_pc: int, src_reg: int) -> Optional[int]:
        """Traces backwards to see if src_reg was loaded with a code address literal."""
        for step in range(1, 24):
            prev_pc = store_pc - step * 2
            off = prev_pc - vma
            if off < 0 or off + 2 > len(raw):
                break
            w = struct.unpack('>H', raw[off:off + 2])[0]
            op_h = (w >> 12) & 0xF
            wn = (w >> 8) & 0xF
            # MOV.L @(disp, PC), Rn
            if op_h == 0xD and wn == src_reg:
                disp = (w & 0xFF) * 4
                lit_pc = ((prev_pc & ~3) + 4) + disp
                lit_off = lit_pc - vma
                if 0 <= lit_off + 4 <= len(raw):
                    val = struct.unpack('>I', raw[lit_off:lit_off + 4])[0]
                    if self.is_valid_code_target(val):
                        return val
                break
        return None

    def recover_field_writers(self) -> List[CallbackFieldWriterRecord]:
        writers: List[CallbackFieldWriterRecord] = []
        modules = [("0TH2.BIN", self.b0, 0x06004000), ("TH2.LOW", self.blow, 0x002DA000)]

        for mod_name, raw, vma in modules:
            for pc in range(vma, vma + len(raw) - 2, 2):
                off = pc - vma
                w = struct.unpack('>H', raw[off:off + 2])[0]
                op_h = (w >> 12) & 0xF
                wn = (w >> 8) & 0xF
                wm = (w >> 4) & 0xF
                disp = (w & 0xF) * 4

                # MOV.L Rm, @(disp, Rn) (0x1nm d)
                if op_h == 1 and disp in (0, 4, 8, 12, 16, 20, 24, 28, 32, 40):
                    tgt = self.trace_store_literal(raw, vma, pc, wm)
                    if tgt is not None:
                        fn = self.find_enclosing_function(pc)
                        writers.append(
                            CallbackFieldWriterRecord(
                                writer_pc=f"0x{pc:08X}",
                                module=mod_name,
                                target_object_type="ACTOR_ENTITY",
                                field_displacement=disp,
                                stored_code_target=f"0x{tgt:08X}",
                                writer_function=fn,
                                provenance="PC_LITERAL_STORE",
                            )
                        )
                # MOV.L Rm, @Rn (0x2nm2)
                elif (w & 0xF00F) == 0x2002:
                    tgt = self.trace_store_literal(raw, vma, pc, wm)
                    if tgt is not None:
                        fn = self.find_enclosing_function(pc)
                        writers.append(
                            CallbackFieldWriterRecord(
                                writer_pc=f"0x{pc:08X}",
                                module=mod_name,
                                target_object_type="ACTOR_ENTITY",
                                field_displacement=0,
                                stored_code_target=f"0x{tgt:08X}",
                                writer_function=fn,
                                provenance="PC_LITERAL_STORE_BASE",
                            )
                        )
        return writers

    def recover_callback_tables(self) -> List[CallbackTableRecord]:
        tables: List[CallbackTableRecord] = []
        modules = [("0TH2.BIN", self.b0, 0x06004000), ("TH2.LOW", self.blow, 0x002DA000)]

        # Map sites using indexed or pointer tables
        indexed_sites = [
            s for s in self.struct_sites["records"] if s["access_pattern"] in ("STRUCT_INDEXED", "STRUCT_PTR")
        ]
        site_pcs = {int(s["runtime_pc"], 16): s["site_id"] for s in indexed_sites}

        for mod_name, raw, vma in modules:
            i = 0
            while i <= len(raw) - 16:
                entries: List[int] = []
                cur = i
                while cur <= len(raw) - 4:
                    val = struct.unpack('>I', raw[cur:cur + 4])[0]
                    if self.is_valid_code_target(val):
                        entries.append(val)
                        cur += 4
                    else:
                        break
                if len(entries) >= 4:
                    tbl_addr = vma + i
                    # Check if associated with any site
                    assoc = []
                    for spc, sid in site_pcs.items():
                        if abs(spc - tbl_addr) < 512:
                            assoc.append(sid)

                    tables.append(
                        CallbackTableRecord(
                            table_address=f"0x{tbl_addr:08X}",
                            module=mod_name,
                            entry_count=len(entries),
                            targets=[f"0x{e:08X}" for e in entries],
                            bounding_mechanism="CONSTANT_LITERAL_ARRAY",
                            associated_sites=assoc,
                        )
                    )
                    i = cur
                else:
                    i += 4
        return tables

    def analyze(self) -> Dict[str, Any]:
        writers = self.recover_field_writers()
        tables = self.recover_callback_tables()

        # Group writers by (object_type, displacement)
        field_domain_map: Dict[str, Set[str]] = {}
        for w in writers:
            k = f"{w.target_object_type}_disp_{w.field_displacement}"
            if k not in field_domain_map:
                field_domain_map[k] = set()
            field_domain_map[k].add(w.stored_code_target)

        state_callbacks = {k: sorted(list(v)) for k, v in field_domain_map.items()}

        return {
            "writers_summary": {
                "total_field_writers": len(writers),
                "fields_with_proven_writers": len(state_callbacks),
            },
            "writers": [asdict(w) for w in writers],
            "callback_tables_summary": {
                "total_tables": len(tables),
                "total_targets_in_tables": sum(t.entry_count for t in tables),
            },
            "callback_tables": [asdict(t) for t in tables],
            "state_machine_callbacks": state_callbacks,
        }


def main():
    repo_root = Path(".")
    analyzer = CallbackFieldAnalyzer(repo_root)
    result = analyzer.analyze()

    out_tables = repo_root / "workstreams/T2-ASM-07/callback_tables.json"
    out_tables.write_text(
        json.dumps(
            {
                "summary": result["callback_tables_summary"],
                "tables": result["callback_tables"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    out_state = repo_root / "workstreams/T2-ASM-07/state_machine_callbacks.json"
    out_state.write_text(
        json.dumps(
            {
                "summary": result["writers_summary"],
                "state_machine_callbacks": result["state_machine_callbacks"],
                "writers": result["writers"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Callback tables written to {out_tables}")
    print(f"State machine callbacks written to {out_state}")
    print(f"Total proven field writers: {result['writers_summary']['total_field_writers']}")
    print(f"Fields with proven writers: {result['writers_summary']['fields_with_proven_writers']}")
    print(f"Total callback tables: {result['callback_tables_summary']['total_tables']}")


if __name__ == "__main__":
    main()
