"""DLL functions a script links with `linkDLL` or `linkDLL32`.

A script names the DLL and declares its functions:

    linkDLL32 "kernel32.dll"
        INT GetPrivateProfileIntA(STRING, STRING, INT, STRING)
    end linkDLL32

A declared function is answered by a shim, one module per DLL. The file
`dlls/<stem>.py` beside the book is used first, then the same file one
folder up, where a course keeps its system books. `engine/dlls/` answers
only when neither file is there. A linked function with no shim is not
answered here.
"""

from __future__ import annotations

import importlib
import importlib.util
import re
from pathlib import Path

_DECLARE = re.compile(r"(?:(\w+)\s+)?([A-Za-z_]\w*)\s*\(([^)]*)\)\s*$")


def link(state, dll: str, declarations: list[str]) -> None:
    """Remember the DLL and the functions declared for it."""
    dll = (dll or "").strip().strip('"').lower()
    if not dll:
        return
    linked = state.variables.setdefault("__linkedDLLs", {})
    functions = linked.setdefault(dll, {})
    for line in declarations:
        found = _DECLARE.match(line.strip())
        if found:
            functions[found.group(2).lower()] = [part.strip().upper() for part in found.group(3).split(",") if part.strip()]


def unlink(state, dll: str) -> None:
    linked = state.variables.get("__linkedDLLs") or {}
    linked.pop((dll or "").strip().strip('"').lower(), None)


def linked_names(state) -> str:
    return ",".join(sorted((state.variables.get("__linkedDLLs") or {}).keys()))


def find(state, name: str):
    """(dll, shim function) for a linked function that has a shim, else None."""
    want = (name or "").lower()
    for dll, functions in (state.variables.get("__linkedDLLs") or {}).items():
        if want not in functions:
            continue
        module = _shim(state, dll)
        handler = getattr(module, "FUNCTIONS", {}).get(want) if module else None
        if handler is not None:
            return dll, handler
    return None


def _folders(state) -> list[Path]:
    """The book's folder, then the folder above it. A missing path looks nowhere."""
    book = getattr(state, "book", None)
    path = getattr(book, "path", None) if book is not None else None
    if not path:
        return []
    folder = Path(path).parent
    return [folder, folder.parent]


def _from_file(path: Path):
    spec = importlib.util.spec_from_file_location(f"bookdll.{path.stem}", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _shim(state, dll: str):
    stem = re.sub(r"\W", "_", dll.rsplit(".", 1)[0])
    for folder in _folders(state):
        found = folder / "dlls" / f"{stem}.py"
        if found.is_file():
            return _from_file(found)
    try:
        return importlib.import_module(f"engine.dlls.{stem}")
    except ImportError:
        return None
