"""Open a ToolBook file by ToolBook rules.

The reader underneath is the one the NIDA books already use. This door
is what keeps a Foolbook change from being applied to those bytes.
"""

from __future__ import annotations

from pathlib import Path

from foolbook.model import Book
from toolbook.format import is_toolbook


def open_book(path: str | Path) -> Book:
    """Open one ToolBook book. The path must already be ToolBook inside."""
    path = Path(path)
    if not is_toolbook(path):
        raise ValueError(f"{path.name} is not a ToolBook file")
    from engine.loader import _load_tbk
    return _load_tbk(path)
