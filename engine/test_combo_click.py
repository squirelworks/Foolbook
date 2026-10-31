"""A click opens a combo box, and a click on a row picks it and closes it."""

from __future__ import annotations

import unittest

from engine import listbox
from engine.place import click_target, shapes_at


def _combo(**extra):
    shape = {"kind": "combo", "name": "Size", "x": 10, "y": 20, "w": 120, "h": 22,
             "choices": ["Small", "Medium", "Large"]}
    shape.update(extra)
    return shape


def _row_y(shape, index):
    return shape["y"] + shape["h"] + listbox.ROW * index + 2


class Click(unittest.TestCase):
    def test_a_click_opens_it(self):
        shape = _combo()
        listbox.combo_click(shape, 20, 30)
        self.assertTrue(shape["open"])

    def test_a_click_on_a_row_picks_it_and_closes(self):
        shape = _combo(open=True)
        listbox.combo_click(shape, 20, _row_y(shape, 2))
        self.assertEqual(shape["value"], 2)
        self.assertFalse(shape["open"])

    def test_a_click_on_the_box_again_closes_it_and_keeps_the_choice(self):
        shape = _combo(open=True, value=1)
        listbox.combo_click(shape, 20, 30)
        self.assertFalse(shape["open"])
        self.assertEqual(shape["value"], 1)


class Reach(unittest.TestCase):
    def test_an_open_combo_is_hit_below_its_box_and_a_closed_one_is_not(self):
        shape = _combo(open=True)
        y = _row_y(shape, 1)
        self.assertEqual(shapes_at([shape], 20, y), [shape])
        shape["open"] = False
        self.assertEqual(shapes_at([shape], 20, y), [])

    def test_its_rows_take_the_click_ahead_of_the_shape_they_cover(self):
        combo = _combo(open=True)
        below = {"kind": "button", "name": "Next", "x": 10, "y": 45, "w": 120, "h": 40, "script": "to handle buttonClick\nend"}
        self.assertIs(click_target([combo, below], 20, _row_y(combo, 1)), combo)
        combo["open"] = False
        self.assertIs(click_target([combo, below], 20, _row_y(combo, 1)), below)


class NidaShapes(unittest.TestCase):
    """The .tbk loader never makes a `combo` shape. A loader-shaped button is hit only
    inside its own box, as on main. Synthetic input; NIDA books are not here."""

    def test_a_tbk_button_is_hit_only_inside_its_box(self):
        button = {"kind": "button", "name": "A", "x": 10, "y": 20, "w": 30, "h": 20, "open": True,
                  "choices": ["x", "y"]}
        self.assertEqual(shapes_at([button], 15, 25), [button])
        self.assertEqual(shapes_at([button], 15, 50), [])


if __name__ == "__main__":
    unittest.main()
