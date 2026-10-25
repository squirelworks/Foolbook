"""A page's enterPage clears its answer fields at reader level, after `forward`."""

from __future__ import annotations

import unittest

from engine import fillin
from engine.engine import enter_page, run_handler, run_page_handlers, split_handlers
from foolbook.model import Book, Page, RuntimeState

PAGE_SCRIPT = """to handle enterpage
  system logical tryagain
  if isobject(field "page#" of parent of this page) then
    set text of field "page#" of parent of this page to name of this page
  end if
  forward
  get SetupFillInFields ()
end
"""

BACKGROUND_SCRIPT = """to handle enterPage
  get clearPagelist()
  get addToPageList()
  forward
end
"""


def _text(name, text="?"):
    return {"kind": "text", "name": name, "text": text, "x": 0, "y": 0, "w": 40, "h": 20, "outline": "#00ffff"}


def _page(shapes):
    handlers = split_handlers(PAGE_SCRIPT) + split_handlers(BACKGROUND_SCRIPT)
    return Page(id="P1", shapes=shapes, handlers=handlers)


def _state(shapes, level="reader"):
    state = RuntimeState(book=Book(path="x", pages=[_page(shapes)]))
    state.variables["sysLevel"] = level
    return state


class ClearOnEnter(unittest.TestCase):
    def test_reader_level_clears_every_answer_field(self):
        shapes = [_text("Response"), _text("Response 1"), _text("response 25"), _text("Text", "What is 2 + 5?")]
        state = _state(shapes)
        enter_page(state)
        self.assertEqual([s["text"] for s in shapes[:3]], ["", "", ""])
        self.assertEqual(shapes[3]["text"], "What is 2 + 5?")

    def test_author_level_writes_the_placeholder(self):
        shapes = [_text("Response", "7")]
        state = _state(shapes, level="author")
        enter_page(state)
        self.assertEqual(shapes[0]["text"], "?")

    def test_a_typed_answer_is_gone_when_the_page_is_entered_again(self):
        shapes = [_text("Response", "12")]
        state = _state(shapes)
        enter_page(state)
        shapes[0]["text"] = "3"
        enter_page(state)
        self.assertEqual(shapes[0]["text"], "")

    def test_a_field_beyond_the_range_is_left(self):
        shapes = [_text("Response 26"), _text("Responses")]
        state = _state(shapes)
        enter_page(state)
        self.assertEqual([s["text"] for s in shapes], ["?", "?"])

    def test_form_fields_clear_and_turn_yellow(self):
        shapes = [_text("Response"), _text("response 12"), _text("Response 13")]
        state = _state(shapes)
        fillin.call(state, "SetupFormFields", "")
        self.assertEqual([s["text"] for s in shapes], ["", "", "?"])
        self.assertEqual([s["outline"] for s in shapes], ["#ffff00", "#ffff00", "#00ffff"])


class Forward(unittest.TestCase):
    def test_lines_after_forward_run(self):
        state = RuntimeState(book=Book(path="x"))
        run_handler(state, "a = 1\nforward\nb = 2\n")
        self.assertEqual((state.variables["a"], state.variables["b"]), (1, 2))

    def test_forward_runs_the_parent_at_that_line(self):
        state = RuntimeState(book=Book(path="x"))
        parent = "order = order & \"P\"\n"
        actions = run_handler(state, "order = \"C\"\nforward\norder = order & \"C\"\n", [parent])
        self.assertEqual(state.variables["order"], "CPC")
        self.assertEqual([a["kind"] for a in actions].count("forward"), 1)

    def test_page_then_background_then_the_rest_of_the_page(self):
        page = Page(id="P1", handlers=split_handlers(
            "to handle enterpage\n x = \"1\"\n forward\n x = x & \"3\"\nend\n"
        ) + split_handlers("to handle enterPage\n x = x & \"2\"\nend\n"))
        state = RuntimeState(book=Book(path="x", pages=[page]))
        run_page_handlers(state, "enterpage")
        self.assertEqual(state.variables["x"], "123")

    def test_a_handler_that_does_not_forward_still_lets_the_background_run(self):
        page = Page(id="P1", handlers=split_handlers(
            "to handle enterpage\n x = \"1\"\nend\n"
        ) + split_handlers("to handle enterPage\n x = x & \"2\"\nend\n"))
        state = RuntimeState(book=Book(path="x", pages=[page]))
        run_page_handlers(state, "enterpage")
        self.assertEqual(state.variables["x"], "12")

    def test_a_parent_runs_once(self):
        page = Page(id="P1", handlers=split_handlers(
            "to handle enterpage\n forward\nend\n"
        ) + split_handlers("to handle enterPage\n x = x & \"2\"\nend\n"))
        state = RuntimeState(book=Book(path="x", pages=[page]))
        state.variables["x"] = ""
        run_page_handlers(state, "enterpage")
        self.assertEqual(state.variables["x"], "2")


class WhatForwardNowReaches(unittest.TestCase):
    """Lines after a forward now run, so they must not damage the page."""

    def _run(self, shapes, source):
        state = RuntimeState(book=Book(path="x", pages=[Page(id="P1", shapes=shapes)]))
        run_handler(state, source)
        return state

    def test_one_line_of_a_field_is_set_not_the_whole_text(self):
        shape = _text("text", "\n\nold")
        self._run([shape], 'set textline 3 of text of field "text" to "third"\n')
        self.assertEqual(shape["text"], "\n\nthird")
        shape = _text("text", "one\ntwo\nthree")
        self._run([shape], 'set textline 2 of text of field "text" to "2"\n')
        self.assertEqual(shape["text"], "one\n2\nthree")

    def test_a_sum_this_reader_cannot_do_is_not_written_into_a_field(self):
        shape = _text("variable23", "0.0  kHz")
        self._run([shape], 'set text of field "variable23" to (var21-var22) & " kHz"\n')
        self.assertEqual(shape["text"], "0.0  kHz")

    def test_an_unknown_call_is_not_written_into_a_field(self):
        shape = _text("variable15", "390.00 ")
        self._run([shape], 'set text of field "variable15" to format(x) & " mA"\n')
        self.assertEqual(shape["text"], "390.00 ")

    def test_a_plain_text_is_written(self):
        shape = _text("variable1", "old")
        self._run([shape], 'set text of field "variable1" to "new" & " mA"\n')
        self.assertEqual(shape["text"], "new mA")


if __name__ == "__main__":
    unittest.main()
