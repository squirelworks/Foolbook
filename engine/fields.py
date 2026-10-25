"""Typed text in a ToolBook field.

A field is canvas text in this reader. A click on an answer field gives it
the keyboard focus, and the keys that follow edit its text:

  a printable key adds its character at the end
  BackSpace removes the last character
  Return is taken by the field (nothing else on the window reacts to it)

The caret is always at the end of the text. Moving it inside the text is
not read yet.

What a field's own keyChar and keyUp scripts do with these keys is not run
here. That is separate behaviour and has its own change.
"""

from __future__ import annotations

import re

# SetupFillInFields clears "response" and "response 1" to "response 25".
_ANSWER_FIELD = re.compile(r"response(?:\s*\d+)?", re.IGNORECASE)


def handles_keys(shape: dict) -> bool:
    """The field's own script has a keyChar or keyUp handler."""
    script = (shape.get("script") or "").lower()
    return "keychar" in script or "keyup" in script


def is_field(shape: dict | None) -> bool:
    """A text object a reader types into.

    The file does not mark a locked text, so this is read from the book's
    own conventions: the object carries a key handler, or it is named like
    the answer fields that SetupFillInFields clears. A label has neither.
    """
    if not shape or (shape.get("kind") or "") != "text":
        return False
    if shape.get("visible") is False:
        return False
    if handles_keys(shape):
        return True
    return _ANSWER_FIELD.fullmatch((shape.get("name") or "").strip()) is not None


def focused(state) -> dict | None:
    """The field that has the keyboard, if it is still on this page."""
    shape = state.variables.get("__focus")
    if shape is None:
        return None
    page = state.page
    if page is None or not any(item is shape for item in page.shapes or []):
        blur(state)
        return None
    return shape


def focus(state, shape: dict) -> None:
    """Give the keyboard to this field."""
    if focused(state) is shape:
        return
    blur(state)
    shape["focused"] = True
    state.variables["__focus"] = shape
    state.variables["__redraw"] = True


def blur(state) -> None:
    shape = state.variables.pop("__focus", None)
    if shape is not None:
        shape.pop("focused", None)
        state.variables["__redraw"] = True


def handle_key(state, keysym: str, char: str) -> bool:
    """One key press for the focused field. True when the field took it."""
    from engine.engine import set_shape_text
    shape = focused(state)
    if shape is None:
        return False
    text = str(shape.get("text") or "")
    if keysym == "BackSpace":
        set_shape_text(state, shape, text[:-1])
        return True
    if keysym in ("Return", "KP_Enter"):
        return True
    if char and len(char) == 1 and ord(char) >= 32 and ord(char) != 127:
        set_shape_text(state, shape, text + char)
        return True
    return False
