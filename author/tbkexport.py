"""Best-effort .tbk writer.

What we know, from the course books and TB80CMP:

  stub            0xC00 bytes, book at ZZZTBKBOOKLOC
  signature       03 4A 42 4F, version 01 00 00 08
  page record     80 65 00 05 00 02 02, id, 32-byte name, 14 00 00 01
  field text      Text\0\0, 8 bytes, u16 length, string
  handler         OpenScript bytecode from engine.openscript.compile

What we do not know yet, so this does not emit it:

  the full object graph, widget bounds, pictures
  tokenized page operands inside handlers
  back-reference compression
  whatever TB80RTM checks before it will open a book

Foolbook's reader opens these. The 8.1 engine would not.
"""

from __future__ import annotations

import struct
from pathlib import Path

MARK = bytes.fromhex("80650005000202")
STUB = 0xC00
# ZZZTBKBOOKLOC, copied from a real book at file 0x9EC:
# dword offset of the book stream, then magic 0x22222222.
LOCATOR = 0x9EC
BOOK_OFF = 0xC00
MAGIC = 0x22222222
# Page property block from 9e954d01 P1: 14 00 00 11, then six words.
PAGE_PROPS = bytes.fromhex("140000110000760068002001000100000000")
# Book-level property tree copied from the real header, 0xC18..0xC80.
BOOK_TREE = bytes.fromhex(
    "1400001100000000"
    "1400001000000000"
    "140000700000000000000000000000000000000000000000"
    "14000090140000b000000000"
    "140000d00000000000000000"
    "140000f00000000000000000"
)


def _script_for(page: dict) -> str:
    lines = ["to handle buttonClick"]
    if page.get("quiz"):
        q = page["quiz"]
        if q.get("next"):
            lines.append(f'  go to page "{q["next"]}"')
    else:
        for it in page.get("items") or []:
            target = it.get("page") or ""
            label = it.get("label") or ""
            if target:
                lines.append(f"  -- {label}")
                lines.append(f'  go to page "{target}"')
    if len(lines) == 1:
        lines.append("  -- end of course")
    lines.append("end")
    return "\n".join(lines) + "\n"


def _record(name: str, oid: int, text: str, script: bytes) -> bytes:
    name_b = (name.encode("ascii", "replace")[:31] + b"\x00").ljust(32, b"\x00")
    body = text.replace("\n", "\r\n")
    if not body.startswith("\r\n"):
        body = "\r\n" + body
    raw = body.encode("latin-1", "replace")
    field = b"Text\x00\x00" + b"\x00" * 8 + struct.pack("<H", len(raw)) + raw
    return MARK + struct.pack("<I", oid) + name_b + PAGE_PROPS + field + b"\x00" + script + b"\x00"


def write_tbk(path: Path, book: dict, compile_script) -> Path:
    path = Path(path)
    stub = bytearray(STUB)
    stub[0:2] = b"MZ"
    # locator the opener searches for: book offset, then 0x22222222
    struct.pack_into("<II", stub, LOCATOR, BOOK_OFF, MAGIC)
    stream = bytearray(bytes.fromhex("034a424f01000008") + b"\x00" * 16)
    stream += BOOK_TREE
    for n, page in enumerate(book.get("pages") or [], start=1):
        text = "\n".join(page.get("text") or [])
        script = compile_script(_script_for(page))
        stream += _record(page.get("id") or f"P{n}", n, text, script)
    path.write_bytes(bytes(stub) + bytes(stream))
    return path
