"""Put each object in the window where its bounds say it goes.

A live object stores left, top, right, bottom as twips. The page records
we can read store the same four numbers, either as a rectangle or as the
extent of a point list. Parent offsets are not applied. The assumption is
that these twips are already the page position.

The window origin is twip ``0, 0``. A negative bound is shifted in so it
stays on the canvas. A positive bound is not pulled back to the first
object: empty page to the left of it is part of the page.
"""

from __future__ import annotations

from engine.polygon import to_pixel

MARGIN = 8


def in_front(shapes: list[dict]) -> list[dict]:
    """A frame is painted under the button and the words that sit on it.

    The file lists P300's equipment bar before the frame, so the frame
    covered it. Anything a picture contains is drawn after that picture.
    """
    def box(shape):
        return (
            float(shape.get("x") or 0),
            float(shape.get("y") or 0),
            float(shape.get("w") or 0),
            float(shape.get("h") or 0),
        )

    def holds(outer, inner) -> bool:
        ox, oy, ow, oh = box(outer)
        ix, iy, iw, ih = box(inner)
        return ow * oh > iw * ih and ox <= ix and oy <= iy and ox + ow >= ix + iw and oy + oh >= iy + ih

    pictures = [shape for shape in shapes if shape.get("kind") == "image"]

    def covers_drawing(shape) -> bool:
        # A filled field that holds the pins is the back of the chip.
        # Putting every text field in front covered P1290.
        if (shape.get("kind") or "") != "text":
            return False
        for other in shapes:
            if other is shape or (other.get("kind") or "") == "text":
                continue
            if holds(shape, other):
                return True
        return False

    def rank(item):
        index, shape = item
        if shape.get("kind") == "text" and not covers_drawing(shape):
            return (2, 0, index)
        cover = sum(1 for picture in pictures if picture is not shape and holds(picture, shape))
        return (1 if cover else 0, cover, index)

    return [shape for _index, shape in sorted(enumerate(shapes), key=rank)]


def _contains(shape, x: float, y: float) -> bool:
    left, top = float(shape.get("x") or 0), float(shape.get("y") or 0)
    return left <= x <= left + float(shape.get("w") or 0) and top <= y <= top + float(shape.get("h") or 0)


def _paper(shape) -> bool:
    """The page fill is the paper, not a control."""
    return (
        (shape.get("kind") or "") == "rect"
        and float(shape.get("w") or 0) > 500
        and float(shape.get("h") or 0) > 400
        and not (shape.get("script") or shape.get("item"))
    )


def shapes_at(shapes, x: float, y: float) -> list:
    """Front to back, the objects under this page point."""
    found = []
    for shape in reversed(in_front(shapes)):
        if shape.get("visible") is False or _paper(shape):
            continue
        if _contains(shape, x, y):
            found.append(shape)
    return found


def click_target(shapes, x: float, y: float):
    """The object a click runs.

    "- Begin" is a field with no buttonClick of its own. The click is
    the button underneath. A field that handles the click keeps it.
    """
    found = shapes_at(shapes, x, y)
    if not found:
        return None
    top = found[0]
    script = top.get("script") or ""
    if (top.get("kind") or "") == "text" and "buttonclick" not in script.lower():
        # The words drawn on a Foolbook button are not the control. The
        # button under them is. A ToolBook word stays, unless a buttonClick
        # is what the click was for.
        button = None
        for shape in found[1:]:
            if "buttonclick" in (shape.get("script") or "").lower():
                return shape
            if button is None and shape.get("item") and (shape.get("kind") or "") == "button":
                button = shape
        if button is not None:
            return button
    return top


def plain_page(text, items=None, quiz=None) -> list[dict]:
    """A book that stored words and buttons, not ToolBook shapes.

    The page paints its own paper, so the previous page does not stay
    on the window. The words are a title and a body. The buttons sit
    under the words.
    """
    lines = [str(line).strip() for line in text or [] if str(line).strip()]
    title = lines[0] if lines else ""
    body = lines[1:]
    width = 760
    margin = 28
    inner = width - margin * 2
    y = 28
    shapes = []
    if title:
        shapes.append(_words(title, margin, y, inner, 40, 18))
        y += 48
    if body:
        block = "\n\n".join(body)
        rows = 0
        for line in body:
            rows += max(1, (len(line) + 64) // 65) + 1
        height = max(56, rows * 20)
        shapes.append(_words(block, margin, y, inner, height, 13))
        y += height + 18
    quiz = quiz or {}
    for choice in quiz.get("choices") or []:
        label = str(choice.get("label") or "").strip()
        if not label:
            continue
        rows = max(1, (len(label) + 54) // 55)
        height = max(36, rows * 18 + 14)
        target = quiz.get("next") if choice.get("correct") else quiz.get("again")
        shapes.append({
            "kind": "button",
            "name": label,
            "text": label,
            "x": margin,
            "y": y,
            "w": inner,
            "h": height,
            "fill": "#f3f3f3",
            "outline": "#222222",
            "item": {"label": label, "page": target or "", "correct": bool(choice.get("correct"))},
            "visible": True,
        })
        y += height + 10
    if shapes and (items or []):
        y += 8
    x = margin
    row_h = 34
    for item in items or []:
        label = str(item.get("label") or item.get("page") or "Go")
        wide = max(96, min(inner, 8 * len(label) + 28))
        if x > margin and x + wide > width - margin:
            x = margin
            y += row_h + 8
        shapes.append({
            "kind": "button",
            "name": label,
            "text": label,
            "x": x,
            "y": y,
            "w": wide,
            "h": row_h,
            "fill": "#f7f7f7",
            "outline": "#222222",
            "item": item,
            "visible": True,
        })
        x += wide + 12
    if items:
        y += row_h
    height = max(560, y + 28)
    paper = {
        "kind": "rect",
        "name": "paper",
        "x": 0,
        "y": 0,
        "w": width,
        "h": height,
        "fill": "#ffffff",
        "outline": "",
        "visible": True,
    }
    return [paper, *shapes]


def _words(text, x, y, w, h, size) -> dict:
    return {
        "kind": "text",
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "text": text,
        "size": size,
        "border": 1,
        "fill": "",
        "outline": "#1a1a1a",
        "visible": True,
    }


def blank_book_lines(lines, book_name: str = "") -> list[dict]:
    """Words for a page that stored text and no shapes.

    The core nida81 stub is that kind of page. A white window is how a
    missing nida81.tbk looks. The words are what the stub actually has.
    """
    words = [str(line).strip() for line in lines or [] if str(line).strip()]
    if not words:
        return []
    shapes = []
    y = 16
    if str(book_name).lower().endswith("nida81.fsk"):
        shapes.append({
            "kind": "text",
            "x": 24,
            "y": y,
            "w": 640,
            "h": 36,
            "text": "nida81.fbk is not beside the lesson. This page has the words only.",
            "size": 12,
        })
        y = 56
    for line in words:
        shapes.append({
            "kind": "text",
            "x": 24,
            "y": y,
            "w": 640,
            "h": 80,
            "text": line,
            "size": 12,
        })
        y += 88
    return shapes


def tighten(text: str) -> str:
    """Drop the padding a justified line stored as a run of spaces."""
    import re
    return re.sub(r" {3,}", " ", text)


def clip_to_page(shapes, width: float, height: float) -> list[dict]:
    """A field may be stored past the page. ToolBook clips it when it draws.

    The P0 copyright box ends at 9638 twips on a page that is 9360 wide,
    so the words run off the right edge. The box stops at the page.
    """
    if not width or not height:
        return shapes
    clipped = []
    for shape in shapes:
        item = dict(shape)
        if item.get("kind") == "text":
            x = float(item.get("x") or 0)
            y = float(item.get("y") or 0)
            if x < width:
                item["w"] = min(float(item.get("w") or 0), width - x)
            if y < height:
                item["h"] = min(float(item.get("h") or 0), height - y)
        clipped.append(item)
    return clipped


def opening_size(screen_w: int, screen_h: int, saved: tuple[int, int] | None = None) -> tuple[int, int]:
    """How big the reader opens.

    The page is about 624 by 442. Stopping the window there made every
    course a postage stamp. Most of the screen, once, and a resize is
    remembered for the next book.
    """
    screen_w = max(1, int(screen_w))
    screen_h = max(1, int(screen_h))
    if saved:
        width, height = int(saved[0]), int(saved[1])
        return (
            max(640, min(width, screen_w - 16)),
            max(480, min(height, max(480, screen_h - 40))),
        )
    width = max(960, min(screen_w - 48, int(screen_w * 0.78)))
    height = max(640, min(screen_h - 64, int(screen_h * 0.78)))
    if screen_w < 1100:
        width = max(640, screen_w - 24)
    if screen_h < 760:
        height = max(480, screen_h - 48)
    return width, height


def fit_view(box, width: int, height: int, margin: int = 12):
    """Scale a drawing so it sits inside the window, and center it.

    ``box`` is ``(x0, y0, x1, y1)`` in the coordinates the shapes were drawn
    in. The scale is applied about ``(x0, y0)``. ``dx`` and ``dy`` then move
    that corner. ``ox`` and ``oy`` are where it lands, which is what a click
    turns back into a page coordinate.
    """
    x0, y0, x1, y1 = box
    pw = max(1, x1 - x0)
    ph = max(1, y1 - y0)
    avail_w = max(1, width - 2 * margin)
    avail_h = max(1, height - 2 * margin)
    scale = min(avail_w / pw, avail_h / ph)
    ox = (width - pw * scale) / 2
    oy = (height - ph * scale) / 2
    return scale, ox - x0, oy - y0, ox, oy


def page_box(page, shapes) -> tuple[float, float, float, float]:
    """The window shows the page, not the bounding box of whatever is on it.

    ToolBook sizes the viewer to the page. A second book uses the same
    rectangle, so a stray object cannot shrink or slide the whole page.
    """
    size = ((getattr(page, "raw", None) or {}).get("size") if page is not None else None) or ()
    if len(size) >= 2 and size[0] and size[1]:
        return (0.0, 0.0, float(size[0]), float(size[1]))
    return content_box(shapes)


def content_box(shapes) -> tuple[float, float, float, float]:
    """The bounds the window scales. Glyphs that spill a field do not count."""
    left = top = right = bottom = None
    for shape in shapes:
        xs: list[float] = []
        ys: list[float] = []
        if shape.get("w"):
            x = float(shape.get("x") or 0)
            y = float(shape.get("y") or 0)
            xs += [x, x + float(shape["w"])]
            ys += [y, y + float(shape.get("h") or 0)]
        for pt in list(shape.get("points") or []) + list(shape.get("ends") or []):
            if len(pt) >= 2:
                xs.append(float(pt[0]))
                ys.append(float(pt[1]))
        if not xs:
            continue
        lo_x, hi_x = min(xs), max(xs)
        lo_y, hi_y = min(ys), max(ys)
        left = lo_x if left is None else min(left, lo_x)
        top = lo_y if top is None else min(top, lo_y)
        right = hi_x if right is None else max(right, hi_x)
        bottom = hi_y if bottom is None else max(bottom, hi_y)
    if left is None:
        return (0.0, 0.0, 1.0, 1.0)
    return (left, top, right, bottom)


def place_window(shapes, scale: float, x0: float, y0: float, dx: float, dy: float):
    """Page pixels to window pixels.

    ``scale`` multiplies every bound. ``(x0, y0)`` is the point the scale
    is about, and ``(dx, dy)`` is the offset that then centres the page.
    Pictures and text go through the same numbers, which a canvas scale
    does not: Tk moves an image and leaves its pixels, and it leaves the
    font alone.
    """

    def mx(value):
        return (float(value) - x0) * scale + x0 + dx

    def my(value):
        return (float(value) - y0) * scale + y0 + dy

    placed = []
    for shape in shapes:
        item = dict(shape)
        if "x" in shape or shape.get("w"):
            item["x"] = mx(shape.get("x") or 0)
            item["y"] = my(shape.get("y") or 0)
            item["w"] = float(shape.get("w") or 0) * scale
            item["h"] = float(shape.get("h") or 0) * scale
        if shape.get("tile"):
            item["cell"] = max(1, int(round(scale)))
        if shape.get("points"):
            item["points"] = [
                [mx(pt[0]), my(pt[1])] for pt in shape["points"] if len(pt) >= 2
            ]
        if shape.get("ends"):
            item["ends"] = [
                [mx(pt[0]), my(pt[1])] for pt in shape["ends"] if len(pt) >= 2
            ]
        # The book stores points. ToolBook draws them at 96 dpi, so 12 point
        # is 16 pixels. The window scale multiplies that once. Tk is given
        # pixels, or it would apply 96/72 a second time. Measured on the
        # real viewer: the glyph rows stay within 3% of ToolBook at every
        # window size, and Tk's own scaling does not add to a negative size.
        if shape.get("kind") == "text" or shape.get("size"):
            recorded = float(shape.get("size") or 12)
            item["size"] = max(1, int(round(recorded * scale * 96 / 72)))
            item["px"] = True
        if shape.get("runs"):
            scaled = []
            for run in shape["runs"]:
                item_run = dict(run)
                # A colour run has no size of its own. Inventing one hid the
                # 10-point runs on the P2170 table.
                if run.get("size"):
                    item_run["size"] = max(1, int(round(float(run["size"]) * scale * 96 / 72)))
                scaled.append(item_run)
            item["runs"] = scaled
        if shape.get("radius"):
            item["radius"] = float(shape["radius"]) * scale
        for key in ("marginL", "marginR", "indentRest"):
            if shape.get(key):
                item[key] = int(round(float(shape[key]) * scale))
        placed.append(item)
    return placed


def bounds_twips(shape: dict) -> tuple[int, int, int, int]:
    if shape.get("bounds"):
        left, top, right, bottom = shape["bounds"]
        return int(left), int(top), int(right), int(bottom)
    points = shape.get("points") or []
    if shape.get("type") == "rect" and len(points) == 2:
        return points[0][0], points[0][1], points[1][0], points[1][1]
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def place_page(shapes: list[dict], dpi: int = 96) -> dict:
    """Return the window size and each shape with window pixels."""
    if not shapes:
        return {"width": 0, "height": 0, "shapes": []}
    boxes = [bounds_twips(s) for s in shapes]
    origin_x = min(0, min(b[0] for b in boxes))
    origin_y = min(0, min(b[1] for b in boxes))

    def px(value: int, origin: int) -> int:
        return to_pixel(value, dpi) - to_pixel(origin, dpi)

    placed = []
    far_x = 0
    far_y = 0
    for shape, box in zip(shapes, boxes):
        left, top, right, bottom = box
        x = px(left, origin_x) + MARGIN
        y = px(top, origin_y) + MARGIN
        w = max(px(right, origin_x) - px(left, origin_x), 1)
        h = max(px(bottom, origin_y) - px(top, origin_y), 1)
        item = dict(shape)
        item["bounds"] = [left, top, right, bottom]
        item["at"] = [x, y, w, h]
        points = shape.get("points") or []
        if points and shape.get("type") != "rect":
            item["pixels"] = [[px(p[0], origin_x) + MARGIN, px(p[1], origin_y) + MARGIN] for p in points]
        else:
            item["pixels"] = [[x, y], [x + w, y + h]]
        placed.append(item)
        far_x = max(far_x, x + w)
        far_y = max(far_y, y + h)
    return {
        "width": far_x + MARGIN,
        "height": far_y + MARGIN,
        "shapes": placed,
    }
