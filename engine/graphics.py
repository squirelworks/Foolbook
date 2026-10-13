"""Graphics scaffold.

Extracts drawable shapes from a book if present. The native viewer
calls draw() on a canvas. If the book has no shapes, draw() does nothing.
This does not change text rendering.
"""

from __future__ import annotations

from pathlib import Path


def extract(book) -> list[dict]:
    """Return a list of shape dicts from a book. Empty if none.

    A shape dict has: kind, points (list of [x, y]), fill, bounds.
    """
    shapes = []
    raw = getattr(book, "raw", None) or {}
    for s in raw.get("shapes") or []:
        shapes.append(s)
    # Page-level shapes, if the loader put them there
    for page in getattr(book, "pages", []) or []:
        for s in getattr(page, "shapes", None) or []:
            shapes.append(s)
    return shapes


def draw(canvas, shapes: list[dict], scale: float = 0.05) -> None:
    """Draw shapes on a tkinter Canvas. No-op if shapes is empty."""
    if not shapes or canvas is None:
        return
    for s in shapes:
        pts = s.get("points") or []
        if len(pts) < 2:
            continue
        flat = []
        for x, y in pts:
            flat.extend([x * scale, y * scale])
        fill = s.get("fill") or ""
        try:
            canvas.create_polygon(flat, fill=fill or "", outline="black")
        except Exception:
            continue
