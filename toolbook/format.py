"""Recognize a ToolBook file by what is inside it, not by its name."""

from __future__ import annotations

from pathlib import Path

# Click2learn shell: the book object lives at 0xC00 and starts with this word.
_BOOK = b"\x22\x22\x22\x22"
_AT = 0xC00
# The object store used by a real .tbk / .sbk.
_STORE = b"\x03JBO"


def is_toolbook(path: str | Path | bytes) -> bool:
    """True when the bytes are a ToolBook shell or object store.

    An .fbk envelope is never ToolBook, even if the name says otherwise.
    A ToolBook file renamed to .fbk still is.
    """
    blob = _head(path)
    if len(blob) < 4:
        return False
    if blob[:4] in (b"FBK1", b"FSK1", b"FSC1") or blob[:1] in (b"{", b"["):
        return False
    if _STORE in blob[:0x1000]:
        return True
    return len(blob) >= _AT + 4 and blob[_AT:_AT + 4] == _BOOK


def _head(path: str | Path | bytes) -> bytes:
    if isinstance(path, (bytes, bytearray)):
        return bytes(path[:0x1004])
    file = Path(path)
    if not file.is_file():
        return b""
    try:
        with file.open("rb") as handle:
            return handle.read(0x1004)
    except OSError:
        return b""
