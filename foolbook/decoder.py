"""OpenScript bytecode → source.

Thin wrapper around the existing decoder. The decoder itself stays
outside this package so it can be improved independently.
"""

from __future__ import annotations

from pathlib import Path


def decode(bytecode: bytes, keywords: list[str] | None = None) -> str:
    """Decode a handler bytecode stream into source text.

    If keywords is None, attempts to load them from a nearby res_77.bin.
    Returns an empty string on failure.
    """
    if not bytecode:
        return ""
    try:
        from Maybe4.openscript_decode import decode as _decode, load_keywords
    except ImportError:
        try:
            import sys
            root = Path(__file__).resolve().parents[2]
            if str(root) not in sys.path:
                sys.path.insert(0, str(root))
            from Maybe4.openscript_decode import decode as _decode, load_keywords
        except ImportError:
            return ""

    if keywords is None:
        for candidate in (
            Path(__file__).resolve().parents[2] / "Maybe4" / "res_77.bin",
            Path("res_77.bin"),
        ):
            if candidate.exists():
                keywords = load_keywords(candidate)
                break
        if keywords is None:
            return ""

    try:
        return _decode(bytecode, keywords).decode("latin-1", errors="replace")
    except Exception:
        return ""
