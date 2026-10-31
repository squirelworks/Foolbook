"""A quiz answer button is graded by the choice index it stores.

The question is written for this test.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine.choice import grade
from engine.engine import click
from foolbook.model import Book, Page, RuntimeState

QUIZ = {
    "version": 1,
    "question": "How many legs does a spider have?",
    "choices": [{"label": "Six", "correct": False}, {"label": "Eight", "correct": True}],
}


def _state(quiz=QUIZ):
    shapes = [
        {"kind": "text", "name": "Question", "text": QUIZ["question"]},
        {"kind": "button", "name": "Six", "text": "Six", "choice": 0},
        {"kind": "button", "name": "Eight", "text": "Eight", "choice": 1},
        {"kind": "text", "name": "Feedback right", "feedback": "right", "visible": False},
        {"kind": "text", "name": "Feedback wrong", "feedback": "wrong", "visible": False},
    ]
    pages = [Page(id="P1", quiz=dict(quiz), shapes=shapes), Page(id="P2"), Page(id="P3")]
    return RuntimeState(book=Book(path="q.fbk", pages=pages)), shapes


class ChoiceGradeTests(unittest.TestCase):
    def test_the_right_choice(self):
        state, shapes = _state()
        self.assertIs(grade(state, shapes[2]), True)
        self.assertEqual(state.variables["__answer"], {"page": "P1", "choice": 1, "right": True})

    def test_a_wrong_choice(self):
        state, shapes = _state()
        self.assertIs(grade(state, shapes[1]), False)
        self.assertEqual(state.variables["__answer"], {"page": "P1", "choice": 0, "right": False})

    def test_the_name_does_not_matter(self):
        state, shapes = _state()
        shapes[2]["name"] = "Something"
        shapes[2]["text"] = "Something else"
        self.assertIs(grade(state, shapes[2]), True)

    def test_a_button_with_no_choice_is_not_graded(self):
        state, shapes = _state()
        self.assertIsNone(grade(state, {"kind": "button", "name": "Eight"}))
        self.assertIsNone(grade(state, {"kind": "button", "choice": 7}))
        self.assertNotIn("__answer", state.variables)

    def test_a_click_grades(self):
        state, shapes = _state()
        self.assertFalse(click(state, shapes[2]))
        self.assertTrue(state.variables["__answer"]["right"])

    def test_a_toolbook_file_is_not_graded(self):
        from toolbook.format import _AT, _BOOK
        state, shapes = _state()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "q.fbk"
            path.write_bytes(b"\0" * _AT + _BOOK + b"\0" * 64)
            state.book.path = str(path)
            self.assertIsNone(grade(state, shapes[2]))
        self.assertNotIn("__answer", state.variables)


if __name__ == "__main__":
    unittest.main()
