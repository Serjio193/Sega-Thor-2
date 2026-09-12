import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.disc.census_saturn_cd import Mode1RawImage, parse_iso9660

p = Path("Legend of Oasis The (USA)/Legend of Oasis, The (USA) (Track 1).bin")
img = Mode1RawImage(p)
print(f"USA Track 1 total sectors: {img.sector_count}")
vol, entries = parse_iso9660(img)
for e in sorted(entries, key=lambda x: x['lba']):
    end_lba = e['lba'] + (e['size'] + 2047) // 2048
    print(f"{e['path']:<20} lba={e['lba']:<6} size={e['size']:<10} end_lba={end_lba:<6} in_range={end_lba <= img.sector_count}")
img.close()
