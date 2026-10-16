"""32-bit thunk. The `TB80W32.DLL` role.

The other half of the W16 thunk. ToolBook II 8.1 in this record is
the 16-bit image. This module is the slot a 32-bit Windows host
loads. The body is not ported.
"""

NAME = "w32"
IMAGE = "TB80W32.DLL"
BITS = 32
ROLE = "thunk"


def open():
    return {"image": IMAGE, "body": "not-read"}
