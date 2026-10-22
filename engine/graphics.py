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
import math
import tkinter as tk
from pathlib import Path

from engine.place import in_front, tighten


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
    shapes = in_front(shapes)
    photos = []
    for shape in shapes:
        kind = (shape.get("kind") or "rect").lower()
        if shape.get("visible") is False:
            continue
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
        elif kind == "arc":
            x, y, w, h = _box(shape)
            ends = shape.get("ends") or []
            if len(ends) >= 2:
                flat = _arc_between(x, y, w, h, ends)
                if len(flat) >= 4:
                    canvas.create_line(*flat, fill=outline or "#ffffff", width=2)
            elif int(shape.get("pattern") or 0) == 0x39:
                flat = _arc_curve(x, y, w, h, shape.get("rays") or [])
                if len(flat) >= 4:
                    canvas.create_line(*flat, fill=outline or "#808080")
            else:
                flat = _arc_pie(x, y, w, h, shape.get("rays") or [])
                if len(flat) >= 6:
                    canvas.create_polygon(*flat, fill=fill, outline=outline or "")
                else:
                    canvas.create_oval(x, y, x + w, y + h, fill=fill, outline=outline or "")
        elif kind == "text":
            x, y, w, h = _box(shape)
            _field_frame(canvas, x, y, w, h, fill, int(shape.get("border") if shape.get("border") is not None else 1))
            pad = 4 if int(shape.get("border") or 1) != 1 else 2
            text, size, wrap, anchor, tx, ty = _fit_text(
                shape, x + pad, y + pad, max(1, w - 2 * pad), max(1, h - 2 * pad)
            )
            ink = outline or "black"
            if fill and _pale(ink) and _pale(fill):
                ink = "#202020"
            face = shape.get("font") or "TkDefaultFont"
            text_kwargs = {}
            if wrap:
                text_kwargs["width"] = wrap
            canvas.create_text(
                tx,
                ty,
                text=text,
                anchor=anchor,
                font=(face, size),
                fill=ink,
                **text_kwargs,
            )
        elif kind == "button":
            x, y, w, h = _box(shape)
            src = shape.get("src") or ""
            path = Path(src)
            if not path.is_file() and base and src:
                path = Path(base) / src
            drawn = False
            if path.is_file():
                try:
                    image = tk.PhotoImage(file=str(path), master=canvas)
                    photos.append(image)
                    canvas.create_image(x, y, image=image, anchor="nw")
                    drawn = True
                except tk.TclError:
                    drawn = False
            if not drawn:
                canvas.create_rectangle(x, y, x + w, y + h, fill=fill or "", outline=outline or "black")
                if shape.get("text"):
                    canvas.create_text(x + 4, y + 2, text=str(shape.get("text")), anchor="nw", fill=fill or "black")
        elif kind == "image":
            photo = _photo(canvas, shape, base)
            if photo is not None:
                photos.append(photo)
                x, y, _w, _h = _box(shape)
                canvas.create_image(x, y, image=photo, anchor="nw")
        else:
            x, y, w, h = _box(shape)
            canvas.create_rectangle(x, y, x + w, y + h, fill=fill, outline=outline or "")
    # Tk drops an image the moment nothing else references it.
    canvas._foolbook_photos = photos


def _field_frame(canvas, x, y, w, h, paper, style):
    """A field's box. 1 is no border. The others are the ToolBook frame styles."""
    if style == 3:
        canvas.create_rectangle(x + 3, y + 3, x + w + 3, y + h + 3, fill="#404040", outline="")
    if paper or style != 1:
        canvas.create_rectangle(x, y, x + w, y + h, fill=paper or "", outline="")
    if style in (0, 2, 3):
        canvas.create_rectangle(x, y, x + w, y + h, outline="#000000")
    elif style == 4:
        _bevel(canvas, x, y, w, h, "#ffffff", "#404040")
    elif style == 5:
        _bevel(canvas, x, y, w, h, "#404040", "#ffffff")


def _bevel(canvas, x, y, w, h, light, dark):
    canvas.create_line(x, y + h, x, y, x + w, y, fill=light)
    canvas.create_line(x + w, y, x + w, y + h, x, y + h, fill=dark)


def _wrapped_rows(text, width, size):
    chars = max(1, int(width / max(1, size * 0.55)))
    rows = 0
    for line in text.split("\n"):
        if not line:
            rows += 1
            continue
        length = 0
        line_rows = 1
        for word in line.split(" "):
            extra = len(word) if length == 0 else len(word) + 1
            if length and length + extra > chars:
                line_rows += 1
                length = len(word)
            else:
                length += extra
        rows += line_rows
    return max(1, rows)


def _pale(color: str) -> bool:
    if not (isinstance(color, str) and len(color) == 7 and color.startswith("#")):
        return False
    red = int(color[1:3], 16)
    green = int(color[3:5], 16)
    blue = int(color[5:7], 16)
    return (red + green + blue) / 3 >= 220


def _fit_text(shape, x, y, w, h):
    """Keep a line inside its box. A tall field wraps. A label does not.

    The wrap width used to be the box, at a fixed 12-point bold. A label
    such as 7400 or INTRODUCTION then broke in the middle of the word.
    """
    raw = tighten(str(shape.get("text") or "").replace("\r\n", "\n").replace("\r", "\n").rstrip("\n"))
    lines = raw.split("\n")
    words = [line for line in lines if line.strip()]
    longest = max((len(line.strip()) for line in words), default=1)
    amount = sum(len(line.strip()) for line in words)
    wrap = w if w > 80 and h > 48 and amount > 40 else 0
    if wrap:
        size = 15
        while size > 8 and _wrapped_rows(raw, w, size) * size * 1.25 > h:
            size -= 1
        return raw, size, w, "nw", x, y
    count = max(1, len(words))
    by_height = ((h - 2) / count / 1.3) if h else 12
    by_width = ((w - 4) / longest / 0.62) if w else 12
    size = int(max(7, min(20, by_height, by_width)))
    align = int(shape.get("align") or 0)
    if align == 2:
        return raw, size, 0, "center", x + w / 2, y + h / 2
    if align == 1:
        return raw, size, 0, "e", x + w, y + h / 2
    return raw, size, 0, "w", x + 2, y + h / 2


def _arc_between(x, y, w, h, ends) -> list[int]:
    """The stroke between two endpoints. The nose is the sweep through the right.

    ToolBook calls Arc, not Pie, so the interior stays empty. Checked on P1140:
    the inside is the page colour and the outline is white.
    """
    if w < 1 or h < 1 or len(ends) < 2:
        return []
    try:
        sx, sy = float(ends[0][0]), float(ends[0][1])
        ex, ey = float(ends[1][0]), float(ends[1][1])
    except (TypeError, IndexError, ValueError):
        return []
    cx, cy = x + w / 2, y + h / 2
    rx, ry = w / 2, h / 2
    start = math.atan2(-(sy - cy), sx - cx)
    stop = math.atan2(-(ey - cy), ex - cx)
    ccw = (stop - start) % (2 * math.pi)
    cw = ccw - 2 * math.pi

    def toward_east(delta):
        mid = math.atan2(math.sin(start + delta / 2), math.cos(start + delta / 2))
        return abs(mid)

    delta = ccw if toward_east(ccw) <= toward_east(cw) else cw
    flat = []
    steps = 40
    for step in range(steps + 1):
        angle = start + delta * step / steps
        flat.append(int(round(cx + rx * math.cos(angle))))
        flat.append(int(round(cy - ry * math.sin(angle))))
    return flat


def _arc_curve(x, y, w, h, rays) -> list[int]:
    """The elliptical curve between two rays, with no return to the centre."""
    pie = _arc_pie(x, y, w, h, rays)
    return pie[2:]


def _arc_pie(x, y, w, h, rays) -> list[int]:
    """The long elliptical sweep of two rays, filled back to the centre.

    The rays are directions, the same pair on every arc of one style.
    Angle zero is east and increases counterclockwise on the page.
    The short turn between the rays is the one that is not drawn.
    """
    if w < 1 or h < 1 or len(rays) < 2:
        return []
    try:
        sx, sy = float(rays[0][0]), float(rays[0][1])
        ex, ey = float(rays[1][0]), float(rays[1][1])
    except (TypeError, IndexError, ValueError):
        return []
    start = math.degrees(math.atan2(-sy, sx))
    end = math.degrees(math.atan2(-ey, ex))
    delta = (end - start) % 360
    if delta < 180:
        delta -= 360
    cx, cy = x + w / 2, y + h / 2
    rx, ry = w / 2, h / 2
    steps = 48
    flat = [int(round(cx)), int(round(cy))]
    for step in range(steps + 1):
        angle = math.radians(start + delta * step / steps)
        flat.append(int(round(cx + rx * math.cos(angle))))
        flat.append(int(round(cy - ry * math.sin(angle))))
    return flat


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


def _fit_image(raw: bytes, width: int, height: int) -> bytes:
    """Stretch a picture to the button. The page scale is applied later, to everything."""
    if width < 2 or height < 2:
        return raw
    try:
        import io
        from PIL import Image
        image = Image.open(io.BytesIO(raw))
        if image.size == (width, height):
            return raw
        image = image.resize((width, height), Image.Resampling.NEAREST)
        out = io.BytesIO()
        image.save(out, "PNG")
        return out.getvalue()
    except Exception:
        return raw


def _photo(canvas, shape: dict, base: str | Path | None):
    """A button picture. The grey matte is transparent, so it must not paint black."""
    try:
        import io
        from PIL import Image, ImageTk
    except Exception:
        return None
    try:
        if shape.get("src") and base:
            image = Image.open(Path(base) / shape["src"])
        else:
            data = shape.get("data")
            if not data:
                return None
            image = Image.open(io.BytesIO(base64.b64decode(data)))
        image = image.convert("RGBA")
        width, height = int(shape.get("w") or 0), int(shape.get("h") or 0)
        if width > 1 and height > 1 and image.size != (width, height):
            image = image.resize((width, height), Image.Resampling.NEAREST)
        return ImageTk.PhotoImage(image, master=canvas)
    except Exception:
        return None
