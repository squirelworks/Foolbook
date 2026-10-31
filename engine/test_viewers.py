"""A book's `viewers` records are kept by the loader, in file order."""

import tempfile
import unittest
from pathlib import Path

from engine.formats import pack
from engine.loader import load


def _open(data: dict):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "v.fbk"
        path.write_bytes(pack(data, compress=False))
        return load(path)


def _book(viewers=None) -> dict:
    data = {"id": "v", "title": "V", "pages": [{"id": "P0"}, {"id": "P100"}, {"id": "P200"}]}
    if viewers is not None:
        data["viewers"] = viewers
    return data


class Viewers(unittest.TestCase):
    def test_the_viewers_are_kept_in_order(self):
        book = _open(_book([
            {"name": "Main", "size": [640, 480], "buttons": ["next", "page"]},
            {"name": "Other", "buttons": ["previous"]},
        ]))
        self.assertEqual([v["name"] for v in book.viewers], ["Main", "Other"])
        self.assertEqual(book.viewers[0]["size"], [640, 480])
        self.assertEqual(book.viewers[0]["buttons"], ["next", "page"])

    def test_a_book_with_no_viewers_has_none(self):
        self.assertEqual(_open(_book()).viewers, [])

    def test_a_record_that_is_not_a_dict_is_left_out(self):
        book = _open(_book(["Main", {"name": "Real"}, None]))
        self.assertEqual(book.viewers, [{"name": "Real"}])


if __name__ == "__main__":
    unittest.main()
