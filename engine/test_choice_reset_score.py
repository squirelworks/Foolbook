"""send resetScore forgets the book's quiz results.

The question is written for this test.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine.choice import results
from engine.engine import click, follow, run_handler
from foolbook.model import Book, Page, RuntimeState


def _state():
    quiz = {"question": "How many sides has a triangle?",
            "choices": [{"label": "Three", "correct": True}, {"label": "Four", "correct": False}]}
    shapes = [{"kind": "button", "name": "Choice 1", "choice": 0},
              {"kind": "button", "name": "Choice 2", "choice": 1},
              {"kind": "button", "name": "Start over", "script": "send resetScore"}]
    return RuntimeState(book=Book(path="r.fbk", pages=[Page(id="Q1", quiz=quiz, shapes=shapes)])), shapes


class ResetScoreTests(unittest.TestCase):
    def test_reset_score_forgets_the_results(self):
        state, shapes = _state()
        click(state, shapes[0])
        self.assertEqual(len(results(state)), 1)
        self.assertFalse(click(state, shapes[2]))
        self.assertEqual(results(state), [])
        self.assertEqual(state.page.id, "Q1")

    def test_a_toolbook_file_does_not_take_the_message(self):
        from toolbook.format import _AT, _BOOK
        state, shapes = _state()
        click(state, shapes[0])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.fbk"
            path.write_bytes(b"\0" * _AT + _BOOK + b"\0" * 64)
            state.book.path = str(path)
            follow(state, run_handler(state, "send resetScore"))
        self.assertEqual(len(results(state)), 1)


if __name__ == "__main__":
    unittest.main()
