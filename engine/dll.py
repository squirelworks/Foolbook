"""DLL functions a script links with `linkDLL` or `linkDLL32`.

A script names the DLL and declares its functions:

    linkDLL32 "kernel32.dll"
        INT GetPrivateProfileIntA(STRING, STRING, INT, STRING)
    end linkDLL32

A declared function is answered by a shim in engine/dlls/, one module per
DLL, when there is one. A DLL with no shim is linked by name only, and a
call to it is not answered here.
"""

from __future__ import annotations

import importlib
import re

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
        module = _shim(dll)
        handler = getattr(module, "FUNCTIONS", {}).get(want) if module else None
        if handler is not None:
            return dll, handler
    return None


def _shim(dll: str):
    stem = re.sub(r"\W", "_", dll.rsplit(".", 1)[0])
    try:
        return importlib.import_module(f"engine.dlls.{stem}")
    except ImportError:
        return None
