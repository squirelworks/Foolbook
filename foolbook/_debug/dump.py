"""Dump Foolbook diagnostics into _debug/."""

from __future__ import annotations

import importlib
import sys
import traceback
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def dump(note: str = "") -> Path:
    HERE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = HERE / f"{stamp}.txt"
    lines = [
        f"Foolbook debug  {stamp}",
        f"python: {sys.version}",
        f"executable: {sys.executable}",
        f"note: {note}",
        "",
    ]
    for name in ("foolbook", "openscript_analysis", "engine", "viewer"):
        try:
            mod = importlib.import_module(name)
            lines.append(f"{name}: ok  {getattr(mod, '__file__', '?')}")
        except Exception:
            lines.append(f"{name}: FAIL")
            lines.append(traceback.format_exc())
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
