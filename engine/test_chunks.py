"""Chunks of text: word, item, char and textline N of a value."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


def _value(source: str, **variables):
    state = RuntimeState(book=Book(path="x", pages=[Page(id="P1")]))
    state.variables.update(variables)
    run_handler(state, f"result = {source}")
    return state.variables["result"]


class Chunks(unittest.TestCase):
    def test_word_n_of_a_variable(self):
        self.assertEqual(_value("word 2 of cmd", cmd="tb.exe /Quester 7 9"), "/Quester")

    def test_item_n_with_an_index_expression(self):
        self.assertEqual(_value("item i + 1 of pool", pool="110,111,112", i=1), "111")

    def test_item_from_an_array_element_index(self):
        state = RuntimeState(book=Book(path="x", pages=[Page(id="P1")]))
        state.variables["pool"] = "110 111 112"
        run_handler(state, "system int numbers[]\nnumbers[1] = 3\nresult = word numbers[1] of pool")
        self.assertEqual(state.variables["result"], "112")

    def test_a_range_of_chars(self):
        self.assertEqual(_value("chars 2 to 4 of name", name="P10301"), "103")

    def test_textline_of_a_value(self):
        self.assertEqual(_value("textline 2 of body", body="one\r\ntwo\r\nthree"), "two")

    def test_past_the_end_is_empty(self):
        self.assertEqual(_value("item 9 of pool", pool="a,b"), "")

    def test_a_chunk_in_a_comparison(self):
        state = RuntimeState(book=Book(path="x", pages=[Page(id="P1")]))
        state.variables["cmd"] = "tb.exe /Quester"
        run_handler(state, 'if word 2 of cmd = "/Quester" then\nhit = 1\nend if')
        self.assertEqual(state.variables.get("hit"), 1)


if __name__ == "__main__":
    unittest.main()
