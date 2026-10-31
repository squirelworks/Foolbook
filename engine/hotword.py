"""A hotword is a span of a field, not a shape of its own.

The click runs that span's buttonClick. A click on the rest of the field
does what it did. The line breaks are the ones graphics._fit_text draws.
"""

from __future__ import annotations

from engine.place import tighten


def hotword_under(shape: dict, x: float, y: float) -> dict | None:
    """The hotword drawn under this point, or nothing.

    ``shape`` is in the same coordinates the point is, at the size it is drawn.
    """
    hits = shape.get("hotwords") or ()
    if not hits or (shape.get("kind") or "") != "text" or shape.get("visible") is False:
        return None
    left, top = float(shape.get("x") or 0), float(shape.get("y") or 0)
    width, height = float(shape.get("w") or 0), float(shape.get("h") or 0)
    if width <= 0 or height <= 0 or not (left <= x <= left + width and top <= y <= top + height):
        return None
    pad_l = int(shape["marginL"]) if shape.get("marginL") is not None else 0
    pad_r = int(shape["marginR"]) if shape.get("marginR") is not None else 0
    text, size, wrap, anchor, tx, ty = _layout(
        shape, left + pad_l, top + 4, max(1, width - pad_l - pad_r), max(1, height - 8)
    )
    sources = _sources(str(shape.get("text") or ""))
    if not text or len(sources) != len(text):
        return None
    measure = lambda sample: _measure(shape, size, sample)
    lines = _wrap(text, wrap, measure) if wrap else text.split("\n")
    if anchor == "nw":
        if y < ty:
            return None
        row = int((y - ty) // _linespace(shape, size))
    else:
        row = 0
    if row < 0 or row >= len(lines):
        return None
    line = lines[row]
    offset = sum(len(lines[index]) + 1 for index in range(row))
    local = x - tx
    if anchor == "e":
        local = x - (tx - measure(line))
    elif anchor == "center":
        local = x - (tx - measure(line) / 2)
    if local < 0:
        return None
    at = len(line)
    for index in range(len(line)):
        if measure(line[: index + 1]) > local:
            at = index
            break
    painted = offset + at
    if painted < 0 or painted >= len(sources):
        return None
    where = sources[painted]
    for hot in hits:
        if int(hot["start"]) <= where < int(hot["end"]) and (hot.get("script") or "").strip():
            return {"name": hot.get("name") or "", "script": hot["script"]}
    return None


def _sources(text: str) -> list[int]:
    """Where each drawn character sits in the field, after the same cuts the painter makes."""
    raw = text.replace("\r\n", "\n").replace("\r", "\n")
    end = len(raw.rstrip("\n"))
    found = []
    index = 0
    while index < end:
        if raw[index] == " ":
            nxt = index
            while nxt < end and raw[nxt] == " ":
                nxt += 1
            if nxt - index >= 3:
                found.append(index)
                index = nxt
                continue
        found.append(index)
        index += 1
    return found


def _wrap(text: str, width: int, measure) -> list[str]:
    """Break on spaces the way a text line does. A word wider than the line stays whole."""
    lines = []
    for para in text.split("\n"):
        if para == "":
            lines.append("")
            continue
        line = ""
        for word in para.split(" "):
            trial = word if line == "" else line + " " + word
            if line and measure(trial) > width:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
    return lines


def _layout(shape, x, y, w, h):
    """The text, size, wrap, anchor and origin graphics._fit_text uses."""
    raw = tighten(str(shape.get("text") or "").replace("\r\n", "\n").replace("\r", "\n").rstrip("\n"))
    size = int(shape.get("size") or 0) or 12
    if w <= 1:
        return raw, size, 0, "nw", x, y
    size = _fit_words(shape, size, w, raw)
    pieces = raw.split("\n")
    widest = max((_measure(shape, size, line) for line in pieces), default=0)
    if len(pieces) > 1 or widest > max(1, w):
        return raw, size, max(1, w), "nw", x, y
    align = _align(shape.get("align"))
    if align == 2:
        return raw, size, 0, "center", x + w / 2, y + h / 2
    if align == 1:
        return raw, size, 0, "e", x + w, y + h / 2
    return raw, size, 0, "w", x, y + h / 2


def _fit_words(shape, size, width, raw):
    if not shape.get("px") or width <= 1:
        return size
    words = [word for word in raw.replace("\n", " ").split(" ") if word]
    if not words:
        return size
    px = abs(int(size))
    while px > 6:
        if max(_measure(shape, px, word) for word in words) <= width + 1:
            return px
        px -= 1
    return px


def _align(value) -> int:
    if isinstance(value, str):
        named = {"left": 0, "right": 1, "center": 2, "centre": 2}
        if value.strip().lower() in named:
            return named[value.strip().lower()]
    try:
        code = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return code if code in (0, 1, 2) else 0


def _measure(shape, size, text) -> int:
    try:
        import tkinter.font as tkfont

        face = shape.get("font") or "TkDefaultFont"
        weight = "bold" if shape.get("bold") else "normal"
        slant = "italic" if shape.get("italic") else "roman"
        font = tkfont.Font(family=face, size=int(size), weight=weight, slant=slant)
        return font.measure(text)
    except Exception:
        return int(len(text) * max(int(size), 1) * 0.55)


def _linespace(shape, size) -> int:
    try:
        import tkinter.font as tkfont

        face = shape.get("font") or "TkDefaultFont"
        font = tkfont.Font(family=face, size=int(size))
        return max(1, int(font.metrics("linespace")))
    except Exception:
        return max(1, int(size))
