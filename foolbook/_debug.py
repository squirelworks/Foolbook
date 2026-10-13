"""Foolbook diagnostics.

  python3 -m foolbook --doctor
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def run() -> int:
    print("Foolbook doctor")
    print(f"  python: {sys.version.split()[0]}")
    print(f"  executable: {sys.executable}")
    here = Path(__file__).resolve().parent
    print(f"  package: {here}")
    for name in ("foolbook", "openscript_analysis", "engine", "viewer"):
        try:
            mod = importlib.import_module(name)
            print(f"  {name}: ok  {getattr(mod, '__file__', '?')}")
        except Exception as e:
            print(f"  {name}: FAIL  {e}")
    book = here / "books" / "using_foolbook.json"
    print(f"  default book: {book}  exists={book.exists()}")
    return 0
