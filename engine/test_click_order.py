"""A button click: its script, then the page's buttonClick, then its item.

The NIDA guards run when NIDA_BOOKS names a folder holding those books.
The books are not in this repository.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from engine.engine import _TO_HANDLE, click, click_script
from engine.loader import load
from foolbook.model import Book, Handler, Page, RuntimeState


def _state():
    pages = [Page(id="P1"), Page(id="P2"), Page(id="P3")]
    return RuntimeState(book=Book(path="book.fbk", pages=pages))


def _nida(name, page_id):
    path = Path(os.environ.get("NIDA_BOOKS") or "/nonexistent") / name
    if not path.exists():
        raise unittest.SkipTest(f"{name} is not here; set NIDA_BOOKS")
    book = load(path)
    state = RuntimeState(book=book)
    state.index = [p.id for p in book.pages].index(page_id)
    return state


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

    def test_a_page_buttonclick_that_moves_wins_over_the_item(self):
        state = _state()
        state.page.handlers = [Handler(name="buttonClick", source='go to page "P3"')]
        self.assertTrue(click(state, {"item": {"page": "P2"}}))
        self.assertEqual(state.page.id, "P3")

    def test_a_toolbook_book_does_not_read_a_bare_script_as_the_click(self):
        pages = [Page(id="P1"), Page(id="P2"), Page(id="P3")]
        state = RuntimeState(book=Book(path="course.tbk", pages=pages))
        self.assertFalse(click(state, {"kind": "button", "script": 'go to page "P3"\n'}))
        self.assertEqual(state.page.id, "P1")

    def test_nothing_set_does_nothing(self):
        state = _state()
        self.assertFalse(click(state, {"kind": "button"}))
        self.assertEqual(state.page.id, "P1")


class NidaClickTests(unittest.TestCase):
    """Real books land where the window lands on main."""

    def test_93951204_p1125_next_runs_its_own_handler(self):
        state = _nida("93951204.fbk", "P1125")
        button = next(s for s in state.page.shapes if s.get("name") == "Next")
        self.assertTrue(click(state, button))
        self.assertEqual(state.page.id, "P1160")

    def test_9395T903_p16015_item_button_after_the_page_buttonclick(self):
        state = _nida("9395T903.fbk", "P16015")
        item = next(i for i in state.page.items if i.get("label") == "p16020")
        self.assertTrue(click(state, {"kind": "button", "name": "p16020", "text": "p16020", "item": item}))
        self.assertEqual(state.page.id, "P16020")

    def test_93950101_p1910_next_with_its_page(self):
        state = _nida("93950101.fbk", "P1910")
        button = next(s for s in state.page.shapes if s.get("name") == "Next")
        self.assertTrue(click(state, button))
        self.assertEqual(state.page.id, "P1001")

    def test_93950101_has_no_bare_button_script(self):
        state = _nida("93950101.fbk", "P1")
        for page in state.book.pages:
            for shape in page.shapes:
                own = shape.get("script") or ""
                if "buttonclick" in own.lower() or _TO_HANDLE.search(own):
                    continue
                self.assertEqual(click_script(shape, state.book), shape.get("group_script") or "", page.id)


if __name__ == "__main__":
    unittest.main()
