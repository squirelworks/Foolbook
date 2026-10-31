"""A DLL shim beside the book answers a link. The copy in engine/dlls/ does not."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page

LINK = """linkDLL32 "nc81rec.dll"
    INT RecCheckStatus(STRING, STRING)
end linkDLL32
"""

SHIM = """
def rec_check(state, args, refs):
    return 7

FUNCTIONS = {"reccheckstatus": rec_check}
"""

KERNEL = """
def tick(state, args, refs):
    return 99

FUNCTIONS = {"gettickcount": tick}
"""


class DllBeside(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.course = self.root / "courses"
        self.course.mkdir()
        self.state = RuntimeState(book=Book(path=str(self.course / "course.fbk"), pages=[Page(id="P1")]))

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_shim_one_folder_up_answers_the_call(self):
        folder = self.root / "dlls"
        folder.mkdir()
        (folder / "nc81rec.py").write_text(SHIM)
        run_handler(self.state, LINK + 'status = RecCheckStatus("id", "lesson")')
        self.assertEqual(self.state.variables["status"], 7)

    def test_a_shim_beside_the_book_beats_the_one_in_the_reader(self):
        folder = self.course / "dlls"
        folder.mkdir()
        (folder / "kernel32.py").write_text(KERNEL)
        run_handler(self.state, 'linkDLL32 "kernel32.dll"\n    INT GetTickCount()\nend linkDLL32\n'
                    'n = GetTickCount()')
        self.assertEqual(self.state.variables["n"], 99)


if __name__ == "__main__":
    unittest.main()
