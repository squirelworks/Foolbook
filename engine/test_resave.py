"""Opening and saving a book ten times writes the same bytes."""

import base64
import tempfile
import unittest
from pathlib import Path

from engine.formats import load, save_book

_PICTURE = base64.b64encode(b"\x89PNG" + bytes(range(256)) * 2).decode("ascii")


def _book() -> dict:
    return {"id": "again", "title": "Again", "pages": [
        {"id": "P0", "text": ["One"], "shapes": [
            {"kind": "image", "name": "a", "x": 1, "y": 2, "w": 3, "h": 4, "data": _PICTURE},
            {"kind": "image", "name": "b", "x": 5, "y": 6, "w": 3, "h": 4, "data": _PICTURE},
            {"kind": "button", "name": "Next", "text": "Next", "item": {"page": "P100"}},
        ]},
        {"id": "P100", "text": ["Two"], "shapes": []},
    ]}


class Resave(unittest.TestCase):
    def _ten(self, compress: bool):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "again.fbk"
            save_book(path, _book(), compress=compress)
            first, first_dict = path.read_bytes(), load(path)
            for _ in range(10):
                save_book(path, load(path), compress=compress)
                self.assertEqual(load(path), first_dict)
                self.assertEqual(path.read_bytes(), first)

    def test_uncompressed(self):
        self._ten(False)

    def test_compressed(self):
        self._ten(True)


if __name__ == "__main__":
    unittest.main()
