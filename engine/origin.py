"""Which reader a book is for: ToolBook's, or Foolbook's own.

Foolbook is a reader for its own format. ToolBook behavior belongs to
ToolBook files. The file says which it is in its first bytes, whatever its
name: a ToolBook file renamed .fbk is still ToolBook, and an FBK1 envelope
named .tbk is still Foolbook. Code that differs between the two asks here.
"""

from __future__ import annotations

from functools import lru_cache

from foolbook.model import Book


def is_toolbook(book: Book | None) -> bool:
    if book is None or not book.path:
        return False
    return _sniff(str(book.path))


@lru_cache(maxsize=64)
def _sniff(path: str) -> bool:
    """Read once per file. A script asks on every line it runs."""
    from toolbook.format import is_toolbook as toolbook_bytes
    if toolbook_bytes(path):
        return True
    from engine.tbx import is_tbx
    try:
        return bool(is_tbx(path))
    except Exception:
        return False
