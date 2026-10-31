"""OpenScript arrays: `system int a[10]`, `a[i] = v` and `a[i]`."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


def _state() -> RuntimeState:
    return RuntimeState(book=Book(path="x", pages=[Page(id="P1")]))


class Arrays(unittest.TestCase):
    def test_an_element_is_set_and_read_by_its_index(self):
        state = _state()
        run_handler(state, "system int flags[10]\ni = 3\nflags[i] = 2\nseen = flags[3]")
        self.assertEqual(state.variables["seen"], 2)

    def test_an_element_never_set_is_blank_for_its_type(self):
        state = _state()
        run_handler(state, "system int flags[10]\nsystem string names[]\na = flags[4]\nb = names[1]")
        self.assertEqual(state.variables["a"], 0)
        self.assertEqual(state.variables["b"], "")

    def test_an_element_is_compared(self):
        state = _state()
        run_handler(state, 'system string pages[]\npages[1] = "P10301"\nif pages[1] = "P10301" then\nhit = 1\nend if')
        self.assertEqual(state.variables.get("hit"), 1)

    def test_a_system_array_keeps_its_elements_after_a_called_handler(self):
        from foolbook.model import Handler
        state = _state()
        state.book.handlers = [Handler(
            name="setFlag",
            source=" index\n    system int __flags[10]\n    __flags[index] = 2\n    return 0\nend",
        )]
        run_handler(state, "get setFlag(3)\nsystem int __flags[10]\nseen = __flags[3]")
        self.assertEqual(state.variables["seen"], 2)


if __name__ == "__main__":
    unittest.main()
