"""A combo box shows its choice and an arrow, and open, its rows hang in front of the page."""

from __future__ import annotations

import unittest

from engine import listbox
from engine.place import in_front

try:
    from engine import graphics
except ImportError:  # no Tk in this Python
    graphics = None


def _combo(**extra):
    shape = {"kind": "combo", "name": "Size", "x": 10, "y": 20, "w": 120, "h": 22,
             "choices": ["Small", "Medium", "Large"]}
    shape.update(extra)
    return shape


class _Canvas:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return len(self.calls)
        return record

    def texts(self):
        return [kw["text"] for name, _a, kw in self.calls if name == "create_text"]


@unittest.skipIf(graphics is None, "tkinter is not installed")
class Draw(unittest.TestCase):
    def _drawn(self, *shapes):
        canvas = _Canvas()
        graphics.draw(canvas, list(shapes))
        return canvas

    def test_closed_it_shows_the_chosen_row_and_an_arrow(self):
        canvas = self._drawn(_combo(value=1))
        self.assertEqual(canvas.texts(), ["Medium"])
        self.assertIn("create_polygon", [name for name, _a, _kw in canvas.calls])

    def test_open_its_rows_hang_below_the_box(self):
        canvas = self._drawn(_combo(value=1, open=True))
        self.assertEqual(canvas.texts(), ["Medium", "Small", "Medium", "Large"])

    def test_open_rows_are_drawn_after_a_shape_that_comes_later(self):
        below = {"kind": "button", "name": "Next", "text": "Next", "x": 10, "y": 50, "w": 120, "h": 30}
        canvas = self._drawn(_combo(open=True), below)
        texts = canvas.texts()
        self.assertLess(texts.index("Next"), texts.index("Large"))


class Front(unittest.TestCase):
    def test_an_open_combo_is_in_front_and_a_closed_one_keeps_its_place(self):
        below = {"kind": "rect", "name": "Box", "x": 10, "y": 50, "w": 120, "h": 30}
        self.assertEqual(in_front([_combo(open=True), below])[-1]["kind"], "combo")
        self.assertEqual(in_front([_combo(), below])[-1]["kind"], "rect")

    def test_the_shown_text_is_the_chosen_row(self):
        self.assertEqual(listbox.combo_text(_combo(value=1)), "Medium")
        self.assertEqual(listbox.combo_text(_combo()), "")
        self.assertEqual(listbox.combo_text(_combo(value=7)), "")


class NidaShapes(unittest.TestCase):
    """The .tbk loader never makes a `combo` shape, so the front order of a NIDA page is
    as on main. Synthetic loader-shaped input; NIDA books are not here."""

    def test_a_tbk_page_keeps_its_order(self):
        page = [{"kind": "rect", "name": "A", "x": 0, "y": 0, "w": 50, "h": 50, "open": True},
                {"kind": "button", "name": "B", "x": 10, "y": 10, "w": 20, "h": 20},
                {"kind": "text", "name": "C", "x": 60, "y": 0, "w": 50, "h": 20}]
        self.assertEqual([s["name"] for s in in_front(page)], ["A", "B", "C"])


if __name__ == "__main__":
    unittest.main()
