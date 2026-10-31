"""uppercase(x) and lowercase(x) change the case of text."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


class CaseFunctions(unittest.TestCase):
    def test_both(self):
        state = RuntimeState(book=Book(path="", title="b", pages=[Page(id="P1")]))
        run_handler(state, 'q = uppercase("Quiz")\nr = uppercase(ansiToChar(120))\nl = lowercase("ABC d")\nn = uppercase(7)')
        found = state.variables
        self.assertEqual((found["q"], found["r"], found["l"], found["n"]), ("QUIZ", "X", "abc d", "7"))


if __name__ == "__main__":
    unittest.main()
