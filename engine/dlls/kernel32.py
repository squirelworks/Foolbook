"""kernel32.dll: the private profile (INI) functions.

The INI file is looked for beside the book. A key that is not there gives
the default the script passed, as Windows does. A write is kept for the
session and not written to disk.
"""

from __future__ import annotations

import configparser
from pathlib import Path


def _profile(state, filename: str) -> dict:
    cache = state.variables.setdefault("__profiles", {})
    key = Path(str(filename).replace("\\", "/")).name.lower()
    if key in cache:
        return cache[key]
    sections: dict = {}
    book = getattr(state, "book", None)
    if book is not None and book.path:
        folder = Path(book.path).parent
        for child in (folder.iterdir() if folder.is_dir() else []):
            if child.name.lower() == key and child.is_file():
                parser = configparser.RawConfigParser(strict=False)
                parser.optionxform = str.lower
                try:
                    parser.read_string(child.read_text(encoding="latin-1"))
                except configparser.Error:
                    break
                for section in parser.sections():
                    sections[section.lower()] = dict(parser.items(section))
                break
    cache[key] = sections
    return sections


def _get(state, section, key, filename):
    return _profile(state, filename).get(str(section).lower(), {}).get(str(key).lower())


def get_profile_int(state, args, refs):
    section, key, default, filename = (list(args) + ["", "", 0, ""])[:4]
    found = _get(state, section, key, filename)
    try:
        return int(str(found).strip()) if found is not None else int(default)
    except (TypeError, ValueError):
        return 0


def get_profile_string(state, args, refs):
    section, key, default, _buffer, size, filename = (list(args) + ["", "", "", "", 0, ""])[:6]
    found = _get(state, section, key, filename)
    text = str(default if found is None else found)
    try:
        size = int(size)
    except (TypeError, ValueError):
        size = len(text) + 1
    text = text[:max(size - 1, 0)]
    if len(refs) > 3 and refs[3]:
        state.variables[refs[3]] = text
    return len(text)


def write_profile_string(state, args, refs):
    section, key, value, filename = (list(args) + ["", "", "", ""])[:4]
    _profile(state, filename).setdefault(str(section).lower(), {})[str(key).lower()] = str(value)
    return 1


FUNCTIONS = {
    "getprivateprofileinta": get_profile_int,
    "getprivateprofilestringa": get_profile_string,
    "writeprivateprofilestringa": write_profile_string,
    "getprivateprofileint": get_profile_int,
    "getprivateprofilestring": get_profile_string,
    "writeprivateprofilestring": write_profile_string,
}
