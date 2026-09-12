#!/usr/bin/env python3
"""tools/asm/object_provenance_analyzer.py — Object & Struct Field Provenance Engine.

Classifies base registers and pointers of struct-derived indirect call sites
into concrete object types (Engine State, Actor Entity, System Vector, Script VM,
Jump Table Dispatch), and generates a comprehensive struct field inventory.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import json
import struct
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


@dataclass
class ObjectTypeDefinition:
    type_id: str
    name: str
    category: str
    base_ram_ranges: List[str]
    description: str
    callback_fields: Dict[int, str]
    site_count: int


@dataclass
class StructFieldRecord:
    object_type: str
    field_displacement: Optional[int]
    field_name: str
    semantic_role: str
    access_width: str
    sites: List[str]
    dynamic_count: int
    cold_count: int


class ObjectProvenanceAnalyzer:
    """Classifies object instances and tracks struct field layouts."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.struct_sites_data = json.loads(
            (repo_root / "workstreams/T2-ASM-07/struct_indirect_sites.json").read_text(encoding="utf-8")
        )
        self.b0 = (repo_root / ".private/rus/0TH2.BIN").read_bytes()
        self.blow = (repo_root / ".private/rus/TH2.LOW").read_bytes()

    def classify_site_object_type(self, site: Dict[str, Any]) -> str:
        """Determines the object archetype for a struct-derived site."""
        pat = site["access_pattern"]
        prov = site["base_provenance"]
        cand = site.get("literal_target_candidate")
        disp = site.get("field_displacement")
        reg = site.get("base_register")

        if pat == "STRUCT_INDEXED":
            return "JUMP_TABLE_DISPATCH"

        if prov == "GLOBAL_RAM" and cand:
            addr = int(cand, 16)
            if 0x06000000 <= addr < 0x06004000:
                return "SYSTEM_VECTOR"
            elif addr in (0x06088D14, 0x06088D10, 0x06088D00):
                return "ENGINE_STATE"
            elif 0x06080000 <= addr < 0x060A0000:
                return "ACTOR_ENTITY"

        if prov == "LOCAL_STACK":
            return "LOCAL_STACK_FRAME"

        if prov == "ARG_REG":
            return "ACTOR_ENTITY"

        if disp in (4, 8, 12, 16, 20, 24, 28, 32, 40):
            return "ACTOR_ENTITY"

        if pat == "STRUCT_PTR" and disp == 0:
            if reg in ("R0", "R1", "R2", "R3"):
                return "SCRIPT_VM"
            return "ACTOR_ENTITY"

        return "UNKNOWN_OBJECT"

    def analyze(self) -> Dict[str, Any]:
        records = self.struct_sites_data["records"]
        struct_records = [
            r for r in records if r["access_pattern"] in ("STRUCT_FIELD", "STRUCT_PTR", "STRUCT_INDEXED")
        ]

        # Definitions
        types: Dict[str, ObjectTypeDefinition] = {
            "ENGINE_STATE": ObjectTypeDefinition(
                type_id="ENGINE_STATE",
                name="Main Game Engine State",
                category="GLOBAL_SINGLETON",
                base_ram_ranges=["0x06088D00..0x06088E00"],
                description="Global engine coordinator handling stage state, timers, and subsystem dispatchers.",
                callback_fields={24: "subsystem_dispatch_callback", 12: "stage_event_callback"},
                site_count=0,
            ),
            "ACTOR_ENTITY": ObjectTypeDefinition(
                type_id="ACTOR_ENTITY",
                name="Actor / Entity Instance",
                category="DYNAMIC_HEAP_OBJECT",
                base_ram_ranges=["0x060828CC..0x060A0000"],
                description="Player, enemy, NPC, projectile, or room entity struct holding update and draw callbacks.",
                callback_fields={
                    0: "state_action_callback",
                    4: "animation_update_callback",
                    8: "render_callback",
                    12: "interaction_callback",
                    16: "damage_callback",
                    20: "despawn_callback",
                    24: "secondary_action_callback",
                    28: "collision_callback",
                    32: "timer_callback",
                    40: "aux_callback",
                },
                site_count=0,
            ),
            "SCRIPT_VM": ObjectTypeDefinition(
                type_id="SCRIPT_VM",
                name="Script Virtual Machine Context",
                category="INTERPRETER_STATE",
                base_ram_ranges=["0x06090000..0x060A0000"],
                description="Bytecode and event trigger interpreter execution context with dynamic opcode handlers.",
                callback_fields={0: "opcode_handler_callback"},
                site_count=0,
            ),
            "SYSTEM_VECTOR": ObjectTypeDefinition(
                type_id="SYSTEM_VECTOR",
                name="Saturn System Vector",
                category="LOW_RAM_SYSTEM",
                base_ram_ranges=["0x06000000..0x06004000"],
                description="Sega Saturn 1st stage boot / BIOS / SMPC / sound system call jump vector.",
                callback_fields={0: "bios_smpc_entry"},
                site_count=0,
            ),
            "JUMP_TABLE_DISPATCH": ObjectTypeDefinition(
                type_id="JUMP_TABLE_DISPATCH",
                name="Indexed Jump Table Dispatcher",
                category="INDEXED_TABLE",
                base_ram_ranges=["0x06004000..0x06086C00"],
                description="Indexed callback array dispatched via MOV.L @(R0, Rm), Rn.",
                callback_fields={-1: "indexed_table_entry"},
                site_count=0,
            ),
            "LOCAL_STACK_FRAME": ObjectTypeDefinition(
                type_id="LOCAL_STACK_FRAME",
                name="Stack Frame Context",
                category="STACK_FRAME",
                base_ram_ranges=["0x060FFFF0..0x06100000"],
                description="Function pointer preserved in stack frame across subroutine calls.",
                callback_fields={0: "stack_restored_callback"},
                site_count=0,
            ),
            "UNKNOWN_OBJECT": ObjectTypeDefinition(
                type_id="UNKNOWN_OBJECT",
                name="Unclassified Struct",
                category="UNRESOLVED",
                base_ram_ranges=[],
                description="Struct reference whose base instance has not yet been bounded to a known heap range.",
                callback_fields={},
                site_count=0,
            ),
        }

        # Field inventory grouping: (obj_type, disp) -> StructFieldRecord
        fields: Dict[str, StructFieldRecord] = {}

        for s in struct_records:
            obj_type = self.classify_site_object_type(s)
            types[obj_type].site_count += 1

            disp = s.get("field_displacement")
            disp_key = -1 if disp is None else disp
            field_key = f"{obj_type}_disp_{disp_key}"

            field_name = types[obj_type].callback_fields.get(disp_key, f"field_offset_0x{disp_key:02X}" if disp_key >= 0 else "indexed_entry")
            sem_role = "CALLBACK_FUNCTION_POINTER" if disp_key >= 0 else "INDEXED_BRANCH_TARGET"

            if field_key not in fields:
                fields[field_key] = StructFieldRecord(
                    object_type=obj_type,
                    field_displacement=disp,
                    field_name=field_name,
                    semantic_role=sem_role,
                    access_width="LONG",
                    sites=[],
                    dynamic_count=0,
                    cold_count=0,
                )

            fields[field_key].sites.append(s["site_id"])
            if s["is_dynamically_active"]:
                fields[field_key].dynamic_count += 1
            else:
                fields[field_key].cold_count += 1

        return {
            "object_types": {k: asdict(v) for k, v in types.items()},
            "struct_field_inventory": {k: asdict(v) for k, v in fields.items()},
        }


def main():
    repo_root = Path(".")
    analyzer = ObjectProvenanceAnalyzer(repo_root)
    result = analyzer.analyze()

    out_types = repo_root / "workstreams/T2-ASM-07/object_types.json"
    out_types.write_text(json.dumps(result["object_types"], indent=2), encoding="utf-8")

    out_fields = repo_root / "workstreams/T2-ASM-07/struct_field_inventory.json"
    out_fields.write_text(json.dumps(result["struct_field_inventory"], indent=2), encoding="utf-8")

    print(f"Object types written to {out_types}")
    print(f"Struct field inventory written to {out_fields}")
    print("Object type breakdown:")
    for tid, tdef in result["object_types"].items():
        if tdef["site_count"] > 0:
            print(f"  {tid}: {tdef['site_count']} sites")
    print(f"Total distinct struct fields mapped: {len(result['struct_field_inventory'])}")


if __name__ == "__main__":
    main()
