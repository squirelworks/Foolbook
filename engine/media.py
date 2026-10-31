"""A media clip on a Foolbook page.

A `media` shape names a file in `src`, beside the book or absolute. The
page shows the clip as a box with a play mark and the path. A click asks
each player in turn to play it. When none can, or the file is not there,
the clip says so in `note`, on the page. Nothing fails silently.

PLAYERS is empty: this reader does not play media yet. A player is a
function that takes a Path and returns True when it started the clip.
"""

from __future__ import annotations

from pathlib import Path

PLAYERS: list = []


def resolve(shape: dict, base: str | Path | None) -> Path | None:
    src = str(shape.get("src") or "").strip()
    if not src:
        return None
    path = Path(src)
    if not path.is_absolute() and base:
        path = Path(base) / path
    return path


def click(shape: dict, base: str | Path | None, players: list | None = None) -> None:
    """Try to play the clip. `note` says what happened."""
    src = str(shape.get("src") or "").strip()
    path = resolve(shape, base)
    if path is None:
        shape["note"] = "No file named"
        return
    if not path.is_file():
        shape["note"] = f"Not found: {src}"
        return
    for player in PLAYERS if players is None else players:
        try:
            if player(path):
                shape["note"] = f"Playing {path.name}"
                return
        except Exception:  # a player that breaks is a player that could not play it
            continue
    shape["note"] = f"Cannot play here: {src}"
