"""A page's leavePage runs before the next page, once, and a go to in it does not loop."""

from __future__ import annotations

import unittest
from pathlib import Path

from engine.engine import goto
from engine.loader import _book_from_dict
from foolbook.model import RuntimeState


def _state(script):
    data = {"pages": [{"id": "P1", "script": script}, {"id": "P2"}, {"id": "P3"}]}
    return RuntimeState(book=_book_from_dict(Path("book.fbk"), data))


class PageLeaveTests(unittest.TestCase):
    def test_leave_runs_before_the_next_page(self):
        state = _state("to handle leavePage\n  increment left\nend\n")
        self.assertTrue(goto(state, "P2"))
        self.assertEqual(state.variables.get("left"), 1)
        self.assertEqual(state.page.id, "P2")

    def test_a_leave_that_goes_elsewhere_lands_there_once(self):
        state = _state('to handle leavePage\n  increment left\n  go to page "P3"\nend\n')
        self.assertTrue(goto(state, "P2"))
        self.assertEqual(state.page.id, "P3")
        self.assertEqual(state.variables.get("left"), 1)

    def test_a_leave_that_goes_back_to_itself_does_not_loop(self):
        state = _state('to handle leavePage\n  increment left\n  go to page "P1"\nend\n')
        goto(state, "P2")
        self.assertEqual(state.page.id, "P1")
        self.assertEqual(state.variables.get("left"), 1)

    def test_a_missing_page_does_not_leave(self):
        state = _state("to handle leavePage\n  increment left\nend\n")
        self.assertFalse(goto(state, "P9"))
        self.assertNotIn("left", state.variables)

    def test_staying_on_the_page_does_not_leave(self):
        state = _state("to handle leavePage\n  increment left\nend\n")
        goto(state, "p1")
        self.assertNotIn("left", state.variables)


if __name__ == "__main__":
    unittest.main()
