"""A bare `end` closes the block that is open, whatever kind it is."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


def _run(source: str, **variables) -> dict:
    state = RuntimeState(book=Book(path="x", pages=[Page(id="P1")]))
    state.variables.update(variables)
    run_handler(state, source)
    return state.variables


NESTED = """
conditions
    when  mode = 1
        conditions
            when sub = 0
                got = "inner0"
            when sub = 1
                got = "inner1"
        end
    when  mode = 5
        got = "five"
end conditions
after = 1
"""


class BareEnd(unittest.TestCase):
    def test_a_bare_end_closes_the_inner_conditions(self):
        got = _run(NESTED, mode=1, sub=1)
        self.assertEqual((got["got"], got["after"]), ("inner1", 1))

    def test_the_branch_after_a_bare_end_is_its_own(self):
        got = _run(NESTED, mode=5, sub=1)
        self.assertEqual(got["got"], "five")

    def test_an_if_closed_by_end_inside_a_when(self):
        got = _run("conditions\nwhen a = 1\nif b = 1\nx = 1\nend\ny = 2\nwhen a = 2\ny = 3\nend conditions", a=1, b=0)
        self.assertEqual(got.get("y"), 2)
        self.assertNotIn("x", got)

    def test_conditions_inside_an_if_closed_by_end(self):
        got = _run("if a = 1\nconditions\nwhen b = 1\nx = 1\nend\ny = 2\nend if\nz = 3", a=1, b=1)
        self.assertEqual((got.get("x"), got.get("y"), got.get("z")), (1, 2, 3))


if __name__ == "__main__":
    unittest.main()
