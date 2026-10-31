"""`a is in b`, `a is not in b` and `b contains a` test for text inside text."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


def _value(source: str, **variables):
    state = RuntimeState(book=Book(path="x", pages=[Page(id="P1")]))
    state.variables.update(variables)
    run_handler(state, f"if {source} then\nresult = 1\nelse\nresult = 0\nend if")
    return state.variables["result"]


class IsIn(unittest.TestCase):
    def test_a_character_in_a_list(self):
        self.assertEqual(_value('r is in "0,1,2,3,4,5,6,7,8,9,.,+,-"', r="7"), 1)
        self.assertEqual(_value('r is in "0,1,2,3,4,5,6,7,8,9,.,+,-"', r="A"), 0)

    def test_is_not_in(self):
        self.assertEqual(_value('"nc81base.sbk" is not in books', books="tb80r.sbk"), 1)
        self.assertEqual(_value('"nc81base.sbk" is not in books', books="tb80r.sbk,nc81base.sbk"), 0)

    def test_case_does_not_matter(self):
        self.assertEqual(_value('"ABC" is in word', word="xxabcxx"), 1)

    def test_contains(self):
        self.assertEqual(_value('word contains "bc"', word="abcd"), 1)

    def test_a_push_guarded_by_is_not_in_happens_once(self):
        state = RuntimeState(book=Book(path="/nowhere/course.fbk", pages=[Page(id="P1")]))
        guard = 'if "base.sbk" is not in sysBooks\npush "base.sbk" onto sysBooks\nend'
        run_handler(state, guard + "\n" + guard)
        self.assertEqual([name for name, _book in state.sysbooks], ["base.sbk"])


if __name__ == "__main__":
    unittest.main()
