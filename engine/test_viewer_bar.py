"""The first viewer on a book says which buttons the reader's bar shows."""

import tempfile
import unittest
from pathlib import Path

from engine.formats import pack
from engine.loader import load
from engine.viewers import chrome, first_viewer, page_number, step


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


class ViewerBar(unittest.TestCase):
    def test_the_first_viewer_names_the_buttons(self):
        book = _open(_book([
            {"name": "Main", "buttons": ["next", "page"]},
            {"name": "Other", "buttons": ["previous"]},
        ]))
        self.assertEqual(first_viewer(book)["name"], "Main")
        self.assertEqual(chrome(first_viewer(book)), ["next", "page"])

    def test_no_viewer_shows_no_bar(self):
        book = _open(_book())
        self.assertIsNone(first_viewer(book))
        self.assertEqual(chrome(None), [])

    def test_an_unknown_button_is_left_out_and_order_is_fixed(self):
        self.assertEqual(chrome({"buttons": ["page", "zoom", "previous", "next", "next"]}), ["previous", "next", "page"])

    def test_previous_and_next_stop_at_the_ends(self):
        self.assertEqual(step(0, 3, -1), 0)
        self.assertEqual(step(0, 3, 1), 1)
        self.assertEqual(step(2, 3, 1), 2)

    def test_the_page_number_counts_from_one(self):
        self.assertEqual(page_number(1, 3), "2 of 3")


if __name__ == "__main__":
    unittest.main()
