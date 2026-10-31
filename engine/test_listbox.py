"""A list box shows the choices that fit, the chosen one marked, and a bar when it is long."""

from __future__ import annotations

import unittest

from engine import listbox

try:
    from engine import graphics
except ImportError:  # no Tk in this Python
    graphics = None


def _list(n=3, h=60, **extra):
    shape = {"kind": "list", "name": "Fruit", "x": 10, "y": 20, "w": 120, "h": h,
             "choices": [f"Item {i}" for i in range(n)]}
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

    def names(self):
        return [name for name, _a, _kw in self.calls]


@unittest.skipIf(graphics is None, "tkinter is not installed")
class Draw(unittest.TestCase):
    def _drawn(self, shape):
        canvas = _Canvas()
        graphics.draw(canvas, [shape])
        return canvas

    def test_a_short_list_shows_every_row_and_no_bar(self):
        canvas = self._drawn(_list(3, h=60))
        self.assertEqual(canvas.texts(), ["Item 0", "Item 1", "Item 2"])
        self.assertNotIn("create_polygon", canvas.names())

    def test_a_long_list_shows_what_fits_and_a_bar(self):
        canvas = self._drawn(_list(10, h=listbox.ROW * 3))
        self.assertEqual(canvas.texts(), ["Item 0", "Item 1", "Item 2"])
        self.assertEqual(canvas.names().count("create_polygon"), 2)

    def test_scroll_is_the_first_row_shown_and_stops_at_the_end(self):
        self.assertEqual(self._drawn(_list(10, h=listbox.ROW * 3, scroll=4)).texts(), ["Item 4", "Item 5", "Item 6"])
        self.assertEqual(self._drawn(_list(4, h=listbox.ROW * 3, scroll=9)).texts(), ["Item 1", "Item 2", "Item 3"])

    def test_the_chosen_row_is_marked(self):
        canvas = self._drawn(_list(3, h=60, value=1))
        marked = [kw for name, _a, kw in canvas.calls if name == "create_rectangle" and kw.get("fill") == listbox.CHOSEN]
        self.assertEqual(len(marked), 1)


@unittest.skipIf(graphics is None, "tkinter is not installed")
class NidaShapes(unittest.TestCase):
    """The .tbk loader never makes a `list` shape. A loader-shaped field with lines of
    text is still drawn as text, not rows. Synthetic input; NIDA books are not here."""

    def test_a_tbk_field_draws_no_chosen_row(self):
        canvas = _Canvas()
        graphics.draw(canvas, [{"kind": "text", "name": "Response", "text": "Item 0\nItem 1",
                                "x": 10, "y": 20, "w": 120, "h": 60}])
        self.assertFalse([kw for name, _a, kw in canvas.calls if kw.get("fill") == listbox.CHOSEN])


if __name__ == "__main__":
    unittest.main()
