"""An editor group in an .fbk is drawn, clicked and hidden through its children."""

from __future__ import annotations

import unittest
from pathlib import Path

from engine.engine import run_handler, split_handlers
from engine.loader import _book_from_dict
from foolbook.model import RuntimeState


def _book():
    return {"pages": [{"id": "P0", "script": 'to handle enterPage\n  hide group "Choices"\nend\n', "shapes": [
        {"kind": "rect", "name": "paper", "x": 0, "y": 0, "w": 640, "h": 480},
        {"kind": "group", "name": "Choices", "children": [
            {"kind": "button", "name": "A", "x": 10, "y": 10, "w": 90, "h": 28},
            {"kind": "group", "name": "Inner", "children": [
                {"kind": "button", "name": "B", "x": 10, "y": 50, "w": 90, "h": 28, "item": {"page": "P1"}},
            ]},
        ]},
        {"kind": "text", "name": "after", "x": 0, "y": 400, "w": 100, "h": 20},
    ]}, {"id": "P1"}]}


class FbkGroupTests(unittest.TestCase):
    def test_the_children_are_on_the_page_in_order(self):
        page = _book_from_dict(Path("g.fbk"), _book()).pages[0]
        self.assertEqual([s["name"] for s in page.shapes], ["paper", "A", "B", "after"])
        self.assertEqual(page.shapes[2]["item"], {"page": "P1"})

    def test_children_carry_the_group_names_nearest_first(self):
        page = _book_from_dict(Path("g.fbk"), _book()).pages[0]
        self.assertEqual(page.shapes[1]["groups"], ["Choices"])
        self.assertEqual(page.shapes[2]["groups"], ["Inner", "Choices"])

    def test_the_stored_book_keeps_the_group(self):
        data = _book()
        _book_from_dict(Path("g.fbk"), data)
        self.assertEqual(data["pages"][0]["shapes"][1]["kind"], "group")
        self.assertNotIn("groups", data["pages"][0]["shapes"][1]["children"][0])

    def test_a_hidden_group_hides_its_children(self):
        data = _book()
        data["pages"][0]["shapes"][1]["visible"] = False
        page = _book_from_dict(Path("g.fbk"), data).pages[0]
        self.assertEqual([s.get("visible") for s in page.shapes[1:3]], [False, False])

    def test_hide_group_reaches_the_children(self):
        book = _book_from_dict(Path("g.fbk"), _book())
        page = book.pages[0]
        state = RuntimeState(book=book)
        run_handler(state, split_handlers(page.raw["script"])[0].source)
        self.assertEqual({s["name"]: s.get("visible", True) for s in page.shapes},
                         {"paper": True, "A": False, "B": False, "after": True})


if __name__ == "__main__":
    unittest.main()
