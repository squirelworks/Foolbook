"""A quiz answer button is graded by the choice index it stores.

The question is written for this test.
"""

from __future__ import annotations

import unittest

from engine.choice import grade
from engine.engine import click
from foolbook.model import Book, Page, RuntimeState

QUIZ = {
    "version": 1,
    "question": "How many legs does a spider have?",
    "choices": [{"label": "Six", "correct": False}, {"label": "Eight", "correct": True}],
    "feedback_right": "Right, eight.",
    "feedback_wrong": "Count again.",
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
    def test_the_right_choice_shows_the_right_feedback(self):
        state, shapes = _state()
        self.assertIs(grade(state, shapes[2]), True)
        self.assertIs(shapes[3]["visible"], True)
        self.assertIs(shapes[4]["visible"], False)

    def test_a_wrong_choice_shows_the_wrong_feedback(self):
        state, shapes = _state()
        self.assertIs(grade(state, shapes[1]), False)
        self.assertIs(shapes[3]["visible"], False)
        self.assertIs(shapes[4]["visible"], True)

    def test_the_name_does_not_matter(self):
        state, shapes = _state()
        shapes[2]["name"] = "A"
        shapes[2]["text"] = "Something else"
        self.assertIs(grade(state, shapes[2]), True)

    def test_a_button_with_no_choice_is_not_graded(self):
        state, shapes = _state()
        self.assertIsNone(grade(state, {"kind": "button", "name": "Eight"}))
        self.assertIsNone(grade(state, {"kind": "button", "choice": 7}))

    def test_click_goes_to_next_or_again(self):
        state, shapes = _state(dict(QUIZ, next="P3", again="P2"))
        self.assertTrue(click(state, shapes[2]))
        self.assertEqual(state.page.id, "P3")
        state, shapes = _state(dict(QUIZ, next="P3", again="P2"))
        self.assertTrue(click(state, shapes[1]))
        self.assertEqual(state.page.id, "P2")

    def test_click_with_no_pages_stays_and_shows_feedback(self):
        state, shapes = _state()
        self.assertFalse(click(state, shapes[1]))
        self.assertEqual(state.page.id, "P1")
        self.assertIs(shapes[4]["visible"], True)


if __name__ == "__main__":
    unittest.main()
