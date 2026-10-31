"""A hotword is a range of a field's text with a jump. A click in the range follows it."""

from __future__ import annotations

import os
import unittest

from engine import hotwords

try:
    import tkinter as tk
    import tkinter.font
    from engine import graphics
except ImportError:  # no Tk in this Python
    tk = graphics = None


def _field():
    return {"kind": "text", "name": "Body", "text": "See the glossary or go on.", "x": 10, "y": 10, "w": 360, "h": 40,
            "size": 12, "hotwords": [{"start": 8, "end": 16, "item": {"page": "P900"}}]}


class At(unittest.TestCase):
    def test_an_index_inside_the_range_is_the_hotword(self):
        self.assertEqual(hotwords.at(_field(), 8)["item"], {"page": "P900"})
        self.assertEqual(hotwords.at(_field(), 15)["item"], {"page": "P900"})

    def test_the_end_is_not_in_the_range(self):
        self.assertIsNone(hotwords.at(_field(), 16))
        self.assertIsNone(hotwords.at(_field(), 7))

    def test_a_field_without_hotwords_has_none(self):
        self.assertIsNone(hotwords.at({"kind": "text", "text": "x"}, 0))

    def test_a_range_past_the_text_is_ignored(self):
        shape = _field()
        shape["hotwords"] = [{"start": 50, "end": 60, "item": {"page": "P1"}}]
        self.assertEqual(hotwords.ranges(shape), [])


@unittest.skipIf(tk is None or not os.environ.get("DISPLAY"), "needs tkinter and a display")
class Click(unittest.TestCase):
    def test_a_click_on_the_word_finds_the_hotword(self):
        root = tk.Tk()
        try:
            canvas = tk.Canvas(root, width=400, height=100)
            canvas.pack()
            shape = _field()
            graphics.draw(canvas, [shape])
            root.update()
            [item] = [i for i in canvas.find_all() if canvas.type(i) == "text"]
            left, top, _right, bottom = canvas.bbox(item)
            font = tk.font.Font(root=root, font=canvas.itemcget(item, "font"))
            x = left + font.measure("See the gl")
            word = hotwords.clicked(canvas, shape, x, (top + bottom) / 2)
            self.assertEqual(word["item"], {"page": "P900"})
            self.assertIsNone(hotwords.clicked(canvas, shape, left + 2, (top + bottom) / 2))
        finally:
            root.destroy()


if __name__ == "__main__":
    import tkinter.font  # noqa: F401
    unittest.main()
