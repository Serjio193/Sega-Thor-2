#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

RAW_SECTOR = 2352
MODE1_USER_OFFSET = 16
USER_SECTOR = 2048


def parse_cue(path: Path) -> dict:
    raw = path.read_bytes()
    text = raw.decode('ascii', 'strict').replace('\r\n', '\n').replace('\r', '\n')
    file_match = re.search(
        r'^FILE\s+\"([^\"]+)\"\s+BINARY\s*$',
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    track_match = re.search(
        r'^\s*TRACK\s+(\d+)\s+(MODE1/2352)\s*$',
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    index_match = re.search(
        r'^\s*INDEX\s+01\s+(\d{2}:\d{2}:\d{2})\s*$',
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    if not file_match or not track_match or not index_match:
        raise ValueError(
            'unsupported CUE: expected one BINARY MODE1/2352 track with INDEX 01'
        )
    if track_match.group(1) != '01' or index_match.group(1) != '00:00:00':
        raise ValueError('unsupported CUE layout: track must start at 00:00:00')
    return {
        'declared_file': file_match.group(1),
        'track': 1,
        'mode': track_match.group(2).upper(),
        'index01': index_match.group(1),
    }


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


class Mode1RawImage:
    def __init__(self, path: Path):
        self.path = path
        self.f = path.open('rb')
        size = path.stat().st_size
        if size % RAW_SECTOR:
            raise ValueError(f'image size {size} is not divisible by {RAW_SECTOR}')
        self.sector_count = size // RAW_SECTOR

    def close(self):
        self.f.close()

    def read_user_sector(self, lba: int) -> bytes:
        if not 0 <= lba < self.sector_count:
            raise ValueError(f'LBA out of range: {lba}')
        self.f.seek(lba * RAW_SECTOR + MODE1_USER_OFFSET)
        data = self.f.read(USER_SECTOR)
        if len(data) != USER_SECTOR:
            raise EOFError(f'short sector at LBA {lba}')
        return data

    def read_extent(self, lba: int, size: int) -> bytes:
        out = bytearray()
        sectors = (size + USER_SECTOR - 1) // USER_SECTOR
        for i in range(sectors):
            out.extend(self.read_user_sector(lba + i))
        return bytes(out[:size])

    def hash_extent(self, lba: int, size: int) -> str:
        h = hashlib.sha256()
        remaining = size
        sector = 0
        while remaining:
            data = self.read_user_sector(lba + sector)
            take = min(remaining, USER_SECTOR)
            h.update(data[:take])
            remaining -= take
            sector += 1
        return h.hexdigest()


def ascii_field(data: bytes, start: int, end: int) -> str:
    return data[start:end].decode('ascii', 'replace').rstrip(' \0')


def parse_saturn_header(sector0: bytes) -> dict:
    if sector0[:16] != b'SEGA SEGASATURN ':
        raise ValueError('missing SEGA SEGASATURN header')
    return {
        'hardware_id': ascii_field(sector0, 0x00, 0x10),
        'maker_id': ascii_field(sector0, 0x10, 0x20),
        'product_code': ascii_field(sector0, 0x20, 0x2A),
        'version': ascii_field(sector0, 0x2A, 0x30),
        'date': ascii_field(sector0, 0x30, 0x38),
        'disc_info': ascii_field(sector0, 0x38, 0x40),
        'regions': ascii_field(sector0, 0x40, 0x50),
        'peripherals': ascii_field(sector0, 0x50, 0x60),
        'title': ascii_field(sector0, 0x60, 0xD0),
        'ip_size': int.from_bytes(sector0[0xE0:0xE4], 'big'),
        'master_stack': int.from_bytes(sector0[0xE8:0xEC], 'big'),
        'slave_stack': int.from_bytes(sector0[0xEC:0xF0], 'big'),
        'first_read_address': int.from_bytes(sector0[0xF0:0xF4], 'big'),
        'first_read_size': int.from_bytes(sector0[0xF4:0xF8], 'big'),
    }


def parse_dir_record(rec: bytes):
    extent = int.from_bytes(rec[2:6], 'little')
    size = int.from_bytes(rec[10:14], 'little')
    flags = rec[25]
    name_len = rec[32]
    name = rec[33:33 + name_len]
    return extent, size, flags, name


def parse_iso9660(image: Mode1RawImage):
    pvd = image.read_user_sector(16)
    if pvd[0] != 1 or pvd[1:6] != b'CD001' or pvd[6] != 1:
        raise ValueError('primary volume descriptor not found at LBA 16')
    volume_id = ascii_field(pvd, 40, 72)
    root_len = pvd[156]
    root = pvd[156:156 + root_len]
    root_lba, root_size, root_flags, _ = parse_dir_record(root)
    if not (root_flags & 2):
        raise ValueError('root record is not a directory')

    entries = []
    seen_dirs = set()

    def walk(prefix: str, lba: int, size: int):
        key = (lba, size)
        if key in seen_dirs:
            return
        seen_dirs.add(key)
        data = image.read_extent(lba, size)
        pos = 0
        while pos < len(data):
            rec_len = data[pos]
            if rec_len == 0:
                pos = ((pos // USER_SECTOR) + 1) * USER_SECTOR
                continue
            rec = data[pos:pos + rec_len]
            extent, item_size, flags, raw_name = parse_dir_record(rec)
            if raw_name not in (b'\x00', b'\x01'):
                name = raw_name.decode('ascii', 'replace')
                if ';' in name:
                    name = name.rsplit(';', 1)[0]
                full = f'{prefix}/{name}'.lstrip('/')
                is_dir = bool(flags & 2)
                entries.append({
                    'path': full,
                    'lba': extent,
                    'size': item_size,
                    'flags': flags,
                    'is_dir': is_dir,
                })
                if is_dir:
                    walk(full, extent, item_size)
            pos += rec_len

    walk('', root_lba, root_size)
    return volume_id, entries


def write_manifest(path: Path, rows: list[dict]):
    fields = ['path', 'lba', 'size', 'sha256']
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)


def main():
    ap = argparse.ArgumentParser(
        description='Legal-safe Sega Saturn MODE1/2352 disc census'
    )
    ap.add_argument('--bin', required=True, type=Path)
    ap.add_argument('--cue', type=Path)
    ap.add_argument('--out', required=True, type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    cue_info = parse_cue(args.cue) if args.cue else None
    image = Mode1RawImage(args.bin)
    try:
        header = parse_saturn_header(image.read_user_sector(0))
        volume_id, entries = parse_iso9660(image)
        files = [e for e in entries if not e['is_dir']]
        manifest = []
        for entry in files:
            manifest.append({
                'path': entry['path'],
                'lba': entry['lba'],
                'size': entry['size'],
                'sha256': image.hash_extent(entry['lba'], entry['size']),
            })

        write_manifest(args.out / 'disc_manifest.tsv', manifest)
        summary = {
            'image_name': args.bin.name,
            'image_size': args.bin.stat().st_size,
            'image_sha256': sha256_path(args.bin),
            'sector_format': 'MODE1/2352',
            'sector_count': image.sector_count,
            'cue_name': args.cue.name if args.cue else None,
            'cue_sha256': sha256_path(args.cue) if args.cue else None,
            'cue': cue_info,
            'volume_id': volume_id,
            'file_count': len(files),
            'saturn_header': header,
        }
        (args.out / 'disc_summary.json').write_text(
            json.dumps(summary, indent=2, sort_keys=True) + '\n',
            encoding='utf-8',
        )
    finally:
        image.close()


if __name__ == '__main__':
    main()
