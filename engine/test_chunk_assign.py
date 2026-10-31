"""`char i of pool = " "` changes that chunk of the variable."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


def _run(script):
    state = RuntimeState(book=Book(path="", title="b", pages=[Page(id="P1")]))
    run_handler(state, script)
    return state.variables


class ChunkAssign(unittest.TestCase):
    def test_a_char_is_replaced(self):
        found = _run('pool = "1,2,3"\nstep i from 1 to 5\nif char i of pool = "," then\nchar i of pool = " "\nend if\nend step')
        self.assertEqual(found["pool"], "1 2 3")

    def test_an_item_and_a_word_are_replaced(self):
        found = _run('list = "a,b,c"\nitem 2 of list = "x"\nwords = "one two three"\nword 3 of words = "four"')
        self.assertEqual((found["list"], found["words"]), ("a,x,c", "one two four"))

    def test_an_item_past_the_end_pads_the_list(self):
        found = _run('list = "a"\nitem 3 of list = "c"')
        self.assertEqual(found["list"], "a,,c")


if __name__ == "__main__":
    unittest.main()
