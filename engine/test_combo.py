"""A combo box shows its choice, opens on a click, and closes on the row picked."""

from __future__ import annotations

import unittest

from engine import listbox
from engine.place import shapes_at


def _combo(**extra):
    shape = {"kind": "combo", "name": "Size", "x": 10, "y": 20, "w": 120, "h": 22,
             "choices": ["Small", "Medium", "Large"]}
    shape.update(extra)
    return shape


class Combo(unittest.TestCase):
    def test_a_click_opens_it(self):
        shape = _combo()
        listbox.combo_click(shape, 20, 30)
        self.assertTrue(shape["open"])

    def test_a_click_on_a_row_picks_it_and_closes(self):
        shape = _combo(open=True)
        listbox.combo_click(shape, 20, shape["y"] + shape["h"] + listbox.ROW * 2 + 2)
        self.assertEqual(shape["value"], 2)
        self.assertFalse(shape["open"])

    def test_a_click_on_the_box_again_closes_it_and_keeps_the_choice(self):
        shape = _combo(open=True, value=1)
        listbox.combo_click(shape, 20, 30)
        self.assertFalse(shape["open"])
        self.assertEqual(shape["value"], 1)

    def test_the_shown_text_is_the_chosen_row(self):
        self.assertEqual(listbox.combo_text(_combo(value=1)), "Medium")
        self.assertEqual(listbox.combo_text(_combo()), "")

    def test_an_open_combo_is_hit_below_its_box(self):
        shape = _combo(open=True)
        y = shape["y"] + shape["h"] + listbox.ROW + 2
        self.assertEqual(shapes_at([shape], 20, y), [shape])
        shape["open"] = False
        self.assertEqual(shapes_at([shape], 20, y), [])


if __name__ == "__main__":
    unittest.main()
