"""A graded answer shows its feedback shape and hides the other.

The question is written for this test.
"""

from __future__ import annotations

import unittest

from engine.choice import grade
from foolbook.model import Book, Page, RuntimeState

QUIZ = {"question": "Which planet is closest to the Sun?",
        "choices": [{"label": "Venus", "correct": False}, {"label": "Mercury", "correct": True}]}


def _state():
    shapes = [
        {"kind": "button", "name": "Choice 1", "choice": 0},
        {"kind": "button", "name": "Choice 2", "choice": 1},
        {"kind": "text", "name": "Feedback right", "feedback": "right", "visible": False},
        {"kind": "text", "name": "Feedback wrong", "feedback": "wrong", "visible": False},
        {"kind": "text", "name": "Note", "visible": False},
    ]
    return RuntimeState(book=Book(path="q.fbk", pages=[Page(id="P1", quiz=QUIZ, shapes=shapes)])), shapes


class ChoiceFeedbackTests(unittest.TestCase):
    def test_right_shows_right(self):
        state, shapes = _state()
        grade(state, shapes[1])
        self.assertEqual([s["visible"] for s in shapes[2:]], [True, False, False])

    def test_wrong_shows_wrong(self):
        state, shapes = _state()
        grade(state, shapes[0])
        self.assertEqual([s["visible"] for s in shapes[2:]], [False, True, False])

    def test_a_second_answer_swaps_them(self):
        state, shapes = _state()
        grade(state, shapes[0])
        grade(state, shapes[1])
        self.assertEqual([s["visible"] for s in shapes[2:]], [True, False, False])


if __name__ == "__main__":
    unittest.main()
