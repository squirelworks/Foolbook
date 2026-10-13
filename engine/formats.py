"""Foolbook formats.

.fbk is the Foolbook book format. It is the standard.
.fsk is the Foolbook system-book format. It is the standard.
.json is the working copy.

.fbk and .fsk are not renamed JSON. They are a small binary envelope:

    4 bytes  magic   FBK1 or FSK1
    1 byte   flags   bit 0 set means the payload is zlib-compressed
    rest     payload JSON bytes, compressed or not

The engine reads all three. .tbk and .sbk remain the backward-compatible path.
"""

from __future__ import annotations

import json
import zlib
from pathlib import Path


FBK = "fbk"
FSK = "fsk"
FSC = "fsc"
FORMAT_VERSION = 1
MAGIC = {FBK: b"FBK1", FSK: b"FSK1", FSC: b"FSC1"}
FLAG_COMPRESSED = 0x01


def is_book(path: Path) -> bool:
    return path.suffix.lower() in (".fbk", ".json")


def is_system(path: Path) -> bool:
    return path.suffix.lower() == ".fsk"


def kind_of(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".fsk":
        return FSK
    if suffix == ".fsc":
        return FSC
    return FBK


def pack(data: dict, kind: str = FBK, compress: bool = True) -> bytes:
    """Build an .fbk or .fsk byte string."""
    magic = MAGIC.get(kind, MAGIC[FBK])
    payload = json.dumps(data, separators=(",", ":")).encode("utf-8")
    flags = 0
    if compress:
        payload = zlib.compress(payload, 9)
        flags |= FLAG_COMPRESSED
    return magic + bytes([flags]) + payload


def unpack(blob: bytes) -> dict:
    """Read an .fbk/.fsk envelope. Plain JSON is accepted so older files still open."""
    if blob[:1] in (b"{", b"["):
        return json.loads(blob.decode("utf-8"))
    if len(blob) < 5 or blob[:4] not in MAGIC.values():
        raise ValueError("not an .fbk or .fsk")
    flags = blob[4]
    payload = blob[5:]
    if flags & FLAG_COMPRESSED:
        payload = zlib.decompress(payload)
    return json.loads(payload.decode("utf-8"))


def load(path: Path) -> dict:
    path = Path(path)
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = unpack(path.read_bytes())
    data.setdefault("format", kind_of(path) if path.suffix.lower() != ".json" else "json")
    data.setdefault("format_version", FORMAT_VERSION)
    return data


def save_book(path: Path, book: dict, compress: bool = True) -> Path:
    """Write a .json working copy and a sibling .fbk."""
    path = Path(path)
    if path.suffix.lower() != ".json":
        path = path.with_suffix(".json")
    book = dict(book)
    book.pop("format", None)
    book.pop("will_become", None)
    book["format_version"] = FORMAT_VERSION
    path.write_text(json.dumps({**book, "format": "json"}, indent=2) + "\n", encoding="utf-8")

    fbk = path.with_suffix(".fbk")
    fbk.write_bytes(pack({**book, "format": FBK}, FBK, compress=compress))
    return path


def save_system(path: Path, system: dict, compress: bool = True) -> Path:
    """Write an .fsk."""
    path = Path(path)
    if path.suffix.lower() != ".fsk":
        path = path.with_suffix(".fsk")
    system = dict(system)
    system.pop("will_become", None)
    system["format"] = FSK
    system["format_version"] = FORMAT_VERSION
    path.write_bytes(pack(system, FSK, compress=compress))
    return path


def save_fsc(path: Path, book: dict, compress: bool = True) -> Path:
    """Write an .fsc. Same envelope as a book, different magic."""
    path = Path(path)
    if path.suffix.lower() != ".fsc":
        path = path.with_suffix(".fsc")
    book = dict(book)
    book.pop("will_become", None)
    book["format"] = FSC
    book["format_version"] = FORMAT_VERSION
    path.write_bytes(pack(book, FSC, compress=compress))
    return path
