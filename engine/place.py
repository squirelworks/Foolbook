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
