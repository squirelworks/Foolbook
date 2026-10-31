"""A viewer is the window a book asks for.

The book stores a list of records: name, size, and the buttons the reader
shows (previous, next, page number). The reader reads the first one.
Custom viewer chrome is not drawn.
"""

from __future__ import annotations

BUTTONS = ("previous", "next", "page")


def first_viewer(book) -> dict | None:
    """The first viewer record on the book, or None."""
    for viewer in getattr(book, "viewers", None) or []:
        if isinstance(viewer, dict):
            return viewer
    return None


def chrome(viewer: dict | None) -> list[str]:
    """The buttons to show, in the reader's order. Unknown names are left out."""
    asked = {str(name).lower() for name in (viewer or {}).get("buttons") or []}
    return [name for name in BUTTONS if name in asked]


def step(index: int, count: int, delta: int) -> int:
    """Previous and next move one page in book order, and stop at the ends."""
    if count <= 0:
        return 0
    return max(0, min(count - 1, index + delta))


def page_number(index: int, count: int) -> str:
    return f"{index + 1} of {count}"
