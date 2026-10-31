"""`while`, `do ... until`, `break while`, `break step`, `break conditions` and `continue`."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


def _run(source: str, **variables) -> dict:
    state = RuntimeState(book=Book(path="x", pages=[Page(id="P1")]))
    state.variables.update(variables)
    run_handler(state, source)
    return state.variables


class Loops(unittest.TestCase):
    def test_while_runs_until_its_condition_is_false(self):
        got = _run("n = 0\nwhile n < 5\nn = n + 1\nend while\nafter = 1")
        self.assertEqual((got["n"], got["after"]), (5, 1))

    def test_break_while_leaves_the_loop_and_the_handler_goes_on(self):
        got = _run("n = 0\nwhile true\nn = n + 1\nif n = 3 then\nbreak while\nend if\nend while\nafter = 1")
        self.assertEqual((got["n"], got["after"]), (3, 1))

    def test_do_until_runs_at_least_once(self):
        got = _run("n = 10\ndo\nn = n + 1\nuntil n > 5\nafter = 1")
        self.assertEqual((got["n"], got["after"]), (11, 1))

    def test_break_step_leaves_the_step(self):
        got = _run("last = 0\nstep i from 1 to 10\nlast = i\nif i = 4 then\nbreak step\nend if\nend step\nafter = 1")
        self.assertEqual((got["last"], got["after"]), (4, 1))

    def test_break_conditions_leaves_the_branch(self):
        got = _run("conditions\nwhen true\na = 1\nbreak conditions\na = 2\nend conditions\nafter = 1")
        self.assertEqual((got["a"], got["after"]), (1, 1))

    def test_continue_skips_the_rest_of_the_pass(self):
        got = _run("n = 0\ntotal = 0\nwhile n < 4\nn = n + 1\nif n = 2 then\ncontinue\nend if\ntotal = total + n\nend while")
        self.assertEqual(got["total"], 8)


if __name__ == "__main__":
    unittest.main()
