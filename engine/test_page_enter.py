"""An .fbk page script runs when the page is shown."""

from __future__ import annotations

import unittest
from pathlib import Path

from engine.engine import enter_page, goto
from engine.loader import _book_from_dict
from foolbook.model import RuntimeState


def _state(script):
    data = {"pages": [{"id": "P1"}, {"id": "P2", "script": script}, {"id": "P3"}]}
    return RuntimeState(book=_book_from_dict(Path("book.fbk"), data))


class PageEnterTests(unittest.TestCase):
    def test_a_bare_page_script_runs_on_enter(self):
        state = _state("entered = 1\n")
        goto(state, "P2")
        enter_page(state)
        self.assertEqual(state.variables.get("entered"), 1)

    def test_it_does_not_run_on_another_page(self):
        state = _state("entered = 1\n")
        enter_page(state)
        self.assertNotIn("entered", state.variables)

    def test_a_to_handle_enterpage_still_runs(self):
        state = _state("to handle enterPage\n  entered = 2\nend\n")
        goto(state, "P2")
        enter_page(state)
        self.assertEqual(state.variables.get("entered"), 2)

    def test_an_enter_script_can_move_on(self):
        state = _state('go to page "P3"\n')
        goto(state, "P2")
        self.assertTrue(enter_page(state))
        self.assertEqual(state.page.id, "P3")


if __name__ == "__main__":
    unittest.main()
