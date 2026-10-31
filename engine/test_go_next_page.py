"""go to next page and go to previous page move like the Next and Back buttons."""

from __future__ import annotations

import unittest

from engine.engine import follow, run_handler
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

    def test_next_uses_the_page_next_item_like_the_button(self):
        state = _state([{"label": "Next", "page": "P1"}])
        self.assertTrue(follow(state, run_handler(state, "go to next page")))
        self.assertEqual(state.page.id, "P1")


if __name__ == "__main__":
    unittest.main()
