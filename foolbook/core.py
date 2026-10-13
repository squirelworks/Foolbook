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


def save_fsc(path: str | Path, book: dict, compress: bool = True) -> Path:
    """Write an .fsc."""
    return _formats().save_fsc(Path(path), book, compress=compress)


def export_book(path: str | Path, book: dict, compile_script=None) -> Path:
    """Save a book as whatever the suffix asks for.

    .fbk .fsk .fsc .tbk .sbk .tbx .pdf .ppt .pptx .doc .docx .odt
    .tbx is an expanded folder. .tbk and .sbk are shells.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in ("",) or path.is_dir() or suffix == ".tbx":
        from openscript_analysis.formats.tbx import write_tbx
        return write_tbx(path if suffix == ".tbx" or path.is_dir() else path.with_suffix(".tbx"), book)
    if suffix == ".sbk":
        from openscript_analysis.formats.tbk import write_sbk
        return write_sbk(path, book, compile_script or _compile)
    if suffix == ".tbk":
        from openscript_analysis.formats.tbk import write_tbk
        return write_tbk(path, book, compile_script or _compile)
    if suffix == ".fsk":
        return save_system(path, book)
    if suffix == ".fsc":
        return save_fsc(path, book)
    if suffix in (".fbk", ".json"):
        return save_book(path, book)
    if _office().is_office(path):
        return write_office(path, book)
    raise ValueError(f"cannot save {path.suffix}")


def compile_script(source: str, keywords: list[str] | None = None) -> bytes:
    """Compile OpenScript source to the bytecode a .tbk shell stores."""
    from engine.openscript import compile as compile_source
    return compile_source(source, keywords)


def _compile(source: str, keywords: list[str] | None = None) -> bytes:
    return compile_script(source, keywords)
