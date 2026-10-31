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
