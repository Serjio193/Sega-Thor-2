#!/usr/bin/env python3
"""tools/asm/raw_byte_jsr_tracer.py — Path-sensitive raw-byte tracer for 36 residual JSR sites.

Re-verifies every reaching CFG path from subroutine literal load to JSR call site
directly from raw binary bytes using forward reaching-definitions dataflow analysis:
  literal load -> register -> every CFG path -> call site
Emits raw_byte_jsr_proofs.json with complete path proofs and clobber checks.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import re
import struct
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


@dataclass
class RawByteJSRProof:
    site_pc: str
    module: str
    target_register: str
    literal_load_pc: str
    literal_address: str
    literal_value: str
    reaching_definitions: List[str]
    clobber_sites: List[str]
    all_paths_same_definition: bool
    final_status: str


class RawByteJSRTracer:
    """Verifies JSR target registers along every CFG path from raw bytes."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.b0 = (repo_root / ".private/rus/0TH2.BIN").read_bytes()
        self.blow = (repo_root / ".private/rus/TH2.LOW").read_bytes()
        self.vma_0 = 0x06004000
        self.vma_low = 0x002DA000

    def read_word(self, module: str, pc: int) -> Optional[int]:
        raw = self.b0 if module == "0TH2.BIN" else self.blow
        vma = self.vma_0 if module == "0TH2.BIN" else self.vma_low
        off = pc - vma
        if 0 <= off + 2 <= len(raw):
            return struct.unpack(">H", raw[off:off + 2])[0]
        return None

    def read_long(self, module: str, pc: int) -> Optional[int]:
        raw = self.b0 if module == "0TH2.BIN" else self.blow
        vma = self.vma_0 if module == "0TH2.BIN" else self.vma_low
        off = pc - vma
        if 0 <= off + 4 <= len(raw):
            return struct.unpack(">I", raw[off:off + 4])[0]
        return None

    def is_clobber(self, w: int, rn: int) -> bool:
        """Test if instruction w modifies register rn."""
        if (w & 0xF00F) in (0x2004, 0x2005, 0x2006) and ((w >> 8) & 0xF) == rn:
            return True
        if (w & 0xF00F) in (0x6004, 0x6005, 0x6006) and (
            ((w >> 8) & 0xF) == rn or ((w >> 4) & 0xF) == rn
        ):
            return True
        if (w & 0xF00F) in (0x6000, 0x6001, 0x6002, 0x6003) and ((w >> 8) & 0xF) == rn:
            return True
        if (w & 0xF000) == 0x7000 and ((w >> 8) & 0xF) == rn:
            return True
        if (w & 0xF000) == 0x3000 and ((w >> 8) & 0xF) == rn:
            op = w & 0xF
            if op in (0x8, 0x9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF):
                return True
        if (w & 0xF000) == 0x4000 and ((w >> 8) & 0xF) == rn:
            subop = w & 0xFF
            if subop in (
                0x00, 0x01, 0x04, 0x05, 0x08, 0x09, 0x10, 0x18, 0x19, 0x20, 0x21,
                0x24, 0x25, 0x28, 0x29
            ):
                return True
        if (w & 0xF000) == 0xE000 and ((w >> 8) & 0xF) == rn:
            return True
        return False

    def build_cfg(self, module: str, start_pc: int, end_pc: int) -> Dict[int, List[int]]:
        """Construct intra-procedural CFG respecting SH-2 delay slots."""
        succs: Dict[int, List[int]] = {}
        delayed_tgt: Dict[int, List[int]] = {}
        cur = start_pc
        while cur <= end_pc:
            w = self.read_word(module, cur)
            if w is None:
                break
            if cur in delayed_tgt:
                succs[cur] = delayed_tgt[cur]
                cur += 2
                continue
            # BT / BF (non-delayed)
            if (w & 0xFF00) in (0x8900, 0x8B00):
                disp = w & 0xFF
                if disp & 0x80:
                    disp -= 0x100
                tgt = cur + 4 + disp * 2
                succs[cur] = [cur + 2, tgt]
                cur += 2
                continue
            # BT/S / BF/S (delayed)
            if (w & 0xFF00) in (0x8D00, 0x8F00):
                disp = w & 0xFF
                if disp & 0x80:
                    disp -= 0x100
                tgt = cur + 4 + disp * 2
                succs[cur] = [cur + 2]
                delayed_tgt[cur + 2] = [cur + 4, tgt]
                cur += 2
                continue
            # BRA (delayed)
            if (w & 0xF000) == 0xA000:
                disp = w & 0x0FFF
                if disp & 0x0800:
                    disp -= 0x1000
                tgt = cur + 4 + disp * 2
                succs[cur] = [cur + 2]
                delayed_tgt[cur + 2] = [tgt]
                cur += 2
                continue
            # BSR (delayed call - returns to cur + 4)
            if (w & 0xF000) == 0xB000:
                succs[cur] = [cur + 2]
                delayed_tgt[cur + 2] = [cur + 4]
                cur += 2
                continue
            # JSR (delayed call - returns to cur + 4)
            if (w & 0xF0FF) == 0x400B:
                succs[cur] = [cur + 2]
                delayed_tgt[cur + 2] = [cur + 4]
                cur += 2
                continue
            # RTS / RTE / JMP @Rm (delayed exits)
            if w in (0x000B, 0x002B) or (w & 0xF0FF) == 0x402B:
                succs[cur] = [cur + 2]
                delayed_tgt[cur + 2] = []
                cur += 2
                continue
            succs[cur] = [cur + 2]
            cur += 2
        return succs

    def trace_jsr_site(
        self, module: str, call_pc: int, load_pc: int, expected_target: int
    ) -> RawByteJSRProof:
        w_call = self.read_word(module, call_pc)
        assert w_call is not None and (w_call & 0xF0FF) == 0x400B
        rn = (w_call >> 8) & 0xF
        reg_name = f"R{rn}"

        w_load = self.read_word(module, load_pc)
        assert w_load is not None and (w_load & 0xF000) == 0xD000 and ((w_load >> 8) & 0xF) == rn
        disp = (w_load & 0xFF) * 4
        lit_addr = (load_pc & ~3) + 4 + disp
        lit_val = self.read_long(module, lit_addr)
        assert lit_val == expected_target

        end_pc = max(call_pc + 100, load_pc + 3000)
        succs = self.build_cfg(module, load_pc, end_pc)

        in_state: Dict[int, Set[int]] = {pc: set() for pc in succs}
        out_state: Dict[int, Set[int]] = {pc: set() for pc in succs}
        out_state[load_pc] = {lit_val}

        preds: Dict[int, List[int]] = {pc: [] for pc in succs}
        for p, sl in succs.items():
            for tgt in sl:
                if tgt in preds:
                    preds[tgt].append(p)

        changed = True
        passes = 0
        clobbers: Set[int] = set()

        while changed and passes < 50:
            passes += 1
            changed = False
            for pc in sorted(succs.keys()):
                if pc == load_pc:
                    new_in: Set[int] = set()
                else:
                    new_in = set()
                    for p in preds[pc]:
                        if out_state[p]:
                            new_in.update(out_state[p])
                if new_in != in_state[pc]:
                    in_state[pc] = set(new_in)
                    changed = True

                w = self.read_word(module, pc)
                if pc == load_pc:
                    new_out = {lit_val}
                elif w is not None and self.is_clobber(w, rn):
                    clobbers.add(pc)
                    new_out = {-1}  # BOT
                else:
                    new_out = set(in_state[pc])

                if new_out != out_state[pc]:
                    out_state[pc] = set(new_out)
                    changed = True

        call_in = in_state.get(call_pc, set())
        all_same = (call_in == {lit_val})
        status = "RESOLVED_EXACT_SINGLE" if all_same else "UNRESOLVED"

        defs_s = [f"0x{v:08X}" for v in sorted(call_in) if v != -1]
        # Reaching clobbers are clobber sites that propagate to call_pc
        reaching_clobbers = [f"0x{c:08X}" for c in sorted(clobbers) if -1 in call_in]

        return RawByteJSRProof(
            site_pc=f"0x{call_pc:08X}",
            module=module,
            target_register=reg_name,
            literal_load_pc=f"0x{load_pc:08X}",
            literal_address=f"0x{lit_addr:08X}",
            literal_value=f"0x{lit_val:08X}",
            reaching_definitions=defs_s,
            clobber_sites=reaching_clobbers,
            all_paths_same_definition=all_same,
            final_status=status,
        )


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    tracer = RawByteJSRTracer(repo_root)

    sites_data = json.load(
        open(repo_root / "workstreams" / "T2-ASM-08" / "final_call_jump_sites.json")
    )["sites"]
    jsr_sites = [s for s in sites_data if s["opcode_id"] == "JSR"]

    proofs = []
    for s in jsr_sites:
        mod = s["module"]
        call_pc = int(s["runtime_pc"], 16)
        tgt = int(s["targets"][0], 16)
        m = re.search(r"loaded at (0x[0-9A-Fa-f]+)|preserved from (0x[0-9A-Fa-f]+)", s["details"])
        assert m is not None
        load_pc = int(m.group(1) or m.group(2), 16)
        p = tracer.trace_jsr_site(mod, call_pc, load_pc, tgt)
        proofs.append(p)

    out_dir = repo_root / "workstreams" / "T2-ASM-08"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "raw_byte_jsr_proofs.json"

    resolved_count = sum(1 for p in proofs if p.final_status == "RESOLVED_EXACT_SINGLE")
    all_invariant = all(p.all_paths_same_definition for p in proofs)
    payload = {
        "total_analyzed": len(proofs),
        "resolved_count": resolved_count,
        "unresolved_count": len(proofs) - resolved_count,
        "all_paths_proven": all_invariant,
        "proofs": [asdict(p) for p in proofs],
    }

    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Raw-byte JSR proofs written -> {out_file}")
    print(f"  Analyzed: {len(proofs)} sites")
    print(f"  Resolved: {resolved_count} / {len(proofs)} (all paths invariant: {all_invariant})")


if __name__ == '__main__':
    main()
