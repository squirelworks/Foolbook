"""An object the reader marks hidden is a shape that is not shown, not clicked and not read as page text."""

from __future__ import annotations

import unittest

from engine.loader import _store_shape
from engine.polygon import to_pixel
from engine.place import shapes_at


def _obj(**more):
    base = {"kind": "text", "name": "response", "bounds": (0, 0, 1440, 720), "text": ""}
    base.update(more)
    return base


class HiddenObjects(unittest.TestCase):
    def test_a_hidden_object_is_a_shape_with_visible_false(self):
        self.assertIs(_store_shape(_obj(hidden=True), to_pixel)["visible"], False)

    def test_an_ordinary_object_is_visible(self):
        self.assertIs(_store_shape(_obj(), to_pixel)["visible"], True)

    def test_the_answer_key_rectangle_is_still_hidden_by_name(self):
        shape = _store_shape(_obj(kind="rect", name="Correct"), to_pixel)
        self.assertIs(shape["visible"], False)

    def test_a_hidden_object_is_not_under_the_pointer(self):
        shape = _store_shape(_obj(hidden=True), to_pixel)
        self.assertEqual(shapes_at([shape], 5, 5), [])


if __name__ == "__main__":
    unittest.main()
