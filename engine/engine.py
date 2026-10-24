"""OpenScript engine.

Runs handler source and returns actions the viewer should perform.
The same runner serves .tbk/.sbk (decoded source) and .fbk/.fsk (authored source).

Handled:
  go to page "P" [of book "B"]
  send NAME
  NAME = EXPR
  put EXPR into NAME
  set PROP of TARGET to EXPR
  get EXPR
  increment / decrement NAME
  if / else / end if (nested)
  step NAME from A to B
  name of this book / name of this page
  system declarations (ignored)
  stops at the first standalone end, so trailing decode garbage is dropped
"""

from __future__ import annotations

import re
from pathlib import Path
from foolbook.model import RuntimeState, Page


_GOTO = re.compile(
    r'go\s+to\s+page\s*'
    r'(?:\(\s*"([^"]+)"\s*\)|"([^"]+)"|\(\s*([A-Za-z_]\w*)\s*\)|([A-Za-z_]\w*))'
    r'(?:\s+of\s+book\s*'
    r'(?:\(\s*"([^"]+)"\s*\)|"([^"]+)"|\(\s*([A-Za-z_]\w*)\s*\)|([A-Za-z_]\w*))'
    r')?',
    re.IGNORECASE,
)
_SEND = re.compile(r'send\s+(\w+)(?:\s+(\w+))?', re.IGNORECASE)
_PUT = re.compile(r'put\s+(.+?)\s+into\s+(\w+)', re.IGNORECASE)
_SET = re.compile(r'set\s+(.+?)\s+to\s+(.+)', re.IGNORECASE)
_GET = re.compile(r'get\s+(.+)', re.IGNORECASE)
_STEP = re.compile(
    r'step\s+(\w+)\s+from\s+(.+?)\s+to\s+(.+?)(?:\s+by\s+(.+))?$',
    re.IGNORECASE,
)
_INC = re.compile(r'(increment|decrement)\s+(\w+)', re.IGNORECASE)
_ASSIGN = re.compile(r'(\w+)\s*=\s*(.+)')
_NAME_OF = re.compile(r'name\s+of\s+this\s+(book|page)', re.IGNORECASE)


_TO_HANDLE = re.compile(
    r"(?im)^[ \t]*to[ \t]+(?:handle|get|set)[ \t]+([A-Za-z_][A-Za-z0-9_]*)"
)


def split_handlers(source: str) -> list[Handler]:
    """Split a ToolBook script into one block per `to handle`, `to get`, or `to set`.

    A system book closes an `if` with `end`, the same word that closes the
    handler. The handler's own `end` is removed here so the runner can keep
    the inner ones.
    """
    from foolbook.model import Handler
    if not source:
        return []
    matches = list(_TO_HANDLE.finditer(source))
    out = []
    for i, match in enumerate(matches):
        stop = matches[i + 1].start() if i + 1 < len(matches) else len(source)
        body = _strip_handler_end(source[match.end():stop])
        out.append(Handler(name=match.group(1), source=body))
    return out


def _strip_handler_end(body: str) -> str:
    lines = body.replace("\r", "").split("\n")
    depth = 0
    cut = None
    for i, raw in enumerate(lines):
        low = raw.strip().lower()
        if not low or low.startswith("--"):
            continue
        if low.startswith("if ") or low.startswith("step ") or low.startswith("conditions"):
            depth += 1
            continue
        if low in ("end", "end if", "end step", "end handler"):
            if depth == 0:
                cut = i
                break
            depth -= 1
    if cut is None:
        return body
    return "\n".join(lines[:cut])


def click_script(obj: dict | None) -> str:
    """The buttonClick a click should run.

    The object's own script wins when it handles the click. Otherwise the
    group's script runs. A field's mouse handlers are not that click.
    """
    if not obj:
        return ""
    own = obj.get("script") or ""
    if "buttonclick" in own.lower():
        return own
    return obj.get("group_script") or ""


def run_handler(state: RuntimeState, source: str) -> list[dict]:
    """Execute a handler source against the current state."""
    actions: list[dict] = []
    if not source:
        return actions
    lines = _lines(source)
    _run_block(state, lines, 0, len(lines), actions)
    return actions


def _lines(source: str) -> list[str]:
    """Normalize and stop at the first standalone end."""
    out = []
    for raw in source.replace("\r", "").split("\n"):
        line = raw.strip()
        if not line or line.startswith("--"):
            continue
        low = line.lower()
        if low.startswith("to handle"):
            continue
        if low in ("end handler",):
            break
        out.append(line)
    return out


def _run_block(state: RuntimeState, lines: list[str], start: int, end: int, actions: list[dict]) -> int:
    """Run lines[start:end]. Returns the index after the block consumed."""
    i = start
    while i < end:
        line = lines[i]
        low = line.lower()

        if low.startswith("if "):
            cond = line[3:].strip()
            if cond.lower().endswith(" then"):
                cond = cond[:-5].strip()
            body_start = i + 1
            else_at, end_at = _split_if(lines, body_start, end)
            if _truth(_eval(cond, state)):
                _run_block(state, lines, body_start, else_at, actions)
            elif else_at < end_at:
                _run_block(state, lines, else_at + 1, end_at, actions)
            i = end_at + 1
            continue

        if low.startswith("step "):
            m = _STEP.match(line)
            if m:
                name, a, b, by = m.group(1), m.group(2), m.group(3), m.group(4)
                body_start = i + 1
                end_at = _find_end_step(lines, body_start, end)
                _run_step(state, name, a, b, by, lines, body_start, end_at, actions)
                i = end_at + 1
                continue

        if low.startswith("system "):
            i += 1
            continue

        m = _GOTO.search(line)
        if m:
            actions.append({
                "kind": "goto",
                "page": _token(state, m.group(1) or m.group(2), m.group(3) or m.group(4)),
                "book": _token(state, m.group(5) or m.group(6), m.group(7) or m.group(8)),
            })
            i += 1
            continue
        m = _SEND.search(line)
        if m:
            name = m.group(1)
            key = (m.group(2) or "").lower()
            if name.lower() == "keyup" and key in ("keyf2", "keyf4"):
                page, book = _menu_return(state, key)
                if page:
                    actions.append({"kind": "goto", "page": page, "book": book})
                i += 1
                continue
            actions.append({"kind": "send", "name": name})
            i += 1
            continue
        m = _PUT.match(line)
        if m:
            value = _eval(m.group(1), state)
            state.variables[m.group(2)] = value
            actions.append({"kind": "set", "name": m.group(2), "value": value})
            i += 1
            continue
        m = _SET.match(line)
        if m:
            value = _eval(m.group(2), state)
            actions.append({"kind": "setprop", "target": m.group(1).strip(), "value": value})
            i += 1
            continue
        m = _GET.match(line)
        if m:
            call = m.group(1).strip()
            page = _builtin_page(state, call)
            if page:
                actions.append({"kind": "goto", "page": page, "book": None})
                i += 1
                continue
            value = _eval(call, state)
            if isinstance(value, tuple) and value and value[0] == "goto":
                actions.append({
                    "kind": "goto",
                    "page": value[1],
                    "book": value[2] if len(value) > 2 else None,
                })
            else:
                actions.append({"kind": "get", "expr": call, "value": value})
            i += 1
            continue
        m = _INC.match(line)
        if m:
            name = m.group(2)
            cur = state.variables.get(name, 0)
            try:
                cur = int(cur)
            except (TypeError, ValueError):
                cur = 0
            cur = cur + 1 if m.group(1).lower() == "increment" else cur - 1
            state.variables[name] = cur
            actions.append({"kind": "set", "name": name, "value": cur})
            i += 1
            continue
        m = _ASSIGN.match(line)
        if m and not low.startswith("if "):
            name, expr = m.group(1), m.group(2).strip().rstrip(".")
            value = _eval(expr, state)
            state.variables[name] = value
            actions.append({"kind": "set", "name": name, "value": value})
            i += 1
            continue

        actions.append({"kind": "note", "text": line})
        i += 1
    return i


def _split_if(lines: list[str], start: int, end: int) -> tuple[int, int]:
    """Return (else_index_or_end, end_if_index) for the if that opened before start."""
    depth = 1
    else_at = end
    for i in range(start, end):
        low = lines[i].lower()
        if low.startswith("if "):
            depth += 1
        elif low.startswith("else") and depth == 1 and else_at == end:
            else_at = i
        elif low in ("end", "end if"):
            depth -= 1
            if depth == 0:
                return (else_at if else_at < i else i), i
    return end, end


def _find_end_step(lines: list[str], start: int, end: int) -> int:
    depth = 1
    for i in range(start, end):
        low = lines[i].lower()
        if low.startswith("step "):
            depth += 1
        elif low in ("end", "end step"):
            depth -= 1
            if depth == 0:
                return i
    return end


def _run_step(state, name, a, b, by, lines, start, end, actions):
    try:
        lo = int(_eval(a, state))
        hi = int(_eval(b, state))
        step = int(_eval(by, state)) if by else 1
    except (TypeError, ValueError):
        actions.append({"kind": "note", "text": f"step {name} not numeric"})
        return
    if step == 0:
        return
    cur = lo
    guard = 0
    while (cur <= hi if step > 0 else cur >= hi) and guard < 10000:
        state.variables[name] = cur
        _run_block(state, lines, start, end, actions)
        cur += step
        guard += 1


def _eval(expr: str, state: RuntimeState):
    """Evaluate a small OpenScript expression."""
    expr = expr.strip().rstrip(".")
    if not expr:
        return ""
    low = expr.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low == "null":
        return None
    m = _NAME_OF.fullmatch(expr)
    if m:
        if m.group(1).lower() == "book":
            return state.book.title or state.book.path
        page = state.page
        return page.id if page else ""
    if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
        return expr[1:-1]
    if re.fullmatch(r"-?\d+", expr):
        return int(expr)
    # and / or
    if " and " in low:
        i = low.index(" and ")
        return _truth(_eval(expr[:i], state)) and _truth(_eval(expr[i + 5:], state))
    if " or " in low:
        i = low.index(" or ")
        return _truth(_eval(expr[:i], state)) or _truth(_eval(expr[i + 4:], state))
    if low.startswith("not "):
        return not _truth(_eval(expr[4:], state))
    # comparisons, longest operator first
    padded = f" {expr} "
    for op in (" <> ", " != ", " <= ", " >= ", " < ", " > ", " = "):
        idx = padded.find(op)
        if idx >= 0:
            left = padded[:idx].strip()
            right = padded[idx + len(op):].strip()
            return _cmp(op.strip(), _eval(left, state), _eval(right, state))
    if expr in state.variables:
        return state.variables[expr]
    called = _call_value(expr, state)
    if called is not _NOT_A_CALL:
        return called
    return expr


def _cmp(op: str, a, b) -> bool:
    if op in ("=",):
        return a == b
    if op in ("<>", "!="):
        return a != b
    try:
        if op == "<":
            return a < b
        if op == ">":
            return a > b
        if op == "<=":
            return a <= b
        if op == ">=":
            return a >= b
    except TypeError:
        return False
    return False


def _truth(value) -> bool:
    if isinstance(value, str):
        return value.lower() not in ("", "false", "0")
    return bool(value)


_NOT_A_CALL = object()


def _call_value(expr: str, state: RuntimeState):
    match = re.fullmatch(r"([A-Za-z_]\w*)\s*\((.*)\)", expr.strip(), re.DOTALL)
    if not match:
        return _NOT_A_CALL
    from engine.quiz import call
    return call(state, match.group(1), match.group(2))


def _menu_return(state: RuntimeState, key: str) -> tuple[str, str | None]:
    """F4 is the lesson menu. F2 is Exit the Lesson.

    Exit quits. From another book, the lesson that opened it is the menu
    to return to. On the menu page itself there is nowhere further to go.
    """
    last = str(state.variables.get("lastbook") or "")
    here = ""
    if state.book is not None:
        here = Path(state.book.path).stem
    other = bool(last) and last.lower() != here.lower()
    if key == "keyf4" or (key == "keyf2" and other):
        if other:
            return "P900", last
        if _has_page(state, "P900") and (state.page is None or state.page.id.lower() != "p900"):
            return "P900", None
    return "", None


def _lesson_mode(state: RuntimeState) -> int:
    """The INI default is 2. Mode 0 and 1 are the assessment and the pretest."""
    value = state.variables.get("__lessonMode", 2)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 2


def _has_page(state: RuntimeState, page_id: str) -> bool:
    book = state.book
    if book is None:
        return False
    return any(page.id.lower() == page_id.lower() for page in book.pages)


def _builtin_page(state: RuntimeState, call: str) -> str | None:
    """Pages named by nc81base, which the book calls and does not inline.

    Lesson mode defaults to 2, so the menu is P900 and the final quiz is
    P10004. Mode 1 is the pretest, and that quiz is P10003.
    """
    name = call.strip().rstrip("()").split("(")[0].strip().lower()
    if name == "gotomenupage":
        mode = _lesson_mode(state)
        assess = state.variables.get("__quizAssessment", 0) or 0
        pretest = state.variables.get("__quizPreTest", 0) or 0
        page = "P900"
        if mode == 0 and int(assess) == 0:
            page = "P10001"
        elif mode == 1 and int(pretest) == 0:
            page = "P10002"
        return page if _has_page(state, page) else "P900"
    if name == "gotoquizpage":
        page = "P10003" if _lesson_mode(state) == 1 else "P10004"
        return page if _has_page(state, page) else "P900"
    return None


def goto(state: RuntimeState, page_id: str) -> bool:
    idx = state.book.index_of(page_id)
    if idx < 0:
        # case-insensitive fallback; real books mix P1292 and p1292
        for i, p in enumerate(state.book.pages):
            if p.id.lower() == page_id.lower():
                state.index = i
                state.note(f"goto {p.id}")
                return True
        state.note(f"missing page {page_id}")
        return False
    state.index = idx
    state.note(f"goto {page_id}")
    return True


def _token(state: RuntimeState, quoted: str | None, bare: str | None):
    """A quoted name, or a variable such as nextpage and lastbook."""
    if quoted:
        return quoted
    if not bare:
        return None
    if bare in state.variables:
        value = state.variables[bare]
        return "" if value is None else str(value)
    return bare


def _book_keys(book) -> set[str]:
    path = Path(book.path) if book.path else None
    keys = set()
    if path is not None:
        keys.add(path.stem.lower())
        keys.add(path.name.lower())
    if book.title:
        keys.add(str(book.title).lower())
    return {key for key in keys if key}


def _remember(state: RuntimeState) -> None:
    book = state.book
    if book is None:
        return
    state.where[id(book)] = state.index
    for key in _book_keys(book):
        state.shelf[key] = book


def _shelved(state: RuntimeState, name: str):
    if not name:
        return None
    found = state.shelf.get(name.lower())
    if found is not None:
        return found
    return state.shelf.get(Path(name).stem.lower())


def open_book(state: RuntimeState, book_name: str, page_id: str) -> bool:
    """Show a book that is already open, or open it and keep the previous one.

    ToolBook leaves the caller's pages in memory. The return is
    ``go to page (nextpage) of book(lastbook)``, and lastbook is the
    book still on the shelf, not a file searched for again.
    """
    from engine.loader import load, find_book
    _remember(state)
    book = _shelved(state, book_name)
    fresh = book is None
    if fresh:
        found = find_book(book_name, state.book.path)
        if not found:
            state.note(f"missing book {book_name}")
            return False
        book = load(found)
    state.book = book
    state.index = state.where.get(id(book), 0)
    state.note(f"open {Path(book.path).name}")
    if fresh:
        enter_book(state)
    if page_id:
        ok = goto(state, page_id)
        _remember(state)
        return ok
    _remember(state)
    return True


def follow(state: RuntimeState, actions: list[dict]) -> bool:
    """Apply the first navigation action. Returns True if the page changed."""
    for act in actions:
        if act.get("kind") == "goto":
            page = act.get("page")
            book = act.get("book")
            if book:
                return open_book(state, book, page or "")
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


def enter_book(state: RuntimeState) -> bool:
    """Run the book's enterBook handler once. ToolBook does this on open."""
    actions: list[dict] = []
    for handler in state.book.handlers or []:
        if handler.name.lower() != "enterbook":
            continue
        actions.extend(run_handler(state, handler.source))
    return follow(state, actions)


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


def enter_page(state: RuntimeState, hops: int = 8) -> bool:
    """Run enterPage and follow it. A ToolBook page is this source, not a new graphics pass."""
    start = state.index
    for _ in range(hops):
        if not follow(state, run_page_handlers(state, "enterpage")):
            break
    return state.index != start


def press(state: RuntimeState, label: str = "", target: str = "") -> bool:
    """A button in the window.

    buttonClick runs first, so a ToolBook handler is what moves the page.
    The button's own page is used when that handler does not navigate.
    Nothing else is invented.
    """
    start = (id(state.book), state.index)
    if follow(state, run_page_handlers(state, "buttonclick")):
        return True
    if target and goto(state, target):
        return (id(state.book), state.index) != start
    low = (label or "").lower()
    if low == "next" and state.index + 1 < len(state.book.pages):
        state.index += 1
        return True
    if low in ("back", "previous") and state.index > 0:
        state.index -= 1
        return True
    return False
