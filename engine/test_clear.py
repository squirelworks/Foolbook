"""`clear` empties a field's text or a variable, and takes a chunk out of one."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, run_handler
from foolbook.model import Book, Page


def _state(*shapes):
    return RuntimeState(book=Book(path="", title="b", pages=[Page(id="P1", shapes=list(shapes))]))


class Clear(unittest.TestCase):
    def test_setup_fillin_fields(self):
        page_shapes = [
            {"kind": "text", "name": "Response", "layer": "page", "text": "?"},
            {"kind": "text", "name": "Response 2", "layer": "page", "text": "?"},
        ]
        state = _state(*page_shapes)
        run_handler(state, 'clear text of field "response" of this page\n'
                           'i = 2\nclear text of field("response" && i) of this page\nx = "abc"\nclear x')
        self.assertEqual((page_shapes[0]["text"], page_shapes[1]["text"], state.variables["x"]), ("", "", ""))

    def test_a_chunk_is_taken_out_with_its_delimiter(self):
        state = _state()
        run_handler(state, '__pageList = "a,b,c,d"\ni = 4\nclear items 1 to i - 2 of __pageList\n'
                           'data = "one two"\nclear word 1 of data\nlist = "a,b,c"\nn = 2\nclear item n of list')
        found = state.variables
        self.assertEqual((found["__pageList"], found["data"], found["list"]), ("c,d", "two", "a,c"))

    def test_a_char_of_an_array_element(self):
        state = _state()
        run_handler(state, '__menuOption[1] = "/SO"\nclear char 1 of __menuOption[1]\nafter = 1')
        self.assertEqual(state.variables["__menuOption"][1], "SO")
        self.assertEqual(state.variables["after"], 1)

    def test_a_textline_of_a_field(self):
        shape = {"kind": "text", "name": "text", "layer": "page", "text": "one\r\ntwo\r\nthree"}
        state = _state(shape)
        run_handler(state, 'n = 2\nclear textline n of text of field "text"')
        self.assertEqual(shape["text"], "one\r\nthree")

    def test_a_target_it_cannot_clear_is_noted_and_the_handler_goes_on(self):
        state = _state()
        actions = run_handler(state, 'clear selection of the moon\nafter = 1')
        self.assertEqual(state.variables["after"], 1)
        self.assertIn("cannot clear: clear selection of the moon", [a.get("text") for a in actions or []])


if __name__ == "__main__":
    unittest.main()
