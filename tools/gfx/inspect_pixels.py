#!/usr/bin/env python3
"""Inspect raw pixel payload following sprite records."""
import struct
import sys
from pathlib import Path

def main():
    p = Path(".private/rus/ARELE.BIN").read_bytes()
    sprite_off = 0x1DBC
    payload = p[sprite_off:]
    print("=== ARELE.BIN Pixel Payload after records (+0x13C) ===")
    for i in range(0x13C, 0x13C + 160, 16):
        row = payload[i:i+16]
        hex_s = " ".join(f"{b:02X}" for b in row)
        print(f"  +0x{i:04X}: {hex_s}")
        
    print("\nLet's check nibbles (4bpp pixels) of the first 32 bytes:")
    for i in range(0x13C, 0x13C + 32, 16):
        row = payload[i:i+16]
        nibs = "".join(f"{(b>>4):X}{b&0xF:X}" for b in row)
        print(f"  +0x{i:04X}: {nibs}")

if __name__ == "__main__":
    main()
