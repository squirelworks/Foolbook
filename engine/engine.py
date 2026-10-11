"""OpenScript engine.

Parses and executes handlers from a loaded book and returns actions
the Foolbook viewer should perform.
"""

from __future__ import annotations

import re
from foolbook.model import RuntimeState, Page


_GOTO = re.compile(
    r'go\s+to\s+page\s+"([^"]+)"(?:\s+of\s+book\s+"([^"]+)")?',
    re.IGNORECASE,
)
_SEND = re.compile(r'send\s+(\w+)', re.IGNORECASE)
_ASSIGN = re.compile(r'(\w+)\s*=\s*(.+)')


def run_handler(state: RuntimeState, source: str) -> list[dict]:
    """Execute a handler source against the current state."""
    actions: list[dict] = []
    if not source:
        return actions

    lines = [ln.strip() for ln in source.replace("\r", "").split("\n")]
    skipping = False
    for line in lines:
        if not line or line.startswith("--"):
            continue
        low = line.lower()
        if low.startswith("to handle") or low == "end" or low.startswith("end "):
            continue
        if low.startswith("if ") and " then" in low:
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
    expr = expr.strip()
    if expr.lower() == "true":
        return True
    if expr.lower() == "false":
        return False
    if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
        return expr[1:-1]
    if expr in state.variables:
        return state.variables[expr]
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


def follow(state: RuntimeState, actions: list[dict]) -> bool:
    """Apply the first navigation action. Returns True if the page changed."""
    for act in actions:
        if act.get("kind") == "goto":
            page = act.get("page")
            book = act.get("book")
            if book:
                state.note(f"cross-book {book} {page}")
                continue
            if page and goto(state, page):
                return True
        if act.get("kind") == "send":
            name = (act.get("name") or "").lower()
            if name == "next":
                if _follow_label(state, "next"):
                    return True
                if state.index + 1 < len(state.book.pages):
                    state.index += 1
                    return True
            if name in ("previous", "back"):
                if _follow_label(state, "back"):
                    return True
                if state.index > 0:
                    state.index -= 1
                    return True
    return False


def _follow_label(state: RuntimeState, label: str) -> bool:
    page = state.page
    if not page:
        return False
    for item in page.items or []:
        if (item.get("label") or "").lower() == label and item.get("page"):
            return goto(state, item["page"])
    return False


def run_page_handlers(state: RuntimeState, kind: str = "enterpage") -> list[dict]:
    """Run handlers of the given kind on the current page."""
    page = state.page
    if not page:
        return []
    actions: list[dict] = []
    for h in page.handlers or []:
        if h.name.lower() != kind.lower():
            continue
        actions.extend(run_handler(state, h.source))
    return actions


def current_page(state: RuntimeState) -> Page | None:
    return state.page
