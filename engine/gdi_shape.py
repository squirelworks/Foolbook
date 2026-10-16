"""The other GDI shape calls, and the ToolBook values that feed them.

``Polygon`` is ``polygon.py``. These are the rest of the painters in
chapter 5. Each function returns the arguments of one GDI call. A field
the file does not hold is ``None``. Nothing here invents a pen.

``to_pixel`` is ``FUN_1008_01dd``: ``(coord * dpi + 720) / 1440``.
"""

from __future__ import annotations

from engine.polygon import to_pixel


def _box(left: int, top: int, right: int, bottom: int, dpi: int) -> dict:
    return {
        "left": to_pixel(left, dpi),
        "top": to_pixel(top, dpi),
        "right": to_pixel(right, dpi),
        "bottom": to_pixel(bottom, dpi),
    }


def rectangle(left: int, top: int, right: int, bottom: int, dpi: int = 96, fill: str | None = None) -> dict:
    """``Rectangle(hdc, left, top, right, bottom)``.

    GDI draws the box with the current pen and fills it with the current
    brush. ToolBook's content record stores four twips and a fill dword.
    """
    return {"gdi": "Rectangle", "box": _box(left, top, right, bottom, dpi), "fill": fill, "pen": None}


def ellipse(left: int, top: int, right: int, bottom: int, dpi: int = 96, fill: str | None = None) -> dict:
    """``Ellipse(hdc, left, top, right, bottom)``.

    The ellipse is the one bounded by that box. No file marker for an
    ellipse is known, so the page scan does not call this.
    """
    return {"gdi": "Ellipse", "box": _box(left, top, right, bottom, dpi), "fill": fill, "pen": None}


def round_rect(left: int, top: int, right: int, bottom: int, corner_w: int, corner_h: int, dpi: int = 96, fill: str | None = None) -> dict:
    """``RoundRect(hdc, left, top, right, bottom, width, height)``.

    ``width`` and ``height`` are the ellipse that rounds the corners.
    The painter reads a rect at object ``+0x12``. The file marker is not known.
    """
    box = _box(left, top, right, bottom, dpi)
    box["corner_w"] = to_pixel(corner_w, dpi)
    box["corner_h"] = to_pixel(corner_h, dpi)
    return {"gdi": "RoundRect", "box": box, "fill": fill, "pen": None}


def polyline(pairs: list[tuple[int, int]], dpi: int = 96) -> dict:
    """``Polyline(hdc, points, count)``.

    The current pen connects the points. The figure is not closed and it
    is not filled. The live painter ``FUN_13e8_00e6`` reads the count at
    object ``+0x2D`` and converts the pairs at ``DS:30AC``.
    """
    pixels = [[to_pixel(x, dpi), to_pixel(y, dpi)] for x, y in pairs]
    return {"gdi": "Polyline", "count": len(pixels), "pixels": pixels, "fill": None, "pen": None}


def arc(left: int, top: int, right: int, bottom: int, start: tuple[int, int], end: tuple[int, int], dpi: int = 96) -> dict:
    """``Arc(hdc, left, top, right, bottom, xStart, yStart, xEnd, yEnd)``.

    The two points are not angles. Each is a ray from the center of the
    box. The pen draws from the start ray to the end ray. The arc is not
    filled. ToolBook does not call ``Pie``.
    """
    box = _box(left, top, right, bottom, dpi)
    start_px = (to_pixel(start[0], dpi), to_pixel(start[1], dpi))
    end_px = (to_pixel(end[0], dpi), to_pixel(end[1], dpi))
    return {
        "gdi": "Arc",
        "box": box,
        "start": list(start_px),
        "end": list(end_px),
        "fill": None,
        "pen": None,
    }


def pie(*_args, **_kwargs) -> dict:
    """``Pie`` is a GDI call. ``TB80BAS`` does not import it."""
    return {"gdi": None, "reason": "TB80 does not call Pie"}


def bracket(_left: int, _top: int, _right: int, _bottom: int, dpi: int = 96) -> dict:
    """A bracket is a polyline whose points are computed from the bounds.

    P1170's four live points were not the four corners. The formula that
    produced them is not known, so this does not invent the points.
    """
    return {"gdi": "Polyline", "count": None, "pixels": None, "dpi": dpi, "pen": None,
            "reason": "computed from bounds; the formula is not known"}
