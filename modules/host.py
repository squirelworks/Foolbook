"""Load one module by file. The others stay unloaded."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORDER = ("bas", "rtm", "utl", "rcr", "w16", "w32", "w64", "bmp", "jpg")


def load(name: str, refresh: bool = False):
    if name not in ORDER:
        raise KeyError(name)
    key = f"{__name__}.{name}"
    if key in sys.modules and not refresh:
        return sys.modules[key]
    path = HERE / f"{name}.py"
    if not path.is_file():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location(key, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod
