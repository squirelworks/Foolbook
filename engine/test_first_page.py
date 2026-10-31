"""A book can name its first page, and the reader opens there."""

import tempfile
import unittest
from pathlib import Path

from engine import formats
from engine.loader import load

PAGES = [{"id": "Cover"}, {"id": "Start"}, {"id": "End"}]


def _load(data: dict):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "b.fbk"
        path.write_bytes(formats.pack(data))
        return load(path)


class FirstPage(unittest.TestCase):
    def test_the_book_opens_at_its_first_page_id(self):
        book = _load({"id": "b", "title": "B", "author": "Ana", "firstPage": "Start", "pages": PAGES})
        self.assertEqual((book.author, book.first_page), ("Ana", "Start"))
        self.assertEqual(book.start(), 1)

    def test_without_one_or_with_a_missing_page_it_opens_at_the_first_page(self):
        self.assertEqual(_load({"id": "b", "pages": PAGES}).start(), 0)
        self.assertEqual(_load({"id": "b", "firstPage": "Gone", "pages": PAGES}).start(), 0)


if __name__ == "__main__":
    unittest.main()
