"""Return in a field of a multi-answer page moves the keyboard to the next field."""

from __future__ import annotations

import unittest

from engine import fields
from engine.engine import follow
from foolbook.model import Book, Page, RuntimeState


def _script(next_name):
    move = f'  set focus to field "{next_name}"\n  set caretLocation to 1,1\n' if next_name else "  forward\n"
    return (
        "to handle keyChar key\nif DoNumeric(key) then\nforward\nend if\nend\n"
        "TO HANDLE KeyUp key\n"
        "  if key <> KeyEnter\n    forward\n    break\n  end if\n"
        f"{move}end\n"
    )


def _page():
    shapes = [
        {"kind": "text", "name": "Response 1", "text": "", "script": _script("response 2")},
        {"kind": "text", "name": "Response 2", "text": "", "script": _script("response 3")},
        {"kind": "text", "name": "Response 3", "text": "", "script": _script("response 4")},
        {"kind": "text", "name": "Response 4", "text": "", "script": ""},
        {"kind": "text", "name": "a", "text": "5 + 0 =", "script": ""},
    ]
    state = RuntimeState(book=Book(path="x", pages=[Page(id="P1090", shapes=shapes)]))
    state.variables["sysLevel"] = "reader"
    return state, shapes


def _press(state, keysym, char):
    fields.handle_key(state, keysym, char)
    follow(state, fields.key_up(state, keysym, char))


def _focused_name(state):
    shape = fields.focused(state)
    return shape["name"] if shape else None


class Chain(unittest.TestCase):
    def test_return_moves_down_the_fields_and_typing_follows(self):
        state, shapes = _page()
        fields.focus(state, shapes[0])
        _press(state, "0", "0")
        _press(state, "Return", "\r")
        self.assertEqual(_focused_name(state), "Response 2")
        _press(state, "5", "5")
        _press(state, "Return", "\r")
        _press(state, "1", "1")
        _press(state, "0", "0")
        _press(state, "Return", "\r")
        self.assertEqual(_focused_name(state), "Response 4")
        _press(state, "9", "9")
        self.assertEqual([s["text"] for s in shapes[:4]], ["0", "5", "10", "9"])

    def test_the_last_field_has_nowhere_to_go(self):
        state, shapes = _page()
        fields.focus(state, shapes[3])
        _press(state, "Return", "\r")
        self.assertEqual(_focused_name(state), "Response 4")

    def test_another_key_leaves_the_focus(self):
        state, shapes = _page()
        fields.focus(state, shapes[0])
        _press(state, "3", "3")
        self.assertEqual(_focused_name(state), "Response 1")

    def test_a_refused_key_still_leaves_the_focus(self):
        state, shapes = _page()
        fields.focus(state, shapes[0])
        _press(state, "a", "a")
        self.assertEqual(_focused_name(state), "Response 1")
        self.assertEqual(shapes[0]["text"], "")

    def test_the_old_field_loses_the_caret(self):
        state, shapes = _page()
        fields.focus(state, shapes[0])
        _press(state, "Return", "\r")
        self.assertNotIn("focused", shapes[0])
        self.assertTrue(shapes[1]["focused"])

    def test_a_field_that_is_not_on_the_page_is_ignored(self):
        state, shapes = _page()
        fields.focus(state, shapes[2])
        shapes[2]["script"] = _script("response 9")
        _press(state, "Return", "\r")
        self.assertEqual(_focused_name(state), "Response 3")

    def test_the_name_is_not_case_sensitive(self):
        state, shapes = _page()
        self.assertTrue(fields.focus_named(state, "RESPONSE 2"))
        self.assertEqual(_focused_name(state), "Response 2")


if __name__ == "__main__":
    unittest.main()
