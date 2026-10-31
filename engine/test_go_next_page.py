"""go to next page and go to previous page are the pages beside this one in book order.

The NIDA guards run when NIDA_BOOKS names a folder holding the book.
The books are not in this repository.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from engine.engine import click, follow, run_handler
from engine.loader import load
from foolbook.model import Book, Page, RuntimeState


def _state(items=None):
    pages = [Page(id="P1"), Page(id="P2", items=items or []), Page(id="P3")]
    return RuntimeState(book=Book(path="b.fbk", pages=pages), index=1)


class GoNextPageTests(unittest.TestCase):
    def test_go_to_next_page(self):
        state = _state()
        self.assertTrue(follow(state, run_handler(state, "go to next page")))
        self.assertEqual(state.page.id, "P3")

    def test_go_to_previous_page(self):
        state = _state()
        self.assertTrue(follow(state, run_handler(state, "Go To Previous Page")))
        self.assertEqual(state.page.id, "P1")

    def test_go_to_prev_page(self):
        state = _state()
        self.assertTrue(follow(state, run_handler(state, "go to prev page")))
        self.assertEqual(state.page.id, "P1")

    def test_of_this_book(self):
        state = _state()
        self.assertTrue(follow(state, run_handler(state, "go to previous page of this book")))
        self.assertEqual(state.page.id, "P1")
        self.assertTrue(follow(state, run_handler(state, "go to next page of this book")))
        self.assertEqual(state.page.id, "P2")

    def test_next_page_is_book_order_not_the_next_item(self):
        state = _state([{"label": "Next", "page": "P1"}])
        self.assertTrue(follow(state, run_handler(state, "go to next page")))
        self.assertEqual(state.page.id, "P3")

    def test_past_the_last_page_stays(self):
        state = _state()
        state.index = 2
        self.assertFalse(follow(state, run_handler(state, "go to next page")))
        self.assertEqual(state.page.id, "P3")


def _nida(page_id):
    path = Path(os.environ.get("NIDA_BOOKS") or "/nonexistent") / "9395T903.fbk"
    if not path.exists():
        raise unittest.SkipTest("9395T903.fbk is not here; set NIDA_BOOKS")
    book = load(path)
    state = RuntimeState(book=book)
    state.index = [p.id for p in book.pages].index(page_id)
    return state


class NidaGoNextPageTests(unittest.TestCase):
    def test_9395T903_p16201_a_click_on_the_page_goes_back(self):
        state = _nida("P16201")
        overlay = next(s for s in state.page.shapes if s.get("name") == "Overlay")
        self.assertTrue(click(state, overlay))
        self.assertEqual(state.page.id, "P16200")

    def test_9395T903_p15030_next_and_back(self):
        state = _nida("P15030")
        nxt = next(s for s in state.page.shapes if s.get("name") == "Next")
        self.assertTrue(click(state, nxt))
        self.assertEqual(state.page.id, "P15040")
        back = next(s for s in state.page.shapes if s.get("name") == "Back")
        self.assertTrue(click(state, back))
        self.assertEqual(state.page.id, "P15030")


if __name__ == "__main__":
    unittest.main()
