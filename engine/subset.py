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


_GO = re.compile(
    r'go\s+to\s+(?:(?:next|previous|prev)\s+page$|page\s*(?:"[^"]*"|\(.+\)|[A-Za-z_]\w*))',
    re.IGNORECASE,
)


def check(source: str) -> list[tuple[int, str]]:
    """Parse a script in the subset. Errors as (line number, message), first line 1.

    This is a check, not a compile. It finds what would make the reader
    stop short: a quote left open, a block left open or closed twice, a
    ``go to`` with no page, an ``if`` with no condition. Words the reader
    does not run are warnings, from ``unknown_words``, not errors.
    """
    errors: list[tuple[int, str]] = []
    open_blocks: list[tuple[str, int]] = []
    for number, raw in enumerate((source or "").replace("\r", "").split("\n"), 1):
        line = raw.strip()
        if not line or line.startswith("--"):
            continue
        if line.count('"') % 2:
            errors.append((number, "a quote is not closed"))
            continue
        low = re.sub(r"\s+", " ", line.lower())
        first = low.split(" ", 1)[0]
        if first == "to" and re.match(r"to (handle|get|set) [a-z_]\w*", low):
            open_blocks.append(("handler", number))
        elif first == "if":
            cond = low[2:].strip()
            if cond.endswith(" then") or cond == "then":
                cond = cond[:-4].strip()
            if not cond:
                errors.append((number, "if has no condition"))
            open_blocks.append(("if", number))
        elif first == "step":
            if not re.match(r"step [a-z_]\w* from .+ to .+", low):
                errors.append((number, "step needs NAME from A to B"))
            open_blocks.append(("step", number))
        elif first == "conditions":
            open_blocks.append(("conditions", number))
        elif first == "else":
            if not open_blocks or open_blocks[-1][0] != "if":
                errors.append((number, "else is not inside an if"))
        elif first == "end":
            want = low[4:].strip() or None
            if not open_blocks:
                errors.append((number, "end with nothing open"))
                continue
            kind, _ = open_blocks[-1]
            if want is not None and want != kind:
                errors.append((number, f"end {want} closes {kind}"))
                continue
            open_blocks.pop()
        elif first == "go" and not _GO.match(line):
            errors.append((number, "go to needs a page"))
    for kind, number in reversed(open_blocks):
        errors.append((number, f"{kind} is not closed with end"))
    errors.sort(key=lambda error: error[0])
    return errors
