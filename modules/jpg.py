"""JPEG. The TB80JPG role.

The version resource still says TB60JPG.DLL. The decoder was not
ported. This file only recognizes the SOI marker, and it will not
call a BMP a JPEG.
"""

NAME = "jpg"
IMAGE = "TB80JPG.DLL"
BITS = 16
ROLE = "jpeg"
OLD_NAME = "TB60JPG.DLL"


def sniff(blob: bytes) -> dict:
    if blob[:2] == b"\xff\xd8":
        return {"format": "jpeg", "module": "jpg", "expanded": False, "old_name": OLD_NAME}
    return {"format": None, "module": "jpg", "expanded": False}


def open():
    return {"image": IMAGE, "sniff": sniff, "body": "identify"}
