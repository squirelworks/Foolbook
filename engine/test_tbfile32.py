"""fileExists32 linked from tbfile32.dll looks beside the book."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page

LINK = """linkDLL "tbfile32.dll"
    INT fileExists32(STRING)
end linkDLL
"""


class FileExists32(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name)
        self.state = RuntimeState(book=Book(path=str(self.folder / "course.fbk"), pages=[Page(id="P1")]))

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_file_beside_the_book_exists_whatever_its_case(self):
        (self.folder / "Logo81.TBK").write_bytes(b"x")
        run_handler(self.state, LINK + 'if fileExists32("logo81.tbk") = 1 then\nfound = "yes"\nend if\nother = fileExists32("mrj81.tbk")')
        self.assertEqual(self.state.variables.get("found"), "yes")
        self.assertEqual(self.state.variables.get("other"), 0)


if __name__ == "__main__":
    unittest.main()
