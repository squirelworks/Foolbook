"""Extract drawable shapes from a page blob.

Discipline: explicit point lists first.
Deviance: bounds-only records become simple rectangles.
"""

from __future__ import annotations


def extract_shapes(blob: bytes) -> list[dict]:
    """Return a list of shape dicts ready for the viewer.

    Each shape is {"type": "polygon"|"rect", "points": [...], "fill": "#rrggbb"}.
    Points are in twips; the viewer scales them.
    """
    shapes = []
    if not blob:
        return shapes

    # Polygons: kind=0400, count at +0x1A, points at +0x22
    marker = b"\x14\x00\x00"
    idx = 0
    while True:
        i = blob.find(marker, idx)
        if i < 0 or i + 0x30 > len(blob):
            break
        if blob[i + 0x0C:i + 0x0E] == b"\x04\x00":
            from .polygon import gdi_points, read_polygon
            found = read_polygon(blob[i:])
            points = _on_page(blob, i, found)
            if points:
                shapes.append({
                    "type": "polygon",
                    "points": points,
                    "pixels": gdi_points(points),
                    "fill": found["fill"],
                    "pen": found["pen"],
                })
        idx = i + 1

    # Content rectangles: bounds at -16, fill at -4, marker 01 00 00 04
    rect_marker = b"\x01\x00\x00\x04"
    idx = 0
    while True:
        i = blob.find(rect_marker, idx)
        if i < 0 or i + 4 > len(blob):
            break
        if i >= 20:
            vals = [
                int.from_bytes(blob[i - 16 + k:i - 14 + k], "little")
                for k in range(0, 8, 2)
            ]
            if all(0 < v < 15000 for v in vals) and vals[2] > vals[0] and vals[3] > vals[1]:
                from .gdi_shape import rectangle
                fill = _color(blob, i - 4)
                call = rectangle(vals[0], vals[1], vals[2], vals[3], fill=fill)
                shapes.append({
                    "type": "rect",
                    "points": [[vals[0], vals[1]], [vals[2], vals[3]]],
                    "pixels": [
                        [call["box"]["left"], call["box"]["top"]],
                        [call["box"]["right"], call["box"]["bottom"]],
                    ],
                    "fill": fill,
                    "pen": None,
                })
        idx = i + 1

    return shapes


def _on_page(blob: bytes, at: int, found: dict | None) -> list[list[int]] | None:
    """Move a local outline onto the page, or reject it.

    The count word is followed by the page position of the outline's
    top-left, a zero, and then the outline in its own coordinates.
    Every pin of one kind shares that outline, so reading the outline
    as page coordinates stacks them all on one spot. A point list that
    still falls outside a lesson page (9600 by 7200, with a little
    room) is another copy in the same record, or not an outline.
    """
    if not found or found["count"] < 3 or at + 0x22 > len(blob):
        return None
    gap = int.from_bytes(blob[at + 0x20:at + 0x22], "little", signed=True)
    if gap != 0:
        return None
    points = found["points"]
    anchor_x = int.from_bytes(blob[at + 0x1C:at + 0x1E], "little", signed=True)
    anchor_y = int.from_bytes(blob[at + 0x1E:at + 0x20], "little", signed=True)
    origin_x = min(point[0] for point in points)
    origin_y = min(point[1] for point in points)
    moved = [
        [point[0] - origin_x + anchor_x, point[1] - origin_y + anchor_y]
        for point in points
    ]
    xs = [point[0] for point in moved]
    ys = [point[1] for point in moved]
    if min(xs) < -200 or min(ys) < -200 or max(xs) > 11000 or max(ys) > 8000:
        return None
    if max(xs) - min(xs) > 8000 or max(ys) - min(ys) > 8000:
        return None
    return moved


def _color(blob: bytes, off: int) -> str:
    if off + 3 > len(blob) or off < 0:
        return "#c0c0c0"
    # ToolBook stores BGR in the low three bytes of the dword
    b, g, r = blob[off], blob[off + 1], blob[off + 2]
    return f"#{r:02x}{g:02x}{b:02x}"
