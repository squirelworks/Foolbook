"""`local int count` starts a handler's own variable blank."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Handler, Page


def _state() -> RuntimeState:
    return RuntimeState(book=Book(path="x", pages=[Page(id="P1")]))


class Locals(unittest.TestCase):
    def test_a_number_local_starts_at_zero(self):
        state = _state()
        run_handler(state, "local int count\nresult = count + 1")
        self.assertEqual(state.variables["result"], 1)

    def test_a_text_local_starts_empty(self):
        state = _state()
        state.variables["name"] = "left over"
        run_handler(state, "local string name\nresult = name")
        self.assertEqual(state.variables["result"], "")

    def test_a_local_array_starts_empty(self):
        state = _state()
        run_handler(state, "local int numbers[5]\nnumbers[2] = 4\nresult = numbers[1] + numbers[2]")
        self.assertEqual(state.variables["result"], 4)

    def test_several_names_in_one_line(self):
        state = _state()
        state.variables.update(a="x", b="y")
        run_handler(state, "local a, b\nresult = a & b")
        self.assertEqual(state.variables["result"], "")

    def test_a_called_handler_counts_from_zero_each_time(self):
        state = _state()
        state.book.handlers = [Handler(
            name="countUp",
            source="\n    local int count\n    count = count + 1\n    return count\nend",
        )]
        state.variables["count"] = 5
        run_handler(state, "a = countUp()\nb = countUp()")
        self.assertEqual((state.variables["a"], state.variables["b"]), (1, 1))
        self.assertEqual(state.variables["count"], 5)


if __name__ == "__main__":
    unittest.main()
