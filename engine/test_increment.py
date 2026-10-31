"""increment x, increment(x), and increment x by n."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


def _run(script):
    state = RuntimeState(book=Book(path="", title="b", pages=[Page(id="P1")]))
    run_handler(state, script)
    return state.variables


class Increment(unittest.TestCase):
    def test_with_brackets(self):
        found = _run("tries = 1\nincrement(tries)\ncount = 5\ndecrement( count )")
        self.assertEqual((found["tries"], found["count"]), (2, 4))

    def test_by_an_amount(self):
        found = _run("n = 1\nstep = 3\nincrement n by step\ndecrement n by 2")
        self.assertEqual(found["n"], 2)

    def test_a_blank_starts_at_zero(self):
        found = _run("system int __embeddedTries\nincrement(__embeddedTries)")
        self.assertEqual(found["__embeddedTries"], 1)


if __name__ == "__main__":
    unittest.main()
