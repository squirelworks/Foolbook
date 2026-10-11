"""Intermediate authoring formats.

.fbk is a Foolbook book. It will become a .tbk when the binary format is ready.
.fsk is a Foolbook system book. It will become a .sbk when that format is ready.

Until then both are JSON with a format marker so the structure can evolve
without changing the editor or the loader.
"""

from __future__ import annotations

import json
from pathlib import Path


FBK = "fbk"
FSK = "fsk"
FORMAT_VERSION = 1


def is_book(path: Path) -> bool:
    return path.suffix.lower() in (".fbk", ".json")


def is_system(path: Path) -> bool:
    return path.suffix.lower() == ".fsk"


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("format", "fbk" if path.suffix.lower() == ".fbk" else "json")
    data.setdefault("format_version", FORMAT_VERSION)
    return data


def save_book(path: Path, book: dict) -> Path:
    """Write a .json and a sibling .fbk.

    The .json is the working copy. The .fbk is the intermediate that will
    become a .tbk.
    """
    path = Path(path)
    if path.suffix.lower() != ".json":
        path = path.with_suffix(".json")
    book = dict(book)
    book["format"] = "json"
    book["format_version"] = FORMAT_VERSION
    path.write_text(json.dumps(book, indent=2), encoding="utf-8")

    fbk = path.with_suffix(".fbk")
    fbk_book = dict(book)
    fbk_book["format"] = FBK
    fbk_book["format_version"] = FORMAT_VERSION
    fbk_book["will_become"] = "tbk"
    fbk.write_text(json.dumps(fbk_book, indent=2), encoding="utf-8")
    return path


def save_system(path: Path, system: dict) -> Path:
    """Write a .fsk. It will become a .sbk."""
    path = Path(path)
    if path.suffix.lower() != ".fsk":
        path = path.with_suffix(".fsk")
    system = dict(system)
    system["format"] = FSK
    system["format_version"] = FORMAT_VERSION
    system["will_become"] = "sbk"
    path.write_text(json.dumps(system, indent=2), encoding="utf-8")
    return path
