"""The words an authored script can use and the reader acts on.

FoolbookEditor warns about a line the reader does not run. That answer is
asked of the interpreter, line by line, so it cannot drift from what the
interpreter does. ``MESSAGES`` lists the ``send`` messages that move the
reader, and its test checks each one against ``follow``.
"""

from __future__ import annotations

import re

# Messages ``send`` moves the reader with.
MESSAGES = {
    "next": "the next page",
    "previous": "the previous page",
    "back": "the previous page",
    "exit": "close the reader",
    "tryagain": "hide the page's quiz feedback; the book's results stay",
}

# Lines that open or close a block. The interpreter reads them as part of
# the block around them, so a line on its own is not judged.
_STRUCTURE = re.compile(
    r"^(?:end\b.*|else|when\b.*|to\s+(?:handle|get|set)\b.*)$",
    re.IGNORECASE,
)
_WORD = re.compile(r"[A-Za-z_]\w*")


def _runs(line: str) -> bool:
    """True when the interpreter acts on this line, rather than noting it."""
    from engine.engine import run_handler
    from foolbook.model import Book, Page, RuntimeState
    state = RuntimeState(book=Book(path="", pages=[Page(id="P1"), Page(id="P2")]))
    try:
        actions = run_handler(state, line)
    except Exception:
        return False
    return not any(a.get("kind") == "note" for a in actions)


def unknown_words(source: str) -> list[tuple[int, str]]:
    """Each line the reader's interpreter does not act on, as (line number, first word).

    The answer comes from the interpreter itself: each line is run on its own
    against an empty book, and a line the interpreter only notes is named.
    Line numbers start at 1. Blank lines, comments, and the lines that open
    or close a block are not judged.
    """
    out = []
    for number, raw in enumerate((source or "").replace("\r", "").split("\n"), 1):
        line = raw.strip()
        if not line or line.startswith("--") or _STRUCTURE.match(line):
            continue
        if _runs(line):
            continue
        words = _WORD.findall(line)
        out.append((number, words[0] if words else line))
    return out




_BLOCKS = {"if", "step", "conditions", "while", "linkdll", "linkdll32", "do"}


def check(source: str) -> list[tuple[int, str]]:
    """Parse a script in the subset. Errors as (line number, message), first line 1.

    This is a check, not a compile. It finds what would make the reader
    stop short: a quote left open, a block left open or closed twice, a
    ``go to`` with no page, an ``if`` with no condition. Words the reader
    does not run are warnings, from ``unknown_words``, not errors.

    A script with no ``to handle`` line is one handler's body, the way the
    reader runs it, so a last ``end`` or ``end NAME`` closes it. A quote may
    run onto the next line; it is an error only if the script ends inside it.
    """
    errors: list[tuple[int, str]] = []
    # (kind, line, name). A handler's name is what `end NAME` may close it with.
    open_blocks: list[tuple[str, int, str]] = []
    implicit = False
    quote_line = 0
    for number, raw in enumerate((source or "").replace("\r", "").split("\n"), 1):
        line = raw.strip()
        if quote_line:
            if line.count('"') % 2:
                quote_line = 0
                line = line.split('"', 1)[1].strip()
            else:
                continue
        if not line or line.startswith("--"):
            continue
        opened_quote = bool(line.count('"') % 2)
        if opened_quote:
            quote_line = number
            line = line.rsplit('"', 1)[0]
        low = re.sub(r"\s+", " ", line.lower())
        first = low.split(" ", 1)[0]
        header = re.match(r"(?:to (?:handle|get|set)|notifybefore|notifyafter) ([a-z_]\w*)", low)
        if not header and not open_blocks and not implicit:
            implicit = True
            open_blocks.append(("handler", number, ""))
        if header:
            open_blocks.append(("handler", number, header.group(1)))
        elif first == "if":
            cond = low[2:].strip()
            if cond.endswith(" then") or cond == "then":
                cond = cond[:-4].strip()
            if not cond:
                errors.append((number, "if has no condition"))
            open_blocks.append(("if", number, "if"))
        elif first == "step":
            if not re.match(r"step [a-z_]\w* from .+ to .+", low):
                errors.append((number, "step needs NAME from A to B"))
            open_blocks.append(("step", number, "step"))
        elif first in ("conditions", "while", "linkdll", "linkdll32", "do"):
            open_blocks.append((first, number, first))
        elif first == "until":
            if open_blocks and open_blocks[-1][0] == "do":
                open_blocks.pop()
            else:
                errors.append((number, "until with no do"))
        elif first == "else":
            if not open_blocks or open_blocks[-1][0] not in ("if", "conditions"):
                errors.append((number, "else is not inside an if or conditions"))
        elif first == "end":
            want = low[4:].strip() or None
            if not open_blocks:
                errors.append((number, "end with nothing open"))
                continue
            kind, _, name = open_blocks[-1]
            if kind == "handler" and not name and want in _BLOCKS:
                errors.append((number, "end with nothing open"))
                continue
            if want is not None and want not in (kind, name) and not (kind == "handler" and not name):
                errors.append((number, f"end {want} closes {kind}"))
                continue
            open_blocks.pop()
        elif first == "go" and not opened_quote and not re.match(r"go\s+to\s+\S", line, re.IGNORECASE):
            errors.append((number, "go to needs a page"))
    if quote_line:
        errors.append((quote_line, "a quote is not closed"))
    for kind, number, name in reversed(open_blocks):
        if kind == "handler":
            # The script's end closes a handler. NIDA books shipped with handlers
            # whose `end` was commented out (nc81trnr getWinPointer, nida81 reader).
            continue
        errors.append((number, f"{kind} is not closed with end"))
    errors.sort(key=lambda error: error[0])
    return errors
