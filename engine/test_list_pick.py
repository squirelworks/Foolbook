"""A click on a list box's row picks that row."""

from __future__ import annotations

import unittest

from engine import listbox


def _list(n=3, h=60, **extra):
    shape = {"kind": "list", "name": "Fruit", "x": 10, "y": 20, "w": 120, "h": h,
             "choices": [f"Item {i}" for i in range(n)]}
    shape.update(extra)
    return shape


class Pick(unittest.TestCase):
    def test_a_click_on_a_row_picks_that_index(self):
        shape = _list(3, h=60)
        listbox.click(shape, 20, 20 + listbox.ROW + 2)
        self.assertEqual(shape["value"], 1)

    def test_a_click_on_a_scrolled_list_picks_the_row_shown(self):
        shape = _list(10, h=listbox.ROW * 3, scroll=4)
        listbox.click(shape, 20, 20 + 2)
        self.assertEqual(shape["value"], 4)

    def test_a_click_past_the_last_row_picks_nothing(self):
        shape = _list(2, h=listbox.ROW * 4, value=0)
        listbox.click(shape, 20, shape["y"] + listbox.ROW * 3 + 2)
        self.assertEqual(shape["value"], 0)


class NidaShapes(unittest.TestCase):
    """The .tbk loader never makes a `list` shape, so the reader's click hook (only for
    kind `list`) never reaches a NIDA page."""

    def test_the_hook_is_behind_kind_list(self):
        import inspect
        from viewer import native
        source = inspect.getsource(native)
        self.assertEqual(source.count("listbox.click("), 1)
        self.assertIn('(target.get("kind") or "") == "list"', source)


if __name__ == "__main__":
    unittest.main()
