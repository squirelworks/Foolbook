"""A list box on a Foolbook page.

A `list` shape has `choices`, a list of strings, and `value`, the index
of the chosen one. Rows are ROW pixels high. When there are more rows
than fit, a bar BAR pixels wide sits at the right edge: a click on its
upper half scrolls up one row, on its lower half down one. `scroll` is
the first row shown.
"""

from __future__ import annotations

ROW = 18
BAR = 14
CHOSEN = "#c8d8f0"


def _box(shape: dict) -> tuple[float, float, float, float]:
    return (float(shape.get("x") or 0), float(shape.get("y") or 0),
            float(shape.get("w") or 0), float(shape.get("h") or 0))


def rows_that_fit(shape: dict) -> int:
    return max(1, int(_box(shape)[3] // ROW))


def scrolls(shape: dict) -> bool:
    return len(shape.get("choices") or []) > rows_that_fit(shape)


def _first(shape: dict) -> int:
    most = max(0, len(shape.get("choices") or []) - rows_that_fit(shape))
    return min(max(0, int(shape.get("scroll") or 0)), most)


def visible_rows(shape: dict) -> list[tuple[int, str, float]]:
    """(index, text, top) for each row that is drawn."""
    _x, y, _w, _h = _box(shape)
    found = list(shape.get("choices") or [])
    first = _first(shape)
    shown = found[first:first + rows_that_fit(shape)]
    return [(first + n, str(text), y + n * ROW) for n, text in enumerate(shown)]


def click(shape: dict, px: float, py: float) -> None:
    """A click at this page point. Picks a row, or scrolls one row when it is on the bar."""
    x, y, w, h = _box(shape)
    if scrolls(shape) and px >= x + w - BAR:
        shape["scroll"] = _first(shape) + (-1 if py < y + h / 2 else 1)
        shape["scroll"] = _first(shape)
        return
    for index, _text, top in visible_rows(shape):
        if top <= py < top + ROW:
            shape["value"] = index
            return


# A combo box is a list that opens. Closed, it shows the chosen row and an
# arrow. Open, its rows hang below the box, in front of every other shape.
# `open` is only held while the book is shown.

def combo_text(shape: dict) -> str:
    found = list(shape.get("choices") or [])
    value = shape.get("value")
    if isinstance(value, int) and 0 <= value < len(found):
        return str(found[value])
    return ""


def combo_rows(shape: dict) -> list[tuple[int, str, float]]:
    """(index, text, top) of each row of the open list, under the box."""
    _x, y, _w, h = _box(shape)
    return [(n, str(text), y + h + n * ROW) for n, text in enumerate(shape.get("choices") or [])]


def combo_reach(shape: dict) -> float:
    """How far below its top an open combo box takes clicks."""
    _x, _y, _w, h = _box(shape)
    if not shape.get("open"):
        return h
    return h + len(shape.get("choices") or []) * ROW


def combo_click(shape: dict, px: float, py: float) -> None:
    """Closed, a click opens it. Open, a click on a row picks it, and any click closes it."""
    if not shape.get("open"):
        shape["open"] = True
        return
    shape["open"] = False
    for index, _text, top in combo_rows(shape):
        if top <= py < top + ROW:
            shape["value"] = index
            return
