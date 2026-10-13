"""Plain notes in the viewer.

.txt .text .md .markdown .rst .log are read as written.
.rtf is reduced to the words. The font table is not shown.
The same reduction is used when a ToolBook field is rich text.
"""

from __future__ import annotations

import re
from pathlib import Path


SUFFIXES = frozenset({".txt", ".text", ".md", ".markdown", ".rst", ".log", ".rtf"})
_SKIP_GROUP = frozenset({
    "fonttbl", "colortbl", "stylesheet", "info", "pict", "object",
    "datastore", "themedata", "xmlnstbl", "listtable", "listoverridetable",
    "generator", "mmathpr", "rsidtbl", "filetbl",
})


def is_note(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUFFIXES


def to_book(path: str | Path) -> dict:
    """One note file as a book dict the viewer already shows."""
    path = Path(path)
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".rtf" or _looks_rtf(raw):
        pages = _rtf_pages(raw)
    elif path.suffix.lower() in (".md", ".markdown", ".rst"):
        pages = _heading_pages(raw)
    else:
        pages = _plain_pages(raw)
    if not pages:
        pages = [("Note", path.stem)]
    out = []
    for i, (title, body) in enumerate(pages):
        page = {"id": title if len(pages) > 1 else path.stem, "text": [body] if body else []}
        if len(pages) > 1 and i + 1 < len(pages):
            page["items"] = [{"label": "Next", "page": pages[i + 1][0]}]
        if len(pages) > 1 and i > 0:
            page.setdefault("items", []).insert(0, {"label": "Back", "page": pages[i - 1][0]})
        out.append(page)
    seen: dict[str, int] = {}
    for page in out:
        n = seen.get(page["id"], 0)
        seen[page["id"]] = n + 1
        if n:
            page["id"] = f"{page['id']} {n + 1}"
    return {"title": path.stem, "pages": out}


def plain(value: str) -> str:
    """Leave ordinary text alone. If it is rich text, return the words."""
    if not value:
        return ""
    value = value.replace("\x00", "")
    if not _looks_rtf(value):
        return value.strip()
    return _rtf(value).strip()


def _looks_rtf(value: str) -> bool:
    head = value.lstrip()[:32].lower()
    if head.startswith("{\\rtf"):
        return True
    return "\\fonttbl" in value[:800].lower()


def _plain_pages(raw: str) -> list[tuple[str, str]]:
    parts = [plain(part) for part in raw.split("\f")]
    parts = [part for part in parts if part]
    if len(parts) <= 1:
        return [("Note", parts[0] if parts else "")]
    return [(f"P{i}", part) for i, part in enumerate(parts)]


def _heading_pages(raw: str) -> list[tuple[str, str]]:
    pages: list[tuple[str, list[str]]] = []
    title = ""
    buf: list[str] = []
    for line in raw.replace("\r\n", "\n").split("\n"):
        if line.startswith("#"):
            if title or any(part.strip() for part in buf):
                pages.append((title or "Note", buf))
            title = line.lstrip("#").strip() or "Note"
            buf = []
        else:
            buf.append(line)
    if title or any(part.strip() for part in buf):
        pages.append((title or "Note", buf))
    return [(name, plain("\n".join(lines)).strip()) for name, lines in pages]


def _rtf_pages(raw: str) -> list[tuple[str, str]]:
    text = _rtf(raw)
    parts = [part.strip() for part in text.split("\f")]
    parts = [part for part in parts if part]
    if len(parts) <= 1:
        return [("Note", parts[0] if parts else "")]
    return [(f"P{i}", part) for i, part in enumerate(parts)]


def _rtf(data: str) -> str:
    out: list[str] = []
    i = 0
    n = len(data)
    skip = [False]
    while i < n:
        c = data[i]
        if c == "{":
            skip.append(skip[-1])
            i += 1
            continue
        if c == "}":
            if len(skip) > 1:
                skip.pop()
            i += 1
            continue
        if c != "\\":
            if c not in "\r\n" and not skip[-1]:
                out.append(c)
            i += 1
            continue
        if i + 1 < n and data[i + 1] in "{}\\":
            if not skip[-1]:
                out.append(data[i + 1])
            i += 2
            continue
        if i + 1 < n and data[i + 1] == "*":
            skip[-1] = True
            i += 2
            continue
        if i + 1 < n and data[i + 1] == "'":
            token = data[i + 2:i + 4]
            i += 4
            if not skip[-1]:
                try:
                    out.append(bytes.fromhex(token).decode("cp1252"))
                except ValueError:
                    pass
            continue
        if i + 1 < n and data[i + 1] == "u" and i + 2 < n and (data[i + 2].isdigit() or data[i + 2] == "-"):
            j = i + 2
            sign = 1
            if data[j] == "-":
                sign = -1
                j += 1
            num = 0
            while j < n and data[j].isdigit():
                num = num * 10 + int(data[j])
                j += 1
            if j < n and data[j] in " ?":
                j += 1
            i = j
            if not skip[-1]:
                code = sign * num
                if code < 0:
                    code += 65536
                if 0 <= code <= 0x10FFFF:
                    out.append(chr(code))
            continue
        j = i + 1
        while j < n and data[j].isalpha():
            j += 1
        word = data[i + 1:j].lower()
        if j < n and (data[j] == "-" or data[j].isdigit()):
            if data[j] == "-":
                j += 1
            while j < n and data[j].isdigit():
                j += 1
        if j < n and data[j] == " ":
            j += 1
        i = j if word else i + 1
        if not word:
            continue
        if word in _SKIP_GROUP:
            skip[-1] = True
            continue
        if skip[-1]:
            continue
        if word in ("par", "line"):
            out.append("\n")
        elif word == "page":
            out.append("\f")
        elif word == "tab":
            out.append("\t")
    text = "".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip()
