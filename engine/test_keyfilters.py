"""DoNumeric and DoAlphabetic decide which keys a fill-in field takes."""

from __future__ import annotations

import unittest

from engine import fields, fillin
from engine.engine import run_handler
from foolbook.model import Book, Page, RuntimeState

NUMERIC_FIELD = """to handle keyChar key
  if DoNumeric (key) then
    forward
  end if
end

TO HANDLE KeyUp key
  forward
end
"""

ALPHA_FIELD = NUMERIC_FIELD.replace("DoNumeric", "DoAlphabetic")


def _typed(script: str, keys: str, start: str = ""):
    shape = {"kind": "text", "name": "Response", "text": start, "script": script, "x": 0, "y": 0, "w": 40, "h": 20}
    state = RuntimeState(book=Book(path="x", pages=[Page(id="P1", shapes=[shape])]))
    fields.focus(state, shape)
    beeps = 0
    for char in keys:
        keysym = "BackSpace" if char == "\b" else char
        fields.handle_key(state, keysym, char)
        if state.variables.pop("__beep", None):
            beeps += 1
    return shape["text"], beeps, state


class Numeric(unittest.TestCase):
    def test_digits_point_and_signs_go_in(self):
        text, beeps, _ = _typed(NUMERIC_FIELD, "-12.5+")
        self.assertEqual(text, "-12.5+")
        self.assertEqual(beeps, 0)

    def test_other_keys_are_refused_with_a_beep(self):
        text, beeps, _ = _typed(NUMERIC_FIELD, "1a,b 2/")
        self.assertEqual(text, "12")
        self.assertEqual(beeps, 5)

    def test_backspace_is_allowed(self):
        text, beeps, _ = _typed(NUMERIC_FIELD, "123\b\b")
        self.assertEqual(text, "1")
        self.assertEqual(beeps, 0)

    def test_return_is_allowed_and_adds_nothing(self):
        shape = {"kind": "text", "name": "Response", "text": "7", "script": NUMERIC_FIELD}
        state = RuntimeState(book=Book(path="x", pages=[Page(id="P1", shapes=[shape])]))
        fields.focus(state, shape)
        self.assertTrue(fields.handle_key(state, "Return", "\r"))
        self.assertEqual(shape["text"], "7")
        self.assertNotIn("__beep", state.variables)


class Alphabetic(unittest.TestCase):
    def test_letters_of_either_case_go_in(self):
        text, beeps, _ = _typed(ALPHA_FIELD, "aBz")
        self.assertEqual(text, "aBz")
        self.assertEqual(beeps, 0)

    def test_digits_and_punctuation_are_refused(self):
        text, beeps, _ = _typed(ALPHA_FIELD, "a1-b c")
        self.assertEqual(text, "abc")
        self.assertEqual(beeps, 3)


class NoFilter(unittest.TestCase):
    def test_a_field_without_keychar_takes_every_key(self):
        text, beeps, _ = _typed("", "(3,5) ab")
        self.assertEqual(text, "(3,5) ab")
        self.assertEqual(beeps, 0)


class Calls(unittest.TestCase):
    def test_the_call_in_a_script_answers_for_the_key(self):
        state = RuntimeState(book=Book(path="x"))
        state.variables["key"] = ord("7")
        actions = run_handler(state, "if DoNumeric (key) then\n forward\nend if\n")
        self.assertEqual([a["kind"] for a in actions], ["forward"])
        state.variables["key"] = ord("x")
        self.assertEqual(run_handler(state, "if DoNumeric (key) then\n forward\nend if\n"), [])
        self.assertTrue(state.variables.get("__beep"))

    def test_the_key_variable_is_put_back(self):
        _, _, state = _typed(NUMERIC_FIELD, "1")
        self.assertNotIn("key", state.variables)

    def test_the_allowed_lists(self):
        for char in "0123456789.+-":
            self.assertTrue(fillin.allows(ord(char), fillin.NUMERIC), char)
        for char in "aA,/* _":
            self.assertFalse(fillin.allows(ord(char), fillin.NUMERIC), repr(char))
        self.assertTrue(fillin.allows(8, fillin.NUMERIC))
        self.assertTrue(fillin.allows(13, fillin.ALPHABETIC))
        self.assertFalse(fillin.allows(0, fillin.ALPHABETIC))
        self.assertFalse(fillin.allows(ord("é"), fillin.ALPHABETIC))


if __name__ == "__main__":
    unittest.main()
