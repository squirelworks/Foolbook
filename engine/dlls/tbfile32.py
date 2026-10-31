"""tbfile32.dll: ToolBook's file utility DLL.

A relative name is looked for beside the book, without regard to case, as
it would be on Windows.
"""

from __future__ import annotations

from pathlib import Path


def _find(state, name: str):
    name = str(name).replace("\\", "/").strip()
    if not name:
        return None
    path = Path(name)
    if path.is_absolute():
        return path if path.exists() else None
    book = getattr(state, "book", None)
    folder = Path(book.path).parent if book is not None and book.path else Path.cwd()
    for part in path.parts:
        if not folder.is_dir():
            return None
        match = next((child for child in folder.iterdir() if child.name.lower() == part.lower()), None)
        if match is None:
            return None
        folder = match
    return folder


def file_exists(state, args, refs):
    found = _find(state, (list(args) + [""])[0])
    return 1 if found is not None and found.is_file() else 0


FUNCTIONS = {
    "fileexists32": file_exists,
    "fileexists": file_exists,
}
