"""A book is ToolBook or Foolbook by what its file is, not by its name."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine.formats import pack
from engine.origin import is_toolbook
from foolbook.model import Book, Page
from toolbook.format import _AT, _BOOK


def _book(path):
    return Book(path=str(path), pages=[Page(id="P1")])


class OriginTests(unittest.TestCase):
    def test_an_fbk_envelope_is_foolbook_even_named_tbk(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "course.tbk"
            path.write_bytes(pack({"pages": [{"id": "P1"}]}))
            self.assertFalse(is_toolbook(_book(path)))

    def test_a_toolbook_file_is_toolbook_even_named_fbk(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "course.fbk"
            path.write_bytes(b"\0" * _AT + _BOOK + b"\0" * 64)
            self.assertTrue(is_toolbook(_book(path)))

    def test_a_book_with_no_file_is_foolbook(self):
        self.assertFalse(is_toolbook(_book("")))
        self.assertFalse(is_toolbook(Book(path="nowhere.tbk")))

    def test_the_bundled_books_are_foolbook(self):
        from engine.loader import load
        root = Path(__file__).resolve().parents[1] / "_books"
        books = sorted(root.rglob("*.fbk"))
        self.assertTrue(books)
        for path in books:
            self.assertFalse(is_toolbook(load(path)), path.name)


if __name__ == "__main__":
    unittest.main()
