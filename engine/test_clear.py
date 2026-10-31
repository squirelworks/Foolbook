"""`clear` empties a field's text, a variable, or a chunk of one."""

from __future__ import annotations

import unittest

from engine.engine import RuntimeState, ScriptError, run_handler
from foolbook.model import Book, Page


class Clear(unittest.TestCase):
    def test_clear(self):
        page = Page(id="P1", shapes=[
            {"kind": "text", "name": "Response", "layer": "page", "text": "?"},
            {"kind": "text", "name": "Response 2", "layer": "page", "text": "?"},
        ])
        state = RuntimeState(book=Book(path="", title="b", pages=[page]))
        run_handler(state, 'clear text of field "response" of this page\n'
                           'i = 2\nclear text of field("response" && i) of this page\n'
                           'x = "abc"\nclear x\nlist = "a,b,c"\nn = 2\nclear item n of list')
        self.assertEqual((page.shapes[0]["text"], page.shapes[1]["text"]), ("", ""))
        self.assertEqual((state.variables["x"], state.variables["list"]), ("", "a,,c"))

    def test_clear_a_textline_of_a_field(self):
        page = Page(id="P1", shapes=[{"kind": "text", "name": "text", "layer": "page", "text": "one\r\ntwo\r\nthree"}])
        state = RuntimeState(book=Book(path="", title="b", pages=[page]))
        run_handler(state, 'n = 2\nclear textline n of text of field "text"')
        self.assertEqual(page.shapes[0]["text"], "one\r\n\r\nthree")

    def test_a_target_it_cannot_clear_fails(self):
        state = RuntimeState(book=Book(path="", title="b", pages=[Page(id="P1")]))
        with self.assertRaises(ScriptError):
            run_handler(state, 'clear selection of the moon')


if __name__ == "__main__":
    unittest.main()
