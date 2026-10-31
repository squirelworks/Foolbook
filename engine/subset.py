"""The words an authored script can use and the reader acts on.

This is the table FoolbookEditor reads to warn about a word the reader
does not run. It is written down once, here, beside the engine that runs
the words. A line is judged by its first word. ``send`` is judged by the
message it sends, because the reader acts on only a few of them.
"""

from __future__ import annotations

import re

# First word of a line -> what the reader does with it.
COMMANDS = {
    "go": "go to page \"P\" [of book \"B\"]",
    "send": "send a message; see MESSAGES",
    "put": "put EXPR into NAME",
    "set": "set PROP of TARGET to EXPR",
    "get": "get EXPR",
    "increment": "increment NAME",
    "decrement": "decrement NAME",
    "if": "if COND [then]",
    "else": "else",
    "end": "end, end if, end step",
    "step": "step NAME from A to B [by C]",
    "forward": "forward the message to the next handler",
    "break": "end the handler",
    "beep": "beep",
    "show": "show CLASS \"name\"",
    "hide": "hide CLASS \"name\"",
    "request": "request \"text\"",
    "conditions": "conditions ... end conditions",
    "when": "when COND inside conditions",
    "system": "system TYPE NAME",
    "clear": "clear char N of NAME",
    "to": "to handle NAME",
}

# Messages ``send`` moves the reader with.
MESSAGES = {
    "next": "the next page",
    "previous": "the previous page",
    "back": "the previous page",
    "exit": "close the reader",
}

_ASSIGN = re.compile(r"^[A-Za-z_]\w*\s*=")
_WORD = re.compile(r"[A-Za-z_]\w*")


def unknown_words(source: str) -> list[tuple[int, str]]:
    """Each line whose word the reader does not run, as (line number, word).

    Line numbers start at 1. Blank lines, comments, and ``name = value``
    are not judged.
    """
    out = []
    for number, raw in enumerate((source or "").replace("\r", "").split("\n"), 1):
        line = raw.strip()
        if not line or line.startswith("--") or _ASSIGN.match(line):
            continue
        words = _WORD.findall(line)
        if not words:
            continue
        first = words[0].lower()
        if first not in COMMANDS:
            out.append((number, words[0]))
            continue
        if first == "send" and len(words) > 1 and words[1].lower() not in MESSAGES:
            out.append((number, f"send {words[1]}"))
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
