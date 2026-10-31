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

    def test_a_saved_last_page_wins_over_the_first_page_id(self):
        book = _load({"id": "b", "firstPage": "Start", "pages": PAGES})
        self.assertEqual(book.start("End"), 2)
        self.assertEqual(book.start("Gone"), 1)


class ToolBookBook(unittest.TestCase):
    """A .tbk book never has a first page id: the .tbk loader does not read one.
    Synthetic loader-shaped Book; NIDA books are not in this environment."""

    def _tbk(self):
        from foolbook.model import Book, Page
        return Book(path="course.tbk", pages=[Page(id="P1000"), Page(id="P1010"), Page(id="P1020")])

    def test_it_opens_on_page_zero(self):
        book = self._tbk()
        self.assertEqual(book.first_page, "")
        self.assertEqual(book.start(), 0)

    def test_a_saved_last_page_still_wins(self):
        self.assertEqual(self._tbk().start("P1020"), 2)


if __name__ == "__main__":
    unittest.main()
