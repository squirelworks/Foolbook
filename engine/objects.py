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
_NAME = (
    r'\s*(?:\(\s*(?P<paren>[^()]*(?:\([^()]*\)[^()]*)*)\s*\)|(?P<quoted>"[^"]*")'
    r'|(?<=\s)(?P<bare>(?!of\b)[A-Za-z_]\w*))'
)
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
    name = _eval(match.group("quoted") or match.group("paren") or match.group("bare"), state)
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


# ---- a reference held in a value: target, or a variable set from it ---------------------------------------
#   object of target is button      name of vTarget is "OK"      enabled of target
# The reader hands a click its object as `button "B" of page "P10210"`, the
# form a script can name it by.
_KIND_CLASS = {"text": "field", "rect": "rectangle", "ellipse": "ellipse", "line": "line",
               "polygon": "polygon", "arc": "arc", "button": "button", "picture": "picture",
               "paint": "paintobject"}
REFERENCE = re.compile(r'\s*' + REF + r'\s*$', re.IGNORECASE)
PAGE_REFERENCE = re.compile(r'\s*page\s+"(?P<name>[^"]*)"\s*$', re.IGNORECASE)
OF_VALUE = re.compile(r'\s*(?P<prop>\w+)\s+of\s+(?P<var>[A-Za-z_]\w*)\s*$', re.IGNORECASE)


def reference(state: RuntimeState, shape: dict | None) -> str:
    """How a script names a shape on this page, or this page when there is none."""
    page = state.page
    where = f' of page "{page.id}"' if page is not None else ""
    if not shape:
        return f'page "{page.id}"' if page is not None else ""
    kind = shape.get("kind") or ""
    cls = _KIND_CLASS.get(kind)
    if kind == "image":
        cls = "button" if shape.get("invert_data") or shape.get("checked_data") else "picture"
    name = (shape.get("name") or "").replace('"', "'")
    parent = "parent of " if shape.get("layer") == "background" and where else ""
    return f'{cls or "button"} "{name}"' + (f" of {parent}{where[4:]}" if where else "")


def of_value(state: RuntimeState, match: re.Match):
    """`object of target`, `name of target`, or a property of the object a variable holds.

    None when the variable does not hold a reference.
    """
    from engine.engine import _var, _MISSING
    held = _var(state, match.group("var"))
    if held is _MISSING or not isinstance(held, str):
        return None
    prop = match.group("prop").lower()
    page = PAGE_REFERENCE.match(held)
    if page:
        return {"object": "page", "name": page.group("name")}.get(prop, "")
    ref = REFERENCE.match(held)
    if not ref:
        return None
    if prop == "object":
        return ref.group("cls").lower()
    if prop == "name":
        return _eval(ref.group("quoted") or ref.group("paren") or ref.group("bare"), state)
    whole = PROPERTY.fullmatch(f"{match.group('prop')} of {held}")
    return get_property(state, whole) if whole else ""
