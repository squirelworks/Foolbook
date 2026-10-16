"""Beside the book server. The `TB80RCR.DLL` role.

Exports only partly named. Not classified. This file stays empty
until a body is read. It is not a guess at what RCR does.
"""

NAME = "rcr"
IMAGE = "TB80RCR.DLL"
BITS = 16
ROLE = "unclassified"


def open():
    return {"image": IMAGE, "classified": False}
