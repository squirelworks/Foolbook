"""The workhorse.

Foolbook reads a book, packs it, and understands the formats.
FoolbookEditor calls this module. It does not keep a second copy
of that work. This module does not edit.
"""

from __future__ import annotations

from pathlib import Path


def _formats():
    from engine import formats
    return formats


def _office():
    from engine import office
    return office


def load(path: str | Path) -> dict:
    """Read an .fbk, .fsk, or .json into the book dict."""
    return _formats().load(Path(path))


def save_book(path: str | Path, book: dict, compress: bool = True) -> Path:
    """Write the .json working copy and the sibling .fbk."""
    return _formats().save_book(Path(path), book, compress=compress)


def save_system(path: str | Path, system: dict, compress: bool = True) -> Path:
    """Write an .fsk."""
    return _formats().save_system(Path(path), system, compress=compress)


def pack(data: dict, kind: str = "fbk", compress: bool = True) -> bytes:
    return _formats().pack(data, kind, compress=compress)


def unpack(blob: bytes) -> dict:
    return _formats().unpack(blob)


def is_office(path: str | Path) -> bool:
    return _office().is_office(path)


def to_book(path: str | Path) -> dict:
    """Read a PDF, PowerPoint, Word, or ODT file as a book dict."""
    return _office().to_book(path)


def write_office(path: str | Path, book: dict) -> Path:
    """Write a book dict back to an office file."""
    return _office().write(path, book)


def compile_script(source: str, keywords: list[str] | None = None) -> bytes:
    """Compile OpenScript source to the bytecode a .tbk shell stores."""
    from engine.openscript import compile as compile_source
    return compile_source(source, keywords)
