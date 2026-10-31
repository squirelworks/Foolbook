"""Foolbook formats.

.fbk is the Foolbook book format. It is the standard.
.fsk is the Foolbook system-book format. It is the standard.
.json is written only when the path is .json, or when an export is asked for one.

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
    """Build an .fbk or .fsk byte string.

    ``fbk`` is the Foolbook book generation. ``foolbook`` is the reader
    this file was written for. Neither one is a ToolBook rule.
    """
    from foolbook import __version__
    # The stamps go last, in one order, so a book opened and saved again
    # writes the same bytes as the save before it.
    stamped = {key: value for key, value in data.items() if key not in ("fbk", "foolbook")}
    stamped["fbk"] = FORMAT_VERSION
    stamped["foolbook"] = __version__
    magic = MAGIC.get(kind, MAGIC[FBK])
    payload = json.dumps(_share_pictures(stamped), separators=(",", ":")).encode("utf-8")
    flags = 0
    if compress:
        payload = zlib.compress(payload, 9)
        flags |= FLAG_COMPRESSED
    return magic + bytes([flags]) + payload


def unpack(blob: bytes) -> dict:
    """Read an .fbk/.fsk envelope. Plain JSON is accepted so older files still open."""
    if blob[:1] in (b"{", b"["):
        return _restore_pictures(json.loads(blob.decode("utf-8")))
    if len(blob) < 5 or blob[:4] not in MAGIC.values():
        raise ValueError("not an .fbk or .fsk")
    flags = blob[4]
    payload = blob[5:]
    if flags & FLAG_COMPRESSED:
        payload = zlib.decompress(payload)
    return _restore_pictures(json.loads(payload.decode("utf-8")))


_PICTURE_KEYS = ("data", "invert_data", "checked_data")


def _share_pictures(data: dict) -> dict:
    """One copy of each bitmap. A repeated face is a #N token.

    The same button picture is drawn on most pages. Written out each
    time, it is larger than a zlib window, so the envelope could not
    fold the copies. The token is shorter than that window.
    """
    images: list[str] = []
    index: dict[str, int] = {}

    def token(value: str) -> str:
        if len(value) < 64:
            return value
        found = index.get(value)
        if found is None:
            found = len(images)
            index[value] = found
            images.append(value)
        return f"#{found}"

    def shapes(items: list) -> list:
        out = []
        changed = False
        for shape in items:
            if not isinstance(shape, dict):
                out.append(shape)
                continue
            copy = None
            for key in _PICTURE_KEYS:
                value = shape.get(key)
                if isinstance(value, str) and len(value) >= 64:
                    if copy is None:
                        copy = dict(shape)
                    copy[key] = token(value)
            if copy is None:
                out.append(shape)
            else:
                out.append(copy)
                changed = True
        return out if changed else items

    def walk(node):
        if isinstance(node, dict):
            out = node
            for key, value in node.items():
                if key == "images":
                    continue
                if key == "shapes" and isinstance(value, list):
                    nxt = shapes(value)
                elif isinstance(value, (dict, list)):
                    nxt = walk(value)
                else:
                    continue
                if nxt is not value:
                    if out is node:
                        out = dict(node)
                    out[key] = nxt
            return out
        if isinstance(node, list):
            out = node
            for i, item in enumerate(node):
                nxt = walk(item)
                if nxt is not item:
                    if out is node:
                        out = list(node)
                    out[i] = nxt
            return out
        return node

    shared = walk(data)
    if not images:
        return data
    if shared is data:
        shared = dict(data)
    shared["images"] = images
    return shared


def _restore_pictures(data: dict) -> dict:
    images = data.get("images") if isinstance(data, dict) else None
    if not isinstance(images, list) or not images:
        return data

    def restore(shape: dict) -> dict:
        copy = None
        for key in _PICTURE_KEYS:
            value = shape.get(key)
            if not isinstance(value, str) or len(value) < 2 or value[0] != "#":
                continue
            if not value[1:].isdigit():
                continue
            number = int(value[1:])
            if number >= len(images):
                continue
            if copy is None:
                copy = dict(shape)
            copy[key] = images[number]
        return copy or shape

    def walk(node):
        if isinstance(node, dict):
            out = node
            for key, value in node.items():
                if key == "images":
                    continue
                if key == "shapes" and isinstance(value, list):
                    nxt = [restore(item) if isinstance(item, dict) else item for item in value]
                    if nxt != value:
                        if out is node:
                            out = dict(node)
                        out[key] = nxt
                elif isinstance(value, (dict, list)):
                    nxt = walk(value)
                    if nxt is not value:
                        if out is node:
                            out = dict(node)
                        out[key] = nxt
            return out
        if isinstance(node, list):
            out = node
            for i, item in enumerate(node):
                nxt = walk(item)
                if nxt is not item:
                    if out is node:
                        out = list(node)
                    out[i] = nxt
            return out
        return node

    restored = walk(data)
    if restored is data:
        restored = dict(data)
    else:
        restored = dict(restored)
    restored.pop("images", None)
    return restored


def load(path: Path) -> dict:
    path = Path(path)
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = unpack(path.read_bytes())
    data.setdefault("format", kind_of(path) if path.suffix.lower() != ".json" else "json")
    data.setdefault("format_version", FORMAT_VERSION)
    return data


def save_book(path: Path, book: dict, compress: bool = True, json_copy: bool = False) -> Path:
    """Write the book. A .json is written only when that is the path, or when asked."""
    path = Path(path)
    suffix = path.suffix.lower()
    book = dict(book)
    book.pop("format", None)
    book.pop("will_become", None)
    book["format_version"] = FORMAT_VERSION
    if suffix == ".json":
        path.write_text(json.dumps({**book, "format": "json"}, indent=2) + "\n", encoding="utf-8")
        return path
    fbk = path if suffix == ".fbk" else path.with_suffix(".fbk")
    fbk.write_bytes(pack({**book, "format": FBK}, FBK, compress=compress))
    if json_copy:
        fbk.with_suffix(".json").write_text(
            json.dumps({**book, "format": "json"}, indent=2) + "\n", encoding="utf-8"
        )
    return fbk


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
