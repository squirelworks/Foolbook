"""Playing a media clip.

A click on a `media` shape plays its `src` with an audio player the
platform already has: winsound for a .wav on Windows, afplay on a Mac,
and paplay, pw-play, or aplay (a .wav only) on Linux, when they are on
the PATH. Nothing is installed.

Only a file under the book's folder is played. `src` must be a relative
path made of letters, digits, spaces and `_ . - /`, with no `..` part,
and it must still be under the folder once links are followed. The path
goes to the player as one argument, never through a shell. Anything
else, a file that is not there, or no player for it, puts the reason in
the clip's `note`, which is drawn under the path.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

AUDIO = {".wav", ".aif", ".aiff", ".mp3", ".ogg", ".flac", ".au"}
_LINUX = (("paplay", AUDIO), ("pw-play", AUDIO), ("aplay", {".wav"}))
_PLAIN = re.compile(r"[A-Za-z0-9 _./-]+")


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


def in_book(src: str, base: str | Path | None) -> tuple[Path | None, str]:
    """The file `src` names under the book's folder, or None and why not."""
    src = src.strip()
    if not src:
        return None, "No file named"
    if base is None:
        return None, f"Not beside a saved book: {src}"
    if not _PLAIN.fullmatch(src) or src.startswith("/") or ".." in Path(src).parts:
        return None, f"Not played, outside the book's folder: {src}"
    folder = Path(base).resolve()
    path = (folder / src).resolve()
    if folder not in path.parents:
        return None, f"Not played, outside the book's folder: {src}"
    if not path.is_file():
        return None, f"Not found: {src}"
    return path, ""


def click(shape: dict, base: str | Path | None, players: list | None = None) -> None:
    """Play the clip, or say in `note` why not."""
    src = str(shape.get("src") or "")
    path, why = in_book(src, base)
    if path is None:
        shape["note"] = why
        return
    for player in platform_players() if players is None else players:
        try:
            if player(path):
                shape["note"] = f"Playing {path.name}"
                return
        except Exception:  # a player that breaks is a player that could not play it
            continue
    shape["note"] = f"Cannot play here: {src.strip()}"
