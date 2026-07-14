import struct
import unittest

from tools.uaf_inspect import records, rom_stream


class UafInspectTests(unittest.TestCase):
    def test_records_are_sorted(self):
        data = b"xx@CMD" + struct.pack("<III", 0x30, 1, 0) + b"yy@UAF" + struct.pack("<III", 0x40, 2, 3)
        self.assertEqual([item[1] for item in records(data)], ["@CMD", "@UAF"])

    def test_extracts_bounds_valid_rom_stream(self):
        stream = struct.pack("<II", 4, 32) + b"data"
        data = b"@ROM" + struct.pack("<III", 0x24, 0, 0) + stream
        self.assertEqual(rom_stream(data), stream)

    def test_rejects_truncated_rom_stream(self):
        data = b"@ROM" + struct.pack("<III", 0x24, 0, 0) + struct.pack("<II", 20, 32) + b"short"
        with self.assertRaises(ValueError):
            rom_stream(data)


if __name__ == "__main__":
    unittest.main()
