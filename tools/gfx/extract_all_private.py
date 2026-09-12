#!/usr/bin/env python3
"""Extract private research binaries to .private/ for local static/dynamic analysis."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.gfx.disc_extractor import SaturnDisc

def main():
    root = Path(__file__).resolve().parents[2]
    rus_bin = root / "The_Story_of_Thor_2_[RUS]_(NTSC).bin"
    usa_bin = root / "Legend of Oasis The (USA)" / "Legend of Oasis, The (USA) (Track 1).bin"
    usa_cue = root / "Legend of Oasis The (USA)" / "Legend of Oasis, The (USA).cue"
    
    priv_rus = root / ".private" / "rus"
    priv_usa = root / ".private" / "usa"
    priv_rus.mkdir(parents=True, exist_ok=True)
    priv_usa.mkdir(parents=True, exist_ok=True)
    
    print("Opening RUS disc...")
    rus_disc = SaturnDisc(rus_bin)
    for fname in rus_disc.get_file_list():
        out_f = priv_rus / fname
        if not out_f.exists() or out_f.stat().st_size != rus_disc.files[fname]["size"]:
            print(f"  Extracting RUS {fname} ({rus_disc.files[fname]['size']} bytes)...")
            out_f.write_bytes(rus_disc.read_file(fname))
    rus_disc.close()
    
    print("Opening USA disc...")
    usa_disc = SaturnDisc(usa_bin, usa_cue)
    for fname in usa_disc.get_file_list():
        out_f = priv_usa / fname
        if not out_f.exists() or out_f.stat().st_size != usa_disc.files[fname]["size"]:
            print(f"  Extracting USA {fname} ({usa_disc.files[fname]['size']} bytes)...")
            out_f.write_bytes(usa_disc.read_file(fname))
    usa_disc.close()
    
    print("Extraction to .private/ complete.")

if __name__ == "__main__":
    main()
