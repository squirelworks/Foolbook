"""An editor group in an .fbk keeps its children on the page, clickable and in paint order."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

from engine.loader import _book_from_dict
from engine.place import click_target


def _book():
    return {"pages": [{"id": "P0", "shapes": [
        {"kind": "rect", "name": "paper", "x": 0, "y": 0, "w": 640, "h": 480},
        {"kind": "group", "name": "Choices", "children": [
            {"kind": "button", "name": "A", "x": 10, "y": 10, "w": 90, "h": 28, "item": {"page": "P1"}},
            {"kind": "group", "name": "Inner", "children": [
                {"kind": "button", "name": "B", "x": 10, "y": 50, "w": 90, "h": 28, "item": {"page": "P1"}},
            ]},
        ]},
        {"kind": "text", "name": "after", "x": 0, "y": 400, "w": 100, "h": 20},
    ]}, {"id": "P1"}]}


class FbkGroupTests(unittest.TestCase):
    def test_the_children_take_the_group_place_in_paint_order(self):
        page = _book_from_dict(Path("g.fbk"), _book()).pages[0]
        self.assertEqual([s["name"] for s in page.shapes], ["paper", "A", "B", "after"])

    def test_a_click_on_a_child_reaches_the_child(self):
        page = _book_from_dict(Path("g.fbk"), _book()).pages[0]
        self.assertEqual(click_target(page.shapes, 20, 20)["name"], "A")
        self.assertEqual(click_target(page.shapes, 20, 60)["name"], "B")

    def test_the_stored_book_keeps_the_group(self):
        data = _book()
        _book_from_dict(Path("g.fbk"), data)
        self.assertEqual(data, _book())


class ToolBookGroupGuardTests(unittest.TestCase):
    """A ToolBook export names its groups in ``groups`` and has no ``group`` shape."""

    def test_a_hidden_toolbook_group_page_is_passed_through_unchanged(self):
        members = [{"kind": "rect", "name": f"m{i}", "x": i, "y": 0, "w": 4, "h": 4,
                    "visible": False, "groups": ["Feedback"]} for i in range(315)]
        data = {"pages": [{"id": "P30020", "shapes": members}]}
        page = _book_from_dict(Path("export.fbk"), copy.deepcopy(data)).pages[0]
        self.assertEqual(page.shapes, data["pages"][0]["shapes"])


if __name__ == "__main__":
    unittest.main()
