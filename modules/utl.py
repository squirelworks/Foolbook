"""Utilities. The `TB80UTL.DLL` role.

Type-name strings, the string manager, metrics, and the `GHeap`
wrapper. Not the `0x76` object and not the record reader.
"""

NAME = "utl"
IMAGE = "TB80UTL.DLL"
BITS = 16
ROLE = "utilities"


def open():
    from engine.heap import GHeap
    return {"GHeap": GHeap}
