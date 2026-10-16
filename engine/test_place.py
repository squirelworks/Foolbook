"""Objects sit where their twip bounds say, not packed to the corner."""

import unittest

from engine.place import place_page


class PlaceTests(unittest.TestCase):
    def test_a_bound_at_one_inch_is_one_inch_across_the_window(self):
        page = place_page([
            {"type": "rect", "points": [[0, 0], [15, 15]], "fill": "#fff"},
            {"type": "rect", "points": [[1440, 0], [2880, 1440]], "fill": "#ccc"},
        ])
        first, second = page["shapes"]
        self.assertEqual(first["at"][0], 8)
        self.assertEqual(second["at"][0], 8 + 96)
        self.assertGreater(page["width"], second["at"][0] + second["at"][2])

    def test_a_polygon_moves_with_its_bounds(self):
        page = place_page([
            {"type": "polygon", "points": [[1440, 1440], [2880, 1440], [2880, 2880]], "fill": "#c0c0c0"},
        ])
        shape = page["shapes"][0]
        self.assertEqual(shape["bounds"], [1440, 1440, 2880, 2880])
        self.assertEqual(shape["pixels"][0], [8 + 96, 8 + 96])

    def test_a_negative_bound_is_shifted_onto_the_window(self):
        page = place_page([
            {"type": "rect", "points": [[-15, -15], [15, 15]], "fill": "#fff"},
        ])
        self.assertEqual(page["shapes"][0]["at"][0], 8)
        self.assertEqual(page["shapes"][0]["at"][1], 8)


if __name__ == "__main__":
    unittest.main()
