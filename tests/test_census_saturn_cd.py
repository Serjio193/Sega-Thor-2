import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1] / 'tools' / 'disc' / 'census_saturn_cd.py'
)
spec = importlib.util.spec_from_file_location('census_saturn_cd', MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class CensusTests(unittest.TestCase):
    def test_parse_cue_single_mode1_track(self):
        text = (
            'FILE "game.bin" BINARY\r\n'
            '  TRACK 01 MODE1/2352\r\n'
            '    INDEX 01 00:00:00\r\n'
        )
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'game.cue'
            path.write_bytes(text.encode('ascii'))
            info = mod.parse_cue(path)
        self.assertEqual(info['declared_file'], 'game.bin')
        self.assertEqual(info['mode'], 'MODE1/2352')
        self.assertEqual(info['index01'], '00:00:00')

    def test_parse_saturn_header_big_endian_addresses(self):
        data = bytearray(2048)
        data[0:16] = b'SEGA SEGASATURN '
        data[0x10:0x20] = b'SEGA ENTERPRISES'
        data[0x20:0x2A] = b'MK-00000  '
        data[0x2A:0x30] = b'V1.000'
        data[0x30:0x38] = b'19960101'
        data[0x38:0x40] = b'CD-1/1  '
        data[0x40:0x50] = b'J               '
        data[0x50:0x60] = b'J               '
        data[0x60:0xD0] = b'TEST'.ljust(0x70, b' ')
        data[0xE0:0xE4] = (0x1000).to_bytes(4, 'big')
        data[0xE8:0xEC] = (0x06001000).to_bytes(4, 'big')
        data[0xEC:0xF0] = (0x06002000).to_bytes(4, 'big')
        data[0xF0:0xF4] = (0x06004000).to_bytes(4, 'big')
        out = mod.parse_saturn_header(bytes(data))
        self.assertEqual(out['product_code'], 'MK-00000')
        self.assertEqual(out['first_read_address'], 0x06004000)
        self.assertEqual(out['master_stack'], 0x06001000)

    def test_parse_directory_record(self):
        record = bytearray(40)
        record[0] = 40
        record[2:6] = (123).to_bytes(4, 'little')
        record[10:14] = (4567).to_bytes(4, 'little')
        record[25] = 0
        record[32] = 5
        record[33:38] = b'A.B;1'
        extent, size, flags, name = mod.parse_dir_record(bytes(record))
        self.assertEqual((extent, size, flags, name), (123, 4567, 0, b'A.B;1'))


if __name__ == '__main__':
    unittest.main()
