"""OpenScript engine.

Core module. Given a loaded book, it executes handlers and returns
actions the viewer should perform (goto, send, set, note).

This is what lets a .tbk or .sbk drive the Foolbook experience.
The decoder is not required on this path.
"""

from __future__ import annotations

import re
from .model import RuntimeState, Page


# Action kinds the viewer understands
# {"kind": "goto", "page": "P400", "book": None}
# {"kind": "send", "name": "next"}
# {"kind": "set", "name": "...", "value": ...}
# {"kind": "note", "text": "..."}


_GOTO = re.compile(
    r'go\s+to\s+page\s+"([^"]+)"(?:\s+of\s+book\s+"([^"]+)")?',
    re.IGNORECASE,
)
_SEND = re.compile(r'send\s+(\w+)', re.IGNORECASE)
_ASSIGN = re.compile(r'(\w+)\s*=\s*(.+)')


def run_handler(state: RuntimeState, source: str) -> list[dict]:
    """Execute a handler source against the current state.

    Returns the list of actions produced.
    """
    actions: list[dict] = []
    if not source:
        return actions

    # Very shallow: split on lines, skip comments and structural keywords
    lines = [ln.strip() for ln in source.replace("\r", "").split("\n")]
    skipping = False
    for line in lines:
        if not line or line.startswith("--"):
            continue
        low = line.lower()
        if low.startswith("to handle") or low == "end" or low.startswith("end "):
            continue
        if low.startswith("if ") and " then" in low:
            # Evaluate a trivial equality; otherwise skip the body
            cond = line[3:low.rfind(" then")].strip()
            skipping = not _eval_simple(cond, state)
            continue
        if low.startswith("else"):
            skipping = not skipping
            continue
        if low.startswith("end if"):
            skipping = False
            continue
        if skipping:
            continue

        m = _GOTO.search(line)
        if m:
            actions.append({"kind": "goto", "page": m.group(1), "book": m.group(2)})
            continue
        m = _SEND.search(line)
        if m:
            actions.append({"kind": "send", "name": m.group(1)})
            continue
        m = _ASSIGN.match(line)
        if m and not line.lower().startswith("if "):
            name, expr = m.group(1), m.group(2).strip().rstrip(".")
            value = _eval_simple(expr, state)
            state.variables[name] = value
            actions.append({"kind": "set", "name": name, "value": value})
            continue
        actions.append({"kind": "note", "text": line})

    return actions


def _eval_simple(expr: str, state: RuntimeState):
    """Extremely limited expression evaluator.

    Supports literals, variable lookup, and a few obvious comparisons.
    """
    expr = expr.strip()
    if expr.lower() == "true":
        return True
    if expr.lower() == "false":
        return False
    if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
        return expr[1:-1]
    if expr in state.variables:
        return state.variables[expr]
    # trivial equality
    if " = " in expr:
        left, right = expr.split(" = ", 1)
        return _eval_simple(left, state) == _eval_simple(right, state)
    return expr


def goto(state: RuntimeState, page_id: str) -> bool:
    idx = state.book.index_of(page_id)
    if idx < 0:
        state.note(f"missing page {page_id}")
        return False
    state.index = idx
    state.note(f"goto {page_id}")
    return True


def current_page(state: RuntimeState) -> Page | None:
    return state.page
