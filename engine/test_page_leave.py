"""A go to in a page's leavePage is where the reader lands.

The NIDA guard runs when NIDA_BOOKS names a folder holding the book.
The books are not in this repository.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest import mock

from engine import engine
from engine.engine import click_script, follow, goto, press, run_handler
from engine.loader import _book_from_dict, load
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

    def test_a_leave_that_goes_elsewhere_lands_there(self):
        state = _state('to handle leavePage\n  increment left\n  go to page "P3"\nend\n')
        self.assertTrue(goto(state, "P2"))
        self.assertEqual(state.page.id, "P3")
        self.assertEqual(state.variables.get("left"), 1)

    def test_a_leave_that_goes_back_to_its_own_page_stays(self):
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


class NidaLeaveTests(unittest.TestCase):
    """93951204 P3910 and 93950101 P1910 set the menu flag in leavePage. It runs once a departure."""

    def _page(self, name, page_id):
        path = Path(os.environ.get("NIDA_BOOKS") or "/nonexistent") / name
        if not path.exists():
            raise unittest.SkipTest(f"{name} is not here; set NIDA_BOOKS")
        book = load(path)
        state = RuntimeState(book=book)
        state.index = [p.id for p in book.pages].index(page_id)
        return state

    def _p3910(self):
        return self._page("93951204.fbk", "P3910")

    def test_93950101_p1910_next_leaves_once(self):
        state = self._page("93950101.fbk", "P1910")
        button = next(s for s in state.page.shapes if s.get("name") == "Next")
        leaves = self._leaves(state, lambda s: follow(s, run_handler(s, click_script(button))))
        self.assertEqual(len(leaves), 1)
        self.assertEqual(state.page.id, "P1001")

    def _leaves(self, state, act):
        real = engine.run_page_handlers
        with mock.patch.object(engine, "run_page_handlers", wraps=real) as spy:
            act(state)
        return [c for c in spy.call_args_list if str(c.args[1]).lower() == "leavepage"]

    def test_the_next_button_script_leaves_once(self):
        state = self._p3910()
        button = next(s for s in state.page.shapes if s.get("name") == "Next")
        leaves = self._leaves(state, lambda s: follow(s, run_handler(s, click_script(button))))
        self.assertEqual(len(leaves), 1)
        self.assertEqual(state.page.id, "P3001")

    def test_the_window_next_leaves_once(self):
        state = self._p3910()
        leaves = self._leaves(state, lambda s: press(s, "Next", "p3001"))
        self.assertEqual(len(leaves), 1)
        self.assertEqual(state.page.id, "P3001")


if __name__ == "__main__":
    unittest.main()
