"""pageNumber of this page, pageCount of this book, and a property of page i."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


def _state():
    pages = [
        Page(id="P1"),
        Page(id="P2", raw={"props": {"QuestionNo": "5", "TestNo": "1"}}),
        Page(id="P3", raw={"props": {"QuestionNo": "6"}}),
    ]
    state = RuntimeState(book=Book(path="", title="b", pages=pages))
    state.index = 1
    return state


class PageNumbers(unittest.TestCase):
    def test_page_number_and_count(self):
        state = _state()
        run_handler(state, "n = pageNumber of this page\nc = pageCount of this book")
        self.assertEqual((state.variables["n"], state.variables["c"]), (2, 3))

    def test_a_property_of_page_i(self):
        state = _state()
        run_handler(state, "step i from 1 to pageCount of this book\n"
                           "if questionno of page i = 6 then\nfound = i\nend if\nend step\n"
                           "t = testno of page 2\nnone = testno of page 3")
        self.assertEqual((state.variables["found"], state.variables["t"], state.variables["none"]), (3, 1, ""))

    def test_the_page_number_of_a_named_page(self):
        state = _state()
        run_handler(state, 'n = pageNumber of page "P3"')
        self.assertEqual(state.variables["n"], 3)


if __name__ == "__main__":
    unittest.main()
