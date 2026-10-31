"""Draw the shapes stored on a Foolbook page.

A page carries its own shapes. Coordinates are pixels in the window.
A ToolBook page stream is not a shape source. When a .tbk is open, that
stream is decoded to handler source and the engine runs it.

  rect, ellipse   x, y, w, h, fill, outline
  roundrect       x, y, w, h, fill, outline, radius (default 8)
  arc             x, y, w, h, start, sweep: degrees, zero east, counterclockwise
  pie             the same, filled back to the centre (start 0, sweep 90 when missing)
  chord           the same, closed by the straight line between the two ends
  hotspot         x, y, w, h and an item. Clicked, never drawn.

stroke, when present, is the width of the outline or line in pixels.
  line, polygon   points: [[x, y], ...]
  curve           points: [[x, y], ...], drawn as a polyline through them for now
  text            x, y, text
  image           x, y, and src (a file beside the book) or data (base64 BMP, PNG, or GIF)

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
    caret = None
    for shape in shapes:
        caret = _flush_caret(canvas, caret)
        kind = (shape.get("kind") or "rect").lower()
        if shape.get("visible") is False or kind == "hotspot":
            continue
        fill = shape.get("fill") or ""
        outline = shape["outline"] if "outline" in shape else "black"
        pen = _pen(shape)
        if kind == "polygon":
            flat = _points(shape)
            if len(flat) >= 6:
                canvas.create_polygon(*flat, fill=fill, outline=outline or "", **pen)
        elif kind in ("line", "curve"):
            flat = _points(shape)
            if len(flat) >= 4:
                canvas.create_line(*flat, fill=outline or fill or "black", **pen)
        elif kind == "roundrect":
            x, y, w, h = _box(shape)
            flat = _round_box(x, y, w, h, shape.get("radius"))
            if len(flat) >= 6:
                canvas.create_polygon(*flat, fill=fill, outline=outline or "", **pen)
        elif kind in ("ellipse", "oval"):
            x, y, w, h = _box(shape)
            canvas.create_oval(x, y, x + w, y + h, fill=fill, outline=outline or "", **pen)
        elif kind in ("pie", "chord"):
            x, y, w, h = _box(shape)
            start, sweep = _angles(shape)
            canvas.create_arc(
                x, y, x + w, y + h, start=start, extent=sweep, style="pieslice" if kind == "pie" else "chord", fill=fill, outline=outline or "", **pen
            )
        elif kind == "arc":
            x, y, w, h = _box(shape)
            ends = shape.get("ends") or []
            if shape.get("start") is not None and shape.get("sweep") is not None:
                start, sweep = _angles(shape)
                canvas.create_arc(
                    x, y, x + w, y + h, start=start, extent=sweep, style="arc", outline=outline or "black", **pen
                )
            elif len(ends) >= 2:
                flat = _arc_between(x, y, w, h, ends)
                if len(flat) >= 4:
                    canvas.create_line(*flat, fill=outline or "#ffffff", width=pen.get("width", 2))
            elif int(shape.get("pattern") or 0) == 0x39:
                flat = _arc_curve(x, y, w, h, shape.get("rays") or [])
                if len(flat) >= 4:
                    canvas.create_line(*flat, fill=outline or "#808080", **pen)
            else:
                flat = _arc_pie(x, y, w, h, shape.get("rays") or [])
                if len(flat) >= 6:
                    canvas.create_polygon(*flat, fill=fill, outline=outline or "", **pen)
                else:
                    canvas.create_oval(x, y, x + w, y + h, fill=fill, outline=outline or "", **pen)
        elif kind == "text":
            x, y, w, h = _box(shape)
            if shape.get("focused"):
                caret = (shape, x, y, w, h, len(canvas.find_all()))
            _field_frame(canvas, x, y, w, h, fill, int(shape.get("border") if shape.get("border") is not None else 1))
            pad_l = int(shape["marginL"]) if shape.get("marginL") is not None else 0
            pad_r = int(shape["marginR"]) if shape.get("marginR") is not None else 0
            rest = shape.get("indentRest")
            if rest is not None and int(rest) != pad_l:
                _hanging(canvas, shape, x, y, w, h, pad_l, int(rest), pad_r, fill, outline)
                continue
            if shape.get("runs") and not any(run.get("color") for run in shape["runs"]):
                if _paint_runs(
                    canvas, shape, x + pad_l, y + 4, max(1, w - pad_l - pad_r), max(1, h - 8), fill, outline
                ):
                    continue
            if shape.get("runs"):
                _paint_marked(
                    canvas, shape, x + pad_l, y + 4, max(1, w - pad_l - pad_r), max(1, h - 8), fill, outline
                )
                continue
            text, size, wrap, anchor, tx, ty = _fit_text(
                shape, x + pad_l, y + 4, max(1, w - pad_l - pad_r), max(1, h - 8)
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
                font=_typeface(shape, size),
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
            if not drawn and shape.get("data"):
                photo = _photo(canvas, shape, base)
                if photo is not None:
                    photos.append(photo)
                    canvas.create_image(x, y, image=photo, anchor="nw")
                    drawn = True
            if not drawn:
                canvas.create_rectangle(x, y, x + w, y + h, fill=fill or "", outline=outline or "black")
                if shape.get("text"):
                    ink = "black"
                    if fill and not _pale(fill):
                        ink = "white"
                    canvas.create_text(
                        x + 8, y + h / 2,
                        text=str(shape.get("text")),
                        anchor="w",
                        fill=ink,
                        width=max(1, int(w) - 16),
                    )
        elif kind == "image":
            shown = shape
            face = ""
            if shape.get("invert") and shape.get("invert_data"):
                face = shape["invert_data"]
            elif shape.get("checked") and shape.get("checked_data"):
                face = shape["checked_data"]
            if face:
                shown = dict(shape)
                shown["data"] = face
            photo = _photo(canvas, shown, base)
            if photo is not None:
                photos.append(photo)
                x, y, _w, _h = _box(shape)
                canvas.create_image(x, y, image=photo, anchor="nw")
            elif shape.get("caption"):
                # A sample page names its picture. A ToolBook picture has no caption,
                # so a book that loads is drawn exactly as before.
                x, y, w, h = _box(shape)
                canvas.create_rectangle(x, y, x + w, y + h, outline="#1f3a5f")
                canvas.create_text(
                    x + 8, y + 8,
                    text=str(shape.get("caption")),
                    anchor="nw",
                    fill="#1a1a1a",
                    width=max(1, int(w) - 16),
                )
        else:
            x, y, w, h = _box(shape)
            tiled = _tiled(canvas, shape, w, h, fill, outline)
            if tiled is not None:
                photos.append(tiled)
                canvas.create_image(x, y, image=tiled, anchor="nw")
                fill = ""
            canvas.create_rectangle(x, y, x + w, y + h, fill=fill, outline=outline or "", **pen)
    _flush_caret(canvas, caret)
    # Tk drops an image the moment nothing else references it.
    canvas._foolbook_photos = photos


def _flush_caret(canvas, caret):
    """Draw the caret of the field that has the keyboard, once its text is down."""
    if caret is None:
        return None
    shape, x, y, w, h, started = caret
    boxes = [
        canvas.bbox(item) for item in canvas.find_all()[started:]
        if canvas.type(item) == "text" and canvas.itemcget(item, "text")
    ]
    if boxes:
        top = min(box[1] for box in boxes)
        bottom = max(box[3] for box in boxes)
        at = max(box[2] for box in boxes) + 1
    else:
        top, bottom = y + h * 0.15, y + h * 0.85
        at = x + int(shape.get("marginL") or 0) + 2
    canvas.create_line(at, top, at, bottom, fill="#000000", width=1)
    return None


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


def _pale(color: str) -> bool:
    if not (isinstance(color, str) and len(color) == 7 and color.startswith("#")):
        return False
    red = int(color[1:3], 16)
    green = int(color[3:5], 16)
    blue = int(color[5:7], 16)
    return (red + green + blue) / 3 >= 220


def _hanging(canvas, shape, x, y, w, h, first, rest, right, fill, outline):
    """First line and the lines under it use different left indents.

    One field in this book does that: the P1 title, first line 0 and the
    line under it 650. A single text item cannot say both.
    """
    raw = tighten(str(shape.get("text") or "").replace("\r\n", "\n").replace("\r", "\n").rstrip("\n"))
    size = int(shape.get("size") or 12)
    face = _typeface(shape, size)
    ink = outline or "black"
    if fill and _pale(ink) and _pale(fill):
        ink = "#202020"
    pitch = int(size * 1.25) or size
    try:
        from tkinter import font as tkfont
        measure = tkfont.Font(font=face).measure
    except Exception:
        measure = lambda words: int(len(words) * size * 0.55)
    lines = []
    for para in raw.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        width = max(8, w - (first if not lines else rest) - right)
        line = ""
        for word in para.split(" "):
            trial = f"{line} {word}".strip()
            if line and measure(trial) > width:
                lines.append(line)
                line = word
                width = max(8, w - rest - right)
            else:
                line = trial
        if line:
            lines.append(line)
    for index, line in enumerate(lines):
        inset = first if index == 0 else rest
        canvas.create_text(x + inset, y + 4 + index * pitch, text=line, anchor="nw", font=face, fill=ink)


def _paint_marked(canvas, shape, x, y, w, h, fill, outline):
    """A run can change the colour or the size. The line stays one string.

    On P1040 the letters T, T, L and TTL are yellow, in the field's own
    face. Drawing each colour as its own word opened a gap and pushed
    "family" onto the next line. On P2170 the table is a 10-point run on
    a 12-point field, so the field size is not the size of those words.
    """
    raw = str(shape.get("text") or "").replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    if not raw:
        return
    try:
        from tkinter import font as tkfont
    except Exception:
        return
    field_size = int(shape.get("size") or 12)
    ink = outline or "black"
    if fill and _pale(ink) and _pale(fill):
        ink = "#202020"
    runs = shape.get("runs") or []
    width = max(8, w)
    pitch = max(field_size, round(field_size * 1.2))

    def style_at(index):
        font = shape.get("font") or "TkDefaultFont"
        size = field_size
        bold = bool(shape.get("bold"))
        italic = bool(shape.get("italic"))
        color = ink
        for run in runs:
            if not (int(run.get("start") or 0) <= index < int(run.get("end") or 0)):
                continue
            if run.get("font"):
                font = run["font"]
                size = int(run.get("size") or size)
                bold = bool(run.get("bold"))
                italic = bool(run.get("italic"))
            ch = raw[index] if 0 <= index < len(raw) else ""
            if _draw_font(font, ch, shape.get("font") or "") != font:
                font = shape.get("font") or "TkDefaultFont"
                size = field_size
                bold = bool(shape.get("bold"))
                italic = bool(shape.get("italic"))
            if run.get("color"):
                color = run["color"]
        return font, size, bold, italic, color

    def face_of(font, size, bold, italic):
        return _typeface(
            {"font": font, "size": size, "bold": bold, "italic": italic, "px": shape.get("px")},
            size,
        )

    def piece_width(text, start):
        # One face is one measure. Adding the pieces up counts each
        # letter's side bearing twice, so the line wraps early and a
        # coloured letter lands on top of the next one.
        font, size, bold, italic, _color = style_at(start)
        if all(style_at(start + i)[:4] == (font, size, bold, italic) for i in range(len(text))):
            return tkfont.Font(font=face_of(font, size, bold, italic)).measure(text)
        total = 0
        i = 0
        while i < len(text):
            font, size, bold, italic, _color = style_at(start + i)
            j = i + 1
            while j < len(text) and style_at(start + j)[:4] == (font, size, bold, italic):
                j += 1
            total += tkfont.Font(font=face_of(font, size, bold, italic)).measure(text[i:j])
            i = j
        return total

    def draw(text, start, left, top):
        pen = left
        i = 0
        while i < len(text):
            font, size, bold, italic, _color = style_at(start + i)
            j = i + 1
            while j < len(text) and style_at(start + j)[:4] == (font, size, bold, italic):
                j += 1
            piece = text[i:j]
            face = face_of(font, size, bold, italic)
            measure = tkfont.Font(font=face).measure
            # Separate items leave a gap where one string would not.
            # Pull a letter back to the ink before it when no space
            # belongs in between. A real space is left alone.
            edge = pen
            prev = ""
            k = 0
            while k < len(piece):
                paint = style_at(start + i + k)[4]
                n = k + 1
                while n < len(piece) and style_at(start + i + n)[4] == paint:
                    n += 1
                chunk = piece[k:n]
                at = pen + measure(piece[:k])
                if prev and not prev.endswith(" ") and not chunk.startswith(" ") and at > edge + 1:
                    at = edge + 1
                item = canvas.create_text(
                    at,
                    top + max(0, field_size - size),
                    text=chunk,
                    anchor="nw",
                    font=face,
                    fill=paint,
                )
                box = canvas.bbox(item)
                edge = box[2] if box else at + measure(chunk)
                prev = chunk
                k = n
            pen += measure(piece)
            i = j

    cursor = 0
    top = y
    for para in raw.split("\n"):
        if not para.strip():
            top += pitch
            cursor += len(para) + 1
            continue
        words = para.split(" ")
        line = ""
        line_at = cursor
        taken = 0
        for word in words:
            if not word:
                if not line:
                    line_at = cursor + taken
                line += " "
                taken += 1
                continue
            gap = 0
            while taken + gap < len(para) and para[taken + gap] == " ":
                gap += 1
            trial = f"{line}{' ' * gap}{word}" if line else word
            trial_at = line_at if line else cursor + taken + gap
            if line and piece_width(trial, trial_at) > width:
                draw(line, line_at, x, top)
                top += pitch
                line = word
                line_at = cursor + taken + gap
            else:
                if not line:
                    line_at = cursor + taken + gap
                line = trial
            taken += gap + len(word)
        if line:
            draw(line, line_at, x, top)
        top += pitch
        cursor += len(para) + 1


def _paint_runs(canvas, shape, x, y, w, h, fill, outline) -> bool:
    """A short run keeps its own face. The rest of the line uses the field.

    P900's "* Lesson Exit" is MS Shell Dlg 8 for the star and Arial 12 for
    the words. One face for the whole field made the words 8 point.
    """
    raw = tighten(str(shape.get("text") or "").replace("\r\n", "\n").replace("\r", "\n").rstrip("\n"))
    if not raw or "\n" in raw:
        return False
    try:
        from tkinter import font as tkfont
    except Exception:
        return False
    size = int(shape.get("size") or 12)
    ink = outline or "black"
    if fill and _pale(ink) and _pale(fill):
        ink = "#202020"
    pieces = []
    cursor = 0
    for run in sorted(shape.get("runs") or [], key=lambda item: int(item.get("start") or 0)):
        start = max(0, int(run.get("start") or 0))
        end = min(len(raw), int(run.get("end") or 0))
        if end <= start or start < cursor:
            continue
        if start > cursor:
            pieces.append((raw[cursor:start], None))
        pieces.append((raw[start:end], run))
        cursor = end
    if cursor < len(raw):
        pieces.append((raw[cursor:], None))
    if not any(run for _text, run in pieces):
        return False
    prepared = []
    total = 0
    for text, run in pieces:
        if not text:
            continue
        span = dict(shape)
        span_size = size
        if run:
            span["font"] = run.get("font") or shape.get("font")
            span_size = int(run.get("size") or size)
            span["size"] = span_size
            span["bold"] = bool(run.get("bold"))
            span["italic"] = bool(run.get("italic"))
            if text and _draw_font(span["font"], text[0], shape.get("font") or "") != span["font"]:
                span["font"] = shape.get("font") or span["font"]
                span_size = size
                span["size"] = span_size
                span["bold"] = bool(shape.get("bold"))
                span["italic"] = bool(shape.get("italic"))
        face = _typeface(span, span_size)
        wide = tkfont.Font(font=face).measure(text)
        prepared.append((text, face, span_size, (run or {}).get("color") or ink, wide))
        total += wide
    # A line that does not fit has to wrap. One row is how the score ran off.
    if total > w + 2:
        return False
    at = x
    edge = x
    prev = ""
    for text, face, span_size, paint, wide in prepared:
        if prev and not prev.endswith(" ") and not text.startswith(" ") and at > edge + 1:
            at = edge + 1
        item = canvas.create_text(at, y + max(0, size - span_size), text=text, anchor="nw", font=face, fill=paint)
        box = canvas.bbox(item)
        edge = box[2] if box else at + wide
        at += wide
        prev = text
    return True


_SYMBOL_FONTS = {"wingdings", "wingdings 2", "wingdings 3", "webdings", "symbol"}


def _draw_font(font: str, char: str, fallback: str) -> str:
    """A symbol face cannot draw a character that is already Unicode.

    The export stores the bullet as • and leaves the face as Wingdings.
    Wingdings has no such character, so the window draws the wrong mark.
    """
    if (font or "").strip().lower() not in _SYMBOL_FONTS:
        return font
    if char and ord(char) > 255:
        return fallback or font
    return font
_FONTS = {}
_FACTOR = None
# Liberation Sans Bold at 16px, the Arial metrics ToolBook uses.
# "INTRODUCTION" advances 123 pixels there. A desktop face that draws
# wider is divided back down to this, or the P400 labels break mid-word.
_PROBE = "INTRODUCTION"
_PROBE_PX = 123


def _family(requested):
    name = (requested or "").strip()
    key = name.lower()
    if key not in ("", "arial", "helvetica", "ms sans serif", "ms shell dlg", "tahoma"):
        return name or "TkDefaultFont"
    try:
        from tkinter import font as tkfont
        have = {item.lower() for item in tkfont.families()}
    except Exception:
        return name or "TkDefaultFont"
    for face in ("Liberation Sans", "Nimbus Sans", "FreeSans", "Arial", "DejaVu Sans"):
        if face.lower() in have:
            return face
    return name or "TkDefaultFont"


def _ink_factor():
    """How much wider the face Tk actually draws is than Arial at 16px.

    One on a machine whose Arial matches the book. More than one where the
    desktop enlarges the face, which is what splits the P400 labels.
    """
    global _FACTOR
    if _FACTOR is not None:
        return _FACTOR
    _FACTOR = 1.0
    try:
        from tkinter import font as tkfont
        got = tkfont.Font(family=_family("Arial"), size=-16, weight="bold").measure(_PROBE)
        if got:
            _FACTOR = got / _PROBE_PX
        if not 0.5 <= _FACTOR <= 3:
            _FACTOR = 1.0
    except Exception:
        _FACTOR = 1.0
    return _FACTOR


def _typeface(shape, size):
    face = _family(shape.get("font") or "")
    # The caller may already have shrunk this so the longest word fits.
    # The recorded size is the fallback, not a replacement for that.
    if not size:
        size = int(shape.get("size") or 0) or 12
    # A placed field stores pixels. A negative Tk size is pixels. The
    # factor puts that pixel size back onto Arial's width.
    if shape.get("px"):
        size = -max(1, int(round(abs(int(size)) / _ink_factor())))
    weight = "bold" if shape.get("bold") else "normal"
    slant = "italic" if shape.get("italic") else "roman"
    key = (face, int(size), weight, slant)
    found = _FONTS.get(key)
    if found is not None:
        return found
    try:
        from tkinter import font as tkfont
        found = tkfont.Font(family=face, size=int(size), weight=weight, slant=slant)
        _FONTS[key] = found
        return found
    except Exception:
        style = " ".join(part for part in ("bold" if weight == "bold" else "", "italic" if slant == "italic" else "") if part)
        if style:
            return (face, size, style)
        return (face, size)


def _text_width(shape, size, text) -> int:
    try:
        from tkinter import font as tkfont
        return tkfont.Font(font=_typeface(shape, size)).measure(text)
    except Exception:
        return int(len(text) * max(int(size), 1) * 0.55)


def _fit_words(shape, size, width, raw):
    """The longest word has to sit on one line. A 10-point label is only
    as wide as the word, so a face that is a pixel too wide breaks "Output"
    into "Out" and "put".
    """
    if not shape.get("px") or width <= 1:
        return size
    words = [word for word in raw.replace("\n", " ").split(" ") if word]
    if not words:
        return size
    px = abs(int(size))
    while px > 6:
        trial = dict(shape)
        trial["size"] = px
        if max(_text_width(trial, px, word) for word in words) <= width + 1:
            return px
        px -= 1
    return px


def _fit_text(shape, x, y, w, h):
    """Keep the words inside the box they were given.

    The size is already the window size. A line that is wider than the box
    wraps on its spaces. A line that fits, such as a short label, stays one
    line so it is not broken in the middle of a word.
    """
    raw = tighten(str(shape.get("text") or "").replace("\r\n", "\n").replace("\r", "\n").rstrip("\n"))
    recorded = int(shape.get("size") or 0)
    size = recorded or 12
    # A title stored with no field. Wrapping it at one pixel stacks the letters.
    if w <= 1:
        return raw, size, 0, "nw", x, y
    size = _fit_words(shape, size, w, raw)
    pieces = raw.split("\n")
    widest = max((_text_width(shape, size, line) for line in pieces), default=0)
    if len(pieces) > 1 or widest > max(1, w):
        return raw, size, max(1, w), "nw", x, y
    words = [line for line in pieces if line.strip()]
    count = max(1, len(words))
    align = int(shape.get("align") or 0)
    if align == 2:
        return raw, size, 0, "center", x + w / 2, y + h / 2
    if align == 1:
        return raw, size, 0, "e", x + w, y + h / 2
    return raw, size, 0, "w", x, y + h / 2


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


def _angles(shape: dict, start: float = 0.0, sweep: float = 90.0) -> tuple[float, float]:
    """Start angle and sweep in degrees. Zero is east and a positive sweep turns counterclockwise."""
    try:
        start = float(shape.get("start") if shape.get("start") is not None else start)
        sweep = float(shape.get("sweep") if shape.get("sweep") is not None else sweep)
    except (TypeError, ValueError):
        pass
    return start, sweep


def _pen(shape: dict) -> dict:
    """The outline width the shape asks for. Nothing when it names none, so Tk keeps its 1."""
    if shape.get("stroke") is None:
        return {}
    try:
        return {"width": max(0.0, float(shape["stroke"]))}
    except (TypeError, ValueError):
        return {}


def _round_box(x, y, w, h, radius=None) -> list[float]:
    """A rectangle whose corners are quarter circles. The radius is clamped to half the short side."""
    if w < 1 or h < 1:
        return []
    r = 8.0 if radius is None else max(0.0, float(radius))
    r = min(r, w / 2, h / 2)
    if r <= 0:
        return [x, y, x + w, y, x + w, y + h, x, y + h]
    steps = 6
    flat = []
    # Corner centres, clockwise from top left, with the angle each quarter starts at.
    for cx, cy, start in (
        (x + r, y + r, 180),
        (x + w - r, y + r, 270),
        (x + w - r, y + h - r, 0),
        (x + r, y + h - r, 90),
    ):
        for step in range(steps + 1):
            angle = math.radians(start + 90 * step / steps)
            flat.append(cx + r * math.cos(angle))
            flat.append(cy + r * math.sin(angle))
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


def _tiled(canvas, shape: dict, w: int, h: int, fill: str, outline: str):
    """The shape's 8 by 8 pattern, repeated to its size. None when it has none."""
    from engine import patterns
    grid = patterns.pixels(shape.get("tile"), outline or "#000000", fill or "#ffffff", shape.get("cell") or 1)
    if not grid or w < 1 or h < 1:
        return None
    tile = tk.PhotoImage(master=canvas, width=len(grid[0]), height=len(grid))
    tile.put(" ".join("{" + " ".join(line) + "}" for line in grid))
    photo = tk.PhotoImage(master=canvas, width=int(w), height=int(h))
    photo.tk.call(photo, "copy", tile, "-to", 0, 0, int(w), int(h))
    return photo


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
        if shape.get("transparent"):
            from engine.loader import _matte
            _matte(image)
        elif shape.get("edge"):
            from engine.loader import _clear_edge
            _clear_edge(image)
        width, height = int(shape.get("w") or 0), int(shape.get("h") or 0)
        if width > 1 and height > 1 and image.size != (width, height):
            image = image.resize((width, height), Image.Resampling.NEAREST)
        return ImageTk.PhotoImage(image, master=canvas)
    except Exception:
        return None
