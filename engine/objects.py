"""Objects named by class and name, on this page, another page, or a background.

    text of field "index" of parent of page iPage
    set checked of button(temp) of page iPage to false
    isObject(rectangle("correct") of page iPage)

`parent of page X` and `this background` are the background objects the page
shows. Without a place the object is on this page, the page's own layer first.
A page is named by its number, counting from 1, or by its name.
"""

from __future__ import annotations

import re

from foolbook.model import RuntimeState
from engine.groups import _CLASSES

_CLASS = "(?P<cls>" + "|".join(sorted(_CLASSES, key=len, reverse=True)) + ")"
_NAME = r'\s*(?:\(\s*(?P<paren>[^()]*(?:\([^()]*\)[^()]*)*)\s*\)|(?P<quoted>"[^"]*"))'
_PLACE = (
    r'(?:\s+of\s+(?:'
    r'(?P<bg>parent\s+of\s+)?this\s+page'
    r'|(?P<thisbg>this\s+background)'
    r'|(?P<parent>parent\s+of\s+)?page\s*(?P<page>"[^"]*"|\(\s*[^()]+\s*\)|\w+)'
    r'))?'
)
REF = _CLASS + _NAME + _PLACE
PROPERTY = re.compile(r'\s*(?P<prop>\w+)\s+of\s+' + REF + r'\s*$', re.IGNORECASE)
IS_OBJECT = re.compile(r'\s*isobject\s*\(\s*' + REF + r'\s*\)\s*$', re.IGNORECASE)


def _eval(text: str, state: RuntimeState):
    from engine.engine import _eval as evaluate
    return evaluate(text, state)


def _page(state: RuntimeState, match: re.Match):
    token = match.group("page")
    if not token:
        return state.page
    token = token.strip()
    if token.startswith("(") and token.endswith(")"):
        token = token[1:-1]
    value = _eval(token, state)
    pages = state.book.pages if state.book is not None else []
    text = "" if value is None else str(value).strip()
    for page in pages:
        if (page.id or "").lower() == text.lower():
            return page
    if re.fullmatch(r"\d+", text):
        at = int(text) - 1
        return pages[at] if 0 <= at < len(pages) else None
    return None


def shapes(state: RuntimeState, match: re.Match) -> list[dict]:
    """The shapes a reference names. Empty when there are none."""
    page = _page(state, match)
    if page is None:
        return []
    name = _eval(match.group("quoted") or match.group("paren"), state)
    name = ("" if name is None else str(name)).strip().lower()
    kinds = _CLASSES[match.group("cls").lower()]
    found = [
        s for s in page.shapes or []
        if (s.get("name") or "").strip().lower() == name and (s.get("kind") or "") in kinds
    ]
    if match.group("bg") or match.group("thisbg") or match.group("parent"):
        return [s for s in found if s.get("layer") == "background"]
    own = [s for s in found if s.get("layer") != "background"]
    return own or found


def exists(state: RuntimeState, match: re.Match) -> bool:
    return bool(shapes(state, match))


def get_property(state: RuntimeState, match: re.Match):
    """A property of the first shape the reference names. Blank when there is none."""
    found = shapes(state, match)
    if not found:
        return ""
    prop = match.group("prop").lower()
    shape = found[0]
    if prop == "text":
        return shape.get("text") or ""
    if prop in ("visible", "enabled"):
        return shape.get(prop) is not False
    if prop == "checked":
        return bool(shape.get("checked"))
    return shape.get(prop, "")


def set_property(state: RuntimeState, match: re.Match, value) -> None:
    """Set a property on every shape the reference names."""
    from engine.engine import _flag, set_shape_text
    prop = match.group("prop").lower()
    for shape in shapes(state, match):
        if prop == "text":
            set_shape_text(state, shape, "" if value is None else str(value))
        elif prop in ("visible", "enabled", "checked"):
            shape[prop] = _flag(value)
        else:
            shape[prop] = value
    state.variables["__redraw"] = True
