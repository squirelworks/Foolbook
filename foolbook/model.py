"""Core data model for Foolbook.

Intentionally small. Extend only when a real book needs a new field.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Handler:
    name: str
    source: str = ""
    bytecode: bytes = b""
    offset: int = 0


@dataclass
class Page:
    id: str
    text: list[str] = field(default_factory=list)
    items: list[dict] = field(default_factory=list)   # {"label", "page", ...}
    jumps: list[str] = field(default_factory=list)
    quiz: dict | None = None
    handlers: list[Handler] = field(default_factory=list)
    shapes: list[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)


@dataclass
class Book:
    path: str
    title: str = ""
    pages: list[Page] = field(default_factory=list)
    shells: list[str] = field(default_factory=list)
    handlers: list[Handler] = field(default_factory=list)
    props: dict = field(default_factory=dict)
    author: str = ""
    first_page: str = ""

    def start(self, last: str = "") -> int:
        """Where a reader opens the book.

        The student's saved last page when there is one and it exists, else
        the book's first page id when that page exists, else the first page.
        A ToolBook book has no first page id, so it opens on page 0 as before.
        """
        for wanted in (last, self.first_page):
            found = self.index_of(wanted) if wanted else -1
            if found >= 0:
                return found
        return 0

    def page(self, page_id: str) -> Page | None:
        for p in self.pages:
            if p.id == page_id:
                return p
        return None

    def index_of(self, page_id: str) -> int:
        for i, p in enumerate(self.pages):
            if p.id == page_id:
                return i
        return -1


@dataclass
class RuntimeState:
    """Mutable state the interpreter and viewer share."""
    book: Book
    index: int = 0
    variables: dict[str, Any] = field(default_factory=dict)
    log: list[str] = field(default_factory=list)
    # Books already open. ToolBook does not close one to show another.
    shelf: dict = field(default_factory=dict)
    where: dict = field(default_factory=dict)
    # sysBooks, first searched first: (name as pushed, Book or None).
    sysbooks: list = field(default_factory=list)

    @property
    def page(self) -> Page | None:
        if 0 <= self.index < len(self.book.pages):
            return self.book.pages[self.index]
        return None

    def note(self, msg: str) -> None:
        self.log.append(msg)
