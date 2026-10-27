"""The sidebar lists the book's main pages by title.

A main page is one the book itself puts on its menu, or names with a
title when it has no menu. A help page, a question, and a demo copy of
a menu are not main. Developer mode lists every page id instead.
"""

from __future__ import annotations

import re

def outline(pages) -> list[tuple[int, str]]:
    """(page index, title) for the pages a reader should see."""
    marks = _landmarks(pages)
    if not marks:
        return []
    secondary = _secondary_targets(pages, marks)
    rows = []
    seen = set()
    for index, label, key in marks:
        if key in secondary or label in seen:
            continue
        seen.add(label)
        rows.append((index, label))
    return rows


def every_page(pages) -> list[tuple[int, str]]:
    """Every page, by id. Developer mode only."""
    return [(index, str(getattr(page, "id", "") or index)) for index, page in enumerate(pages)]


def _landmarks(pages) -> list[tuple[int, str, str]]:
    found = []
    for index, page in enumerate(pages):
        label = _named_title(page)
        if not label:
            continue
        found.append((index, label, str(getattr(page, "id", "") or "").lower()))
    return found


def _secondary_targets(pages, marks) -> set[str]:
    """Pages a later menu points at, once the book already has a main menu.

    The first menu is the lesson menu. A menu reached from there is
    showing an example, and its entries are not main pages.
    """
    titled = {key for _index, _label, key in marks}
    menus = []
    for index, page in enumerate(pages):
        dests = []
        seen = set()
        for item in getattr(page, "items", None) or []:
            dest = str(item.get("page") or "").lower()
            if dest in titled and dest not in seen:
                seen.add(dest)
                dests.append(dest)
        if len(dests) >= 2:
            menus.append((index, str(getattr(page, "id", "") or "").lower(), dests))
    if len(menus) < 2:
        return set()
    by_id = {str(getattr(page, "id", "") or "").lower(): page for page in pages}
    reached = set()
    stack = list(menus[0][2])
    while stack:
        current = stack.pop()
        if current in reached:
            continue
        reached.add(current)
        page = by_id.get(current)
        if page is None:
            continue
        for item in getattr(page, "items", None) or []:
            dest = str(item.get("page") or "").lower()
            if dest and dest not in reached:
                stack.append(dest)
    extra = set()
    for _index, menu_id, dests in menus[1:]:
        if menu_id in reached:
            extra.update(dests)
    return extra


def _named_title(page) -> str:
    for shape in getattr(page, "shapes", None) or []:
        if (shape.get("name") or "").lower() not in ("menutext", "title"):
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
    return True
