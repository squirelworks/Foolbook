"""A book knows whether it came from ToolBook.

The NIDA guard runs when NIDA_BOOKS names a folder holding the book.
The books are not in this repository.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from engine.loader import _book_from_dict, load
from engine.origin import is_toolbook
from foolbook.model import Book, Page


class OriginTests(unittest.TestCase):
    def test_a_foolbook_file_is_foolbook(self):
        book = _book_from_dict(Path("mine.fbk"), {"pages": [{"id": "P1"}]})
        self.assertFalse(is_toolbook(book))

    def test_an_export_from_toolbook_is_toolbook(self):
        book = _book_from_dict(Path("course.fbk"), {"pages": [{"id": "P1", "settled": True}]})
        self.assertTrue(is_toolbook(book))

    def test_a_tbk_is_toolbook(self):
        self.assertTrue(is_toolbook(Book(path="course.tbk", pages=[Page(id="P1")])))

    def test_the_bundled_books_are_foolbook(self):
        root = Path(__file__).resolve().parents[1] / "_books"
        books = sorted(root.rglob("*.fbk"))
        self.assertTrue(books)
        for path in books:
            self.assertFalse(is_toolbook(load(path)), path.name)

    def test_93950101_is_toolbook(self):
        path = Path(os.environ.get("NIDA_BOOKS") or "/nonexistent") / "93950101.fbk"
        if not path.exists():
            raise unittest.SkipTest("93950101.fbk is not here; set NIDA_BOOKS")
        self.assertTrue(is_toolbook(load(path)))


if __name__ == "__main__":
    unittest.main()
