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
            "TBX support is the openscript_analysis module "
            "(pip name openscript-analysis). Install that package."
        ) from exc
    return tbx


def is_tbx(path: str | Path) -> bool:
    return _tbx().is_tbx(path)


def load(path: str | Path) -> Book:
    data = _tbx().settle(path)
    pages = []
    for raw in data.get("pages") or []:
        objects = list(raw.get("objects") or raw.get("shapes") or [])
        pages.append(Page(
            id=raw.get("id") or "",
            text=[_words(t) for t in (raw.get("text") or []) if _words(t)],
            items=list(raw.get("items") or []),
            shapes=objects,
            handlers=_handlers(raw.get("script") or ""),
            quiz=raw.get("quiz"),
            raw={
                "objects": objects,
                "settled": True,
                "size": raw.get("size") or data.get("size"),
            },
        ))
    return Book(
        path=str(path),
        title=data.get("title") or Path(path).stem,
        pages=pages,
        handlers=_handlers(data.get("script") or ""),
    )


def _words(value: str) -> str:
    from engine.notes import plain
    return plain(value)


def _handlers(source: str) -> list[Handler]:
    from engine.engine import split_handlers
    return split_handlers(source)
