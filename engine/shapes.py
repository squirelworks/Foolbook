"""Extract drawable shapes from a page blob.

An irregular polygon is a class ``0x10`` record. Its outline is mapped
onto the bounds stored in that record. A content rectangle is still the
``01 00 00 04`` marker.
"""

from __future__ import annotations


def extract_shapes(blob: bytes) -> list[dict]:
    """Return a list of shape dicts ready for the viewer.

    Each shape is {"type": "polygon"|"rect", "points": [...], "fill": "#rrggbb"}.
    Points are page units. The viewer scales them.
    """
    shapes = []
    if not blob:
        return shapes

    from .polygon import POINTS_AT, read_polygon

    idx = 0
    taken = 0
    while True:
        i = blob.find(b"\x10\x00", idx)
        if i < 0:
            break
        if i < taken:
            idx = i + 1
            continue
        found = read_polygon(blob[i:])
        if found:
            shapes.append({
                "type": "polygon",
                "points": found["points"],
                "bounds": found["bounds"],
                "pixels": found["pixels"],
                "fill": found["fill"],
                "pen": found["pen"],
                "pattern": found["pattern"],
            })
            taken = i + POINTS_AT + found["count"] * 4
            idx = taken
            continue
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


def _color(blob: bytes, off: int) -> str:
    if off + 3 > len(blob) or off < 0:
        return "#c0c0c0"
    # This marker's color dword is still read as stored by the 1.0.1 rectangle scan.
    b, g, r = blob[off], blob[off + 1], blob[off + 2]
    return f"#{r:02x}{g:02x}{b:02x}"
