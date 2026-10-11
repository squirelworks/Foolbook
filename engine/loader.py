"""Load a book into the Foolbook model.

Currently supports:
- .json / .fbk / .fsk
- Raw .tbk via the built-in parser, with handlers decoded from the page stream
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
    """Load a raw .tbk with the built-in parser and decode its handlers."""
    try:
        from . import tbk as rtbk
        from .openscript import load_keywords, decode
        keywords = _keywords()
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
            handlers = _handlers_from_blob(p.blob, keywords, decode)
            items = _items_from_handlers(handlers)
            pages.append(Page(
                id=p.name,
                text=text,
                items=items,
                jumps=list(getattr(p, "quoted_jumps", None) or []),
                handlers=handlers,
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


def _keywords():
    from .openscript import load_keywords
    here = Path(__file__).resolve().parent
    bin_path = here / "res_77.bin"
    if bin_path.exists():
        return load_keywords(bin_path)
    json_path = here / "keywords.json"
    if json_path.exists():
        import json
        return json.loads(json_path.read_text(encoding="utf-8"))
    return []


def _handlers_from_blob(blob: bytes, keywords, decode) -> list:
    """Find 'to handle' streams in a page blob and decode them."""
    import re
    found = []
    if not blob or not keywords:
        return found
    for match in re.finditer(rb"(?i)to handle [A-Za-z][A-Za-z0-9]*", blob):
        start = match.start()
        end = blob.find(b"\rend", start)
        if end < 0 or end - start > 4000:
            end = blob.find(b"\nEND", start)
        if end < 0 or end - start > 4000:
            end = min(len(blob), start + 800)
        else:
            end = min(len(blob), end + 4)
        raw = blob[start:end]
        try:
            source = decode(raw, keywords)
        except Exception:
            source = ""
        if not source:
            continue
        kind = match.group().split()[-1].decode("latin1")
        found.append(Handler(name=kind, source=source, offset=start))
    return found


def _items_from_handlers(handlers: list) -> list:
    """Build next/back items from decoded buttonClick handlers."""
    import re
    items = []
    goto = re.compile(r'go\s+to\s+page\s+"([^"]+)"(?:\s+of\s+book\s+"([^"]+)")?', re.IGNORECASE)
    for h in handlers:
        if h.name.lower() != "buttonclick":
            continue
        src = h.source or ""
        low = src.lower()
        cut = low.find("\nend")
        if cut > 0:
            src = src[:cut]
            low = src.lower()
        m = goto.search(src)
        target = m.group(1) if m else ""
        other = m.group(2) if m else None
        if "go to next page" in low or (not target and "send next" in low):
            label = "Next"
        elif "go to previous" in low or "send previous" in low:
            label = "Back"
        elif other:
            label = f"{target}@{other}"
        elif target:
            label = target
        else:
            continue
        items.append({"label": label, "page": target, "book": other})
    return items
