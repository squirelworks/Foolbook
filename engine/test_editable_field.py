"""A Foolbook field marked editable takes the keyboard and keeps what was typed as value."""

from __future__ import annotations

import unittest

from engine import fields
from foolbook.model import Book, Page, RuntimeState


def _shape(**extra):
    shape = {"kind": "text", "name": "Your name", "text": "", "x": 10, "y": 10, "w": 120, "h": 24}
    shape.update(extra)
    return shape


def _state(shape):
    state = RuntimeState(book=Book(path="x.fbk", pages=[Page(id="P0", shapes=[shape])]))
    state.variables["sysLevel"] = "reader"
    return state


class EditableField(unittest.TestCase):
    def test_editable_makes_a_text_shape_a_field(self):
        self.assertTrue(fields.is_field(_shape(editable=True)))

    def test_a_plain_text_shape_is_still_not_a_field(self):
        self.assertFalse(fields.is_field(_shape()))

    def test_editable_false_locks_even_an_answer_field(self):
        self.assertFalse(fields.is_field(_shape(name="Response", editable=False)))

    def test_typed_keys_are_kept_as_value(self):
        shape = _shape(editable=True)
        state = _state(shape)
        fields.focus(state, shape)
        for char in "Ada":
            self.assertTrue(fields.handle_key(state, char, char))
        fields.handle_key(state, "BackSpace", "")
        self.assertEqual(shape["text"], "Ad")
        self.assertEqual(shape["value"], "Ad")
        self.assertTrue(shape.get("focused"))

    def test_a_field_that_is_not_marked_editable_gets_no_value(self):
        shape = _shape(name="Response")
        state = _state(shape)
        fields.focus(state, shape)
        fields.handle_key(state, "7", "7")
        self.assertEqual(shape["text"], "7")
        self.assertNotIn("value", shape)


if __name__ == "__main__":
    unittest.main()
