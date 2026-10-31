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
