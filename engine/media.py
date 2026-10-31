"""A media clip on a Foolbook page.

A `media` shape names a file in `src`, beside the book or absolute. The
page shows the clip as a box with a play mark and the path. A click asks
each player in turn to play it. When none can, or the file is not there,
the clip says so in `note`, on the page. Nothing fails silently.

A player is a function that takes a Path and returns True when it
started the clip. PLAYERS is what this platform already has for audio:
winsound for a .wav on Windows, afplay on a Mac, and paplay, pw-play, or
aplay (a .wav only) on Linux, when they are on the PATH. Nothing is
installed. Video is not played; the clip says it cannot.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

AUDIO = {".wav", ".aif", ".aiff", ".mp3", ".ogg", ".flac", ".au"}
_LINUX = (("paplay", AUDIO), ("pw-play", AUDIO), ("aplay", {".wav"}))


def _start(argv: list[str]) -> None:
    subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _command_player(program: str, kinds: set[str], runner):
    def play(path: Path) -> bool:
        if path.suffix.lower() not in kinds:
            return False
        runner([program, str(path)])
        return True
    return play


def _winsound_player(path: Path) -> bool:
    if path.suffix.lower() != ".wav":
        return False
    import winsound
    winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
    return True


def platform_players(platform: str = sys.platform, which=shutil.which, runner=_start) -> list:
    """The audio players this machine already has, best first."""
    if platform.startswith("win"):
        return [_winsound_player]
    if platform == "darwin":
        found = which("afplay")
        return [_command_player(found, AUDIO, runner)] if found else []
    players = []
    for name, kinds in _LINUX:
        found = which(name)
        if found:
            players.append(_command_player(found, kinds, runner))
    return players


PLAYERS: list = platform_players()


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
