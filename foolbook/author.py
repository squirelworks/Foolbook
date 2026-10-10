"""Optional authoring helper.

Uses the decoder to turn handler bytecode into editable source.
Not on the main viewer path. A future simple authoring tool can call
this and write back into a book model that the loader/engine understand.
"""

from __future__ import annotations

from .decoder import decode


def bytecode_to_source(bytecode: bytes, keywords: list[str] | None = None) -> str:
    """Return readable OpenScript for a handler bytecode stream."""
    return decode(bytecode, keywords)
