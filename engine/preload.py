"""Open the other books a course names before the viewer asks for them.

ToolBook keeps those books open. Reading one on the click is the pause.
The names are taken from the scripts and from the file, and each book is
read in its own process so the window does not wait on the slow one.
"""

from __future__ import annotations

import multiprocessing
import re
from pathlib import Path


_REF = re.compile(
    r"(?i)(?<![A-Za-z0-9_])([A-Za-z0-9][A-Za-z0-9_-]{3,40})\.(?:tbk|sbk|fbk|fsk)\b"
)
_LIMIT = 16

_pool = None
_pending: dict = {}
_ready: dict = {}
_lock = None


def referenced(book, file_bytes: bytes | None = None) -> list[str]:
    """Book files this course names, apart from itself."""
    chunks = []
    for handler in book.handlers or []:
        chunks.append(handler.source or "")
    for page in book.pages or []:
        for handler in page.handlers or []:
            chunks.append(handler.source or "")
        for shape in page.shapes or []:
            if isinstance(shape, dict):
                chunks.append(shape.get("script") or "")
                chunks.append(shape.get("group_script") or "")
    if file_bytes:
        chunks.append(file_bytes.decode("latin1", errors="ignore"))
    self_stem = Path(book.path).stem.lower() if getattr(book, "path", None) else ""
    found = []
    seen = set()
    for chunk in chunks:
        for match in _REF.finditer(chunk or ""):
            name = match.group(0)
            stem = match.group(1).lower()
            key = name.lower()
            if stem == self_stem or key in seen or stem in seen:
                continue
            seen.add(key)
            seen.add(stem)
            found.append(name)
            if len(found) >= _LIMIT:
                return found
    return found


def _keys(name: str) -> set[str]:
    text = str(name or "")
    return {item for item in (text.lower(), Path(text).stem.lower()) if item}


def _guard():
    global _lock
    if _lock is None:
        import threading
        _lock = threading.Lock()
    return _lock


def _load_path(path: str):
    from engine.loader import load
    return load(path)


def start(book) -> None:
    """Read the books this course names. Safe to call more than once."""
    global _pool
    from engine.loader import find_book

    path = Path(book.path) if getattr(book, "path", None) else None
    blob = b""
    if path is not None and path.is_file() and path.suffix.lower() in (".tbk", ".sbk"):
        try:
            blob = path.read_bytes()
        except OSError:
            blob = b""
    names = referenced(book, blob)
    if not names or path is None:
        return
    guard = _guard()
    jobs = []
    with guard:
        for name in names:
            if any(key in _pending or key in _ready for key in _keys(name)):
                continue
            found = find_book(name, path)
            if found is None:
                continue
            keys = _keys(name) | _keys(found.name)
            if any(key in _pending or key in _ready for key in keys):
                continue
            jobs.append((found, keys))
        if not jobs:
            return
        if _pool is None:
            _pool = _make_pool()
        if _pool is None:
            return
        for found, keys in jobs:
            fut = _pool.submit(_load_path, str(found))
            for key in keys:
                _pending[key] = fut
            print(f"opening {found.name}", flush=True)


def claim(name: str):
    """The book, if a reader was started for it. Waits when it is still opening."""
    if not name:
        return None
    guard = _guard()
    with guard:
        for key in _keys(name):
            if key in _ready:
                return _ready[key]
        fut = None
        for key in _keys(name):
            fut = _pending.get(key)
            if fut is not None:
                break
    if fut is None:
        return None
    try:
        book = fut.result()
    except Exception as exc:
        print(f"fail {name}: {exc}", flush=True)
        return None
    with guard:
        for key in _keys(name) | _keys(Path(getattr(book, "path", "") or name).name):
            _ready[key] = book
            _pending.pop(key, None)
    return book


def stop() -> None:
    """Drop readers that have not finished. The window is closing."""
    global _pool
    guard = _guard()
    with guard:
        pool = _pool
        _pool = None
        _pending.clear()
    if pool is None:
        return
    procs = list(getattr(pool, "_processes", {}).values())
    pool.shutdown(wait=False, cancel_futures=True)
    for proc in procs:
        try:
            proc.terminate()
        except Exception:
            pass


def _make_pool():
    """Fork before the window exists. After that, a fresh process."""
    try:
        import tkinter
        has_window = tkinter._default_root is not None
    except Exception:
        has_window = False
    method = "spawn" if has_window else "fork"
    try:
        ctx = multiprocessing.get_context(method)
        workers = 3
        return __import__("concurrent.futures", fromlist=["ProcessPoolExecutor"]).ProcessPoolExecutor(
            max_workers=workers,
            mp_context=ctx,
        )
    except Exception as exc:
        print(f"not opening books ahead: {exc}", flush=True)
        return None
