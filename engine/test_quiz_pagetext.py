"""A question in a running quiz does not give its page name away."""

from __future__ import annotations

import unittest

from engine import quiz
from foolbook.model import Book, Page, RuntimeState


def _state(show=None):
    page = Page(id="P10228", shapes=[{"name": "PageText", "kind": "text", "text": "P10228"},
                                      {"name": "Index", "kind": "text", "text": "Question 99."}],
                raw={"props": {"QuestionNo": "111"}})
    state = RuntimeState(book=Book(path="x.tbk", pages=[page]), index=0)
    if show is not None:
        state.variables["__quizShowPageNumbers"] = show
    return state, page


class PageText(unittest.TestCase):
    def test_default_says_testing(self):
        state, page = _state()
        quiz._prepare(state, "P10228", 3)
        self.assertEqual(page.shapes[0]["text"], "Testing")
        self.assertEqual(page.shapes[1]["text"], "Question 3.")

    def test_show_page_numbers_keeps_the_name(self):
        state, page = _state(show=1)
        quiz._prepare(state, "P10228", 1)
        self.assertEqual(page.shapes[0]["text"], "P10228")


if __name__ == "__main__":
    unittest.main()
