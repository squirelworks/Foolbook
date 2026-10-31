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

    def test_the_nida_key_handler_lines(self):
        state = RuntimeState(book=Book(path="", title="b", pages=[Page(id="P1")]))
        run_handler(state, 'key = 115\nisCtrl = true\nr = uppercase(ansiToChar(key))\n'
                           'conditions\nwhen uppercase (ansiToChar(key)) is in "S" and isCtrl is true\nw = "yes"\nelse\nw = "no"\nend conditions')
        self.assertEqual((state.variables["r"], state.variables["w"]), ("S", "yes"))


if __name__ == "__main__":
    unittest.main()
