"""A click away from an open combo box closes it."""

from __future__ import annotations

import unittest

from engine import listbox


def _combo(name="Size", **extra):
    shape = {"kind": "combo", "name": name, "x": 10, "y": 20, "w": 120, "h": 22,
             "choices": ["Small", "Medium", "Large"]}
    shape.update(extra)
    return shape


class Close(unittest.TestCase):
    def test_a_click_elsewhere_closes_an_open_combo(self):
        combo = _combo(open=True, value=1)
        self.assertTrue(listbox.close_combos([combo], None))
        self.assertFalse(combo["open"])
        self.assertEqual(combo["value"], 1)

    def test_the_combo_clicked_is_left_to_its_own_click(self):
        clicked, other = _combo(open=True), _combo("Colour", open=True)
        self.assertTrue(listbox.close_combos([clicked, other], clicked))
        self.assertTrue(clicked["open"])
        self.assertFalse(other["open"])

    def test_nothing_open_means_the_click_goes_on(self):
        self.assertFalse(listbox.close_combos([_combo(), {"kind": "button", "name": "Next"}], None))


class NidaShapes(unittest.TestCase):
    """The .tbk loader never makes a `combo` shape, so a click on a NIDA page never
    stops here. Synthetic loader-shaped input; NIDA books are not here."""

    def test_a_tbk_page_has_nothing_to_close(self):
        page = [{"kind": "button", "name": "A", "open": True}, {"kind": "text", "name": "Response", "open": True}]
        self.assertFalse(listbox.close_combos(page, None))
        self.assertTrue(all(shape["open"] for shape in page))


if __name__ == "__main__":
    unittest.main()
