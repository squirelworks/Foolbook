"""Draw the shapes stored on a Foolbook page.

A page carries its own shapes. Coordinates are pixels in the window.
A ToolBook page stream is not a shape source. When a .tbk is open, that
stream is decoded to handler source and the engine runs it.

  rect, ellipse   x, y, w, h, fill, outline
  line, polygon   points: [[x, y], ...]
  text            x, y, text
  image           x, y, and src (a file beside the book) or data (base64 PNG or GIF)

bounds, when present, is [x, y, w, h] and stands in for x, y, w, h.
"""

from __future__ import annotations

import base64
from pathlib import Path


def extract(page) -> list[dict]:
    """Shapes for one page. A book returns every page's shapes, in order."""
    if hasattr(page, "pages"):
        found = []
        for item in page.pages:
            found.extend(extract(item))
        return found
    if isinstance(page, dict):
        return list(page.get("shapes") or [])
    return list(getattr(page, "shapes", None) or [])


def bottom(shapes: list[dict]) -> int:
    """Lowest pixel a shape reaches. Zero when there is nothing to draw."""
    low = 0
    for shape in shapes or []:
        points = shape.get("points") or []
        if points:
            low = max(low, max(int(pt[1]) for pt in points if len(pt) >= 2))
        else:
            y = int(shape.get("y") or 0)
            h = int(shape.get("h") or 0)
            if (shape.get("kind") or "").lower() == "text":
                h = max(h, int(shape.get("size") or 12))
            low = max(low, y + h)
    return low


def draw(canvas, shapes: list[dict], base: str | Path | None = None) -> None:
    """Draw shapes on a tkinter Canvas. No-op when there are none."""
    if not shapes or canvas is None:
        return
    photos = []
    for shape in shapes:
        kind = (shape.get("kind") or "rect").lower()
        fill = shape.get("fill") or ""
        outline = shape["outline"] if "outline" in shape else "black"
        if kind == "polygon":
            flat = _points(shape)
            if len(flat) >= 6:
                canvas.create_polygon(*flat, fill=fill, outline=outline or "")
        elif kind == "line":
            flat = _points(shape)
            if len(flat) >= 4:
                canvas.create_line(*flat, fill=outline or fill or "black")
        elif kind in ("ellipse", "oval"):
            x, y, w, h = _box(shape)
            canvas.create_oval(x, y, x + w, y + h, fill=fill, outline=outline or "")
        elif kind == "text":
            size = int(shape.get("size") or 12)
            font = ("TkDefaultFont", size, "bold") if shape.get("bold") else ("TkDefaultFont", size)
            canvas.create_text(
                int(shape.get("x") or 0),
                int(shape.get("y") or 0),
                text=str(shape.get("text") or ""),
                anchor="nw",
                font=font,
                fill=fill or "black",
            )
        elif kind == "image":
            photo = _photo(canvas, shape, base)
            if photo is not None:
                photos.append(photo)
                canvas.create_image(
                    int(shape.get("x") or 0),
                    int(shape.get("y") or 0),
                    image=photo,
                    anchor="nw",
                )
        else:
            x, y, w, h = _box(shape)
            canvas.create_rectangle(x, y, x + w, y + h, fill=fill, outline=outline or "")
    # Tk drops an image the moment nothing else references it.
    canvas._foolbook_photos = photos


def _box(shape: dict) -> tuple[int, int, int, int]:
    bounds = shape.get("bounds")
    if isinstance(bounds, (list, tuple)) and len(bounds) >= 4:
        return int(bounds[0]), int(bounds[1]), int(bounds[2]), int(bounds[3])
    return (
        int(shape.get("x") or 0),
        int(shape.get("y") or 0),
        int(shape.get("w") or 0),
        int(shape.get("h") or 0),
    )


def _points(shape: dict) -> list[int]:
    flat = []
    for pt in shape.get("points") or []:
        if len(pt) >= 2:
            flat.extend((int(pt[0]), int(pt[1])))
    return flat


def _photo(canvas, shape: dict, base: str | Path | None):
    try:
        import tkinter as tk
    except Exception:
        return None
    try:
        if shape.get("src") and base:
            return tk.PhotoImage(file=str(Path(base) / shape["src"]), master=canvas)
        data = shape.get("data")
        if not data:
            return None
        raw = base64.b64decode(data)
        # PNG and GIF. PhotoImage wants the encoded bytes, not the raw file.
        return tk.PhotoImage(data=base64.b64encode(raw).decode("ascii"), master=canvas)
    except Exception:
        return None
