"""Which reader a book is for: ToolBook's, or Foolbook's own.

Foolbook is a reader for its own format. ToolBook behavior belongs to
books that came from ToolBook: a .tbk, .sbk or TBKX opened as it is, or a
Foolbook file exported from one, whose pages are marked ``settled``. A book
written in Foolbook's own format gets Foolbook behavior. Code that differs
between the two asks here, and nowhere else.
"""

from __future__ import annotations

from pathlib import Path

from foolbook.model import Book

# Files Foolbook writes or reads as its own. Anything else is a ToolBook file.
_OWN = {".fbk", ".fsk", ".fsc", ".json", ".pdf", ".ppt", ".pptx", ".doc", ".docx", ".odt",
        ".txt", ".text", ".md", ".markdown", ".rst", ".log", ".rtf"}


def is_toolbook(book: Book | None) -> bool:
    if book is None:
        return False
    path = Path(book.path or "")
    if path.suffix.lower() not in _OWN and book.path:
        return True
    return any((page.raw or {}).get("settled") for page in book.pages or [])
