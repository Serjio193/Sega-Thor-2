#!/usr/bin/env python3
"""tools/asm/constant_propagator.py — SH-2 Basic-Block Constant Propagator.

Performs local backward and forward constant propagation around indirect
branch and call sites, respecting call-clobber boundaries and memory safety.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
import struct


@dataclass
class PropagatedValue:
    val: int
    provenance: str
    defining_pc: int
    is_exact: bool


class ConstantPropagator:
    """Propagates constants within single basic blocks for SH-2 code."""

    CALL_OPCODES = {0xB, 0x4} # BSR/BRA (0xB), JSR (0x400B)
    
    def __init__(self, raw_bytes: bytes, vma_base: int):
        self.raw_bytes = raw_bytes
        self.vma_base = vma_base
        self.raw_len = len(raw_bytes)

    def read_word(self, pc: int) -> Optional[int]:
        off = pc - self.vma_base
        if 0 <= off + 2 <= self.raw_len:
            return struct.unpack('>H', self.raw_bytes[off : off + 2])[0]
        return None

    def read_long(self, pc: int) -> Optional[int]:
        off = pc - self.vma_base
        if 0 <= off + 4 <= self.raw_len:
            return struct.unpack('>I', self.raw_bytes[off : off + 4])[0]
        return None

    def is_call_or_terminal(self, word: int) -> bool:
        """Call-clobber safety (Rule 3): halt at call/terminal instructions."""
        op_high = (word >> 12) & 0x0F
        if op_high == 0xB: # BSR or BRA
            return True
        if (word & 0xF0FF) in (0x000B, 0x002B): # RTS, RTE
            return True
        if (word & 0xF0FF) == 0x400B: # JSR @Rn
            return True
        if (word & 0xF000) == 0xC300: # TRAPA
            return True
        return False

    def resolve_register_at_site(
        self, site_pc: int, reg_index: int, max_steps: int = 24
    ) -> Optional[PropagatedValue]:
        """Traces backwards to determine if reg_index has an exact constant value."""
        cur_reg = reg_index
        cur_offset_add = 0
        
        for step in range(1, max_steps + 1):
            prev_pc = site_pc - step * 2
            if prev_pc < self.vma_base:
                break
                
            w = self.read_word(prev_pc)
            if w is None:
                break
                
            # Rule 3: Call-clobber safety - halt if crossing a call or terminal
            if self.is_call_or_terminal(w):
                break
                
            op_high = (w >> 12) & 0x0F
            rn = (w >> 8) & 0x0F
            rm = (w >> 4) & 0x0F
            
            # Check if this instruction writes to cur_reg
            if rn == cur_reg:
                # 1. MOV.L @(disp, PC), Rn
                if op_high == 0xD:
                    disp = (w & 0xFF) * 4
                    lit_pc = ((prev_pc & ~3) + 4) + disp
                    # Memory provenance safety (Rule 4): literal must reside in immutable module bytes
                    lit_val = self.read_long(lit_pc)
                    if lit_val is not None:
                        return PropagatedValue(
                            val=(lit_val + cur_offset_add) & 0xFFFFFFFF,
                            provenance="PC_LITERAL_POOL",
                            defining_pc=prev_pc,
                            is_exact=True,
                        )
                    return None
                    
                # 2. MOV #imm, Rn
                elif op_high == 0xE:
                    imm = struct.unpack('b', bytes([w & 0xFF]))[0]
                    return PropagatedValue(
                        val=(imm + cur_offset_add) & 0xFFFFFFFF,
                        provenance="MOV_IMMEDIATE",
                        defining_pc=prev_pc,
                        is_exact=True,
                    )
                    
                # 3. MOV Rm, Rn (Register copy chain)
                elif (w & 0xF00F) == 0x6003:
                    cur_reg = rm
                    continue
                    
                # 4. ADD #imm, Rn
                elif op_high == 0x7:
                    imm = struct.unpack('b', bytes([w & 0xFF]))[0]
                    cur_offset_add += imm
                    continue
                    
                # 5. MOVA @(disp, PC), R0
                elif (w >> 8) == 0xC7 and cur_reg == 0:
                    disp = (w & 0xFF) * 4
                    table_pc = ((prev_pc & ~3) + 4) + disp
                    return PropagatedValue(
                        val=(table_pc + cur_offset_add) & 0xFFFFFFFF,
                        provenance="MOVA_TABLE_BASE",
                        defining_pc=prev_pc,
                        is_exact=True,
                    )
                    
                # Any other modification clobbers without constant proof
                else:
                    return None
                    
        return None
