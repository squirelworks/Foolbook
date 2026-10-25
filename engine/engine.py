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
from engine import groups


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
_REQUEST = re.compile(r'request\s+"([^"]*)"', re.IGNORECASE)
_STEP = re.compile(
    r'step\s+(\w+)\s+from\s+(.+?)\s+to\s+(.+?)(?:\s+by\s+(.+))?$',
    re.IGNORECASE,
)
_INC = re.compile(r'(increment|decrement)\s+(\w+)', re.IGNORECASE)
_ASSIGN = re.compile(r'(\w+)\s*=\s*(.+)')
_FILL = re.compile(
    r'rgbfill\s+of\s+field\s+"([^"]+)"\s*=\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)',
    re.IGNORECASE,
)
_NAME_OF = re.compile(r'name\s+of\s+this\s+(book|page)', re.IGNORECASE)
_FIELD_TEXT = re.compile(
    r'\s*(?:the\s+)?text\s+of\s+(?:field|button)\s+"([^"]+)"',
    re.IGNORECASE,
)
_LINE_OF_TEXT = re.compile(
    r'\s*(?:the\s+)?(?:text)?line\s+(\d+)\s+of\s+text\s+of\s+field\s+"([^"]+)"',
    re.IGNORECASE,
)
_TEXT_OF_FIELD = re.compile(
    r'text\s+of\s+field\s+"([^"]+)"(?:\s+of\s+this\s+page)?',
    re.IGNORECASE,
)
_CHAR_OF = re.compile(r'char\s+(\d+)\s+of\s+(\w+)', re.IGNORECASE)
_CLEAR_CHAR = re.compile(r'clear\s+char\s+(\d+)\s+of\s+(\w+)$', re.IGNORECASE)
_PROP_OF_PAGE = re.compile(r'(\w+)\s+of\s+this\s+page', re.IGNORECASE)
_BEEP = re.compile(r'beep(?:\s+\d+)?$', re.IGNORECASE)
_NUMBER = re.compile(r'[+-]?(?:\d+\.?\d*|\.\d+)')
_SET_FOCUS = re.compile(
    r'set\s+focus\s+to\s+field\s*\(?\s*"([^"]+)"\s*\)?(?:\s+of\s+this\s+page)?$',
    re.IGNORECASE,
)
_INVERT = re.compile(
    r'invert\s+of\s+button\s+"([^"]+)"',
    re.IGNORECASE,
)


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


def one_handler(script: str, name: str) -> str:
    """The body of one `to handle` in a script that holds several."""
    want = (name or "").lower()
    for handler in split_handlers(script or ""):
        if handler.name.lower() == want:
            return handler.source
    return ""


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


class _Break(Exception):
    """`break` ends the handler it is in."""


def run_handler(state: RuntimeState, source: str, parents: list[str] | None = None) -> list[dict]:
    """Execute a handler source against the current state.

    ``parents`` are the handlers of the same message further up the
    hierarchy, nearest first. ``forward`` runs the next one, then the
    handler goes on with the lines after it. The list is used up as it runs.
    """
    actions: list[dict] = []
    if not source:
        return actions
    lines = _lines(source)
    outer = state.variables.get("__parents")
    state.variables["__parents"] = parents if parents is not None else []
    try:
        _run_block(state, lines, 0, len(lines), actions)
    except _Break:
        pass
    finally:
        if outer is None:
            state.variables.pop("__parents", None)
        else:
            state.variables["__parents"] = outer
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
            parts = line.split()
            if len(parts) >= 3 and parts[-1].rstrip("[]") not in state.variables:
                kind = parts[-2].lower()
                state.variables[parts[-1].rstrip("[]")] = 0 if kind in ("int", "long", "word", "byte", "logical") else ""
            i += 1
            continue

        if low == "conditions":
            end_at = _find_conditions(lines, i + 1, end)
            _run_conditions(state, lines, i + 1, end_at, actions)
            i = end_at + 1
            continue

        if low == "forward":
            # The message goes on to the object's parent and then to the
            # default action, and this handler carries on after it. A key
            # handler is allowed or refused by this.
            actions.append({"kind": "forward"})
            parents = state.variables.get("__parents")
            if parents:
                actions.extend(run_handler(state, parents.pop(0), parents))
            i += 1
            continue

        if low == "break":
            raise _Break()

        if low in ("end conditions", "else"):
            return i + 1

        if _BEEP.match(low):
            state.variables["__beep"] = True
            actions.append({"kind": "beep"})
            i += 1
            continue

        m = _SET_FOCUS.match(line)
        if m:
            from engine import fields
            fields.focus_named(state, m.group(1))
            actions.append({"kind": "focus", "field": m.group(1)})
            i += 1
            continue

        m = _CLEAR_CHAR.match(line)
        if m:
            name = m.group(2)
            cur = _var(state, name)
            text = "" if cur is _MISSING or cur is None else str(cur)
            at = int(m.group(1)) - 1
            if 0 <= at < len(text):
                state.variables[name] = text[:at] + text[at + 1:]
            i += 1
            continue

        m = _REQUEST.match(line)
        if m:
            answer = "No"
            ask = getattr(state, "ask", None)
            if ask is not None:
                answer = ask(m.group(1)) or "No"
            state.variables["it"] = answer
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
            if name.lower() == "exit":
                state.variables["__exit"] = True
                actions.append({"kind": "exit"})
                i += 1
                continue
            if name.lower() == "keyup" and key:
                state.variables["key"] = key
                if _book_keyup(state, actions):
                    i += 1
                    continue
                if key in ("keyf2", "keyf4"):
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
            target = m.group(1).strip()
            _apply_set(state, target, value)
            actions.append({"kind": "setprop", "target": target, "value": value})
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
            # `get IncorrectEmbedded` is a call with no brackets.
            if re.fullmatch(r"[A-Za-z_]\w*", call) and _var(state, call) is _MISSING:
                call += "()"
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

        m = groups.OBJECT_SHOW.fullmatch(line)
        if m:
            groups.set_object_visible(state, m, m.group("verb").lower() == "show")
            actions.append({"kind": "setprop", "target": "visible of object", "value": m.group("verb").lower()})
            i += 1
            continue

        m = groups.GROUP_SHOW.fullmatch(line)
        if m:
            groups.set_visible(state, m, m.group("verb").lower() == "show")
            actions.append({"kind": "setprop", "target": "visible of group", "value": m.group("verb").lower()})
            i += 1
            continue

        m = _FILL.search(line)
        if m:
            _recolor(state, m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)))
            actions.append({"kind": "setprop", "target": m.group(1), "value": m.group(0)})
            i += 1
            continue

        actions.append({"kind": "note", "text": line})
        i += 1
    return i


def _recolor(state: RuntimeState, name: str, red: int, green: int, blue: int) -> None:
    """A clicked practice answer names its new fill. The page under an overlay still shows it."""
    page = state.page
    if page is None:
        return
    color = f"#{red & 255:02x}{green & 255:02x}{blue & 255:02x}"
    for shape in page.shapes or []:
        if (shape.get("name") or "").lower() == name.lower():
            shape["fill"] = color
    state.variables["__redraw"] = True


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


def _whole_quote(expr: str) -> str | None:
    """A quote that opens the expression is a string only if it also closes it."""
    if len(expr) < 2 or expr[0] not in "\"'":
        return None
    quote = expr[0]
    i = 1
    while i < len(expr):
        if expr[i] == quote:
            if quote == '"' and i + 1 < len(expr) and expr[i + 1] == '"':
                i += 2
                continue
            if i == len(expr) - 1:
                return expr[1:-1]
            return None
        i += 1
    return None


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
    quoted = _whole_quote(expr)
    if quoted is not None:
        return quoted
    if re.fullmatch(r"-?\d+", expr):
        return int(expr)
    m = _TEXT_OF_FIELD.fullmatch(expr)
    if m:
        return _field_text(state, m.group(1))
    m = _CHAR_OF.fullmatch(expr)
    if m:
        found = _var(state, m.group(2))
        text = "" if found is _MISSING or found is None else str(found)
        at = int(m.group(1)) - 1
        return text[at] if 0 <= at < len(text) else ""
    m = _PROP_OF_PAGE.fullmatch(expr)
    if m:
        return _page_property(state, m.group(1))
    m = groups.GROUP_TEST.fullmatch(expr)
    if m:
        same = groups.is_visible(state, m) == (m.group("val").lower() == "true")
        return same if m.group("op").lower() in ("is", "=") else not same
    m = groups.GROUP_VISIBLE.fullmatch(expr)
    if m:
        return groups.is_visible(state, m)
    m = groups.OBJECT_VISIBLE.fullmatch(expr)
    if m:
        return groups.object_is_visible(state, m)
    m = groups.IS_OBJECT.fullmatch(expr)
    if m:
        return groups.exists(state, m)
    if expr.startswith("(") and _closes_at_end(expr):
        return _eval(expr[1:-1], state)
    joined = _joined(expr, state)
    if joined is not _MISSING:
        return joined
    # and / or
    if " and " in low:
        i = low.index(" and ")
        return _truth(_eval(expr[:i], state)) and _truth(_eval(expr[i + 5:], state))
    if " or " in low:
        i = low.index(" or ")
        return _truth(_eval(expr[:i], state)) or _truth(_eval(expr[i + 4:], state))
    if low.startswith("not "):
        return not _truth(_eval(expr[4:], state))
    is_at = re.search(r"\bis\b", expr, re.IGNORECASE)
    if is_at:
        left = _eval(expr[:is_at.start()], state)
        named = re.search(r'"([^"]+)"', expr[is_at.end():])
        if named:
            return str(left).strip().lower() == named.group(1).lower()
        return False
    # comparisons. OpenScript does not need spaces round the operator.
    split = _split_compare(expr)
    if split is not None:
        left, op, right = split
        return _cmp(op, _eval(left, state), _eval(right, state))
    found = _var(state, expr)
    if found is not _MISSING:
        return found
    called = _call_value(expr, state)
    if called is not _NOT_A_CALL:
        return called
    if _has_arithmetic(expr):
        return _UNRESOLVED
    return expr


_MISSING = object()
# What an expression is worth when this reader cannot work it out. It is
# not text, so nothing is written from it.
_UNRESOLVED = object()
_OPERATOR = re.compile(r"[*/^]|(?<=[\w)])\s*[+-]\s*(?=[\w(])")


def _has_arithmetic(expr: str) -> bool:
    """`(a-b)` and `x+1`: sums that this reader does not do."""
    bare = re.sub(r'"[^"]*"|\'[^\']*\'', "", expr)
    return _OPERATOR.search(bare) is not None


def _var(state: RuntimeState, name: str):
    """A system property is the same word in either case.

    The book writes syslevel. The reader stores sysLevel. With no
    profile and no assignment, ToolBook is at reader level.
    """
    variables = state.variables
    if name in variables:
        return variables[name]
    low = name.lower()
    for key, value in variables.items():
        if isinstance(key, str) and key.lower() == low:
            return value
    if low == "syslevel":
        return "reader"
    if low == "keyenter":
        return 13
    if low == "keyback":
        return 8
    return _MISSING


def _joined(expr: str, state: RuntimeState):
    """OpenScript & joins two texts. && joins them with one space."""
    for op, glue in (("&&", " "), ("&", "")):
        parts = _split_join(expr, op)
        if parts is None:
            continue
        values = [_eval(part, state) for part in parts]
        # A part this reader could not work out makes the whole text unknown.
        for value in values:
            if value is not None and not isinstance(value, (str, int, float, bool)):
                return value
        return glue.join(_as_text(value) for value in values)
    return _MISSING


def _as_text(value) -> str:
    if value is None:
        return ""
    return str(value)


def _split_join(expr: str, op: str) -> list[str] | None:
    """Split on op outside quotes and parentheses. && is not two & joins."""
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    quote = ""
    i = 0
    n = len(expr)
    while i < n:
        ch = expr[i]
        if quote:
            buf.append(ch)
            if ch == quote:
                if ch == '"' and i + 1 < n and expr[i + 1] == '"':
                    buf.append(expr[i + 1])
                    i += 2
                    continue
                quote = ""
            i += 1
            continue
        if ch in "\"'":
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
        elif depth == 0 and expr.startswith(op, i):
            if op == "&" and i + 1 < n and expr[i + 1] == "&":
                buf.append("&")
                i += 1
                continue
            parts.append("".join(buf).strip())
            buf = []
            i += len(op)
            continue
        buf.append(ch)
        i += 1
    if not parts:
        return None
    parts.append("".join(buf).strip())
    return parts


def _flag(value) -> bool:
    return value if isinstance(value, bool) else str(value).lower() not in ("", "false", "0", "none")


def _apply_set(state: RuntimeState, target: str, value) -> None:
    """set text of field "First" changes the field the window draws.

    set invert of button "Selection1" to true sinks that button. The
    checked picture is not this face.
    """
    page = state.page
    shown = groups.GROUP_VISIBLE.fullmatch(target or "")
    if shown is not None:
        groups.set_visible(state, shown, _flag(value))
        return
    shown = groups.OBJECT_VISIBLE.fullmatch(target or "")
    if shown is not None:
        groups.set_object_visible(state, shown, _flag(value))
        return
    invert = _INVERT.search(target or "")
    if invert is not None and page is not None:
        flag = _flag(value)
        name = invert.group(1).lower()
        for shape in page.shapes or []:
            if (shape.get("name") or "").lower() != name or (shape.get("kind") or "") == "text":
                continue
            shape["invert"] = flag
        state.variables["__redraw"] = True
        return
    # A value this reader could not work out is not text.
    if value is not None and not isinstance(value, (str, int, float, bool)):
        return
    # `textline 3 of text of field "x"` is one line of the text, not all of it.
    part = _LINE_OF_TEXT.match(target or "")
    if part is not None and page is not None:
        number = max(1, int(part.group(1)))
        name = part.group(2).lower()
        for shape in page.shapes or []:
            if (shape.get("name") or "").lower() != name:
                continue
            lines = str(shape.get("text") or "").split("\n")
            lines += [""] * (number - len(lines))
            lines[number - 1] = "" if value is None else str(value)
            set_shape_text(state, shape, "\n".join(lines))
        return
    match = _FIELD_TEXT.match(target or "")
    if match is None or page is None:
        return
    text = "" if value is None else str(value)
    # __nidaVersion of this book is a property this reader has not
    # found. Leaving the name in the field wiped "2.003.0001".
    if "__" in text and "of this book" in text.lower():
        return
    name = match.group(1).lower()
    for shape in page.shapes or []:
        if (shape.get("name") or "").lower() != name:
            continue
        set_shape_text(state, shape, text)


def set_shape_text(state: RuntimeState, shape: dict, text: str) -> None:
    """Put new text in a field and ask the window to draw it."""
    old = shape.get("text") or ""
    runs = shape.get("runs") or []
    # One run over the whole field is the field's face. A longer
    # sentence keeps it, or the tail falls back to the record size.
    if len(runs) == 1:
        run = runs[0]
        if int(run.get("start") or 0) <= 0 and int(run.get("end") or 0) >= len(old):
            run["end"] = len(text)
    shape["text"] = text
    state.variables["__redraw"] = True


def _split_compare(expr: str):
    """(left, operator, right) at the first comparison outside quotes and brackets."""
    quote = ""
    depth = 0
    i = 0
    n = len(expr)
    while i < n:
        ch = expr[i]
        if quote:
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch in "\"'":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
        elif depth == 0:
            for op in ("<>", "!=", "<=", ">=", "<", ">", "="):
                if expr.startswith(op, i):
                    left, right = expr[:i].strip(), expr[i + len(op):].strip()
                    if left and right:
                        return left, op, right
                    return None
        i += 1
    return None


def _closes_at_end(expr: str) -> bool:
    """The bracket that opens the expression is the one that closes it."""
    depth = 0
    quote = ""
    for i, ch in enumerate(expr):
        if quote:
            if ch == quote:
                quote = ""
            continue
        if ch in "\"'":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i == len(expr) - 1
    return False


def _field_text(state: RuntimeState, name: str) -> str:
    """`text of field "Response"` is what is in the field now."""
    page = state.page
    for shape in (page.shapes if page is not None else None) or []:
        if (shape.get("name") or "").lower() == name.lower() and (shape.get("kind") or "") == "text":
            return str(shape.get("text") or "")
    return ""


def _page_property(state: RuntimeState, name: str):
    """`testno of this page` is a property stored on the page."""
    page = state.page
    props = ((page.raw or {}).get("props") or {}) if page is not None else {}
    for key, value in props.items():
        if str(key).lower() == name.lower():
            text = str(value)
            return int(text) if re.fullmatch(r"-?\d+", text) else text
    return ""


def _number(value):
    """The number a value stands for, or None when it is not one."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and _NUMBER.fullmatch(value.strip()):
        return float(value)
    return None


def _cmp(op: str, a, b) -> bool:
    """`=` is a number compare when both sides are numbers, 7 and "07" and "+7.0"
    alike, and a compare that ignores case when they are text."""
    x, y = _number(a), _number(b)
    if x is not None and y is not None:
        a, b = x, y
    elif isinstance(a, str) and isinstance(b, str):
        a, b = a.lower(), b.lower()
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
    if match.group(1).lower() == "getfirst":
        # No INI on this machine. The profile default for First is Student.
        found = _var(state, "__studentFirst")
        text = "" if found is _MISSING or found is None else str(found).strip()
        return text or "Student"
    from engine.menu import call as menu_call
    from engine.menu import _UNKNOWN as menu_unknown
    hit = menu_call(state, match.group(1), match.group(2))
    if hit is not menu_unknown:
        return hit
    from engine.fillin import call as fillin_call
    from engine.fillin import _UNKNOWN as fillin_unknown
    hit = fillin_call(state, match.group(1), match.group(2))
    if hit is not fillin_unknown:
        return hit
    from engine.quiz import call
    return call(state, match.group(1), match.group(2))


def _find_conditions(lines: list[str], start: int, end: int) -> int:
    depth = 0
    for i in range(start, end):
        low = lines[i].lower()
        if low == "conditions":
            depth += 1
        elif low == "end conditions" or (low == "end" and depth == 0):
            if depth == 0:
                return i
            depth -= 1
    return end


def _run_conditions(state: RuntimeState, lines: list[str], start: int, end: int, actions: list[dict]) -> None:
    """OpenScript `conditions` / `when`. The first true branch runs."""
    branches = []
    otherwise = None
    depth = 0
    for i in range(start, end):
        low = lines[i].lower()
        if low == "conditions":
            depth += 1
        elif low == "end conditions":
            depth = max(0, depth - 1)
        elif depth == 0 and low.startswith("when "):
            branches.append(i)
        elif depth == 0 and low == "else":
            otherwise = i
    for index, at in enumerate(branches):
        nxt = branches[index + 1] if index + 1 < len(branches) else (otherwise if otherwise is not None else end)
        if _truth(_eval(lines[at][5:].strip(), state)):
            _run_block(state, lines, at + 1, nxt, actions)
            return
    if otherwise is not None:
        _run_block(state, lines, otherwise + 1, end, actions)


def _book_keyup(state: RuntimeState, actions: list[dict]) -> bool:
    """The lesson's own key handler. F2 asks before it exits."""
    book = state.book
    if book is None:
        return False
    ran = False
    for handler in book.handlers or []:
        if handler.name.lower() != "keyup":
            continue
        if "keyf2" not in (handler.source or "").lower():
            continue
        actions.extend(run_handler(state, handler.source))
        ran = True
    return ran


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


def leave_page(state: RuntimeState) -> None:
    """The page being left. P1910 and P2910 set the menu flag here."""
    if state.page is None:
        return
    from engine import fields
    fields.blur(state)
    run_page_handlers(state, "leavepage")


def goto(state: RuntimeState, page_id: str, leave: bool = True) -> bool:
    idx = state.book.index_of(page_id)
    if idx < 0:
        # case-insensitive fallback; real books mix P1292 and p1292
        for i, p in enumerate(state.book.pages):
            if p.id.lower() == page_id.lower():
                if leave and i != state.index:
                    leave_page(state)
                    state.index = i
                elif i != state.index:
                    state.index = i
                state.note(f"goto {p.id}")
                return True
        state.note(f"missing page {page_id}")
        return False
    if leave and idx != state.index:
        leave_page(state)
    state.index = idx
    state.note(f"goto {page_id}")
    return True


def _token(state: RuntimeState, quoted: str | None, bare: str | None):
    """A quoted name, or a variable such as nextpage and lastbook."""
    if quoted:
        return quoted
    if not bare:
        return None
    found = _var(state, bare)
    if found is not _MISSING:
        return "" if found is None else str(found)
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
    previous_book = state.book
    previous_index = state.index
    _remember(state)
    book = _shelved(state, book_name)
    if book is None:
        from engine.preload import claim
        book = claim(book_name)
    fresh = book is None
    if fresh:
        found = find_book(book_name, state.book.path)
        if not found:
            state.note(f"missing book {book_name}")
            return False
        book = load(found)
    if state.page is not None:
        leave_page(state)
    state.book = book
    state.index = state.where.get(id(book), 0)
    state.note(f"open {Path(book.path).name}")
    if fresh:
        enter_book(state)
    if page_id:
        ok = goto(state, page_id, leave=False)
        if not ok:
            # The other book is open, but the page is not in it. Stay here.
            state.book = previous_book
            state.index = previous_index
            _remember(state)
            return False
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
            if name.lower() == "okclicked":
                from engine.quiz import finish
                result = finish(state)
                if isinstance(result, tuple) and result and result[0] == "goto" and result[1]:
                    return goto(state, result[1])
                return False
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
    # The page's handler, then the background's. A forward in the first
    # runs the next at that line. Whatever is still waiting runs after it.
    queue = [h.source for h in page.handlers or [] if h.name.lower() == kind.lower()]
    while queue:
        actions.extend(run_handler(state, queue.pop(0), queue))
    return actions


def enter_page(state: RuntimeState, hops: int = 8) -> bool:
    """Run enterPage and follow it. A ToolBook page is this source, not a new graphics pass."""
    start = state.index
    for _ in range(hops):
        if not follow(state, run_page_handlers(state, "enterpage")):
            break
    _reader_score(state)
    return state.index != start


def _reader_score(state: RuntimeState) -> None:
    """P10303's score handler is not stored on the page.

    At reader level the line already says where the percent goes.
    Author level is the one that still shows XX.
    """
    if str(_var(state, "sysLevel")).lower() != "reader" or state.page is None:
        return
    from engine.quiz import _percent
    number = str(_percent(state))
    for shape in state.page.shapes or []:
        if (shape.get("name") or "").lower() != "stem":
            continue
        text = shape.get("text")
        if not isinstance(text, str) or "XX" not in text:
            continue
        low = text.lower()
        if "xx%" not in low and "your score is" not in low:
            continue
        shape["text"] = text.replace("XX", number)
        state.variables["__redraw"] = True


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
        leave_page(state)
        state.index += 1
        return True
    if low in ("back", "previous") and state.index > 0:
        leave_page(state)
        state.index -= 1
        return True
    return False
