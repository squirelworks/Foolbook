"""Typed text in a ToolBook field.

A field is canvas text in this reader. A click on an answer field gives it
the keyboard focus, and the keys that follow edit its text:

  a printable key adds its character at the end
  BackSpace removes the last character
  Return is taken by the field (nothing else on the window reacts to it)

Each key is first given to the field's own keyChar handler, as `key`, the
character code. The key goes in only when that handler forwards it, which is
how a numeric field refuses a letter.

The caret is always at the end of the text. Moving it inside the text is
not read yet.

When the key is let go the field's own keyUp handler runs (`key_up`).
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


def key_code(keysym: str, char: str) -> int:
    """The number a keyChar handler gets as `key`. 0 when the key is not a character."""
    if keysym == "BackSpace":
        return 8
    if keysym in ("Return", "KP_Enter"):
        return 13
    if char and len(char) == 1 and ord(char) >= 32 and ord(char) != 127:
        return ord(char)
    return 0


def allowed(state, shape: dict, code: int) -> bool:
    """Run the field's own keyChar handler. The key goes in only if it forwards.

    A field with no keyChar handler takes every key.
    """
    from engine.engine import one_handler, run_handler
    body = one_handler(shape.get("script") or "", "keyChar")
    if not body:
        return True
    saved = state.variables.get("key")
    state.variables["key"] = code
    try:
        actions = run_handler(state, body)
    finally:
        if saved is None:
            state.variables.pop("key", None)
        else:
            state.variables["key"] = saved
    return any(action.get("kind") == "forward" for action in actions)


def handle_key(state, keysym: str, char: str) -> bool:
    """One key press for the focused field. True when the field took it."""
    from engine.engine import set_shape_text
    shape = focused(state)
    if shape is None:
        return False
    code = key_code(keysym, char)
    if not code:
        return False
    # Every key asks keyChar first, Return too. Return is not text.
    if not allowed(state, shape, code):
        return True
    text = str(shape.get("text") or "")
    if code == 8:
        set_shape_text(state, shape, text[:-1])
    elif code != 13:
        set_shape_text(state, shape, text + chr(code))
    return True


def key_up(state, keysym: str, char: str) -> list[dict]:
    """The key was let go. Run the field's own keyUp handler and return its actions.

    The handler gets `key`, the character code, as keyChar did. Return is
    the key an answer field acts on: its keyUp reads the field, compares the
    answer and goes to the page that says right or wrong.
    """
    from engine.engine import one_handler, run_handler
    shape = focused(state)
    if shape is None:
        return []
    code = key_code(keysym, char)
    body = one_handler(shape.get("script") or "", "keyUp")
    if not code or not body:
        return []
    saved = state.variables.get("key")
    state.variables["key"] = code
    try:
        return run_handler(state, body)
    finally:
        if saved is None:
            state.variables.pop("key", None)
        else:
            state.variables["key"] = saved
