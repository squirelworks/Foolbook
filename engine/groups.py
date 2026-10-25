"""Groups: hide group, show group, and visible of group.

ToolBook stores a group as a record that holds its children. The reader
(openscript_analysis, ``tag_groups``) keeps the group names on every child as
``shape["groups"]``, nearest group first. A shape is in group "Review 1" when
that name is on its list, whatever the case.

A script names the group with a word or an expression, ``group "Review 1"`` or
``group("Review" && i)``, and may add ``of page "P10410"``. Only the page the
student is on has shapes in this window, so a page that is not this one is
looked up in the book.
"""

from __future__ import annotations

import re

from foolbook.model import RuntimeState

_NAME = r'(?:\(\s*(?P<paren>.+?)\s*\)|(?P<quoted>"[^"]*"))'
_PAGE = r'(?:\s+of\s+page\s+(?P<page>"[^"]*"|\(\s*[^)]+\s*\)|\w+))?'
# visible of group "X" [of page "Y"]
GROUP_VISIBLE = re.compile(r'\s*visible\s+of\s+group\s*' + _NAME + _PAGE + r'\s*$', re.IGNORECASE)
# hide group "X" [of page "Y"]   show group "X" [of page "Y"]
GROUP_SHOW = re.compile(r'\s*(?P<verb>show|hide)\s+group\s*' + _NAME + _PAGE + r'\s*$', re.IGNORECASE)
# visible of group "X" [of page "Y"] is [not] true|false   (also = true)
GROUP_TEST = re.compile(
    r'\s*visible\s+of\s+group\s*' + _NAME + _PAGE + r'\s*(?P<op>is\s+not|is|=|<>)\s*(?P<val>true|false)\s*$',
    re.IGNORECASE,
)
# send playAnimation [args] to group "X" [of page "Y"]
PLAY = re.compile(r'\s*send\s+playanimation\b.*?\bto\s+group\s*' + _NAME + _PAGE + r'\s*$', re.IGNORECASE)
# isObject(group "X")   isObject(group("X" && i))
IS_OBJECT = re.compile(r'\s*isobject\s*\(\s*group\s*' + _NAME + _PAGE + r'\s*\)\s*$', re.IGNORECASE)


def _text(state: RuntimeState, token: str) -> str:
    from engine.engine import _eval
    value = _eval(token, state)
    return "" if value is None else str(value)


def group_name(state: RuntimeState, match: re.Match) -> str:
    return _text(state, match.group("quoted") or match.group("paren"))


def _shapes(state: RuntimeState, match: re.Match) -> list[dict] | None:
    """The shapes of the page the target names. None when there is no such page."""
    page = state.page
    token = match.group("page")
    if token:
        wanted = _text(state, token).strip().lower()
        if page is None or (page.id or "").lower() != wanted:
            page = next((p for p in state.book.pages if (p.id or "").lower() == wanted), None)
    return None if page is None else (page.shapes or [])


def members(state: RuntimeState, match: re.Match) -> list[dict]:
    name = group_name(state, match).strip().lower()
    if not name:
        return []
    shapes = _shapes(state, match) or []
    return [s for s in shapes if any((g or "").lower() == name for g in s.get("groups") or ())]


def set_visible(state: RuntimeState, match: re.Match, flag: bool) -> None:
    for shape in members(state, match):
        shape["visible"] = flag
    state.variables["__redraw"] = True


def is_visible(state: RuntimeState, match: re.Match) -> bool:
    """A group shows when any of its members shows."""
    return any(s.get("visible") is not False for s in members(state, match))


def exists(state: RuntimeState, match: re.Match) -> bool:
    return bool(members(state, match))


# ---- one object by class and name ------------------------------------------------------------------------
#   set visible of button "next" to true     show field "response"     hide rectangle "mark" of page "P1"
# A drawn picture or button is kind "image" in this window, so those classes take "image" too.
_CLASSES = {
    "field": {"text"},
    "recordfield": {"text"},
    "button": {"button", "image"},
    "rectangle": {"rect", "image"},
    "roundedrectangle": {"rect", "image"},
    "ellipse": {"ellipse", "image"},
    "circle": {"ellipse", "image"},
    "line": {"line"},
    "angledline": {"line"},
    "polygon": {"polygon"},
    "irregularpolygon": {"polygon"},
    "regularpolygon": {"polygon"},
    "arc": {"arc"},
    "picture": {"picture", "image"},
    "paintobject": {"paint", "image"},
}
_CLASS = "(?P<cls>" + "|".join(sorted(_CLASSES, key=len, reverse=True)) + ")"
_THIS = r'(?:\s+of\s+this\s+page)?'
OBJECT_VISIBLE = re.compile(r'\s*visible\s+of\s+' + _CLASS + r'\s*' + _NAME + _PAGE + _THIS + r'\s*$', re.IGNORECASE)
OBJECT_SHOW = re.compile(r'\s*(?P<verb>show|hide)\s+' + _CLASS + r'\s*' + _NAME + _PAGE + _THIS + r'\s*$', re.IGNORECASE)


def object_name(state: RuntimeState, match: re.Match) -> str:
    return _text(state, match.group("quoted") or match.group("paren"))


def object_shapes(state: RuntimeState, match: re.Match) -> list[dict]:
    name = object_name(state, match).strip().lower()
    kinds = _CLASSES[match.group("cls").lower()]
    return [
        s for s in _shapes(state, match) or []
        if (s.get("name") or "").strip().lower() == name and (s.get("kind") or "") in kinds
    ]


def set_object_visible(state: RuntimeState, match: re.Match, flag: bool) -> None:
    for shape in object_shapes(state, match):
        shape["visible"] = flag
    state.variables["__redraw"] = True


def object_is_visible(state: RuntimeState, match: re.Match) -> bool:
    return any(s.get("visible") is not False for s in object_shapes(state, match))
