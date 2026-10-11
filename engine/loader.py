"""Load a book into the Foolbook model.

Currently supports:
- Maybe2-style lessonshell JSON (items, quiz, text)
- .fbk and .fsk intermediate formats
- Raw .tbk via the built-in engine.tbk parser
"""

from __future__ import annotations

import json
from pathlib import Path

from foolbook.model import Book, Page, Handler


def load(path: str | Path) -> Book:
    path = Path(path)
    if not path.is_absolute() and not path.exists():
        core = Path(__file__).resolve().parents[1] / "core" / path.name
        if core.exists():
            path = core
    if path.suffix.lower() in (".json", ".fbk", ".fsk"):
        return _load_json(path)
    return _load_tbk(path)


def _load_json(path: Path) -> Book:
    data = json.loads(path.read_text(encoding="utf-8"))
    pages = []
    for raw in data.get("pages") or []:
        handlers = []
        if raw.get("script"):
            handlers.append(Handler(name="script", source=raw["script"]))
        pages.append(Page(
            id=raw.get("id") or raw.get("name") or "",
            text=list(raw.get("text") or []),
            items=list(raw.get("items") or []),
            jumps=list(raw.get("jumps") or []),
            quiz=raw.get("quiz"),
            handlers=handlers,
            raw=raw,
        ))
    return Book(
        path=str(path),
        title=data.get("title") or path.stem,
        pages=pages,
        shells=list(data.get("shells") or []),
    )


def _load_tbk(path: Path) -> Book:
    """Load a raw .tbk with the built-in parser."""
    try:
        from . import tbk as rtbk
        raw = rtbk.load(path)
        pages = []
        for p in raw.pages:
            text = []
            for f in getattr(p, "fields", []) or []:
                t = getattr(f, "text", None)
                if t:
                    text.append(t)
            for para in getattr(p, "paragraphs", []) or []:
                if para and para not in text:
                    text.append(para)
            pages.append(Page(
                id=p.name,
                text=text,
                jumps=list(getattr(p, "quoted_jumps", None) or []),
                raw={"offset": p.offset},
            ))
        return Book(path=str(path), title=path.stem, pages=pages)
    except Exception as exc:
        book = Book(path=str(path), title=path.stem)
        book.pages.append(Page(
            id="(unloadable)",
            text=[f"Could not parse {path.name}: {exc}"],
        ))
        return book
