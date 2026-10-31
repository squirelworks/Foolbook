"""A list box on a Foolbook page.

A `list` shape has `choices`, a list of strings, and `value`, the index
of the chosen one. Rows are ROW pixels high. When there are more rows
than fit, a bar BAR pixels wide sits at the right edge. `scroll` is the
first row shown.
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
