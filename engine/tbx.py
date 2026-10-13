"""TBX entry for Foolbook.

The reader lives in openscript_analysis. This module only turns that
package's page dict into a Foolbook book. A .tbk is not used.
"""

from __future__ import annotations

from pathlib import Path

from foolbook.model import Book, Handler, Page


def _tbx():
    try:
        from openscript_analysis.formats import tbx
    except ImportError as exc:
        raise ImportError(
            "TBX support is in openscript-analysis. Install that package."
        ) from exc
    return tbx


def is_tbx(path: str | Path) -> bool:
    return _tbx().is_tbx(path)


def load(path: str | Path) -> Book:
    data = _tbx().to_book_dict(_tbx().load_tbx(path))
    pages = []
    for raw in data.get("pages") or []:
        pages.append(Page(
            id=raw.get("id") or "",
            text=list(raw.get("text") or []),
            items=list(raw.get("items") or []),
            shapes=list(raw.get("shapes") or []),
            handlers=[
                Handler(name=h.get("name") or "", source=h.get("source") or "")
                for h in raw.get("handlers") or []
            ],
        ))
    return Book(path=str(path), title=data.get("title") or Path(path).stem, pages=pages)
