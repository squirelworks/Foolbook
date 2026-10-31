"""Try again puts the quiz back. Reset score is a separate command.

The question is written for this test.
"""

from __future__ import annotations

import unittest

from engine.choice import results
from engine.engine import click, follow, run_handler
from foolbook.model import Book, Page, RuntimeState


def _state():
    quiz = {"question": "Which is heavier, a kilo of feathers or a kilo of stones?",
            "choices": [{"label": "Stones", "correct": False}, {"label": "Neither", "correct": True}]}
    shapes = [
        {"kind": "button", "name": "Stones", "choice": 0},
        {"kind": "button", "name": "Neither", "choice": 1},
        {"kind": "text", "name": "Feedback right", "feedback": "right", "visible": False},
        {"kind": "text", "name": "Feedback wrong", "feedback": "wrong", "visible": False},
        {"kind": "button", "name": "Try again", "script": "send tryAgain"},
        {"kind": "button", "name": "Start over", "script": "send resetScore"},
    ]
    return RuntimeState(book=Book(path="t.fbk", pages=[Page(id="Q1", quiz=quiz, shapes=shapes), Page(id="Q2")])), shapes


class TryAgainTests(unittest.TestCase):
    def test_try_again_hides_the_feedback_and_keeps_the_score(self):
        state, shapes = _state()
        click(state, shapes[0])
        self.assertIs(shapes[3]["visible"], True)
        self.assertFalse(click(state, shapes[4]))
        self.assertIs(shapes[2]["visible"], False)
        self.assertIs(shapes[3]["visible"], False)
        self.assertEqual(len(results(state)), 1)
        self.assertEqual(state.page.id, "Q1")

    def test_reset_score_forgets_the_results(self):
        state, shapes = _state()
        click(state, shapes[1])
        click(state, shapes[5])
        self.assertEqual(results(state), [])
        self.assertIs(shapes[2]["visible"], True)

    def test_the_lines_do_not_move_the_page(self):
        state, _ = _state()
        self.assertFalse(follow(state, run_handler(state, "send tryagain\nsend resetscore")))
        self.assertEqual(state.page.id, "Q1")


if __name__ == "__main__":
    unittest.main()
