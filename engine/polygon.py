"""Class 0x10 irregular polygon, measured on 9e954d01.tbk.

The class word ``10 00`` is the two bytes before the body.

  body+0x0F   page bounds, four signed words: left, top, right, bottom
  body+0x1B   fill, three bytes, red then green then blue
  body+0x22   kind word ``04 00``
  body+0x25   pattern byte. ``0xFE`` is a solid fill. ``0xFD`` is none.
  body+0x30   vertex count
  body+0x36   zero on every polygon in the specimen book
  body+0x38   ``count`` pairs of signed words, the outline in its own coordinates

Pins share one outline and the bounds are the same size, so placement is a
translation. A house outline is larger than its bounds, so the outline's
own extent is scaled into that rectangle. The bytes at body+0x26 are not a
source rectangle.
"""

from __future__ import annotations

CLASS = b"\x10\x00"
KIND = b"\x04\x00"
TWIPS_PER_INCH = 0x5A0
HALF_TWIP = 0x2D0

BOUNDS_AT = 0x11
COLOR_AT = 0x1D
KIND_AT = 0x24
PATTERN_AT = 0x27
COUNT_AT = 0x32
GAP_AT = 0x38
POINTS_AT = 0x3A
PATTERN_NONE = 0xFD
PATTERN_SOLID = 0xFE


def to_pixel(twip: int, dpi: int = 96) -> int:
    """One page-unit coordinate to one device pixel."""
    value = twip * dpi + HALF_TWIP
    if value < 0:
        value -= TWIPS_PER_INCH
    if value < 0:
        return -((-value) // TWIPS_PER_INCH)
    return value // TWIPS_PER_INCH


def gdi_points(pairs: list[tuple[int, int]], dpi: int = 96) -> list[list[int]]:
    """The ``POINT`` array ``Polygon`` is given."""
    return [[to_pixel(x, dpi), to_pixel(y, dpi)] for x, y in pairs]


def _i16(record: bytes, offset: int) -> int:
    return int.from_bytes(record[offset:offset + 2], "little", signed=True)


def on_bounds(points: list[tuple[int, int]], bounds: tuple[int, int, int, int]) -> list[list[int]]:
    """Map an outline's own extent onto the page rectangle."""
    left, top, right, bottom = bounds
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    span_x = maxx - minx
    span_y = maxy - miny
    width = right - left
    height = bottom - top
    placed = []
    for x, y in points:
        page_x = left if span_x == 0 else left + (x - minx) * width / span_x
        page_y = top if span_y == 0 else top + (y - miny) * height / span_y
        placed.append([int(round(page_x)), int(round(page_y))])
    return placed


def read_polygon(record: bytes, dpi: int = 96) -> dict | None:
    """One class ``0x10`` record to one polygon on the page.

    ``points`` are page units. ``pixels`` is what GDI gets. ``pen`` is None.
    A pattern of ``0xFD`` has no fill. Any other pattern uses the record RGB;
    the 8x8 tile is not applied here.
    """
    if len(record) < POINTS_AT + 4 or record[:2] != CLASS:
        return None
    if record[KIND_AT:KIND_AT + 2] != KIND:
        return None
    if int.from_bytes(record[GAP_AT:GAP_AT + 2], "little") != 0:
        return None
    count = int.from_bytes(record[COUNT_AT:COUNT_AT + 2], "little")
    if count < 3 or POINTS_AT + count * 4 > len(record):
        return None
    bounds = tuple(_i16(record, BOUNDS_AT + step) for step in range(0, 8, 2))
    if bounds[2] <= bounds[0] or bounds[3] <= bounds[1]:
        return None
    pairs = [(_i16(record, POINTS_AT + j * 4), _i16(record, POINTS_AT + j * 4 + 2)) for j in range(count)]
    if any(abs(coord) > 0x7FFF for pair in pairs for coord in pair):
        return None
    red, green, blue = record[COLOR_AT], record[COLOR_AT + 1], record[COLOR_AT + 2]
    pattern = record[PATTERN_AT]
    fill = None if pattern == PATTERN_NONE else f"#{red:02x}{green:02x}{blue:02x}"
    points = on_bounds(pairs, bounds)
    return {
        "count": count,
        "bounds": list(bounds),
        "points": points,
        "pixels": gdi_points([(point[0], point[1]) for point in points], dpi),
        "fill": fill,
        "pattern": pattern,
        "pen": None,
    }
