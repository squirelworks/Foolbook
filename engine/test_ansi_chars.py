"""ansiToChar(n) gives the character with that code, and charToAnsi(c) the code."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


class AnsiChars(unittest.TestCase):
    def test_both_ways(self):
        state = RuntimeState(book=Book(path="", title="b", pages=[Page(id="P1")]))
        run_handler(state, 'i = 2\ntemp = ansiToChar(96 + i)\ncode = charToAnsi("A")\nfirst = charToAnsi("bc")')
        self.assertEqual((state.variables["temp"], state.variables["code"], state.variables["first"]), ("b", 65, 98))

    def test_an_empty_char_is_zero(self):
        state = RuntimeState(book=Book(path="", title="b", pages=[Page(id="P1")]))
        run_handler(state, 'code = charToAnsi("")')
        self.assertEqual(state.variables["code"], 0)


if __name__ == "__main__":
    unittest.main()
