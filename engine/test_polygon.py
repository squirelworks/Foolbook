"""The polygon translator. Twips in, the point array Polygon gets out."""

import unittest

from engine.polygon import read_polygon, to_pixel


class PolygonTests(unittest.TestCase):
    def test_ninety_six_dpi_matches_the_fifteen_rule_when_it_is_whole(self):
        self.assertEqual(to_pixel(15), 1)
        self.assertEqual(to_pixel(0), 0)
        self.assertEqual(to_pixel(-15), -1)
        self.assertEqual(to_pixel(7), 0)

    def test_a_record_becomes_one_polygon_call(self):
        record = bytearray(0x22 + 12)
        record[4:7] = bytes((0xC0, 0xC0, 0xC0))
        record[0x0C:0x0E] = b"\x04\x00"
        record[0x1A:0x1C] = (3).to_bytes(2, "little")
        pairs = (0, 0, 15, 0, 15, 30)
        for n, twip in enumerate(pairs):
            record[0x22 + n * 2:0x22 + n * 2 + 2] = twip.to_bytes(2, "little", signed=True)
        call = read_polygon(bytes(record))
        self.assertEqual(call["count"], 3)
        self.assertEqual(call["pixels"], [[0, 0], [1, 0], [1, 2]])
        self.assertEqual(call["fill"], "#c0c0c0")
        self.assertIsNone(call["pen"])

    def test_a_different_kind_is_not_a_polygon(self):
        record = bytearray(0x30)
        record[0x0C:0x0E] = b"\x01\x00"
        self.assertIsNone(read_polygon(bytes(record)))


if __name__ == "__main__":
    unittest.main()
