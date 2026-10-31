"""A button click: the script first, then the item only if the script did not move."""

from __future__ import annotations

import unittest

from engine.engine import click
from foolbook.model import Book, Page, RuntimeState


def _state():
    pages = [Page(id="P1"), Page(id="P2"), Page(id="P3")]
    return RuntimeState(book=Book(path="book.fbk", pages=pages))


class ClickOrderTests(unittest.TestCase):
    def test_a_bare_script_is_the_click(self):
        state = _state()
        self.assertTrue(click(state, {"kind": "button", "script": 'go to page "P3"\n'}))
        self.assertEqual(state.page.id, "P3")

    def test_an_empty_script_follows_the_item(self):
        state = _state()
        self.assertTrue(click(state, {"kind": "button", "script": "", "item": {"page": "p2"}}))
        self.assertEqual(state.page.id, "P2")

    def test_a_script_that_moves_wins_over_the_item(self):
        state = _state()
        button = {"script": 'go to page "P3"', "item": {"page": "P2"}}
        self.assertTrue(click(state, button))
        self.assertEqual(state.page.id, "P3")

    def test_a_script_that_stays_lets_the_item_run(self):
        state = _state()
        button = {"script": "n = 1", "item": {"page": "P2"}}
        self.assertTrue(click(state, button))
        self.assertEqual(state.page.id, "P2")
        self.assertEqual(state.variables["n"], 1)

    def test_a_next_label_with_no_page(self):
        state = _state()
        self.assertTrue(click(state, {"item": {"label": "Next"}}))
        self.assertEqual(state.page.id, "P2")

    def test_nothing_set_does_nothing(self):
        state = _state()
        self.assertFalse(click(state, {"kind": "button"}))
        self.assertEqual(state.page.id, "P1")


if __name__ == "__main__":
    unittest.main()
