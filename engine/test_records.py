"""A page of records: its fields show one row, and two buttons step through the rows."""

from __future__ import annotations

import unittest

from engine import records
from engine.engine import enter_page
from foolbook.model import Book, Page, RuntimeState


def _page(at=0):
    shapes = [
        {"kind": "text", "name": "Name", "text": "", "x": 10, "y": 10, "w": 120, "h": 20},
        {"kind": "text", "name": "Town", "text": "", "x": 10, "y": 40, "w": 120, "h": 20},
        {"kind": "button", "name": "Next", "text": "Next", "item": {"record": "next"}},
    ]
    raw = {"records": {"fields": ["Name", "Town"], "rows": [["Ada", "Leeds"], ["Ben", "Bath"], ["Cy", "Ely"]], "at": at}}
    return Page(id="P0", shapes=shapes, raw=raw)


def _text(page, name):
    return next(s["text"] for s in page.shapes if s["name"] == name)


class Records(unittest.TestCase):
    def test_the_fields_show_the_current_row(self):
        page = _page(at=1)
        records.fill(page)
        self.assertEqual((_text(page, "Name"), _text(page, "Town")), ("Ben", "Bath"))

    def test_next_and_previous_step_one_row(self):
        page = _page()
        self.assertTrue(records.step(page, "next"))
        self.assertEqual(_text(page, "Name"), "Ben")
        self.assertTrue(records.step(page, "previous"))
        self.assertEqual(_text(page, "Name"), "Ada")

    def test_the_first_and_last_rows_do_not_wrap(self):
        page = _page()
        self.assertFalse(records.step(page, "previous"))
        page.raw["records"]["at"] = 2
        self.assertFalse(records.step(page, "next"))
        self.assertEqual(page.raw["records"]["at"], 2)

    def test_a_short_row_leaves_the_missing_field_empty(self):
        page = _page()
        page.raw["records"]["rows"] = [["Dee"]]
        records.fill(page)
        self.assertEqual((_text(page, "Name"), _text(page, "Town")), ("Dee", ""))

    def test_a_page_without_records_is_left_alone(self):
        page = Page(id="P1", shapes=[{"kind": "text", "name": "Name", "text": "kept"}])
        records.fill(page)
        self.assertFalse(records.step(page, "next"))
        self.assertEqual(page.shapes[0]["text"], "kept")

    def test_entering_the_page_fills_the_fields(self):
        page = _page()
        state = RuntimeState(book=Book(path="r.fbk", pages=[page]))
        enter_page(state)
        self.assertEqual(_text(page, "Name"), "Ada")


if __name__ == "__main__":
    unittest.main()
