"""Load a book into the Foolbook model.

Currently supports:
- Maybe2-style lessonshell JSON (items, quiz, text)
- Placeholder for raw .tbk (delegates to runtime.tbk when present)
"""

from __future__ import annotations

import json
from pathlib import Path

from foolbook.model import Book, Page, Handler


def load(path: str | Path) -> Book:
    path = Path(path)
    if path.suffix.lower() == ".json":
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
    """Best-effort load of a raw .tbk.

    Tries the project's runtime.tbk parser if it is importable.
    Falls back to an empty book with a note.
    """
    try:
        import sys
        # Allow running from Foolbook/ or from the artifacts root
        for candidate in (path.parent, Path(__file__).resolve().parents[2]):
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
        from runtime import tbk as rtbk
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
