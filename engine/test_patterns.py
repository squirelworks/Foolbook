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


# Shapes as the .tbk loader hands a NIDA page to the window: none has `tile`.
TBK_SHAPES = [
    {"kind": "rect", "name": "paper", "x": 0, "y": 0, "w": 640, "h": 480, "fill": "#c0c0c0", "outline": "#000000"},
    {"kind": "button", "name": "next", "x": 560, "y": 440, "w": 64, "h": 24, "text": "Next", "fill": "#c0c0c0"},
    {"kind": "text", "name": "Question", "x": 40, "y": 60, "w": 400, "h": 120, "text": "Which one?", "font": {"face": "Arial", "size": 12}},
    {"kind": "ellipse", "x": 300, "y": 200, "w": 50, "h": 30, "fill": "#ff0000"},
    {"kind": "arc", "x": 100, "y": 300, "w": 80, "h": 40, "ends": [[100, 320], [180, 320]]},
    {"kind": "polygon", "points": [[10, 10], [50, 10], [30, 40]], "fill": "#00ff00"},
]

# place_window(TBK_SHAPES, 1.5, 0, 0, 12, 7) on main (031e8d8), before this change.
TBK_PLACED = [
    {'fill': '#c0c0c0', 'h': 720.0, 'kind': 'rect', 'name': 'paper', 'outline': '#000000', 'w': 960.0, 'x': 12.0, 'y': 7.0},
    {'fill': '#c0c0c0', 'h': 36.0, 'kind': 'button', 'name': 'next', 'text': 'Next', 'w': 96.0, 'x': 852.0, 'y': 667.0},
    {'font': {'face': 'Arial', 'size': 12}, 'h': 180.0, 'kind': 'text', 'name': 'Question', 'px': True, 'size': 24, 'text': 'Which one?', 'w': 600.0, 'x': 72.0, 'y': 97.0},
    {'fill': '#ff0000', 'h': 45.0, 'kind': 'ellipse', 'w': 75.0, 'x': 462.0, 'y': 307.0},
    {'ends': [[162.0, 487.0], [282.0, 487.0]], 'h': 60.0, 'kind': 'arc', 'w': 120.0, 'x': 162.0, 'y': 457.0},
    {'fill': '#00ff00', 'kind': 'polygon', 'points': [[27.0, 22.0], [87.0, 22.0], [57.0, 67.0]]},
]


class NidaPlacement(unittest.TestCase):
    def test_a_page_without_tile_is_placed_exactly_as_before(self):
        self.assertEqual(place_window(TBK_SHAPES, 1.5, 0, 0, 12, 7), TBK_PLACED)
        for scale in (1.0, 2.0, 3.25):
            self.assertFalse(any("cell" in item for item in place_window(TBK_SHAPES, scale, 0, 0, 0, 0)))


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

    def test_a_tile_on_an_arc_is_never_painted_as_a_fill(self):
        import tkinter as tk
        from engine.graphics import draw
        root = tk.Tk()
        try:
            canvas = tk.Canvas(root, width=100, height=100)
            draw(canvas, [{"kind": "arc", "x": 10, "y": 10, "w": 40, "h": 24,
                           "ends": [[10, 22], [50, 22]], "outline": "#000000", "tile": CHECKS}])
            self.assertNotIn("image", [canvas.type(item) for item in canvas.find_all()])
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
