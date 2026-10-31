"""SendMessageA and PostMessageA linked from user32.dll reach no window and answer 0."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page

LINK = """linkDLL32 "user32.dll"
    LONG SendMessageA(WORD, WORD, WORD, LONG)
    LONG PostMessageA(WORD, WORD, WORD, LONG)
end linkDLL32
"""


class User32Messages(unittest.TestCase):
    def test_a_message_to_another_window_answers_zero(self):
        state = RuntimeState(book=Book(path="course.fbk", pages=[Page(id="P1")]))
        run_handler(state, LINK + "s = SendMessageA(77, 1488, 1, 2)\np = PostMessageA(77, 1488, 1, 2)")
        self.assertEqual(state.variables.get("s"), 0)
        self.assertEqual(state.variables.get("p"), 0)


if __name__ == "__main__":
    unittest.main()
