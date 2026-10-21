"""Class 0x10 irregular polygons. An outline is mapped onto its bounds."""

import unittest

from engine.polygon import read_polygon, to_pixel


def _record(bounds, points, color=(0xC0, 0xC0, 0xC0), pattern=0xFE):
    record = bytearray(0x3A + len(points) * 4)
    record[0:2] = b"\x10\x00"
    for n, value in enumerate(bounds):
        record[0x11 + n * 2:0x13 + n * 2] = int(value).to_bytes(2, "little", signed=True)
    record[0x1D:0x20] = bytes(color)
    record[0x24:0x26] = b"\x04\x00"
    record[0x27] = pattern
    record[0x32:0x34] = len(points).to_bytes(2, "little")
    for n, (x, y) in enumerate(points):
        base = 0x3A + n * 4
        record[base:base + 2] = int(x).to_bytes(2, "little", signed=True)
        record[base + 2:base + 4] = int(y).to_bytes(2, "little", signed=True)
    return bytes(record)


class PolygonTests(unittest.TestCase):
    def test_ninety_six_dpi_matches_the_fifteen_rule_when_it_is_whole(self):
        self.assertEqual(to_pixel(15), 1)
        self.assertEqual(to_pixel(0), 0)
        self.assertEqual(to_pixel(-15), -1)
        self.assertEqual(to_pixel(7), 0)

    def test_a_record_becomes_one_polygon_on_its_bounds(self):
        call = read_polygon(_record((100, 200, 115, 230), ((1000, 2000), (1015, 2000), (1015, 2030))))
        self.assertEqual(call["count"], 3)
        self.assertEqual(call["points"], [[100, 200], [115, 200], [115, 230]])
        self.assertEqual(call["fill"], "#c0c0c0")
        self.assertEqual(call["pattern"], 0xFE)
        self.assertIsNone(call["pen"])

    def test_a_larger_outline_is_scaled_into_the_bounds(self):
        call = read_polygon(_record((0, 0, 100, 50), ((0, 0), (200, 0), (200, 100))))
        self.assertEqual(call["points"], [[0, 0], [100, 0], [100, 50]])

    def test_rgb_is_not_swapped(self):
        call = read_polygon(_record((0, 0, 10, 10), ((0, 0), (2, 0), (2, 2)), color=(0xBF, 0x40, 0x10)))
        self.assertEqual(call["fill"], "#bf4010")

    def test_pattern_none_has_no_fill(self):
        call = read_polygon(_record((0, 0, 10, 10), ((0, 0), (2, 0), (2, 2)), pattern=0xFD))
        self.assertIsNone(call["fill"])

    def test_a_different_kind_is_not_a_polygon(self):
        record = bytearray(_record((0, 0, 10, 10), ((0, 0), (2, 0), (2, 2))))
        record[0x24:0x26] = b"\x01\x00"
        self.assertIsNone(read_polygon(bytes(record)))

    def test_a_shared_outline_is_moved_to_its_bounds(self):
        from engine.shapes import extract_shapes
        shapes = extract_shapes(_record(
            (100, 200, 115, 230),
            ((1000, 2000), (1015, 2000), (1015, 2030)),
        ))
        self.assertEqual(len(shapes), 1)
        self.assertEqual(shapes[0]["points"], [[100, 200], [115, 200], [115, 230]])

    def test_the_polygon_header_is_not_also_a_rectangle(self):
        from engine.shapes import extract_shapes
        record = bytearray(_record((100, 200, 130, 260), ((0, 0), (20, 0), (10, 40))))
        record[0x21:0x24] = b"\x01\x00\x00"
        shapes = extract_shapes(bytes(record))
        self.assertEqual([shape["type"] for shape in shapes], ["polygon"])
        xs = [point[0] for point in shapes[0]["points"]]
        self.assertGreater(max(xs) - min(xs), 0)

    def test_a_record_without_area_is_not_drawn(self):
        from engine.shapes import extract_shapes
        shapes = extract_shapes(_record((0, 0, 0, 10), ((0, 0), (2, 0), (2, 2))))
        self.assertEqual(shapes, [])


if __name__ == "__main__":
    unittest.main()
