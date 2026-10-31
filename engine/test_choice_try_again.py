"""Try again puts the quiz back and keeps the book's results.

The question is written for this test.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

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

    def test_the_lines_do_not_move_the_page(self):
        state, _ = _state()
        self.assertFalse(follow(state, run_handler(state, "send tryagain")))
        self.assertEqual(state.page.id, "Q1")

    def test_a_toolbook_file_does_not_take_the_message(self):
        from toolbook.format import _AT, _BOOK
        state, shapes = _state()
        click(state, shapes[0])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.fbk"
            path.write_bytes(b"\0" * _AT + _BOOK + b"\0" * 64)
            state.book.path = str(path)
            follow(state, run_handler(state, "send tryAgain"))
        self.assertIs(shapes[3]["visible"], True)


class NidaTryAgainVariableTests(unittest.TestCase):
    def test_93950101_p2070_system_logical_tryagain(self):
        """In the course, tryagain is a system variable. The message must not touch it."""
        from engine.engine import enter_page
        from engine.loader import load
        path = Path(os.environ.get("NIDA_BOOKS") or "/nonexistent") / "93950101.fbk"
        if not path.exists():
            raise unittest.SkipTest("93950101.fbk is not here; set NIDA_BOOKS")
        book = load(path)
        state = RuntimeState(book=book)
        state.index = [p.id for p in book.pages].index("P2070")
        enter_page(state)
        follow(state, run_handler(state, "system logical tryagain\ntryagain = true\nif tryagain then\n  seen = 1\nend if"))
        self.assertEqual(state.page.id, "P2070")
        self.assertIs(state.variables.get("tryagain"), True)
        self.assertEqual(state.variables.get("seen"), 1)


if __name__ == "__main__":
    unittest.main()
