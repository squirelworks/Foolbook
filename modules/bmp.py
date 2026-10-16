"""Bitmap reader. The TB80BMP role, as far as the bytes identify themselves.

Ordinal 3 is the bitmap reader. Lz77Expand was not ported. A widget
still does not name the bitmap. This file only recognizes a BMP.
"""

NAME = "bmp"
IMAGE = "TB80BMP.DLL"
BITS = 16
ROLE = "bitmap"


def sniff(blob: bytes) -> dict:
    if blob[:2] == b"BM" and len(blob) >= 14:
        size = int.from_bytes(blob[2:6], "little")
        return {"format": "bmp", "size": size, "module": "bmp", "expanded": False}
    return {"format": None, "module": "bmp", "expanded": False}


def open():
    return {"image": IMAGE, "sniff": sniff, "body": "identify"}
