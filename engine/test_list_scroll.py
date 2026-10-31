"""A click on a long list box's bar scrolls it one row."""

from __future__ import annotations

import unittest

from engine import listbox


def _list(n=10, h=listbox.ROW * 3, **extra):
    shape = {"kind": "list", "name": "Fruit", "x": 10, "y": 20, "w": 120, "h": h,
             "choices": [f"Item {i}" for i in range(n)]}
    shape.update(extra)
    return shape


def _bar(shape, half):
    right = shape["x"] + shape["w"] - 2
    return right, (shape["y"] + 2 if half == "up" else shape["y"] + shape["h"] - 2)


class Scroll(unittest.TestCase):
    def test_the_lower_half_scrolls_down_and_the_upper_half_up(self):
        shape = _list()
        listbox.click(shape, *_bar(shape, "down"))
        self.assertEqual(shape["scroll"], 1)
        self.assertEqual([i for i, _t, _y in listbox.visible_rows(shape)], [1, 2, 3])
        listbox.click(shape, *_bar(shape, "up"))
        self.assertEqual(shape["scroll"], 0)

    def test_a_click_on_the_bar_picks_no_row(self):
        shape = _list()
        listbox.click(shape, *_bar(shape, "down"))
        self.assertNotIn("value", shape)

    def test_scrolling_stops_at_the_first_and_last_rows(self):
        shape = _list(4)
        for _ in range(5):
            listbox.click(shape, *_bar(shape, "down"))
        self.assertEqual(shape["scroll"], 1)
        for _ in range(5):
            listbox.click(shape, *_bar(shape, "up"))
        self.assertEqual(shape["scroll"], 0)

    def test_a_short_list_has_no_bar_so_its_right_edge_picks(self):
        shape = _list(2, h=listbox.ROW * 4)
        listbox.click(shape, shape["x"] + shape["w"] - 2, shape["y"] + 2)
        self.assertEqual(shape["value"], 0)
        self.assertNotIn("scroll", shape)


if __name__ == "__main__":
    unittest.main()
