#!/usr/bin/env python3
"""tools/carver/executed_pc_union.py — Canonical Historical Execution Union.

Consolidates all accepted runtime execution evidence across:
- CDL traces (HWR, LWR, gameplay, screen) -> EXECUTED_BYTE_EVIDENCE
- D9 indirect control flow evidence and return sites -> EXECUTED_INSTRUCTION_PC_EVIDENCE
- ASM workstream checkpoints (T2-ASM-01, 02, 03, 04) -> EXECUTED_INSTRUCTION_PC_EVIDENCE

Enforces strict separation of byte-level CDL evidence from architectural instruction PCs.
Enforces fail-closed artifact verification (SHA-256) for D9 return site 0x0600428A.
Guarantees MANIFEST_DERIVED_EXECUTION_ENTRIES == 0.
Guarantees UNALIGNED_INSTRUCTION_PCS == 0.
"""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple


D9_ARTIFACT_REL_PATH = "workstreams/T2-D9-indirect/d9_4_native_indirect_evidence.json"
D9_EXPECTED_SHA256 = "3fb1189d7fc3e12183902a3aae47241a8100be6a235dd17303ff3a17734a7b14"


@dataclass(frozen=True)
class ExecutedByteEntry:
    revision: str
    cpu: str
    module: str
    generation: int
    address: int
    source: str

    def key(self) -> Tuple[str, str, str, int, int]:
        return (self.revision, self.cpu, self.module, self.generation, self.address)


@dataclass
class ExecutedInstructionPCEntry:
    revision: str
    cpu: str
    module: str
    generation: int
    pc: int
    sources: List[str]
    artifact_path: str
    artifact_sha256: str
    provenance_records: List[Dict[str, Any]]
    cycle: Optional[int] = None

    def key(self) -> Tuple[str, str, str, int, int]:
        return (self.revision, self.cpu, self.module, self.generation, self.pc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "revision": self.revision,
            "cpu": self.cpu,
            "module": self.module,
            "generation": self.generation,
            "pc": f"0x{self.pc:08X}",
            "source": self.sources[0] if self.sources else "",
            "sources": list(self.sources),
            "artifact_path": self.artifact_path,
            "artifact_sha256": self.artifact_sha256,
            "cycle": self.cycle,
            "provenance_records": list(self.provenance_records),
        }


@dataclass
class NonExecutionPCEntry:
    revision: str
    cpu: str
    module: str
    generation: int
    address: int
    kind: str  # DEBUG_PRESENTED_PC, RETURN_TARGET_CANDIDATE
    source: str
    artifact_path: str
    artifact_sha256: str
    cycle: Optional[int] = None

    def key(self) -> Tuple[str, str, str, int, int]:
        return (self.revision, self.cpu, self.module, self.generation, self.address)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "revision": self.revision,
            "cpu": self.cpu,
            "module": self.module,
            "generation": self.generation,
            "address": f"0x{self.address:08X}",
            "kind": self.kind,
            "source": self.source,
            "artifact_path": self.artifact_path,
            "artifact_sha256": self.artifact_sha256,
            "cycle": self.cycle,
        }


class ExecutedPCUnion:
    """Canonical registry of all historically executed bytes and instruction PCs."""

    def __init__(self, repo_root: Path, revision: str = "RUS") -> None:
        self.repo_root = repo_root
        self.revision = revision
        self.byte_entries: Dict[Tuple[str, str, str, int, int], ExecutedByteEntry] = {}
        self.instruction_entries: Dict[Tuple[str, str, str, int, int], ExecutedInstructionPCEntry] = {}
        self.debug_presented_entries: Dict[Tuple[str, str, str, int, int], List[NonExecutionPCEntry]] = {}
        self.return_target_candidates: Dict[Tuple[str, str, str, int, int], List[NonExecutionPCEntry]] = {}
        self.rejected_sources: List[Dict[str, Any]] = []
        self._bytes_by_module: Dict[str, Set[int]] = {}
        self._instruction_pcs_by_module: Dict[str, Set[int]] = {}
        self.manifest_derived_entries = 0
        self.unaligned_instruction_pcs = 0
        self.dynamic_evidence_without_real_artifact = 0

    def add_byte_address(
        self, cpu: str, module: str, address: int, source: str, generation: int = 0
    ) -> None:
        key = (self.revision, cpu, module, generation, address)
        if key not in self.byte_entries:
            entry = ExecutedByteEntry(self.revision, cpu, module, generation, address, source)
            self.byte_entries[key] = entry
            self._bytes_by_module.setdefault(module, set()).add(address)

    def add_instruction_pc(
        self,
        cpu: str,
        module: str,
        pc: int,
        source: str,
        artifact_path: str,
        artifact_sha256: str,
        cycle: Optional[int] = None,
        generation: int = 0,
    ) -> None:
        if pc % 2 != 0:
            self.unaligned_instruction_pcs += 1
            raise ValueError(f"Unaligned instruction PC: 0x{pc:08X} in {module} from {source}")

        if "MANIFEST" in source or "STATIC" in source or "VMA" in source:
            self.manifest_derived_entries += 1
            raise ValueError(f"Manifest/static derived execution evidence forbidden: {source}")

        if not artifact_path or not artifact_sha256:
            self.dynamic_evidence_without_real_artifact += 1
            raise ValueError(f"Dynamic evidence missing real artifact provenance: {source}")

        key = (self.revision, cpu, module, generation, pc)
        prov = {
            "source": source,
            "artifact_path": artifact_path,
            "artifact_sha256": artifact_sha256,
            "cycle": cycle,
        }
        if key not in self.instruction_entries:
            entry = ExecutedInstructionPCEntry(
                revision=self.revision,
                cpu=cpu,
                module=module,
                generation=generation,
                pc=pc,
                sources=[source],
                artifact_path=artifact_path,
                artifact_sha256=artifact_sha256,
                provenance_records=[prov],
                cycle=cycle,
            )
            self.instruction_entries[key] = entry
            self._instruction_pcs_by_module.setdefault(module, set()).add(pc)
        else:
            existing = self.instruction_entries[key]
            if source not in existing.sources:
                existing.sources.append(source)
            existing.provenance_records.append(prov)
            if cycle is not None and existing.cycle is None:
                existing.cycle = cycle

    def add_debug_presented_pc(
        self,
        cpu: str,
        module: str,
        pc: int,
        source: str,
        artifact_path: str,
        artifact_sha256: str,
        cycle: Optional[int] = None,
        generation: int = 0,
    ) -> None:
        key = (self.revision, cpu, module, generation, pc)
        entry = NonExecutionPCEntry(
            revision=self.revision,
            cpu=cpu,
            module=module,
            generation=generation,
            address=pc,
            kind="DEBUG_PRESENTED_PC",
            source=source,
            artifact_path=artifact_path,
            artifact_sha256=artifact_sha256,
            cycle=cycle,
        )
        self.debug_presented_entries.setdefault(key, []).append(entry)

    def add_return_target_candidate(
        self,
        cpu: str,
        module: str,
        address: int,
        source: str,
        artifact_path: str,
        artifact_sha256: str,
        cycle: Optional[int] = None,
        generation: int = 0,
    ) -> None:
        key = (self.revision, cpu, module, generation, address)
        entry = NonExecutionPCEntry(
            revision=self.revision,
            cpu=cpu,
            module=module,
            generation=generation,
            address=address,
            kind="RETURN_TARGET_CANDIDATE",
            source=source,
            artifact_path=artifact_path,
            artifact_sha256=artifact_sha256,
            cycle=cycle,
        )
        self.return_target_candidates.setdefault(key, []).append(entry)

    def contains_pc(self, module: str, pc: int) -> bool:
        return pc in self._instruction_pcs_by_module.get(module, set())

    def contains_instruction_pc(self, module: str, pc: int) -> bool:
        return pc in self._instruction_pcs_by_module.get(module, set())

    def contains_byte(self, module: str, address: int) -> bool:
        return address in self._bytes_by_module.get(module, set())

    def get_instruction_pcs_for_module(self, module: str) -> Set[int]:
        return set(self._instruction_pcs_by_module.get(module, set()))

    def get_byte_addresses_for_module(self, module: str) -> Set[int]:
        return set(self._bytes_by_module.get(module, set()))

    def build_union(self) -> Dict[str, Any]:
        """Ingest all authoritative sources into canonical union."""
        self._ingest_cdl_traces()
        self._ingest_d9_evidence()
        self._ingest_asm_workstreams()

        assert self.manifest_derived_entries == 0, "FATAL: Circular manifest execution evidence detected!"
        assert self.unaligned_instruction_pcs == 0, "FATAL: Unaligned instruction PCs detected!"
        assert self.dynamic_evidence_without_real_artifact == 0, "FATAL: Dynamic evidence without real artifact!"
        assert self.contains_instruction_pc("0TH2.BIN", 0x0600428A), (
            "FATAL: 0x0600428A MUST be recognized as historically executed from real D9 evidence!"
        )

        return self.export_summary()

    def _ingest_cdl_traces(self) -> None:
        cdl_specs = [
            (".private/harvest_ipc_hwr/hwr_gameplay_cdl.bin", 0x06000000, "MASTER_SH2", "0TH2.BIN"),
            (".private/cdl_ipc/hwr_cdl.bin", 0x06000000, "MASTER_SH2", "0TH2.BIN"),
            (".private/screen_ipc/hwr_cdl_gameplay.bin", 0x06000000, "MASTER_SH2", "0TH2.BIN"),
            (".private/harvest_ipc_lwr/lwr_gameplay_cdl.bin", 0x00200000, "MASTER_SH2", "TH2.LOW"),
            (".private/cdl_ipc_lwr/lwr_cdl.bin", 0x00200000, "MASTER_SH2", "TH2.LOW"),
        ]
        set07_range = (0x060D8000, 0x060D8000 + 98304)

        for rel_path, ram_base, cpu, default_mod in cdl_specs:
            p = self.repo_root / rel_path
            if not p.exists():
                continue
            with open(p, "rb") as f:
                f.seek(8)
                data = f.read()
            src_label = f"CDL:{p.name}"
            for i, b in enumerate(data):
                if b & 1:
                    addr = ram_base + i
                    if ram_base == 0x06000000:
                        if set07_range[0] <= addr < set07_range[1]:
                            mod = "SET07.BIN"
                        elif 0x06004000 <= addr < 0x06004000 + 535552:
                            mod = "0TH2.BIN"
                        else:
                            continue
                    elif ram_base == 0x00200000:
                        if 0x002DA000 <= addr < 0x002DA000 + 149504:
                            mod = "TH2.LOW"
                        else:
                            continue
                    else:
                        mod = default_mod
                    self.add_byte_address(cpu, mod, addr, src_label)

    def _ingest_d9_evidence(self) -> None:
        d9_path = self.repo_root / D9_ARTIFACT_REL_PATH
        if not d9_path.exists():
            raise FileNotFoundError(f"Canonical D9 evidence file missing: {d9_path}")

        raw_bytes = d9_path.read_bytes()
        actual_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        if actual_sha256.lower() != D9_EXPECTED_SHA256.lower():
            raise ValueError(
                f"D9 evidence SHA-256 mismatch! Expected {D9_EXPECTED_SHA256}, got {actual_sha256}"
            )

        data = json.loads(raw_bytes.decode("utf-8"))
        found_428a = False

        for exp_name, exp in data.get("experiments", {}).items():
            for ev_name, ev in exp.get("events", {}).items():
                addr_str = ev.get("address")
                ev_cycle = ev.get("cycle")
                chk_lbl = ev.get("checkpoint_label", "")
                if addr_str:
                    addr = int(addr_str, 16)
                    if 0x06004000 <= addr < 0x06004000 + 535552:
                        self.add_instruction_pc(
                            "MASTER_SH2",
                            "0TH2.BIN",
                            addr,
                            f"D9_EVENT:{exp_name}:{ev_name}:{chk_lbl}",
                            D9_ARTIFACT_REL_PATH,
                            actual_sha256,
                            cycle=ev_cycle,
                            generation=0,
                        )
                        if addr == 0x0600428A:
                            found_428a = True

                parsed_ack = ev.get("parsed_ack", {})
                ack_pc = parsed_ack.get("pc")
                if ack_pc:
                    p_pc = int(ack_pc, 16)
                    self.add_debug_presented_pc(
                        "MASTER_SH2", "0TH2.BIN", p_pc, f"D9_ACK_PC:{exp_name}:{ev_name}", D9_ARTIFACT_REL_PATH, actual_sha256, cycle=ev_cycle, generation=0
                    )

                parsed_regs = ev.get("parsed_regs", {})
                reg_pc = parsed_regs.get("PC")
                if reg_pc:
                    p_pc = int(reg_pc, 16)
                    self.add_debug_presented_pc(
                        "MASTER_SH2", "0TH2.BIN", p_pc, f"D9_REG_PC:{exp_name}:{ev_name}", D9_ARTIFACT_REL_PATH, actual_sha256, cycle=ev_cycle, generation=0
                    )
                reg_pr = parsed_regs.get("PR")
                if reg_pr:
                    p_pr = int(reg_pr, 16)
                    self.add_return_target_candidate(
                        "MASTER_SH2", "0TH2.BIN", p_pr, f"D9_REG_PR:{exp_name}:{ev_name}", D9_ARTIFACT_REL_PATH, actual_sha256, cycle=ev_cycle, generation=0
                    )

        if not found_428a:
            raise ValueError("0x0600428A not found in D9 evidence artifact event addresses!")

    def _ingest_asm_workstreams(self) -> None:
        for ws in ["T2-ASM-01", "T2-ASM-02", "T2-ASM-03", "T2-ASM-04"]:
            rel_path = f"workstreams/{ws}/experiment_evidence.json"
            p = self.repo_root / rel_path
            if not p.exists():
                continue
            raw_bytes = p.read_bytes()
            art_sha = hashlib.sha256(raw_bytes).hexdigest()
            try:
                data = json.loads(raw_bytes.decode("utf-8"))
            except Exception as e:
                self.rejected_sources.append({
                    "source": ws,
                    "artifact_path": rel_path,
                    "reason": f"Malformed JSON: {e}",
                })
                raise ValueError(f"Authoritative evidence file malformed ({rel_path}): {e}")

            for cp in data.get("checkpoints", []):
                addr_str = cp.get("address")
                cp_cycle = cp.get("cycle")
                cp_lbl = cp.get("label", "cp")
                if addr_str:
                    addr = int(addr_str, 16)
                    if 0x06004000 <= addr < 0x06004000 + 535552:
                        self.add_instruction_pc(
                            "MASTER_SH2", "0TH2.BIN", addr, f"{ws}_CHECKPOINT:{cp_lbl}", rel_path, art_sha, cycle=cp_cycle, generation=0
                        )
                    elif 0x002DA000 <= addr < 0x002DA000 + 149504:
                        self.add_instruction_pc(
                            "MASTER_SH2", "TH2.LOW", addr, f"{ws}_CHECKPOINT:{cp_lbl}", rel_path, art_sha, cycle=cp_cycle, generation=0
                        )
                pr_str = cp.get("pr")
                if pr_str:
                    pr = int(pr_str, 16)
                    if 0x06004000 <= pr < 0x06004000 + 535552:
                        self.add_return_target_candidate(
                            "MASTER_SH2", "0TH2.BIN", pr, f"{ws}_RETURN_SITE:{cp_lbl}", rel_path, art_sha, cycle=cp_cycle, generation=0
                        )
                    elif 0x002DA000 <= pr < 0x002DA000 + 149504:
                        self.add_return_target_candidate(
                            "MASTER_SH2", "TH2.LOW", pr, f"{ws}_RETURN_SITE:{cp_lbl}", rel_path, art_sha, cycle=cp_cycle, generation=0
                        )

    def export_summary(self) -> Dict[str, Any]:
        all_mods = sorted(set(list(self._bytes_by_module.keys()) + list(self._instruction_pcs_by_module.keys())))
        by_module = {}
        for mod in all_mods:
            byte_addrs = self._bytes_by_module.get(mod, set())
            ins_pcs = self._instruction_pcs_by_module.get(mod, set())
            by_module[mod] = {
                "total_executed_bytes": len(byte_addrs),
                "total_executed_instruction_pcs": len(ins_pcs),
                "min_instruction_pc": f"0x{min(ins_pcs):08X}" if ins_pcs else "0x00000000",
                "max_instruction_pc": f"0x{max(ins_pcs):08X}" if ins_pcs else "0x00000000",
            }

        debug_pcs_flat = [e.to_dict() for elist in self.debug_presented_entries.values() for e in elist]
        return_targets_flat = [e.to_dict() for elist in self.return_target_candidates.values() for e in elist]

        return {
            "total_canonical_entries": len(self.byte_entries) + len(self.instruction_entries),
            "executed_byte_addresses_total": len(self.byte_entries),
            "executed_instruction_pcs_total": len(self.instruction_entries),
            "debug_presented_pcs_total": len(debug_pcs_flat),
            "return_target_candidates_total": len(return_targets_flat),
            "unaligned_instruction_pcs": self.unaligned_instruction_pcs,
            "manifest_derived_execution_entries": self.manifest_derived_entries,
            "dynamic_evidence_without_real_artifact": self.dynamic_evidence_without_real_artifact,
            "executed_instruction_pcs": [e.to_dict() for e in self.instruction_entries.values()],
            "debug_presented_pcs": debug_pcs_flat,
            "return_target_candidates": return_targets_flat,
            "rejected_sources": list(self.rejected_sources),
            "by_module": by_module,
            "contains_0x0600428A": self.contains_instruction_pc("0TH2.BIN", 0x0600428A),
        }

    def save_to_json(self, out_path: Path) -> None:
        summary = self.export_summary()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    repo = Path(__file__).resolve().parent.parent.parent
    union = ExecutedPCUnion(repo)
    res = union.build_union()
    out_file = repo / "workstreams" / "T2-ASM-CARVER" / "executed_pc_union.json"
    union.save_to_json(out_file)
    print(f"Historical Execution Union built: {res['total_canonical_entries']} unique entries.")
    print(f"  Executed byte addresses: {res['executed_byte_addresses_total']}")
    print(f"  Executed instruction PCs: {res['executed_instruction_pcs_total']}")
    print(f"  Unaligned instruction PCs: {res['unaligned_instruction_pcs']}")
    print(f"  Manifest-derived entries: {res['manifest_derived_execution_entries']}")
    for m, d in res["by_module"].items():
        print(f"  {m}: {d['total_executed_bytes']} bytes, {d['total_executed_instruction_pcs']} instruction PCs")
    print(f"Regression Invariant 0x0600428A present: {res['contains_0x0600428A']}")
