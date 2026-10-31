"""charCount, wordCount, itemCount and textlineCount count the parts of a value."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


def _run(script):
    state = RuntimeState(book=Book(path="", title="b", pages=[Page(id="P1")]))
    state.variables["lines"] = "a\r\nb"
    run_handler(state, script)
    return state.variables


class CountFunctions(unittest.TestCase):
    def test_counts(self):
        found = _run('pool = "110,111,112"\n'
                     'c = charCount(pool)\n'
                     'i = itemCount(pool)\n'
                     'w = wordCount("one  two three")\n'
                     't = textlineCount(lines)')
        self.assertEqual((found["c"], found["i"], found["w"], found["t"]), (11, 3, 3, 2))

    def test_an_empty_value_counts_none(self):
        found = _run('i = itemCount("")\nw = wordCount("")\nc = charCount("")')
        self.assertEqual((found["i"], found["w"], found["c"]), (0, 0, 0))

    def test_a_count_can_be_used_in_a_sum(self):
        found = _run('n = wordCount("a b c") + 1')
        self.assertEqual(found["n"], 4)


if __name__ == "__main__":
    unittest.main()
