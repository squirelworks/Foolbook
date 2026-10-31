"""Hotwords: a range of a field's words that jumps somewhere.

A text shape may carry `hotwords`, each `{"start", "end", "item"}`.
`start` and `end` count characters of the text as it is drawn
(graphics.drawn_text), and `end` is not in the range. `item` is a jump,
as a button's is. A click whose character falls in a range follows it.
"""

from __future__ import annotations


def ranges(shape: dict) -> list[dict]:
    """The hotwords that fall inside the text."""
    from engine.graphics import drawn_text
    length = len(drawn_text(shape))
    found = []
    for word in shape.get("hotwords") or []:
        try:
            start, end = int(word["start"]), int(word["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if 0 <= start < end <= length and isinstance(word.get("item"), dict):
            found.append(word)
    return found


def at(shape: dict, index: int) -> dict | None:
    for word in ranges(shape):
        if int(word["start"]) <= index < int(word["end"]):
            return word
    return None


def clicked(canvas, shape: dict, x: float, y: float) -> dict | None:
    """The hotword under a canvas point, if the text there is this shape's."""
    from engine.graphics import drawn_text, text_index_at
    if not shape.get("hotwords"):
        return None
    hit = text_index_at(canvas, x, y)
    if hit is None or hit[0] != drawn_text(shape):
        return None
    return at(shape, hit[1])
