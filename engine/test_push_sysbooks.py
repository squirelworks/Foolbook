"""`push "x.sbk" onto sysBooks` opens that system book from beside the book."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine.engine import RuntimeState, run_handler
from engine.formats import FSK, pack
from foolbook.model import Book, Page


def _system_book(folder: Path, name: str, script: str) -> Path:
    path = folder / name
    path.write_bytes(pack({"title": path.stem, "pages": [{"id": "P1"}], "script": script}, FSK))
    return path


class PushOntoSysBooks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name)
        course = self.folder / "course.fbk"
        self.state = RuntimeState(book=Book(path=str(course), title="course", pages=[Page(id="P1")]))

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_pushed_system_book_is_opened_with_its_handlers(self):
        _system_book(self.folder, "shared.fsk", "to get greeting\n\treturn \"hello\"\nend\n")
        run_handler(self.state, 'push "shared.sbk" onto sysBooks')
        self.assertEqual(len(self.state.sysbooks), 1)
        name, book = self.state.sysbooks[0]
        self.assertEqual(name, "shared.sbk")
        self.assertIsNotNone(book)
        self.assertEqual([h.name for h in book.handlers], ["greeting"])

    def test_the_last_push_is_first_in_sysbooks(self):
        _system_book(self.folder, "base.fsk", "to get a\nend\n")
        _system_book(self.folder, "test.fsk", "to get b\nend\n")
        run_handler(self.state, 'push "base.sbk" onto sysBooks\npush "test.sbk" onto sysBooks\nnames = sysBooks')
        self.assertEqual(self.state.variables["names"], "test.sbk,base.sbk")

    def test_a_missing_system_book_keeps_its_name(self):
        run_handler(self.state, 'push "nowhere.sbk" onto sysBooks')
        self.assertEqual(self.state.sysbooks, [("nowhere.sbk", None)])


if __name__ == "__main__":
    unittest.main()
