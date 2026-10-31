"""The system book a page book names.

An .fbk may say `"system": "shared.fsk"`. The reader opens that book once
and keeps its `to handle` and `to get` handlers. A `send NAME` and a call
`NAME(...)` look there before the reader's own approximations in
menu.py, fillin.py, and quiz.py.

Arguments are bound to the header's parameter names. `return EXPR` sets
the value and ends the handler.
"""

from __future__ import annotations

import re
from pathlib import Path

_HEADER = re.compile(r"(?im)^[ \t]*to[ \t]+(?:handle|get)[ \t]+([A-Za-z_]\w*)[ \t]*([^\n]*)$")
_RETURN = re.compile(r"(?i)^(\s*)return\b\s*(.*)$")
_VALUE = "__return"


def handlers(raw: dict) -> dict:
    """Handlers by lowercase name: (parameter names, body)."""
    from engine.engine import _strip_handler_end
    found = {}
    scripts = [raw.get("script") or ""]
    scripts += [page.get("script") or "" for page in raw.get("pages") or [] if isinstance(page, dict)]
    for script in scripts:
        matches = list(_HEADER.finditer(str(script)))
        for i, match in enumerate(matches):
            stop = matches[i + 1].start() if i + 1 < len(matches) else len(script)
            params = [p.strip() for p in match.group(2).split(",") if p.strip()]
            body = _strip_handler_end(script[match.end():stop])
            found.setdefault(match.group(1).lower(), (params, body))
    for listed in raw.get("handlers") or []:
        if isinstance(listed, dict) and listed.get("name"):
            found.setdefault(str(listed["name"]).lower(), (list(listed.get("params") or []), listed.get("source") or ""))
    return found


def _loaded(state) -> dict:
    """The named system book's handlers, read once per book."""
    book = state.book
    names = list(getattr(book, "shells", None) or [])
    cache = state.where.setdefault("__system", {})
    key = (book.path, tuple(names))
    if key in cache:
        return cache[key]
    found = {}
    if names and book.path:
        from engine.formats import unpack
        from engine.loader import find_book
        path = find_book(names[0], Path(book.path))
        if path is not None and path.suffix.lower() in (".fsk", ".fbk", ".json"):
            try:
                found = handlers(unpack(path.read_bytes()))
            except (OSError, ValueError):
                found = {}
    cache[key] = found
    return found


def has(state, name: str) -> bool:
    return str(name).lower() in _loaded(state)


def run(state, name: str, args: list | None = None):
    """Run a system handler. Returns (actions, returned value)."""
    from engine.engine import run_handler
    params, body = _loaded(state)[str(name).lower()]
    for param, value in zip(params, args or []):
        state.variables[param] = value
    lines = []
    for line in body.split("\n"):
        m = _RETURN.match(line)
        if m:
            lines.append(f"{m.group(1)}{_VALUE} = {m.group(2) or 0}")
            lines.append(f"{m.group(1)}break")
        else:
            lines.append(line)
    state.variables.pop(_VALUE, None)
    actions = run_handler(state, "\n".join(lines))
    return actions, state.variables.pop(_VALUE, None)
