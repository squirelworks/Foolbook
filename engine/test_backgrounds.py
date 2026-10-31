"""A background page is painted under every page that uses it."""

import tempfile
import unittest
from pathlib import Path

from engine.formats import pack
from engine.loader import load


def _book() -> dict:
    return {
        "id": "shared",
        "title": "Shared",
        "pages": [
            {"id": "Paper", "background": True, "shapes": [
                {"kind": "rect", "name": "band", "x": 0, "y": 0, "w": 640, "h": 40, "fill": "#071428"},
            ]},
            {"id": "P0", "uses": "Paper", "shapes": [
                {"kind": "text", "name": "hello", "x": 20, "y": 60, "text": "Hello"},
            ]},
            {"id": "P100", "uses": "paper", "shapes": []},
            {"id": "P200", "shapes": [
                {"kind": "rect", "name": "old", "x": 0, "y": 0, "w": 10, "h": 10, "layer": "background"},
            ]},
        ],
    }


def _open(data: dict):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "shared.fbk"
        path.write_bytes(pack(data, compress=False))
        return load(path)


class SharedBackground(unittest.TestCase):
    def test_a_background_is_not_a_page_you_read(self):
        book = _open(_book())
        self.assertEqual([p.id for p in book.pages], ["P0", "P100", "P200"])

    def test_the_background_is_painted_first(self):
        book = _open(_book())
        names = [s.get("name") for s in book.pages[0].shapes]
        self.assertEqual(names, ["band", "hello"])
        self.assertEqual(book.pages[0].shapes[0].get("layer"), "background")

    def test_every_page_that_uses_it_shows_the_same_shapes(self):
        book = _open(_book())
        self.assertIs(book.pages[0].shapes[0], book.pages[1].shapes[0])

    def test_a_page_with_a_layer_tag_still_paints(self):
        book = _open(_book())
        self.assertEqual([s.get("name") for s in book.pages[2].shapes], ["old"])

    def test_an_unknown_background_paints_only_the_page(self):
        data = _book()
        data["pages"][1]["uses"] = "Nowhere"
        book = _open(data)
        self.assertEqual([s.get("name") for s in book.pages[0].shapes], ["hello"])


if __name__ == "__main__":
    unittest.main()
