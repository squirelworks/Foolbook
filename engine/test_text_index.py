"""The reader can say which character of drawn text is under a point."""

from __future__ import annotations

import os
import unittest

try:
    import tkinter as tk
    from engine import graphics
except ImportError:  # no Tk in this Python
    tk = graphics = None


@unittest.skipIf(tk is None or not os.environ.get("DISPLAY"), "needs tkinter and a display")
class TextIndex(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.canvas = tk.Canvas(self.root, width=400, height=200)
        self.canvas.pack()

    def tearDown(self):
        self.root.destroy()

    def _draw(self, text, w=300):
        shape = {"kind": "text", "name": "Body", "text": text, "x": 10, "y": 10, "w": w, "h": 120, "size": 12}
        graphics.draw(self.canvas, [shape])
        self.root.update()
        [item] = [i for i in self.canvas.find_all() if self.canvas.type(i) == "text"]
        return self.canvas.bbox(item)

    def test_the_first_character_is_index_0(self):
        left, top, _right, bottom = self._draw("hello world")
        self.assertEqual(graphics.text_index_at(self.canvas, left + 1, (top + bottom) / 2), ("hello world", 0))

    def test_the_last_character_is_near_the_end(self):
        left, top, right, bottom = self._draw("hello world")
        text, index = graphics.text_index_at(self.canvas, right - 1, (top + bottom) / 2)
        self.assertEqual(text, "hello world")
        self.assertIn(index, (10, 11))

    def test_a_point_on_the_second_line_is_past_the_first_line(self):
        left, top, _right, bottom = self._draw("first line\nsecond line")
        _text, index = graphics.text_index_at(self.canvas, left + 1, bottom - 2)
        self.assertGreaterEqual(index, len("first line\n"))

    def test_a_point_off_the_text_is_none(self):
        _left, _top, right, bottom = self._draw("hello")
        self.assertIsNone(graphics.text_index_at(self.canvas, right + 50, bottom + 50))

    def test_the_drawn_text_is_what_an_index_counts_in(self):
        self.assertEqual(graphics.drawn_text({"text": "a\r\nb   c\n"}), "a\nb c")


if __name__ == "__main__":
    unittest.main()
