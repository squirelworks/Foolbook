"""In a ToolBook file, go to next page and go to previous page are the pages beside this one in book order.

The NIDA guards run when NIDA_BOOKS names a folder holding the book.
The books are not in this repository.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from engine.engine import click, follow, run_handler
from engine.loader import load
from foolbook.model import Book, Page, RuntimeState


_TMP = tempfile.TemporaryDirectory()


def _toolbook_file():
    """A file whose first bytes say ToolBook. The pages come from the test."""
    from toolbook.format import _AT, _BOOK
    path = Path(_TMP.name) / "course.tbk"
    if not path.exists():
        path.write_bytes(b"\0" * _AT + _BOOK + b"\0" * 64)
    return str(path)


def _state(items=None, path=None):
    pages = [Page(id="P1"), Page(id="P2", items=items or []), Page(id="P3")]
    return RuntimeState(book=Book(path=path or _toolbook_file(), pages=pages), index=1)


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

    def test_a_foolbook_book_does_not_read_it(self):
        state = _state(path="b.fbk")
        self.assertFalse(follow(state, run_handler(state, "go to next page")))
        self.assertEqual(state.page.id, "P2")


def _nida(page_id):
    path = Path(os.environ.get("NIDA_BOOKS") or "/nonexistent") / "9395T903.fbk"
    if not path.exists():
        raise unittest.SkipTest("9395T903.fbk is not here; set NIDA_BOOKS")
    book = load(path)
    state = RuntimeState(book=book)
    state.index = [p.id for p in book.pages].index(page_id)
    return state


class NidaGoNextPageTests(unittest.TestCase):
    def test_converted_9395T903_p16201_is_foolbook_and_stays(self):
        """The converted course is an FBK1 file, so it does not get the ToolBook reading. Main stays too."""
        state = _nida("P16201")
        overlay = next(s for s in state.page.shapes if s.get("name") == "Overlay")
        self.assertFalse(click(state, overlay))
        self.assertEqual(state.page.id, "P16201")


if __name__ == "__main__":
    unittest.main()
