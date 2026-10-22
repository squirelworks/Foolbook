"""What a page change leaves on the window.

``go to page`` does not look at the Next button. A background that fills
paints over the window. A background with no fill leaves it. Objects
marked direct are painted for the current page only. ``FUN_1018_1492``
is that flag, bit ``0x20`` of object ``+0x1F``.
"""

from __future__ import annotations


def paints_paper(shapes: list[dict]) -> bool:
    """The background fill is a page-sized rectangle. Pattern ``0xFD`` has none."""
    for shape in shapes:
        if (shape.get("kind") or "rect") != "rect" or not shape.get("fill"):
            continue
        if int(shape.get("x") or 0) <= 4 and int(shape.get("y") or 0) <= 4:
            if int(shape.get("w") or 0) >= 400 and int(shape.get("h") or 0) >= 280:
                return True
    return False


def arrive(window: list, index: int, shapes: list[dict]) -> list:
    """The page at ``index`` is now current. ``window`` is the pages still up."""
    if window and window[-1][0] == index:
        window[-1] = (index, shapes)
        return window
    if paints_paper(shapes):
        window[:] = [(index, shapes)]
    else:
        window.append((index, shapes))
    return window


def visible(window: list) -> list[dict]:
    """Every retained object, plus the direct objects of the page now showing."""
    if not window:
        return []
    shown = []
    last = len(window) - 1
    for place, (_index, shapes) in enumerate(window):
        if place == last:
            shown.extend(shapes)
        else:
            shown.extend(shape for shape in shapes if not shape.get("direct"))
    return shown
