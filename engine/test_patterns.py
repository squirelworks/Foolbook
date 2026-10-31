"""A shape can be filled with an eight by eight pattern that repeats and grows with the page."""

import os
import unittest

from engine import patterns
from engine.place import place_window

CHECKS = ["10101010", "01010101"] * 4


class Rows(unittest.TestCase):
    def test_numbers_and_strings_name_the_same_rows(self):
        self.assertEqual(patterns.rows([0xAA, 0x55] * 4), CHECKS)
        self.assertEqual(patterns.rows(CHECKS), CHECKS)

    def test_anything_else_is_no_pattern(self):
        for bad in (None, 7, CHECKS[:7], ["1010101"] * 8, [256] * 8, ["2" * 8] * 8, [True] * 8):
            self.assertIsNone(patterns.rows(bad), bad)

    def test_one_repeat_uses_outline_for_1_and_fill_for_0_and_grows_with_the_cell(self):
        grid = patterns.pixels(CHECKS, "#000000", "#ffffff", cell=2)
        self.assertEqual(len(grid), 16)
        self.assertEqual(grid[0][:4], ["#000000", "#000000", "#ffffff", "#ffffff"])
        self.assertEqual(grid[2][:2], ["#ffffff", "#ffffff"])

    def test_the_window_scale_reaches_the_tile(self):
        placed = place_window([{"kind": "rect", "x": 0, "y": 0, "w": 80, "h": 80, "tile": CHECKS}], 2.0, 0, 0, 0, 0)
        self.assertEqual(placed[0]["cell"], 2)


@unittest.skipUnless(os.environ.get("DISPLAY"), "needs a display")
class Drawn(unittest.TestCase):
    def test_a_tiled_rectangle_is_painted_as_a_picture(self):
        import tkinter as tk
        from engine.graphics import draw
        root = tk.Tk()
        try:
            canvas = tk.Canvas(root, width=100, height=100)
            draw(canvas, [{"kind": "rect", "x": 10, "y": 10, "w": 40, "h": 24,
                           "fill": "#ffffff", "outline": "#000000", "tile": CHECKS}])
            kinds = [canvas.type(item) for item in canvas.find_all()]
            self.assertIn("image", kinds)
            photo = canvas._foolbook_photos[-1]
            self.assertEqual((photo.width(), photo.height()), (40, 24))
            self.assertEqual(photo.get(0, 0), (0, 0, 0))
            self.assertEqual(photo.get(1, 0), (255, 255, 255))
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
