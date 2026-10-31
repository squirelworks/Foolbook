"""A book can carry a menu bar, and the loader keeps it."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine import bookmenu, formats
from engine.loader import load
from foolbook.model import Book

MENUBAR = [
    {"label": "Go", "items": [
        {"label": "Contents", "page": "P0"},
        {"label": "Glossary", "script": 'to handle buttonClick\n  go to page "P2"\nend'},
        {"label": ""},
    ]},
    {"label": "", "items": [{"label": "Lost", "page": "P1"}]},
    {"label": "Empty", "items": []},
]


class Menus(unittest.TestCase):
    def test_the_bar_keeps_named_menus_and_items_with_somewhere_to_go(self):
        bar = bookmenu.menus(Book(path="x", menubar=MENUBAR))
        self.assertEqual([label for label, _items in bar], ["Go"])
        self.assertEqual([item["label"] for item in bar[0][1]], ["Contents", "Glossary"])

    def test_a_book_without_a_bar_has_none(self):
        self.assertEqual(bookmenu.menus(Book(path="x")), [])

    def test_the_loader_keeps_the_bar(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m.fbk"
            path.write_bytes(formats.pack({"id": "m", "title": "M", "menubar": MENUBAR, "pages": [{"id": "P0"}]}))
            self.assertEqual(load(path).menubar, MENUBAR)


if __name__ == "__main__":
    unittest.main()
