"""A click gives an answer field the keyboard, and typed keys edit its text."""

from __future__ import annotations

import unittest

from engine import fields
from engine.engine import goto, set_shape_text
from foolbook.model import Book, Page, RuntimeState


def _field(name="Response", text="", script=""):
    return {"kind": "text", "name": name, "text": text, "script": script, "x": 10, "y": 10, "w": 40, "h": 20}


def _state(*shapes, other=None):
    pages = [Page(id="P1", shapes=list(shapes))]
    if other is not None:
        pages.append(Page(id="P2", shapes=list(other)))
    state = RuntimeState(book=Book(path="x", pages=pages))
    state.variables["sysLevel"] = "reader"
    return state


class WhichTextTakesKeys(unittest.TestCase):
    def test_the_answer_fields_are_fields(self):
        for name in ("Response", "response 1", "RESPONSE 12"):
            self.assertTrue(fields.is_field(_field(name)), name)

    def test_a_label_is_not(self):
        self.assertFalse(fields.is_field(_field("Text", "What is 2 + 5?")))
        self.assertFalse(fields.is_field(_field("")))
        self.assertFalse(fields.is_field({"kind": "button", "name": "Response"}))
        self.assertFalse(fields.is_field(None))

    def test_a_field_with_a_key_handler_is_a_field(self):
        script = "to handle keyUp key\n  forward\nend\n"
        self.assertTrue(fields.is_field(_field("Answer", script=script)))

    def test_a_hidden_field_is_not(self):
        shape = _field()
        shape["visible"] = False
        self.assertFalse(fields.is_field(shape))


class Typing(unittest.TestCase):
    def test_typed_characters_land_in_the_field(self):
        shape = _field()
        state = _state(shape)
        fields.focus(state, shape)
        self.assertTrue(fields.handle_key(state, "7", "7"))
        self.assertTrue(fields.handle_key(state, "period", "."))
        self.assertEqual(shape["text"], "7.")
        self.assertTrue(state.variables.get("__redraw"))

    def test_backspace_removes_the_last_character(self):
        shape = _field(text="12")
        state = _state(shape)
        fields.focus(state, shape)
        fields.handle_key(state, "BackSpace", "\x08")
        self.assertEqual(shape["text"], "1")
        fields.handle_key(state, "BackSpace", "\x08")
        fields.handle_key(state, "BackSpace", "\x08")
        self.assertEqual(shape["text"], "")

    def test_return_is_taken_and_leaves_the_text(self):
        shape = _field(text="7")
        state = _state(shape)
        fields.focus(state, shape)
        self.assertTrue(fields.handle_key(state, "Return", "\r"))
        self.assertEqual(shape["text"], "7")

    def test_a_control_key_is_not_text(self):
        shape = _field()
        state = _state(shape)
        fields.focus(state, shape)
        self.assertFalse(fields.handle_key(state, "Shift_L", ""))
        self.assertFalse(fields.handle_key(state, "Escape", "\x1b"))
        self.assertEqual(shape["text"], "")

    def test_no_focus_means_no_typing(self):
        shape = _field()
        state = _state(shape)
        self.assertFalse(fields.handle_key(state, "7", "7"))
        self.assertEqual(shape["text"], "")

    def test_a_single_run_grows_with_the_text(self):
        shape = _field(text="")
        shape["runs"] = [{"start": 0, "end": 0, "color": "#ffff00"}]
        state = _state(shape)
        set_shape_text(state, shape, "42")
        self.assertEqual(shape["runs"][0]["end"], 2)


class Focus(unittest.TestCase):
    def test_only_one_field_has_the_keyboard(self):
        one, two = _field("Response 1"), _field("Response 2")
        state = _state(one, two)
        fields.focus(state, one)
        fields.focus(state, two)
        self.assertNotIn("focused", one)
        self.assertTrue(two["focused"])
        self.assertIs(fields.focused(state), two)

    def test_leaving_the_page_drops_the_focus(self):
        shape = _field()
        state = _state(shape, other=[_field()])
        fields.focus(state, shape)
        self.assertTrue(goto(state, "P2"))
        self.assertIsNone(fields.focused(state))
        self.assertNotIn("focused", shape)
        self.assertFalse(fields.handle_key(state, "7", "7"))


if __name__ == "__main__":
    unittest.main()
