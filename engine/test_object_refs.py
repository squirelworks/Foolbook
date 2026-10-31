"""An object named by class and name, on another page or its background."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


def _shape(kind, name, layer, **more):
    shape = {"kind": kind, "name": name, "layer": layer, "text": "", "visible": True}
    shape.update(more)
    return shape


def _state():
    first = Page(id="P1", shapes=[_shape("text", "Index", "background", text="Question 99.")])
    quiz = Page(id="P2", shapes=[
        _shape("text", "Index", "background", text="Question 99."),
        _shape("image", "OK", "background"),
        _shape("rect", "Correct", "page", visible=True),
        _shape("image", "A", "page", checked=True),
        _shape("text", "A", "page", text="Check the setup."),
    ])
    state = RuntimeState(book=Book(path="", title="b", pages=[first, quiz]))
    return state, quiz


class ObjectReferences(unittest.TestCase):
    def test_set_text_of_a_background_field_of_page_i(self):
        state, quiz = _state()
        run_handler(state, 'i = 2\nn = 1\n'
                           'if isObject(field("index") of parent of page i) then\n'
                           'set text of field("index") of parent of page i to "Question " & n & "."\n'
                           'end if')
        self.assertEqual(quiz.shapes[0]["text"], "Question 1.")
        self.assertEqual(state.book.pages[0].shapes[0]["text"], "Question 99.")

    def test_a_button_and_a_field_with_one_name_are_told_apart(self):
        state, quiz = _state()
        run_handler(state, 'temp = "a"\n'
                           'set checked of button(temp) of page 2 to false\n'
                           'words = text of field "A" of page "P2"')
        self.assertFalse(quiz.shapes[3]["checked"])
        self.assertEqual(state.variables["words"], "Check the setup.")

    def test_visible_and_enabled_and_a_missing_object(self):
        state, quiz = _state()
        run_handler(state, 'set visible of rectangle("correct") of page 2 to false\n'
                           'set enabled of button("OK") of parent of page 2 to false\n'
                           'shown = visible of rectangle "correct" of page 2\n'
                           'there = isObject(button("Help") of parent of page 2)')
        self.assertFalse(quiz.shapes[2]["visible"])
        self.assertFalse(quiz.shapes[1]["enabled"])
        self.assertEqual((state.variables["shown"], state.variables["there"]), (False, False))


if __name__ == "__main__":
    unittest.main()
