"""`get f()` puts what f gives in `it`, so `return it` passes it on."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Handler, Page


def _state():
    handlers = [
        Handler(name="inner", source="to get inner\n\treturn 7\nend"),
        Handler(name="outer", source="to get outer\n\tget inner()\n\treturn it\nend"),
    ]
    return RuntimeState(book=Book(path="", title="b", pages=[Page(id="P1")], handlers=handlers))


class GetIt(unittest.TestCase):
    def test_return_it_passes_the_value_on(self):
        state = _state()
        run_handler(state, "x = outer()")
        self.assertEqual(state.variables["x"], 7)

    def test_get_an_expression(self):
        state = _state()
        run_handler(state, "get 2 + 3\ny = it")
        self.assertEqual(state.variables["y"], 5)


if __name__ == "__main__":
    unittest.main()
