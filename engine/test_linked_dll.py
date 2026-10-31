"""A function a script links from kernel32.dll answers from the INI beside the book."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page

LINK = """linkDLL32 "kernel32.dll"
    INT WritePrivateProfileStringA(STRING, STRING, STRING, STRING)
    INT GetPrivateProfileIntA(STRING, STRING, INT, STRING)
    INT GetPrivateProfileStringA(STRING, STRING, STRING, STRING, INT, STRING)
    LONG GetTickCount()
end linkDLL32
"""


class LinkedDll(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name)
        self.state = RuntimeState(book=Book(path=str(self.folder / "course.fbk"), pages=[Page(id="P1")]))

    def tearDown(self):
        self.tmp.cleanup()

    def test_with_no_ini_the_default_is_the_answer(self):
        run_handler(self.state, LINK + 'mode = GetPrivateProfileIntA("Lesson", "Lesson Mode", 2, "NIDAREC.INI")')
        self.assertEqual(self.state.variables["mode"], 2)

    def test_the_ini_beside_the_book_is_read(self):
        (self.folder / "nidarec.ini").write_text("[Lesson]\nLesson Mode=5\nOption1=abc\n")
        run_handler(self.state, LINK + 'mode = GetPrivateProfileIntA("Lesson", "Lesson Mode", 2, "NIDAREC.INI")\n'
                    'temp = "        "\nn = GetPrivateProfileStringA("Lesson", "Option1", "", temp, 8, "NIDAREC.INI")')
        self.assertEqual(self.state.variables["mode"], 5)
        self.assertEqual(self.state.variables["temp"], "abc")

    def test_a_write_is_read_back_in_the_same_session(self):
        run_handler(self.state, LINK + 'get WritePrivateProfileStringA("Lesson", "Window", "7", "NIDAREC.INI")\n'
                    'w = GetPrivateProfileIntA("Lesson", "Window", 0, "NIDAREC.INI")')
        self.assertEqual(self.state.variables["w"], 7)
        self.assertFalse((self.folder / "NIDAREC.INI").exists())

    def test_the_linked_dll_is_in_syslinkeddlls(self):
        run_handler(self.state, LINK + 'if "kernel32.dll" is not in sysLinkedDLLs then\nmissing = 1\nend if\nnames = sysLinkedDLLs')
        self.assertEqual(self.state.variables["names"], "kernel32.dll")

    def test_gettickcount_counts_milliseconds(self):
        from unittest import mock
        with mock.patch("engine.dlls.kernel32.time.monotonic", side_effect=[10.0, 12.5]):
            run_handler(self.state, LINK + "__quizStart = GetTickCount()\nelapsed = GetTickCount() - __quizStart")
        self.assertEqual(self.state.variables["elapsed"], 2500)

    def test_an_unlinked_function_is_not_answered(self):
        run_handler(self.state, 'mode = GetPrivateProfileIntA("Lesson", "Lesson Mode", 2, "NIDAREC.INI")')
        self.assertNotEqual(self.state.variables.get("mode"), 2)


if __name__ == "__main__":
    unittest.main()
