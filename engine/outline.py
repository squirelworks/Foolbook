"""The pages a book treats as its own list.

A lesson names those pages in a menu field. A shell with no menu
names them in the heading on the page. Either way the sidebar shows
those words, not every page id.
"""

from __future__ import annotations

import re

_SKIP = {
    "page#", "copyright", "logo", "next", "back", "solid", "overlay",
    "textbox", "text", "menutextshadow", "titlebox", "menuframe",
}


def outline(pages) -> list[tuple[int, str]]:
    """(page index, label) for the sidebar.

    Menu and title fields win. A book without them uses the heading
    written on the page, and a repeated heading is listed once.
    """
    rows = _rows(pages, named=True)
    if len(rows) < 2:
        rows = _rows(pages, named=False)
    if rows:
        return rows
    return [(i, str(getattr(page, "id", "") or i)) for i, page in enumerate(pages)]


def _rows(pages, named: bool) -> list[tuple[int, str]]:
    found = []
    last = ""
    for index, page in enumerate(pages):
        label = _heading(page, named=named)
        if not label or label == last:
            continue
        found.append((index, label))
        last = label
    return found


def _heading(page, named: bool) -> str:
    shapes = list(getattr(page, "shapes", None) or [])
    for want in ("menutext", "title"):
        for shape in shapes:
            if (shape.get("name") or "").lower() != want:
                continue
            text = _clean(shape.get("text") or "")
            if _usable(text):
                return text
    if named:
        return ""
    for shape in shapes:
        name = (shape.get("name") or "").lower()
        if name in _SKIP:
            continue
        if (shape.get("kind") or "") not in ("text", ""):
            continue
        text = _clean(shape.get("text") or "")
        if _usable(text):
            return text
    return ""


def _clean(text: str) -> str:
    parts = [part.strip() for part in re.split(r" {2,}|\n", str(text)) if part.strip()]
    text = re.sub(r"\s+", " ", parts[0] if parts else "").strip(" :-")
    if text.lower().startswith("title:"):
        text = text.split(":", 1)[1].strip()
    return text


def _usable(text: str) -> bool:
    if not text or len(text) > 42 or text.endswith("."):
        return False
    if len(text.split()) > 7:
        return False
    if text in {"?", "-"}:
        return False
    return True
