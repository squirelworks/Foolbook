"""The lesson menu colours. They live in the session, not in the book file.

nc81base keeps __menuFlags[1..10]. 1 is not done and the label stays black.
2 is done and the label is stroked "270,50,100", which is hue, saturation
and brightness. Leaving P1910 sets flag 1. Leaving P2910 sets flag 2.
A passed quiz sets flag 10. Exit is not one of these fields.
"""

from __future__ import annotations

_UNKNOWN = object()
_DONE = 2
# Hue 270, saturation 50, brightness 100. The 16-colour guest shows this as light blue.
_VISITED = "#bf80ff"
_PLAIN = "#000000"


def call(state, name: str, args: str):
    key = (name or "").lower()
    if key == "setmenuflag":
        set_flag(state, _num(args))
        return 0
    if key in ("setupmenupage", "setupmenupagelocal"):
        paint(state)
        return 0
    return _UNKNOWN


def set_flag(state, index: int) -> None:
    """setMenuFlag. A help quiz does not mark the menu."""
    if state.variables.get("__quizHelp"):
        return
    if not 1 <= index <= 10:
        return
    flags(state)[index - 1] = _DONE


def paint(state) -> None:
    """setupMenuPage. Selection 1, 2 and T are the three labels on P900."""
    page = state.page
    if page is None:
        return
    marks = flags(state)
    chosen = {}
    for index in range(1, 11):
        name = f"selection {index}"
        if not _named(page, name):
            break
        chosen[name] = _VISITED if marks[index - 1] == _DONE else _PLAIN
    if _named(page, "selection t"):
        chosen["selection t"] = _VISITED if marks[9] == _DONE else _PLAIN
    for shape in _shapes(page):
        name = (shape.get("name") or "").lower()
        if shape.get("kind") == "text" and name in chosen:
            shape["outline"] = chosen[name]


def flags(state) -> list:
    value = state.variables.get("__menuFlags")
    if not isinstance(value, list) or len(value) != 10:
        value = [1] * 10
        state.variables["__menuFlags"] = value
    return value


def _shapes(page) -> list:
    found = list(page.shapes or [])
    found.extend((page.raw or {}).get("objects") or [])
    return found


def _named(page, name: str) -> bool:
    return any((shape.get("name") or "").lower() == name for shape in _shapes(page))


def _num(text: str) -> int:
    token = (text or "").split(",")[0].strip().strip("\"'")
    try:
        return int(token)
    except (TypeError, ValueError):
        return 0
