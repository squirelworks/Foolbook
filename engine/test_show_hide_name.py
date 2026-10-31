"""show and hide a shape by its name, whatever its kind, for .fbk scripts."""

from __future__ import annotations

import unittest

from engine.engine import run_handler
from foolbook.model import Book, Page, RuntimeState


def _state():
    shapes = [
        {"kind": "text", "name": "Feedback", "visible": False},
        {"kind": "hotspot", "name": "map"},
        {"kind": "button", "name": "Next", "visible": False},
    ]
    other = [{"kind": "rect", "name": "far", "visible": False}]
    book = Book(path="b.fbk", pages=[Page(id="P1", shapes=shapes), Page(id="P2", shapes=other)])
    return RuntimeState(book=book), shapes, other


class ShowHideByNameTests(unittest.TestCase):
    def test_show_a_name(self):
        state, shapes, _ = _state()
        run_handler(state, 'show "feedback"')
        self.assertIs(shapes[0]["visible"], True)
        self.assertIs(shapes[2]["visible"], False)

    def test_hide_shape_of_a_kind_with_no_class_word(self):
        state, shapes, _ = _state()
        run_handler(state, 'hide shape "Map"')
        self.assertIs(shapes[1]["visible"], False)

    def test_of_page(self):
        state, _, other = _state()
        run_handler(state, 'show "far" of page "P2"')
        self.assertIs(other[0]["visible"], True)

    def test_the_class_form_still_works(self):
        state, shapes, _ = _state()
        run_handler(state, 'show button "next"')
        self.assertIs(shapes[2]["visible"], True)

    def test_show_group_is_not_a_name(self):
        state, shapes, _ = _state()
        actions = run_handler(state, 'show group "feedback"')
        self.assertEqual(actions[0]["target"], "visible of group")
        self.assertIs(shapes[0]["visible"], False)


if __name__ == "__main__":
    unittest.main()
