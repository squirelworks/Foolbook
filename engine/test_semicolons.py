"""A semicolon ends a statement, so two can share a line and a trailing one is harmless."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


class Semicolons(unittest.TestCase):
    def test_semicolons(self):
        state = RuntimeState(book=Book(path="", title="b", pages=[Page(id="P1")]))
        run_handler(state, 'result = true;\na = 1; b = 2\nc = "x;y"')
        found = state.variables
        self.assertEqual((found["result"], found["a"], found["b"], found["c"]), (True, 1, 2, "x;y"))


if __name__ == "__main__":
    unittest.main()
