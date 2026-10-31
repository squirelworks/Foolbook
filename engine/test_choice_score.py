"""Each graded page leaves its result on the book, in memory.

The questions are written for this test.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine.choice import results
from engine.engine import click
from foolbook.model import Book, Page, RuntimeState


def _page(page_id, question, labels, right):
    quiz = {"question": question, "choices": [{"label": l, "correct": i == right} for i, l in enumerate(labels)]}
    shapes = [{"kind": "button", "name": l, "choice": i} for i, l in enumerate(labels)]
    return Page(id=page_id, quiz=quiz, shapes=shapes)


def _state():
    pages = [
        _page("Q1", "Which is a vowel?", ["B", "E"], 1),
        _page("Q2", "Which is a mammal?", ["Whale", "Trout"], 0),
    ]
    return RuntimeState(book=Book(path="s.fbk", pages=pages))


class ChoiceScoreTests(unittest.TestCase):
    def test_results_are_stored_on_the_book(self):
        state = _state()
        click(state, state.page.shapes[1])
        state.index = 1
        click(state, state.page.shapes[1])
        self.assertEqual(results(state), [
            {"page": "Q1", "choice": 1, "right": True},
            {"page": "Q2", "choice": 1, "right": False},
        ])
        self.assertIs(state.book.props["results"], results(state))

    def test_a_second_answer_on_a_page_replaces_the_first(self):
        state = _state()
        click(state, state.page.shapes[0])
        click(state, state.page.shapes[1])
        self.assertEqual(results(state), [{"page": "Q1", "choice": 1, "right": True}])

    def test_a_new_book_has_no_results(self):
        self.assertEqual(results(_state()), [])

    def test_a_toolbook_file_records_nothing(self):
        from toolbook.format import _AT, _BOOK
        state = _state()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "s.fbk"
            path.write_bytes(b"\0" * _AT + _BOOK + b"\0" * 64)
            state.book.path = str(path)
            click(state, state.page.shapes[1])
        self.assertNotIn("results", state.book.props)


if __name__ == "__main__":
    unittest.main()
