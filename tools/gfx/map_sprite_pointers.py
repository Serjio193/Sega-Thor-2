import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from PIL import Image
from tools.gfx.inspect_palettes import decode_rgb555

def main():
    p = Path(".private/rus/ARELE.BIN").read_bytes()
    sprite_off = 0x1DBC
    payload = p[sprite_off:]
    
    # Check all BE16 values in the first 0x1E0 bytes of payload
    print("Searching for pointers/offsets in payload header (first 0x1E0 bytes):")
    pointers = []
    for i in range(0, 0x1E0, 2):
        val = struct.unpack_from(">H", payload, i)[0]
        # Check if val points to a valid offset in payload >= 0x1E0
        if 0x1E0 <= val < len(payload):
            pointers.append((i, val))
            
    print(f"Found {len(pointers)} potential pointers into pixel data:")
    for p_idx, (src, tgt) in enumerate(pointers[:20]):
        first_bytes = payload[tgt:tgt+8].hex(' ')
        print(f"  [{p_idx:02d}] at +0x{src:04X} -> target +0x{tgt:04X}: {first_bytes}")

if __name__ == "__main__":
    main()
