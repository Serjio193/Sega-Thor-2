#!/usr/bin/env python3
"""Print decoded SH-2 IR json files."""
import json
import sys
from pathlib import Path

def print_ir(path: Path, max_lines: int = 60, offset_start: int = 0):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for block in data.get("blocks", []):
        print(f"=== Block: {block.get('block_id')} ({block.get('start_vma')} - {block.get('end_vma')}) ===")
        instructions = block.get("instructions", [])[offset_start : offset_start + max_lines]
        for ins in instructions:
            pc = ins.get("pc", "")
            op = ins.get("opcode", "")
            asm = ins.get("asm_line", "")
            flow = ins.get("flow", "")
            tgt = ins.get("target_vma", "0x00000000")
            extra = f"-> {tgt} ({flow})" if tgt != "0x00000000" else (f"({flow})" if flow != "SEQUENTIAL" else "")
            print(f"  {pc}  {op:<6}  {asm:<32} {extra}")

if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".private/load_chr.json")
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    print_ir(target, count, start)
