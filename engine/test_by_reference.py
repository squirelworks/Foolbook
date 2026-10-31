"""A handler header with `int a[] by reference` binds the caller's array, and writes go back."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Handler, Page


BOOK_SCRIPT = """
to get fill int numbers[] by reference, int count
    step i from 1 to count
        numbers[i] = i * 10
    end step
    return count
end

to get bump int n by reference
    n = n + 1
    return 0
end

to get keepOwn int numbers[]
    numbers[1] = 99
    return 0
end
"""


def _state():
    handlers = []
    for chunk in BOOK_SCRIPT.strip().split("\n\n"):
        name = chunk.split()[2]
        handlers.append(Handler(name=name, source=chunk))
    book = Book(path="", title="b", pages=[Page(id="P1")], handlers=handlers)
    return RuntimeState(book=book)


class ByReference(unittest.TestCase):
    def test_an_array_by_reference_is_filled_for_the_caller(self):
        state = _state()
        run_handler(state, "local int numbers[]\nn = fill(numbers, 3)\nfirst = numbers[1]\nthird = numbers[3]")
        self.assertEqual(state.variables["n"], 3)
        self.assertEqual(state.variables["first"], 10)
        self.assertEqual(state.variables["third"], 30)

    def test_a_number_by_reference_comes_back_changed(self):
        state = _state()
        run_handler(state, "x = 4\nget bump(x)")
        self.assertEqual(state.variables["x"], 5)

    def test_an_array_not_by_reference_is_a_copy(self):
        state = _state()
        run_handler(state, "local int numbers[]\nnumbers[1] = 1\nget keepOwn(numbers)\nfirst = numbers[1]")
        self.assertEqual(state.variables["first"], 1)


if __name__ == "__main__":
    unittest.main()
