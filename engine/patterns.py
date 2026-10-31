"""Eight by eight pattern fills.

A rectangle may carry `tile`: eight rows of eight
bits, each row a string of 0 and 1 or a number from 0 to 255 with the
high bit on the left. A 1 is drawn in the outline colour and a 0 in the
fill colour. The tile repeats across the shape, and each bit grows with
the page scale.
"""

from __future__ import annotations

SIZE = 8


def rows(tile) -> list[str] | None:
    """Eight strings of eight 0s and 1s, or None for anything else."""
    if not isinstance(tile, (list, tuple)) or len(tile) != SIZE:
        return None
    out = []
    for row in tile:
        if isinstance(row, bool):
            return None
        if isinstance(row, int):
            if not 0 <= row <= 255:
                return None
            out.append(format(row, "08b"))
        elif isinstance(row, str) and len(row) == SIZE and set(row) <= {"0", "1"}:
            out.append(row)
        else:
            return None
    return out


def pixels(tile, ink: str, paper: str, cell: int = 1) -> list[list[str]]:
    """One repeat of the tile, each bit `cell` pixels square."""
    bits = rows(tile)
    if bits is None:
        return []
    cell = max(1, int(cell))
    grid = []
    for row in bits:
        line = [ink if bit == "1" else paper for bit in row for _ in range(cell)]
        grid.extend([line] * cell)
    return grid
