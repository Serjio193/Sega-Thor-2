#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sys

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def is_emitter_supported(op: int) -> bool:
    if (op & 0xF00F) == 0x6001: return True  # MOV.W @Rm, Rn
    if (op & 0xF00F) == 0x6003: return True  # MOV Rm, Rn
    if (op & 0xF000) == 0xD000: return True  # MOV.L @(disp, PC), Rn
    if (op & 0xF00F) == 0x6002: return True  # MOV.L @Rm, Rn
    if (op & 0xF000) == 0xA000: return True  # BRA
    if (op & 0xF0FF) == 0x400B: return True  # JSR
    if op == 0x0009: return True             # NOP
    return False

def classify_block(words):
    if not words:
        return 'MNEMONIC_PROVEN', 'INVALID_BLOCK_BOUNDARY'
    
    # Check opcodes
    for w in words:
        if not is_emitter_supported(w):
            return 'MNEMONIC_PROVEN', 'UNSUPPORTED_EMITTER_OPCODE'
            
    # Check control flow and boundaries
    for i, w in enumerate(words):
        is_bra = (w & 0xF000) == 0xA000
        is_jsr = (w & 0xF0FF) == 0x400B
        if is_bra or is_jsr:
            if i == len(words) - 1:
                return 'MNEMONIC_PROVEN', 'INVALID_BLOCK_BOUNDARY'
            if i < len(words) - 2:
                return 'MNEMONIC_PROVEN', 'UNSUPPORTED_CONTROL_FLOW'
                
    return 'CODEGEN_ELIGIBLE', None

def main():
    parser = argparse.ArgumentParser(description='Build native block census')
    parser.add_argument('--bin-0th2', default='scratch/0TH2.BIN')
    parser.add_argument('--bin-th2-low', default='scratch/th2_low_rebuilt.bin')
    parser.add_argument('--manifest-0th2', default='asm/manifests/0TH2.BIN.json')
    parser.add_argument('--manifest-th2-low', default='asm/manifests/TH2.LOW.json')
    parser.add_argument('--out-summary', default='workstreams/T2-D17-native-scaling/block_census_summary.json')
    parser.add_argument('--out-full', default='out/native_block_census.json')
    parser.add_argument('--generated-dir', default='build/generated/native_blocks')
    args = parser.parse_args()

    with open(args.bin_0th2, 'rb') as f:
        b0 = f.read()
    with open(args.bin_th2_low, 'rb') as f:
        bl = f.read()

    modules_cfg = [
        ('0TH2.BIN', args.manifest_0th2, b0, 0x06004000),
        ('TH2.LOW', args.manifest_th2_low, bl, 0x002DA000)
    ]

    all_blocks = []
    summary_by_state = {
        'HARVESTED': 0,
        'MNEMONIC_PROVEN': 0,
        'CODEGEN_ELIGIBLE': 0,
        'GENERATED': 0,
        'COMPILES': 0,
        'SHADOW_ELIGIBLE': 0,
        'NATIVE_PROMOTION_ELIGIBLE': 0,
        'PROMOTED': 0
    }
    summary_by_reason = {
        'UNSUPPORTED_EMITTER_OPCODE': 0,
        'INVALID_BLOCK_BOUNDARY': 0,
        'UNSUPPORTED_CONTROL_FLOW': 0
    }
    module_summaries = {}

    for mod_name, man_path, bin_data, runtime_base in modules_cfg:
        with open(man_path, 'r') as f:
            man = json.load(f)
        proven = [r for r in man['ranges'] if r.get('assembly_representation') == 'MNEMONIC_PROVEN']
        mod_eligible = 0
        mod_reasons = {}

        for r in proven:
            bid = r.get('block_id') or f"bb_{r['runtime_start'][2:]}"
            o_start = r['offset_start']
            o_end = r['offset_end_exclusive']
            raw = bin_data[o_start:o_end]
            words = [int.from_bytes(raw[i*2:i*2+2], 'big') for i in range(len(raw)//2)]
            rt_start = int(r['runtime_start'], 16)
            rt_end = int(r['runtime_end_exclusive'], 16)
            bhash = sha256_bytes(raw)

            state, reason = classify_block(words)
            if state == 'CODEGEN_ELIGIBLE':
                mod_eligible += 1
                summary_by_state['CODEGEN_ELIGIBLE'] += 1
                # Check if already generated
                gen_src = os.path.join(args.generated_dir, f'{bid}.cpp')
                if os.path.exists(gen_src):
                    summary_by_state['GENERATED'] += 1
                    summary_by_state['COMPILES'] += 1
                    if bid in ('bb_06004000', 'bb_06004280'):
                        summary_by_state['SHADOW_ELIGIBLE'] += 1
                        summary_by_state['NATIVE_PROMOTION_ELIGIBLE'] += 1
                        summary_by_state['PROMOTED'] += 1
                        state = 'PROMOTED'
                    else:
                        state = 'COMPILES'
            else:
                summary_by_state['MNEMONIC_PROVEN'] += 1
                summary_by_reason[reason] += 1
                mod_reasons[reason] = mod_reasons.get(reason, 0) + 1

            all_blocks.append({
                'block_id': bid,
                'module': mod_name,
                'offset_start': o_start,
                'offset_end_exclusive': o_end,
                'runtime_start': f'0x{rt_start:08X}',
                'runtime_end_exclusive': f'0x{rt_end:08X}',
                'byte_length': len(raw),
                'instruction_count': len(words),
                'sha256': bhash,
                'state': state,
                'fail_closed_reason': reason
            })

        module_summaries[mod_name] = {
            'total_proven_blocks': len(proven),
            'codegen_eligible': mod_eligible,
            'rejection_reasons': mod_reasons
        }

    summary_by_state['HARVESTED'] = len(all_blocks)

    summary = {
        'total_harvested_blocks': len(all_blocks),
        'summary_by_state': summary_by_state,
        'summary_by_reason': summary_by_reason,
        'modules': module_summaries
    }

    os.makedirs(os.path.dirname(args.out_summary), exist_ok=True)
    with open(args.out_summary, 'w') as f:
        json.dump(summary, f, indent=2)

    os.makedirs(os.path.dirname(args.out_full), exist_ok=True)
    with open(args.out_full, 'w') as f:
        json.dump({'summary': summary, 'blocks': all_blocks}, f, indent=2)

    print('Census complete!')
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
