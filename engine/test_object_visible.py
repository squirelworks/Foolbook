"""show, hide and set visible of one object, found by class and name."""

from __future__ import annotations

import unittest

from engine.engine import _eval, run_handler, split_handlers
from foolbook.model import Book, Page, RuntimeState


def _shape(kind, name, visible=True):
    return {"kind": kind, "name": name, "x": 0, "y": 0, "w": 10, "h": 10, "visible": visible}


def _state(other=False):
    shapes = [_shape("button", "Next", False), _shape("text", "response", False), _shape("text", "Text"),
              _shape("rect", "mark", False), _shape("image", "shoe", False), _shape("button", "Back")]
    pages = [Page(id="P1", shapes=shapes)]
    if other:
        pages.append(Page(id="P2", shapes=[_shape("text", "far", False)]))
    return RuntimeState(book=Book(path="x", pages=pages)), shapes


def _run(state, line):
    run_handler(state, split_handlers("to handle buttonClick\n  %s\nend\n" % line)[0].source)


class ObjectVisible(unittest.TestCase):
    def test_set_visible_of_a_button_to_true(self):
        state, shapes = _state()
        _run(state, 'set visible of button "next" to true')
        self.assertIs(shapes[0]["visible"], True)
        self.assertIs(shapes[1]["visible"], False)

    def test_show_and_hide_a_field(self):
        state, shapes = _state()
        _run(state, 'show field "Response"')
        self.assertIs(shapes[1]["visible"], True)
        _run(state, 'hide field "response"')
        self.assertIs(shapes[1]["visible"], False)

    def test_the_class_has_to_match(self):
        state, shapes = _state()
        _run(state, 'show button "response"')
        self.assertIs(shapes[1]["visible"], False)

    def test_a_drawn_picture_or_button_is_an_image(self):
        state, shapes = _state()
        _run(state, 'show picture "shoe"')
        self.assertIs(shapes[4]["visible"], True)

    def test_a_rectangle_by_name(self):
        state, shapes = _state()
        _run(state, 'set visible of rectangle "mark" to true')
        self.assertIs(shapes[3]["visible"], True)

    def test_of_page_reaches_another_page(self):
        state, _ = _state(other=True)
        _run(state, 'show field "far" of page "P2"')
        self.assertIs(state.book.pages[1].shapes[0]["visible"], True)

    def test_the_name_may_be_an_expression(self):
        state, shapes = _state()
        state.variables["n"] = "Next"
        _run(state, 'show button (n)')
        self.assertIs(shapes[0]["visible"], True)

    def test_visible_of_an_object_reads_back(self):
        state, _ = _state()
        self.assertIs(_eval('visible of button "Back"', state), True)
        self.assertIs(_eval('visible of button "Next"', state), False)


if __name__ == "__main__":
    unittest.main()
