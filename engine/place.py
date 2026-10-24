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

    def rank(item):
        index, shape = item
        if shape.get("kind") == "text":
            return (2, 0, index)
        cover = sum(1 for picture in pictures if picture is not shape and holds(picture, shape))
        return (1 if cover else 0, cover, index)

    return [shape for _index, shape in sorted(enumerate(shapes), key=rank)]


def tighten(text: str) -> str:
    """Drop the padding a justified line stored as a run of spaces."""
    import re
    return re.sub(r" {3,}", " ", text)


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
        # pixels, or it would apply 96/72 a second time.
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
