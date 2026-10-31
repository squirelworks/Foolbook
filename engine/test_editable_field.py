"""`editable` decides whether a Foolbook text shape is a field."""

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

    def test_an_editable_field_takes_typed_keys(self):
        shape = _shape(editable=True)
        state = _state(shape)
        fields.focus(state, shape)
        for char in "Ada":
            self.assertTrue(fields.handle_key(state, char, char))
        self.assertEqual(shape["text"], "Ada")


class NidaResponse(unittest.TestCase):
    # A NIDA fill-in, as the .tbk loader hands it over: no `editable` key,
    # named Response. It is judged as on main, by its name.
    def test_a_response_field_without_editable_is_still_a_field_and_takes_keys(self):
        shape = _shape(name="Response")
        self.assertTrue(fields.is_field(shape))
        state = _state(shape)
        fields.focus(state, shape)
        self.assertTrue(fields.handle_key(state, "7", "7"))
        self.assertEqual(shape["text"], "7")
        self.assertNotIn("value", shape)

    def test_a_hidden_shape_is_not_a_field_even_when_editable(self):
        self.assertFalse(fields.is_field(_shape(editable=True, visible=False)))
        self.assertFalse(fields.is_field({"kind": "button", "name": "Go", "editable": True}))

if __name__ == "__main__":
    unittest.main()
