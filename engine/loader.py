"""Load a book into the Foolbook model.

Currently supports:
- .json / .fbk / .fsk
- Raw .tbk via the built-in parser, with handlers decoded from the page stream
"""

from __future__ import annotations

import json
from pathlib import Path

from main.model import Book, Page, Handler


# Optional override set by --bin. Only used when decoding .tbk / .sbk.
_BIN_OVERRIDE: Path | None = None
# Decoded source is written to _debug/decoded only when this is set.
_KEEP_DECODED = False


def set_keyword_bin(path: str | Path | None) -> None:
    """Use this keyword resource instead of the clean table when decoding .tbk/.sbk."""
    global _BIN_OVERRIDE
    _BIN_OVERRIDE = Path(path) if path else None


def set_keep_decoded(keep: bool) -> None:
    """Keep decoded .tbk/.sbk source on disk. Only set by --debug."""
    global _KEEP_DECODED
    _KEEP_DECODED = bool(keep)


def find_book(name: str, near: str | Path) -> Path | None:
    """Find a book named by a jump.

    Looks in the directory below the loaded file, then beside it, then core/.
    Accepts .fsk, .sbk, .fbk, .tbk, and .json.
    """
    stem = Path(name).stem
    near = Path(near)
    here = near.parent if near.is_file() else near
    below = here.parent
    root = Path(__file__).resolve().parents[1]
    dirs = [below, here, root / "core"]
    suffixes = (".fsk", ".sbk", ".fbk", ".tbk", ".json")
    for d in dirs:
        for suf in suffixes:
            candidate = d / f"{stem}{suf}"
            if candidate.exists():
                return candidate
    return None


def load(path: str | Path) -> Book:
    path = Path(path)
    if not path.is_absolute() and not path.exists():
        core = Path(__file__).resolve().parents[1] / "core" / path.name
        if core.exists():
            path = core
    if path.suffix.lower() == ".json":
        return _load_json(path)
    if path.suffix.lower() in (".fbk", ".fsk"):
        return _load_foolbook(path)
    return _load_tbk(path)


def _load_json(path: Path) -> Book:
    return _book_from_dict(path, json.loads(path.read_text(encoding="utf-8")))


def _load_foolbook(path: Path) -> Book:
    """Load an .fbk or .fsk envelope, compressed or not."""
    from author.formats import unpack
    return _book_from_dict(path, unpack(path.read_bytes()))


def _book_from_dict(path: Path, data: dict) -> Book:
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
        if _KEEP_DECODED:
            _write_decoded(path, pages)
        return Book(path=str(path), title=path.stem, pages=pages)
    except Exception as exc:
        book = Book(path=str(path), title=path.stem)
        book.pages.append(Page(
            id="(unloadable)",
            text=[f"Could not parse {path.name}: {exc}"],
        ))
        return book


def _write_decoded(path: Path, pages: list) -> None:
    """Save decoded handler source under _debug/decoded/ so a load can be inspected later."""
    import json
    from datetime import datetime
    root = Path(__file__).resolve().parents[1]
    dest_dir = root / "_debug" / "decoded"
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    record = {
        "book": path.name,
        "decoded": stamp,
        "pages": [
            {
                "id": p.id,
                "handlers": [
                    {"name": h.name, "offset": h.offset, "source": h.source}
                    for h in (p.handlers or [])
                ],
            }
            for p in pages
            if p.handlers
        ],
    }
    out = dest_dir / f"{path.stem}-{stamp}.json"
    out.write_text(json.dumps(record, indent=2), encoding="utf-8")


def _keywords():
    """Keyword table for decoding .tbk / .sbk handlers.

    --bin overrides everything. Otherwise the clean transcription in
    keywords.py is used. engine/compat/res_77.bin is only a fallback.
    .fbk and .fsk never call this.
    """
    if _BIN_OVERRIDE is not None:
        from .openscript import load_keywords
        if not _BIN_OVERRIDE.exists():
            raise FileNotFoundError(f"keyword bin not found: {_BIN_OVERRIDE}")
        return load_keywords(_BIN_OVERRIDE)
    try:
        from .keywords import KEYWORDS
        if KEYWORDS:
            return KEYWORDS
    except ImportError:
        pass
    here = Path(__file__).resolve().parent
    bin_path = here / "compat" / "res_77.bin"
    if bin_path.exists():
        from .openscript import load_keywords
        return load_keywords(bin_path)
    json_path = here / "keywords.json"
    if json_path.exists():
        try:
            import json
            return json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _handlers_from_blob(blob: bytes, keywords, decode) -> list:
    """Find 'to handle' streams in a page blob and decode them."""
    import re
    found = []
    if not blob or not keywords:
        return found
    for match in re.finditer(rb"(?i)to handle [A-Za-z][A-Za-z0-9]*", blob):
        start = match.start()
        # handlers end at a standalone END; cap the search
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
        # cut at the first END so trailing garbage does not confuse the label
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
