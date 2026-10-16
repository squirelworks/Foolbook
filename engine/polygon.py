"""ToolBook polygon record, translated into a GDI ``Polygon`` call.

The record, measured from the ``14 00 00`` marker the page scan finds:

  +0x04  fill dword, BGR in the low three bytes
  +0x0C  kind word ``04 00``
  +0x1A  count
  +0x22  ``count`` pairs of signed twips

``Polygon`` wants a count and an array of ``POINT {int x, int y}`` in the
device context's units, and it uses the pen and brush already selected.
This record has a fill. It has no pen.

``FUN_1008_01dd`` does the unit change. For each coordinate:

    (coord * dpi + 720) / 1440

720 is half of 1440, so a positive value rounds to the nearest pixel.
A negative sum subtracts another 1440 before the divide, which is what
that function does. At 96 DPI this matches dividing by 15 for the values
that come out whole. The divide-by-15 in the viewer was that special
case, done in floating point.

This is that conversion. It is not ``FUN_1408_0376``.
"""

from __future__ import annotations

KIND = b"\x04\x00"
TWIPS_PER_INCH = 0x5A0
HALF_TWIP = 0x2D0
FILL_AT = 0x04
KIND_AT = 0x0C
COUNT_AT = 0x1A
POINTS_AT = 0x22


def to_pixel(twip: int, dpi: int = 96) -> int:
    """One twip coordinate to one device pixel."""
    value = twip * dpi + HALF_TWIP
    if value < 0:
        value -= TWIPS_PER_INCH
    if value < 0:
        return -((-value) // TWIPS_PER_INCH)
    return value // TWIPS_PER_INCH


def gdi_points(pairs: list[tuple[int, int]], dpi: int = 96) -> list[list[int]]:
    """The ``POINT`` array ``Polygon`` is given."""
    return [[to_pixel(x, dpi), to_pixel(y, dpi)] for x, y in pairs]


def read_polygon(record: bytes, dpi: int = 96) -> dict | None:
    """One record to one ``Polygon`` call.

    ``points`` are the file pairs, in twips. ``pixels`` is what GDI gets.
    ``pen`` is None because this record does not hold one.
    """
    if len(record) < POINTS_AT + 4:
        return None
    if record[KIND_AT:KIND_AT + 2] != KIND:
        return None
    count = int.from_bytes(record[COUNT_AT:COUNT_AT + 2], "little")
    if count < 2 or POINTS_AT + count * 4 > len(record):
        return None
    pairs: list[tuple[int, int]] = []
    for j in range(count):
        base = POINTS_AT + j * 4
        x = int.from_bytes(record[base:base + 2], "little", signed=True)
        y = int.from_bytes(record[base + 2:base + 4], "little", signed=True)
        pairs.append((x, y))
    b, g, r = record[FILL_AT], record[FILL_AT + 1], record[FILL_AT + 2]
    return {
        "count": count,
        "points": [[x, y] for x, y in pairs],
        "pixels": gdi_points(pairs, dpi),
        "fill": f"#{r:02x}{g:02x}{b:02x}",
        "pen": None,
    }
