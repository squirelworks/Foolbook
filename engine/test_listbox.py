"""A list box shows its choices, a click picks one, and a long list scrolls."""

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


class Rows(unittest.TestCase):
    def test_a_short_list_shows_every_row_and_no_scroll_bar(self):
        shape = _list(3, h=60)
        self.assertEqual([i for i, _t, _y in listbox.visible_rows(shape)], [0, 1, 2])
        self.assertFalse(listbox.scrolls(shape))

    def test_a_click_on_a_row_picks_that_index(self):
        shape = _list(3, h=60)
        listbox.click(shape, 20, 20 + listbox.ROW + 2)
        self.assertEqual(shape["value"], 1)

    def test_a_long_list_shows_what_fits_and_scrolls(self):
        shape = _list(10, h=listbox.ROW * 3)
        self.assertTrue(listbox.scrolls(shape))
        self.assertEqual([i for i, _t, _y in listbox.visible_rows(shape)], [0, 1, 2])
        right = shape["x"] + shape["w"] - 2
        listbox.click(shape, right, shape["y"] + shape["h"] - 2)  # the down half of the bar
        self.assertEqual(shape["scroll"], 1)
        self.assertNotIn("value", shape)
        self.assertEqual([i for i, _t, _y in listbox.visible_rows(shape)], [1, 2, 3])
        listbox.click(shape, right, shape["y"] + 2)  # the up half
        self.assertEqual(shape["scroll"], 0)

    def test_scrolling_stops_at_the_last_row(self):
        shape = _list(4, h=listbox.ROW * 3)
        right = shape["x"] + shape["w"] - 2
        for _ in range(5):
            listbox.click(shape, right, shape["y"] + shape["h"] - 2)
        self.assertEqual(shape["scroll"], 1)

    def test_a_click_past_the_last_row_picks_nothing(self):
        shape = _list(2, h=listbox.ROW * 4)
        listbox.click(shape, 20, shape["y"] + listbox.ROW * 3 + 2)
        self.assertNotIn("value", shape)


class _Canvas:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return len(self.calls)
        return record


@unittest.skipIf(graphics is None, "tkinter is not installed")
class Draw(unittest.TestCase):
    def test_the_rows_that_fit_are_drawn_and_the_chosen_one_is_marked(self):
        canvas = _Canvas()
        graphics.draw(canvas, [_list(10, h=listbox.ROW * 3, value=1)])
        texts = [kw["text"] for name, _a, kw in canvas.calls if name == "create_text"]
        self.assertEqual(texts, ["Item 0", "Item 1", "Item 2"])
        marked = [kw for name, _a, kw in canvas.calls if name == "create_rectangle" and kw.get("fill") == listbox.CHOSEN]
        self.assertEqual(len(marked), 1)


if __name__ == "__main__":
    unittest.main()
